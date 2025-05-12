import cv2
import iris
import json
import base64
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
        key = base64.urlsafe_b64encode(kdf.derive(template.tobytes()))
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
            return iris.IrisTemplate.from_bytes(f.read(1024))
    
    def _save_template(self, template):
        with open(self.db_path, 'wb') as f:
            f.write(template.to_bytes())
    
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

if __name__ == "__main__":
    pm = IrisPasswordManager()
    
    # Example usage
    try:
        # Add a password
        pm.add_password("iris.jpg", "gmail", "user@example.com", "secret123")
        
        # Retrieve passwords
        passwords = pm.get_passwords("iris.jpg")
        print("Stored passwords:", passwords)
    except Exception as e:
        print(f"Error: {e}") 