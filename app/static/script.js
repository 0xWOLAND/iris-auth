let currentImageInput = null;
let stream = null;

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

// Camera functions
async function startCamera(inputId) {
    currentImageInput = inputId;
    const modal = document.getElementById('cameraModal');
    const video = document.getElementById('camera');
    
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        modal.style.display = 'block';
        
        // Add keyboard listener
        document.addEventListener('keydown', handleKeyPress);
    } catch (err) {
        showMessage('passwordMessage', 'Error accessing camera: ' + err.message, true);
    }
}

function handleKeyPress(event) {
    if (event.code === 'Space' && document.getElementById('cameraModal').style.display === 'block') {
        event.preventDefault(); // Prevent page scroll
        captureImage();
    }
}

async function captureImage() {
    const video = document.getElementById('camera');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Convert to blob and create file
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
    const file = new File([blob], 'camera.jpg', { type: 'image/jpeg' });
    
    // Set the file input
    const input = document.getElementById(currentImageInput);
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;
    
    // Clean up
    stopCamera();
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    document.getElementById('cameraModal').style.display = 'none';
    // Remove keyboard listener
    document.removeEventListener('keydown', handleKeyPress);
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

        const imageBase64 = await imageToBase64(imageFile);
        
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                image: imageBase64
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            showMessage('registerMessage', 'Registration successful!');
        } else {
            showMessage('registerMessage', data.error || 'Registration failed', true);
        }
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