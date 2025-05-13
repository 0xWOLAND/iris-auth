from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, TypedDict

import appdirs
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
    passwords: Dict[str, Dict[str, PasswordEntry]]


class IrisPasswordManager:
    def __init__(self, db_path: str = "passwords.enc") -> None:
        app_dir = Path(appdirs.user_data_dir("iris-auth", appauthor=False))
        app_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = app_dir / f"{db_path}.npz"
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37

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
            passwords = data['passwords'].item() if 'passwords' in data else {}
            return Database(templates=templates, passwords=passwords)
        except Exception:
            return Database(templates={}, passwords={})

    def _store(self, db: Database) -> None:
        """Store templates and passwords in the database file."""
        np.savez(
            self.db_path,
            templates=np.array(db.templates, dtype=object),
            passwords=np.array(db.passwords, dtype=object)
        )

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

    def register(self, img_path: str, user_id: str) -> None:
        """Register a new user with their iris template."""
        db = self._load()
        if user_id in db.templates:
            raise ValueError(f"User {user_id} already registered")
            
        template = self._load_template_from_image(img_path)
        db.templates[user_id] = template
        self._store(db)

    def check(self, img_path: str, user_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
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
                return user_id, template
        else:
            if matching_user := self._find_matching_template(template, db.templates):
                return matching_user, template

        raise ValueError("Authentication failed")

    def set(self, img_path: str, user_id: str, service: str, username: str, password: str) -> None:
        """Save a password for a service using iris authentication."""
        user_id, template = self.check(img_path, user_id)
        db = self._load()
        
        db.templates[user_id] = template
        if user_id not in db.passwords:
            db.passwords[user_id] = {}
        db.passwords[user_id][service] = PasswordEntry(username=username, password=password)
        
        self._store(db)

    def get(self, img_path: str, user_id: Optional[str] = None) -> Dict[str, PasswordEntry]:
        """Retrieve all passwords after iris authentication."""
        user_id, _ = self.check(img_path, user_id)
        return self._load().passwords.get(user_id, {})
    
    def clear(self) -> None:
        """Delete the password database file."""
        self.db_path.unlink(missing_ok=True)