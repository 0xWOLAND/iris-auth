# Iris Auth

A secure password manager that uses iris biometrics for authentication.

## Usage

```python
from iris_auth import IrisPasswordManager

# Initialize the password manager
pm = IrisPasswordManager()

# Register a new user
pm.register("user1", "path/to/iris/image.jpg")

# Store a password
pm.set("user1", "path/to/iris/image.jpg", "gmail", "user1@example.com", "secret123")

# Retrieve passwords
passwords = pm.get("user1", "path/to/iris/image.jpg")
# Or get passwords for a specific service
gmail_passwords = pm.get("user1", "path/to/iris/image.jpg", "gmail")

# Delete a specific username/password combination
pm.delete("user1", "path/to/iris/image.jpg", "gmail", "user1@example.com")

# Clear the database
pm.clear()
```

## Interface

### register

Register a new user with their iris template.

`register(user_id: str, img_path: str) -> None`

- `user_id`: Unique identifier for the user
- `img_path`: Path to the iris image file

**Raises:**
- `ValueError`: If the user is already registered

### get

Retrieve passwords after iris authentication.

`get(user_id: Optional[str], img_path: str, service: Optional[str] = None) -> Dict[str, List[PasswordEntry]]`

- `user_id`: Optional user ID to check against
- `img_path`: Path to the iris image for authentication
- `service`: Optional service name to filter passwords by

**Returns:**
- Dictionary mapping service names to lists of password entries
- If service is specified, returns only that service's entries
- Returns empty dict if no passwords found

### set

Save a password for a service using iris authentication.

`set(user_id: str, img_path: str, service: str, username: str, password: str) -> None`

- `user_id`: User ID to authenticate
- `img_path`: Path to the iris image for authentication
- `service`: Service name to store password for
- `username`: Username for the service
- `password`: Password to store

**Note:**
- If a password already exists for the given username and service, it will be overwritten

### delete

Delete a specific username/password combination for a service.

`delete(user_id: str, img_path: str, service: str, username: str) -> None`

- `user_id`: User ID to authenticate
- `img_path`: Path to the iris image for authentication
- `service`: Service name to delete credentials from
- `username`: Username to delete

**Raises:**
- `ValueError`: If authentication fails, service not found, or username doesn't exist

### clear

Delete the password database file.

## Testing 
You will need to download [CASIA-Irisv4](https://hycasia.github.io/dataset/casia-irisv4/) into `/dataset`.

## License

MIT
