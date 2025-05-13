import os
from pathlib import Path
import numpy as np
from iris_auth import IrisPasswordManager

def test_password_manager():
    pm = IrisPasswordManager("test_passwords.enc")
    pm.clear()
    
    dataset = Path("dataset")
    img1 = str(dataset / "000" / "S6000S00.jpg")
    img2 = str(dataset / "001" / "S6001S00.jpg")
    
    try:
        # Register first user
        pm.register("user1", img1)
        
        # Test adding and retrieving password for first user
        pm.set("user1", img1, "gmail", "user1@example.com", "secret123")
        passwords = pm.get("user1", img1)
        assert passwords["gmail"]["username"] == "user1@example.com"
        
        # Test security with different iris
        try:
            pm.get("user1", img2)
            assert False, "Security breach: Different iris was accepted"
        except ValueError:
            pass
        
        # Test multiple passwords for first user
        pm.set("user1", img1, "github", "user1", "github123")
        passwords = pm.get("user1", img1)
        assert len(passwords) == 2
        
        # Test registering second user
        pm.register("user2", img2)
        pm.set("user2", img2, "gmail", "user2@example.com", "secret456")
        passwords = pm.get("user2", img2)
        assert passwords["gmail"]["username"] == "user2@example.com"
        
        # Verify users can't access each other's passwords
        try:
            pm.get("user2", img1)
            assert False, "Security breach: User2 accessed User1's passwords"
        except ValueError:
            pass
            
        # Test duplicate registration
        try:
            pm.register("user1", img1)
            assert False, "Security breach: Duplicate user registration allowed"
        except ValueError:
            pass

        # Test that template cannot be changed after registration
        db = pm._load()
        original_template = db.templates["user1"]
        
        pm.set("user1", img1, "test", "test", "test")
        db = pm._load()
        current_template = db.templates["user1"]
        
        assert np.array_equal(original_template['iris_codes'], current_template['iris_codes']), "Iris codes were changed"
        assert np.array_equal(original_template['mask_codes'], current_template['mask_codes']), "Mask codes were changed"

        pm.clear()
    except Exception as e:
        print(e)
        raise e
    finally:
        # Ensure cleanup even if test fails
        pm.clear()

if __name__ == "__main__":
    test_password_manager() 