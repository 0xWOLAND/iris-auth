import os
from pathlib import Path
import numpy as np
import pytest
from iris_auth import IrisPasswordManager

@pytest.fixture
def pm():
    """Create a fresh password manager instance for each test."""
    pm = IrisPasswordManager("test_passwords.enc")
    pm.clear()
    yield pm
    pm.clear()  # Cleanup after test

@pytest.fixture
def dataset():
    """Provide dataset paths."""
    dataset = Path("dataset")
    return {
        "img1": str(dataset / "000" / "S6000S00.jpg"),
        "img2": str(dataset / "001" / "S6001S00.jpg")
    }

def test_user_registration(pm, dataset):
    """Test user registration functionality."""
    # Test successful registration
    pm.register("user1", dataset["img1"])
    
    # Test duplicate registration
    with pytest.raises(ValueError, match="User user1 already registered"):
        pm.register("user1", dataset["img1"])
    
    # Test registering second user
    pm.register("user2", dataset["img2"])

def test_password_management(pm, dataset):
    """Test basic password management operations."""
    pm.register("user1", dataset["img1"])
    
    # Test adding and retrieving password
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    passwords = pm.get("user1", dataset["img1"])
    assert passwords["gmail"][0]["username"] == "user1@example.com"
    assert passwords["gmail"][0]["password"] == "secret123"

def test_multiple_credentials(pm, dataset):
    """Test managing multiple credentials for the same service."""
    pm.register("user1", dataset["img1"])
    
    # Add first credential
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    
    # Add second credential
    pm.set("user1", dataset["img1"], "gmail", "user1.work@example.com", "work123")
    
    # Verify both credentials exist
    passwords = pm.get("user1", dataset["img1"])
    assert len(passwords["gmail"]) == 2
    assert passwords["gmail"][0]["username"] == "user1@example.com"
    assert passwords["gmail"][1]["username"] == "user1.work@example.com"

def test_password_overwrite(pm, dataset):
    """Test overwriting existing passwords."""
    pm.register("user1", dataset["img1"])
    
    # Add initial password
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    
    # Overwrite password
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "newsecret123")
    
    # Verify password was updated
    passwords = pm.get("user1", dataset["img1"])
    assert passwords["gmail"][0]["password"] == "newsecret123"

def test_password_deletion(pm, dataset):
    """Test deleting specific credentials."""
    pm.register("user1", dataset["img1"])
    
    # Add two credentials
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    pm.set("user1", dataset["img1"], "gmail", "user1.work@example.com", "work123")
    
    # Delete one credential
    pm.delete("user1", dataset["img1"], "gmail", "user1.work@example.com")
    
    # Verify deletion
    passwords = pm.get("user1", dataset["img1"])
    assert len(passwords["gmail"]) == 1
    assert passwords["gmail"][0]["username"] == "user1@example.com"

def test_deletion_errors(pm, dataset):
    """Test error cases for deletion."""
    pm.register("user1", dataset["img1"])
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    
    # Test deleting non-existent credential
    with pytest.raises(ValueError, match="No credentials found for username"):
        pm.delete("user1", dataset["img1"], "gmail", "nonexistent@example.com")
    
    # Test deleting from non-existent service
    with pytest.raises(ValueError, match="No credentials found for service"):
        pm.delete("user1", dataset["img1"], "nonexistent", "user1@example.com")

def test_service_filtering(pm, dataset):
    """Test filtering passwords by service."""
    pm.register("user1", dataset["img1"])
    
    # Add credentials for multiple services
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    pm.set("user1", dataset["img1"], "github", "user1", "github123")
    
    # Test retrieving specific service
    gmail_passwords = pm.get("user1", dataset["img1"], "gmail")
    assert len(gmail_passwords) == 1
    assert "gmail" in gmail_passwords
    assert gmail_passwords["gmail"][0]["username"] == "user1@example.com"
    
    # Test retrieving non-existent service
    empty_password = pm.get("user1", dataset["img1"], "nonexistent")
    assert len(empty_password) == 0

def test_security_measures(pm, dataset):
    """Test security features."""
    pm.register("user1", dataset["img1"])
    pm.register("user2", dataset["img2"])
    
    pm.set("user1", dataset["img1"], "gmail", "user1@example.com", "secret123")
    pm.set("user2", dataset["img2"], "gmail", "user2@example.com", "secret456")
    
    # Test cross-user access prevention
    with pytest.raises(ValueError, match="Authentication failed"):
        pm.get("user2", dataset["img1"])
    
    # Test template modification prevention
    db = pm._load()
    original_template = db.templates["user1"]
    
    pm.set("user1", dataset["img1"], "test", "test", "test")
    db = pm._load()
    current_template = db.templates["user1"]
    
    assert np.array_equal(original_template['iris_codes'], current_template['iris_codes'])
    assert np.array_equal(original_template['mask_codes'], current_template['mask_codes'])