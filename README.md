# Iris Auth

A secure iris-based authentication and password management system.

## Installation

```bash
pip install iris-auth
```

## Usage

```python
from iris_auth import IrisPasswordManager

# Initialize the password manager
pm = IrisPasswordManager("passwords.enc")

# Add a password
pm.add_password("iris.jpg", "gmail", "user@example.com", "secret123")

# Retrieve passwords
passwords = pm.get_passwords("iris.jpg")
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Security

This package uses iris biometrics for authentication and encryption. The iris template is used to derive an encryption key using PBKDF2, which is then used to encrypt/decrypt passwords using Fernet symmetric encryption.

## License

MIT
