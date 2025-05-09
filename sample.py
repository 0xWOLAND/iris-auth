import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from iris import detect_iris_hough, unwrap_iris
from preprocess import IrisSegmentation


def show_single_image(image_path: str, segmenter):
    img = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Segmentation
    seg_mask = segmenter.extract(img)
    seg_mask_resized = cv2.resize(seg_mask, (img_gray.shape[1], img_gray.shape[0]), interpolation=cv2.INTER_NEAREST)
    masked = cv2.bitwise_and(img_gray, img_gray, mask=seg_mask_resized)

    # Circle detection
    circles = detect_iris_hough(masked)
    if circles is None:
        print("No circles detected.")
        return

    # Draw annotations
    annotated = img_rgb.copy()
    for key, color in zip(['inner_circle', 'outer_circle'], [(0, 255, 0), (255, 0, 0)]):
        c = circles[key]
        cv2.circle(annotated, (int(c['x']), int(c['y'])), int(c['radius']), color, 2)

    # Unwrap
    unwrapped = unwrap_iris(
        masked,
        (circles['inner_circle']['x'], circles['inner_circle']['y'], circles['inner_circle']['radius']),
        (circles['outer_circle']['x'], circles['outer_circle']['y'], circles['outer_circle']['radius']),
    )

    # Plot
    images = [
        ("Original", img_gray, 'gray'),
        ("Segmentation Mask", seg_mask, 'gray'),
        ("Masked Iris", masked, 'gray'),
        ("Annotated", annotated, None),
        ("Unwrapped", unwrapped, 'gray'),
    ]
    plt.figure(figsize=(15, 4))
    for i, (title, im, cmap) in enumerate(images):
        plt.subplot(1, 5, i + 1)
        plt.title(title)
        plt.imshow(im, cmap=cmap)
        plt.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    image_file = sorted([
        f for f in os.listdir("dataset/039") if f.lower().endswith(".jpg")
    ])[0]
    image_path = os.path.join("dataset/039", image_file)

    segmenter = IrisSegmentation("models/unet_model.h5")
    show_single_image(image_path, segmenter)
