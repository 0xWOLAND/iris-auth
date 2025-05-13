from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, TypedDict, List

import appdirs
import base64
import cv2
import iris
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from iris.io.dataclasses import IrisTemplate


class PasswordEntry(TypedDict):
    username: str
    password: str


@dataclass
class Database:
    templates: Dict[str, Dict[str, Any]]
    passwords: Dict[str, Dict[str, List[PasswordEntry]]]


class IrisPasswordManager:
    def __init__(self, db_path: str = "passwords.enc") -> None:
        app_dir = Path(appdirs.user_data_dir("iris-auth", appauthor=False))
        app_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = app_dir / f"{db_path}.npz"
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37
        self.salt = b'iris_auth_salt' 

    def _derive_key(self, template: Dict[str, Any]) -> bytes:
        """Derive an encryption key from the iris template."""
        template_bytes = np.array(template['iris_codes']).tobytes()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(template_bytes))
        return key

    def _encrypt(self, data: Dict, template: Dict[str, Any]) -> bytes:
        """Encrypt data using a key derived from the iris template."""
        key = self._derive_key(template)
        f = Fernet(key)
        return f.encrypt(str(data).encode())

    def _decrypt(self, data: bytes, template: Dict[str, Any]) -> Dict:
        """Decrypt data using a key derived from the iris template."""
        key = self._derive_key(template)
        f = Fernet(key)
        return eval(f.decrypt(data).decode()) 

    @staticmethod
    def _to_template(t: Dict[str, Any]) -> IrisTemplate:
        return IrisTemplate(
            iris_codes=[np.array(x) for x in t['iris_codes']],
            mask_codes=[np.array(x) for x in t['mask_codes']]
        )

    def _load(self) -> Database:
        """Load templates and passwords from the database file."""
        try:
            data = np.load(self.db_path, allow_pickle=True)
            templates = data['templates'].item() if 'templates' in data else {}
            encrypted_passwords = data['passwords'].item() if 'passwords' in data else {}
            
            # Decrypt passwords using the corresponding template
            passwords = {}
            for user_id, user_passwords in encrypted_passwords.items():
                if user_id in templates:
                    try:
                        key = self._derive_key(templates[user_id])
                        f = Fernet(key)
                        decrypted = eval(f.decrypt(user_passwords).decode())
                        passwords[user_id] = decrypted
                        del decrypted  # Clear decrypted data immediately
                    except Exception:
                        passwords[user_id] = {}
            
            result = Database(templates=templates, passwords=passwords)
            return result
        except Exception:
            return Database(templates={}, passwords={})

    def _store(self, db: Database) -> None:
        """Store templates and passwords in the database file."""
        encrypted_passwords = {}
        for user_id, user_passwords in db.passwords.items():
            if user_id in db.templates:
                encrypted = self._encrypt(user_passwords, db.templates[user_id])
                encrypted_passwords[user_id] = encrypted
                del encrypted  # Clear encrypted data immediately
        
        np.savez(
            self.db_path,
            templates=np.array(db.templates, dtype=object),
            passwords=np.array(encrypted_passwords, dtype=object)
        )
        del encrypted_passwords

    def _load_template_from_image(self, img_path: str) -> Dict[str, Any]:
        """Extract an iris template from an image file."""
        return iris.IRISPipeline()(
            cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE),
            eye_side="left"
        )['iris_template']

    def _find_matching_template(self, template: Dict[str, Any], templates: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Find a matching template in the stored templates."""
        template_obj = self._to_template(template)
        return next(
            (user_id for user_id, stored_template in templates.items()
             if self.matcher.run(template_obj, self._to_template(stored_template)) < self.threshold),
            None
        )

    def register(self, user_id: str, img_path: str) -> None:
        """Register a new user with their iris template."""
        db = self._load()
        if user_id in db.templates:
            raise ValueError(f"User {user_id} already registered")
            
        template = self._load_template_from_image(img_path)
        db.templates[user_id] = template
        self._store(db)
        del template

    def check(self, user_id: Optional[str], img_path: str) -> Tuple[str, Dict[str, Any]]:
        """Verify an iris image against stored templates."""
        template = self._load_template_from_image(img_path)
        db = self._load()
        
        if not db.templates:
            raise ValueError("No users registered")

        if user_id:
            if user_id not in db.templates:
                raise ValueError(f"User {user_id} not found")
                
            stored_template = db.templates[user_id]
            if self.matcher.run(
                self._to_template(template),
                self._to_template(stored_template)
            ) < self.threshold:
                return user_id, stored_template
        else:
            if matching_user := self._find_matching_template(template, db.templates):
                return matching_user, db.templates[matching_user]

        raise ValueError("Authentication failed")

    def get(self, user_id: Optional[str], img_path: str, service: Optional[str] = None) -> Dict[str, List[PasswordEntry]]:
        """Retrieve passwords after iris authentication.
        
        Args:
            user_id: Optional user ID to check against
            img_path: Path to the iris image for authentication
            service: Optional service name to filter passwords by
            
        Returns:
            Dict mapping service names to lists of password entries, or a single service's entries if service is specified
        """
        user_id, _ = self.check(user_id, img_path)
        db = self._load()
        
        if user_id not in db.passwords:
            return {}
            
        passwords = db.passwords[user_id]
        if service is not None:
            result = {service: passwords[service]} if service in passwords else {}
            return result
            
        result = passwords.copy()  # Create a copy to return
        return result

    def set(self, user_id: str, img_path: str, service: str, username: str, password: str) -> None:
        """Save a password for a service using iris authentication.
        
        If a password already exists for the given username and service, it will be overwritten.
        """
        user_id, _ = self.check(user_id, img_path)
        db = self._load()
        
        if user_id not in db.passwords:
            db.passwords[user_id] = {}
        if service not in db.passwords[user_id]:
            db.passwords[user_id][service] = []
            
        # Check if username already exists for this service
        for entry in db.passwords[user_id][service]:
            if entry["username"] == username:
                entry["password"] = password
                self._store(db)
                return
                
        # Add new credentials if username doesn't exist
        db.passwords[user_id][service].append(PasswordEntry(username=username, password=password))
        self._store(db)

    def delete(self, user_id: str, img_path: str, service: str, username: str) -> None:
        """Delete a specific username/password combination for a service.
        
        Args:
            user_id: User ID to authenticate
            img_path: Path to the iris image for authentication
            service: Service name to delete credentials from
            username: Username to delete
            
        Raises:
            ValueError: If authentication fails or if the username doesn't exist for the service
        """
        user_id, _ = self.check(user_id, img_path)
        db = self._load()
        
        if user_id not in db.passwords or service not in db.passwords[user_id]:
            raise ValueError(f"No credentials found for service {service}")
            
        # Find and remove the specific username/password combination
        original_length = len(db.passwords[user_id][service])
        db.passwords[user_id][service] = [
            entry for entry in db.passwords[user_id][service]
            if entry["username"] != username
        ]
        
        if len(db.passwords[user_id][service]) == original_length:
            raise ValueError(f"No credentials found for username {username} in service {service}")
            
        # If no more credentials for this service, remove the service entry
        if not db.passwords[user_id][service]:
            del db.passwords[user_id][service]
            
        self._store(db)

    def clear(self) -> None:
        """Delete the password database file."""
        self.db_path.unlink(missing_ok=True)