from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import appdirs
import base64
import cv2
import iris
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from iris.io.dataclasses import IrisTemplate

class IrisPasswordManager:
    def __init__(self, db_path: str = "passwords.enc") -> None:
        app_dir = Path(appdirs.user_data_dir("iris-auth", appauthor=False))
        app_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = app_dir / f"{db_path}.npz"
        self.matcher = iris.HammingDistanceMatcher()
        self.threshold = 0.37

    def _derive_key(self, template: Dict[str, Any]) -> Fernet:
        return Fernet(base64.urlsafe_b64encode(
            PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'iris_salt',
                iterations=100_000,
            ).derive(np.array(template['iris_codes']).tobytes())
        ))

    def _load(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Dict[str, str]]]:
        try:
            data = np.load(self.db_path, allow_pickle=True)
            return (
                {'iris_codes': data['iris_codes'], 'mask_codes': data['mask_codes']},
                data['passwords'].item() if 'passwords' in data else {}
            )
        except Exception:
            return None, {}

    def _store(self, template: Dict[str, Any], passwords: Dict[str, Dict[str, str]]) -> None:
        np.savez(self.db_path, **template, passwords=np.array(passwords, dtype=object))

    def _load_template_from_image(self, img_path: str) -> Dict[str, Any]:
        return iris.IRISPipeline()(cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE), eye_side="left")['iris_template']

    def verify(self, img_path: str) -> Dict[str, Any]:
        template = self._load_template_from_image(img_path)
        stored_template, _ = self._load()
        
        if stored_template is None:
            return template

        def to_template(t):
            return IrisTemplate(
                    iris_codes=[np.array(x) for x in t['iris_codes']],
                    mask_codes=[np.array(x) for x in t['mask_codes']]
                )
        
        if self.matcher.run(to_template(template), to_template(stored_template)) < self.threshold:
            return template
            
        raise ValueError("Authentication failed")

    def save(self, img_path: str, service: str, username: str, password: str) -> None:
        template = self.verify(img_path)
        stored_template, passwords = self._load()
        self._store(
            stored_template or {'iris_codes': template['iris_codes'], 'mask_codes': template['mask_codes']},
            {**passwords, service: {'username': username, 'password': password}}
        )

    def fetch(self, img_path: str) -> Dict[str, Dict[str, str]]:
        self.verify(img_path)
        return self._load()[1]
    
    def clear(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()