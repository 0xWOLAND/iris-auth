from flask import Flask, request, jsonify, render_template
import base64
import cv2
import numpy as np
from iris_auth.pm import IrisPasswordManager

app = Flask(__name__)
pm = IrisPasswordManager()

def decode_base64_image(base64_string: str) -> str:
    """Decode base64 image and save temporarily."""
    try:
        # Remove header if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        # Save temporarily
        temp_path = "/tmp/iris_temp.jpg"
        cv2.imwrite(temp_path, img)
        return temp_path
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")

@app.route("/")
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route("/register", methods=["POST"])
def register():
    """Register a new user with their iris template."""
    data = request.json
    if not data or 'user_id' not in data or 'image' not in data:
        return jsonify({"error": "Missing user_id or image"}), 400
    
    try:
        img_path = decode_base64_image(data['image'])
        pm.register(data['user_id'], img_path)
        return jsonify({"message": "User registered successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route("/passwords", methods=["GET"])
def get_passwords():
    """Get passwords for a user."""
    data = request.args
    image = data.get('image')
    
    if not image:
        return jsonify({"error": "Missing image"}), 400
    
    try:
        img_path = decode_base64_image(image)
        user_id = data.get('user_id')  
        service = data.get('service')  
        
        passwords = pm.get(user_id, img_path, service)
        return jsonify({"passwords": passwords}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get passwords: {str(e)}"}), 500

@app.route("/passwords/set", methods=["POST"])
def set_password():
    """Set a password for a service."""
    data = request.json
    required_fields = ['user_id', 'image', 'service', 'username', 'password']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        img_path = decode_base64_image(data['image'])
        pm.set(
            data['user_id'],
            img_path,
            data['service'],
            data['username'],
            data['password']
        )
        return jsonify({"message": "Password set successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to set password: {str(e)}"}), 500

@app.route("/passwords", methods=["DELETE"])
def delete_password():
    """Delete a password for a service."""
    data = request.json
    required_fields = ['user_id', 'image', 'service', 'username']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        img_path = decode_base64_image(data['image'])
        pm.delete(
            data['user_id'],
            img_path,
            data['service'],
            data['username']
        )
        return jsonify({"message": "Password deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete password: {str(e)}"}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
