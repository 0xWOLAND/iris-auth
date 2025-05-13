// Helper function to convert image to base64
async function imageToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Helper function to show messages
function showMessage(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = isError ? 'error' : 'success';
    setTimeout(() => {
        element.textContent = '';
        element.className = '';
    }, 5000);
}

// Register a new user
async function register() {
    try {
        const userId = document.getElementById('registerUserId').value;
        const imageFile = document.getElementById('registerImage').files[0];
        
        if (!userId || !imageFile) {
            showMessage('registerMessage', 'Please fill in all fields', true);
            return;
        }

        const response = await fetch('/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: userId,
                image: await imageToBase64(imageFile)
            })
        });

        const data = await response.json();
        showMessage('registerMessage', response.ok ? 'Registration successful!' : (data.error || 'Registration failed'), !response.ok);
    } catch (error) {
        showMessage('registerMessage', 'Error: ' + error.message, true);
    }
}

// Set a password
async function setPassword() {
    try {
        const userId = document.getElementById('userId').value;
        const imageFile = document.getElementById('image').files[0];
        const service = document.getElementById('service').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (!userId || !imageFile || !service || !username || !password) {
            showMessage('passwordMessage', 'Please fill in all fields', true);
            return;
        }

        const response = await fetch('/passwords/set', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: userId,
                image: await imageToBase64(imageFile),
                service, username, password
            })
        });

        const data = await response.json();
        if (response.ok) {
            showMessage('passwordMessage', 'Password saved successfully!');
            getPasswords();
        } else {
            showMessage('passwordMessage', data.error || 'Failed to save password', true);
        }
    } catch (error) {
        showMessage('passwordMessage', 'Error: ' + error.message, true);
    }
}

// Delete a password
async function deletePassword() {
    try {
        const userId = document.getElementById('userId').value;
        const imageFile = document.getElementById('image').files[0];
        const service = document.getElementById('service').value;
        const username = document.getElementById('username').value;

        if (!userId || !imageFile || !service || !username) {
            showMessage('passwordMessage', 'Please fill in all fields', true);
            return;
        }

        const response = await fetch('/passwords', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: userId,
                image: await imageToBase64(imageFile),
                service, username
            })
        });

        const data = await response.json();
        if (response.ok) {
            showMessage('passwordMessage', 'Password deleted successfully!');
            getPasswords();
        } else {
            showMessage('passwordMessage', data.error || 'Failed to delete password', true);
        }
    } catch (error) {
        showMessage('passwordMessage', 'Error: ' + error.message, true);
    }
}

// Get passwords
async function getPasswords() {
    try {
        const userId = document.getElementById('userId').value;
        const imageFile = document.getElementById('image').files[0];
        const service = document.getElementById('service').value;

        if (!imageFile) {
            showMessage('passwordMessage', 'Please select an image', true);
            return;
        }

        const imageBase64 = await imageToBase64(imageFile);
        const params = new URLSearchParams({
            user_id: userId,
            service: service,
            image: imageBase64
        });

        const response = await fetch(`/passwords?${params}`, {
            method: 'GET'
        });

        const data = await response.json();
        if (response.ok) {
            document.getElementById('passwordList').textContent = JSON.stringify(data.passwords, null, 2);
            showMessage('passwordMessage', 'Passwords retrieved successfully!');
        } else {
            showMessage('passwordMessage', data.error || 'Failed to get passwords', true);
        }
    } catch (error) {
        showMessage('passwordMessage', 'Error: ' + error.message, true);
    }
}