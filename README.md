# Iris Auth

A secure iris-based authentication and password management system.

## Installation

```bash
pip install iris-auth
```

## Usage

```python
from iris_auth import IrisPasswordManager

# Initialize password manager
pm = IrisPasswordManager()

# Register a user
pm.register("iris.jpg", "user1")

# Save a password
pm.set("iris.jpg", "user1", "gmail", "user@example.com", "secret123")

# Get all passwords
passwords = pm.get("iris.jpg", "user1")
print(passwords)  # {'gmail': {'username': 'user@example.com', 'password': 'secret123'}}

# Clear all data
pm.clear()
```

## License

MIT
