import os
from pathlib import Path
from iris_auth import IrisPasswordManager

def test_password_manager():
    pm = IrisPasswordManager("test_passwords.enc")
    dataset = Path("dataset")
    img1 = str(dataset / "000" / "S6000S00.jpg")
    img2 = str(dataset / "001" / "S6001S00.jpg")
    
    try:
        # Register first user
        pm.register(img1, "user1")
        
        # Test adding and retrieving password for first user
        pm.set(img1, "user1", "gmail", "user1@example.com", "secret123")
        passwords = pm.get(img1, "user1")
        assert passwords["gmail"]["username"] == "user1@example.com"
        
        # Test security with different iris
        try:
            pm.get(img2, "user1")
            assert False, "Security breach: Different iris was accepted"
        except ValueError:
            pass
        
        # Test multiple passwords for first user
        pm.set(img1, "user1", "github", "user1", "github123")
        passwords = pm.get(img1, "user1")
        assert len(passwords) == 2
        
        # Test registering second user
        pm.register(img2, "user2")
        pm.set(img2, "user2", "gmail", "user2@example.com", "secret456")
        passwords = pm.get(img2, "user2")
        assert passwords["gmail"]["username"] == "user2@example.com"
        
        # Verify users can't access each other's passwords
        try:
            pm.get(img1, "user2")
            assert False, "Security breach: User2 accessed User1's passwords"
        except ValueError:
            pass
            
        # Test duplicate registration
        try:
            pm.register(img1, "user1")
            assert False, "Security breach: Duplicate user registration allowed"
        except ValueError:
            pass
            
        pm.clear()
    except Exception as e:
        print(e)
        raise e

if __name__ == "__main__":
    test_password_manager() 