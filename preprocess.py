import os
import cv2
import numpy as np
from typing import Any, Tuple
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
import random
from iris import detect_iris_hough, unwrap_iris


class IrisSegmentation:
    def __init__(self, model_path: str):
        self.model = load_model(model_path)

    def predict(self, image: np.ndarray) -> np.ndarray:
        img = cv2.resize(image, (320, 240)) / 255.0
        img = img[np.newaxis, ...]
        mask = self.model.predict(img, verbose=0)[0]
        return (mask > 0.01).astype(np.uint8)

    def extract(self, image: np.ndarray) -> np.ndarray:
        mask = self.predict(image)
        gray = cv2.cvtColor(cv2.resize(image, (320, 240)), cv2.COLOR_BGR2GRAY)
        return gray * mask.squeeze()

segmenter = IrisSegmentation("models/unet_model.h5")

def process_image(img_path):
    img = cv2.imread(img_path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Segmentation
    seg_mask = segmenter.extract(img)
    seg_mask_resized = cv2.resize(seg_mask, (img_gray.shape[1], img_gray.shape[0]))
    masked = cv2.bitwise_and(img_gray, img_gray, mask=seg_mask_resized)
    
    # Circle detection
    circles = detect_iris_hough(masked)
    if circles is None:
        return None
        
    # Unwrap iris
    unwrapped = unwrap_iris(
        masked,
        (circles['inner_circle']['x'], circles['inner_circle']['y'], circles['inner_circle']['radius']),
        (circles['outer_circle']['x'], circles['outer_circle']['y'], circles['outer_circle']['radius'])
    )
    
    # Ensure consistent dimensions (adjust these values based on your needs)
    if unwrapped is not None:
        unwrapped = cv2.resize(unwrapped, (64, 256))
        return unwrapped
    return None

def load_dataset(
    base_path: str,
    segmenter: Any
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load and process iris image pairs for matching."""
    cache_file = "cache/processed_data.npz"
    
    # Check if cache exists and load it
    if os.path.exists(cache_file):
        print("Loading cached dataset...")
        data = np.load(cache_file)
        return data['X1'], data['X2'], data['y']
    
    total_images = 0
    successful_detections = 0
    
    person_images = {}
    for pid in tqdm(os.listdir(base_path), desc="Processing persons"):
        if not pid.isdigit():
            continue
            
        person_path = os.path.join(base_path, pid)
        valid_images = []
        
        for f in tqdm(os.listdir(person_path), desc=f"Person {pid}", leave=False):
            if not f.endswith('.jpg'):
                continue
                
            total_images += 1
            img_path = os.path.join(person_path, f)
            result = process_image(img_path)
            
            if result is not None:
                successful_detections += 1
                valid_images.append(result)
                
        if valid_images:
            person_images[pid] = valid_images
    
    # Filter out persons with no valid images
    person_images = {k: v for k, v in person_images.items() if len(v) > 0}
    if not person_images:
        raise ValueError("No valid images found after processing")
    
    X1, X2, y = [], [], []
    pids = list(person_images.keys())
    
    # Positive pairs
    for images in tqdm(person_images.values(), desc="Creating positive pairs"):
        for i, j in zip(*np.triu_indices(len(images), k=1)):
            X1.append(images[i])
            X2.append(images[j])
            y.append(1)
    
    # Negative pairs (equal number to positive)
    for _ in tqdm(range(len(X1)), desc="Creating negative pairs"):
        pid1, pid2 = random.sample(pids, 2)
        X1.append(random.choice(person_images[pid1]))
        X2.append(random.choice(person_images[pid2]))
        y.append(0)
    
    # Convert to numpy arrays with explicit shape
    X1 = np.array(X1, dtype=np.float32)
    X2 = np.array(X2, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    
    # Normalize the data
    X1 = X1 / 255.0
    X2 = X2 / 255.0
    
    idx = np.random.permutation(len(X1))
    X1, X2, y = X1[idx], X2[idx], y[idx]
    
    os.makedirs("cache", exist_ok=True)
    np.savez_compressed(cache_file, X1=X1, X2=X2, y=y)
    
    # Print detection statistics
    detection_rate = (successful_detections / total_images) * 100
    print(f"\nCircle Detection Statistics:")
    print(f"Total images processed: {total_images}")
    print(f"Successful detections: {successful_detections}")
    print(f"Detection rate: {detection_rate:.2f}%")
    
    return X1, X2, y

if __name__ == "__main__":
    X1, X2, y = load_dataset("dataset", segmenter)
    print(f"\nFinal dataset shapes - X1: {X1.shape}, X2: {X2.shape}, y: {y.shape}")
