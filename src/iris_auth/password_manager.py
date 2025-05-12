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
from typing import Dict, Optional, Tuple, Any

class IrisPasswordManager:
    def __init__(self, db_path: str = "passwords.enc") -> None:
        self.db_path = Path(db_path).with_suffix('.npz')
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37

    def _derive_key(self, template: Dict[str, Any]) -> Fernet:
        iris_bytes = np.array(template['iris_codes']).tobytes()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'iris_salt',
            iterations=100_000,
        )
        return Fernet(base64.urlsafe_b64encode(kdf.derive(iris_bytes)))

    def _load(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Dict[str, str]]]:
        if not self.db_path.exists():
            return None, {}
        
        try:
            data = np.load(self.db_path, allow_pickle=True)
            template = {
                'iris_codes': data['iris_codes'],
                'mask_codes': data['mask_codes']
            }
            passwords = data['passwords'].item() if 'passwords' in data else {}
            return template, passwords
        except Exception:
            return None, {}

    def _store(self, template: Dict[str, Any], passwords: Dict[str, Dict[str, str]]) -> None:
        np.savez(
            self.db_path,
            iris_codes=template['iris_codes'],
            mask_codes=template['mask_codes'],
            passwords=np.array(passwords, dtype=object)
        )

    def _load_template_from_image(self, img_path: str) -> Dict[str, Any]:
        return iris.IRISPipeline()(
            cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE),
            eye_side="left"
        )['iris_template']

    def verify(self, img_path: str) -> Dict[str, Any]:
        template = self._load_template_from_image(img_path)
        stored_template, _ = self._load()
        
        if stored_template is None:
            return template

        template_obj = IrisTemplate(
            iris_codes=[np.array(x) for x in template['iris_codes']],
            mask_codes=[np.array(x) for x in template['mask_codes']]
        )
        stored_template_obj = IrisTemplate(
            iris_codes=[np.array(x) for x in stored_template['iris_codes']],
            mask_codes=[np.array(x) for x in stored_template['mask_codes']]
        )
        
        if self.matcher.run(template_obj, stored_template_obj) < self.threshold:
            return template
            
        raise ValueError("Authentication failed")

    def save(self, img_path: str, service: str, username: str, password: str) -> None:
        template = self.verify(img_path)
        stored_template, passwords = self._load()
        
        if stored_template is None:
            stored_template = {
                'iris_codes': template['iris_codes'],
                'mask_codes': template['mask_codes']
            }

        passwords[service] = {'username': username, 'password': password}
        self._store(stored_template, passwords)

    def fetch(self, img_path: str) -> Dict[str, Dict[str, str]]:
        self.verify(img_path)
        _, passwords = self._load()
        return passwords
