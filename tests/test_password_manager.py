import os
from pathlib import Path
from iris_auth.password_manager import IrisPasswordManager

def test_password_manager():
    pm = IrisPasswordManager("test_passwords.enc")
    dataset = Path("dataset")
    img1 = str(dataset / "000" / "S6000S00.jpg")
    img2 = str(dataset / "001" / "S6000S00.jpg")
    
    try:
        # Test adding and retrieving password
        pm.save(img1, "gmail", "user1@example.com", "secret123")
        passwords = pm.fetch(img1)
        assert passwords["gmail"]["username"] == "user1@example.com"
        
        # Test security with different iris
        try:
            pm.fetch(img2)
            assert False, "Security breach: Different iris was accepted"
        except ValueError:
            pass
        
        # Test multiple passwords
        pm.save(img1, "github", "user1", "github123")
        passwords = pm.fetch(img1)
        assert len(passwords) == 2
        
    finally:
        if os.path.exists("test_passwords.enc"):
            os.remove("test_passwords.enc")

if __name__ == "__main__":
    test_password_manager() 