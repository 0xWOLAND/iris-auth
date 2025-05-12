import os
from pathlib import Path
from iris_auth.password_manager import IrisPasswordManager

def test_password_manager():
    # Initialize password manager
    pm = IrisPasswordManager("test_passwords.enc")
    
    # Get paths to test images
    dataset_path = Path("dataset")
    person1_folder = dataset_path / "000"  # First person
    person2_folder = dataset_path / "001"  # Second person
    
    # Get first image from each person
    person1_img = str(person1_folder / "S6000S00.jpg")
    person2_img = str(person2_folder / "S6000S00.jpg")
    
    print("\nTesting Password Manager with Real Iris Images")
    print("---------------------------------------------")
    
    try:
        # Test 1: Add password with person1's iris
        print("\nTest 1: Adding password with person1's iris")
        pm.add_password(person1_img, "gmail", "user1@example.com", "secret123")
        print("✓ Successfully added password")
        
        # Test 2: Retrieve password with same person's iris
        print("\nTest 2: Retrieving password with same person's iris")
        passwords = pm.get_passwords(person1_img)
        print(f"Retrieved passwords: {passwords}")
        assert passwords["gmail"]["username"] == "user1@example.com"
        print("✓ Successfully retrieved password")
        
        # Test 3: Try to retrieve with different person's iris
        print("\nTest 3: Attempting to retrieve with different person's iris")
        try:
            pm.get_passwords(person2_img)
            print("✗ Security breach! Different iris was accepted")
        except ValueError as e:
            print("✓ Security check passed: Different iris was rejected")
        
        # Test 4: Add another password with same person
        print("\nTest 4: Adding another password with same person")
        pm.add_password(person1_img, "github", "user1", "github123")
        passwords = pm.get_passwords(person1_img)
        print(f"Retrieved passwords: {passwords}")
        assert len(passwords) == 2
        print("✓ Successfully added and retrieved second password")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
    finally:
        # Cleanup
        if os.path.exists("test_passwords.enc"):
            os.remove("test_passwords.enc")

if __name__ == "__main__":
    test_password_manager() 