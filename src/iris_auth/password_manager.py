import cv2
import iris
import json
import base64
import numpy as np
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class IrisPasswordManager:
    def __init__(self, db_path="passwords.enc"):
        self.db_path = Path(db_path)
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37
        
    def _get_key(self, template):
        # Convert iris template to encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'iris_salt',
            iterations=100000,
        )
        # Convert template dictionary to bytes for key derivation
        template_bytes = np.array(template['iris_codes']).tobytes()
        key = base64.urlsafe_b64encode(kdf.derive(template_bytes))
        return Fernet(key)
    
    def authenticate(self, img_path):
        template = iris.IRISPipeline()(cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE), eye_side="left")['iris_template']
        if not self.db_path.exists():
            return template
        stored_template = self._load_template()
        if self.matcher.run(template, stored_template) < self.threshold:
            return template
        raise ValueError("Authentication failed")
    
    def _load_template(self):
        if not self.db_path.exists():
            return None
        with open(self.db_path, 'rb') as f:
            template_bytes = f.read(1024)
            # Convert bytes back to template dictionary
            template_array = np.frombuffer(template_bytes, dtype=bool)
            template_array = template_array.reshape((32, 32, 2, 2))  # Adjust shape based on your template size
            return {'iris_codes': template_array}
    
    def _save_template(self, template):
        with open(self.db_path, 'wb') as f:
            # Convert template dictionary to bytes
            template_bytes = np.array(template['iris_codes']).tobytes()
            f.write(template_bytes)
    
    def add_password(self, img_path, service, username, password):
        template = self.authenticate(img_path)
        if not self.db_path.exists():
            self._save_template(template)
        
        passwords = self.get_passwords(img_path)
        passwords[service] = {'username': username, 'password': password}
        
        f = self._get_key(template)
        with open(self.db_path, 'ab') as db:
            db.write(f.encrypt(json.dumps(passwords).encode()))
    
    def get_passwords(self, img_path):
        template = self.authenticate(img_path)
        if not self.db_path.exists():
            return {}
        
        f = self._get_key(template)
        with open(self.db_path, 'rb') as db:
            db.seek(1024)  # Skip template
            return json.loads(f.decrypt(db.read())) 