import cv2
import iris
from iris.io.dataclasses import IrisTemplate
import json
import base64
import numpy as np
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

print(f'iris version: {iris.__version__}')

class IrisPasswordManager:
    def __init__(self, db_path="passwords.enc"):
        # Remove .npz if it's already in the path
        if db_path.endswith('.npz'):
            db_path = db_path[:-4]
        self.db_path = Path(db_path)
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37
        print(f"Initialized with db path: {self.db_path}")

    def _derive_key(self, template: dict):
        iris_bytes = np.array(template.iris_codes).tobytes()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'iris_salt',
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(iris_bytes))
        return Fernet(key)

    def _load(self):
        npz_path = self.db_path.with_suffix('.npz')
        print(f"Attempting to load from: {npz_path}")
        if not npz_path.exists():
            print("No existing database file found")
            return None, {}
        try:
            data = np.load(npz_path, allow_pickle=True)
            print("Loaded data keys:", data.files)
            template = {
                'iris_codes': data['iris_codes'],
                'mask_codes': data['mask_codes']
            }
            passwords = data['passwords'].item() if 'passwords' in data else {}
            print("Loaded passwords:", passwords)
            return template, passwords
        except Exception as e:
            print(f"Failed to load: {e}")
            return None, {}

    def _store(self, template: dict, passwords: dict):
        print("Storing passwords:", passwords)
        try:
            npz_path = self.db_path.with_suffix('.npz')
            np.savez(
                npz_path,
                iris_codes=template['iris_codes'],
                mask_codes=template['mask_codes'],
                passwords=np.array(passwords, dtype=object)
            )
            print("Data stored successfully at:", npz_path)
            # Verify the file exists after saving
            if not npz_path.exists():
                print("WARNING: File was not created!")
            else:
                print("File exists after save, size:", npz_path.stat().st_size)
        except Exception as e:
            print(f"Error storing data: {e}")
            raise

    def _load_template_from_image(self, img_path):
        return iris.IRISPipeline()(cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE), eye_side="left")['iris_template']

    def verify(self, img_path):
        template = self._load_template_from_image(img_path)
        stored_template, _ = self._load()
        if stored_template is None:
            return template
        # Keep as NumPy arrays for validation
        template = IrisTemplate(
            iris_codes=[x for x in template['iris_codes']],
            mask_codes=[x for x in template['mask_codes']]
        )
        stored_template = IrisTemplate(
            iris_codes=[x for x in stored_template['iris_codes']],
            mask_codes=[x for x in stored_template['mask_codes']]
        )
        distance = self.matcher.run(template, stored_template)
        if distance < self.threshold:
            return template
        raise ValueError("Authentication failed")

    def save(self, img_path, service, username, password):
        print(f"\nSaving password for service: {service}")
        template = self.verify(img_path)
        stored_template, passwords = self._load()
        print("Current passwords before save:", passwords)
        if stored_template is None:
            stored_template = {
                'iris_codes': template['iris_codes'],
                'mask_codes': template['mask_codes']
            }
            print("Created new template")

        passwords[service] = {'username': username, 'password': password}
        print("Updated passwords:", passwords)
        self._store(stored_template, passwords)

    def fetch(self, img_path):
        print("\nFetching passwords")
        template = self.verify(img_path)
        _, passwords = self._load()
        print("Retrieved passwords:", passwords)
        return passwords
