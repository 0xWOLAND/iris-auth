import cv2
import numpy as np
from typing import Optional, Dict, Tuple

def detect_iris_hough(
    image: np.ndarray,
    dp: float = 1.0,
    min_dist: int = 80,
    param1: float = 20,
    param2: float = 30,
    min_radius: int = 70,
    max_radius: int = 150,
) -> Optional[Dict[str, Dict[str, int]]]:
    """
    Detect pupil and iris using Hough transform and return their parameters and mask.
    """
    smoothed = cv2.GaussianBlur(image, (9, 9), 3)
    mask = np.zeros_like(image, dtype=np.uint8)

    # Detect pupil (inner circle)
    pupil_circles = cv2.HoughCircles(
        smoothed,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=min_dist // 2,
        param1=param1,
        param2=param2 // 2,
        minRadius=20,
        maxRadius=50,
    )

    if pupil_circles is None:
        print("No pupil circles detected")
        return None

    pupil = np.uint16(np.around(pupil_circles))[0][0]
    ix, iy, ir = int(pupil[0]), int(pupil[1]), int(pupil[2])

    # Region of interest for outer circle
    pad = max_radius + 20
    y1, y2 = max(0, iy - pad), min(image.shape[0], iy + pad)
    x1, x2 = max(0, ix - pad), min(image.shape[1], ix + pad)
    roi = smoothed[y1:y2, x1:x2]

    outer_circles = cv2.HoughCircles(
        roi,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if outer_circles is None:
        print("No outer circles detected")
        return None

    outer = np.uint16(np.around(outer_circles))[0][0]
    ox, oy = int(outer[0]) + x1, int(outer[1]) + y1
    orad = int(outer[2])

    # Generate binary mask
    cv2.circle(mask, (ix, iy), ir, 0, -1)          # black pupil
    cv2.circle(mask, (ox, oy), orad, 255, -1)      # white iris region

    # Refine mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    _, bright_mask = cv2.threshold(image, np.percentile(image, 80), 255, cv2.THRESH_BINARY)
    mask[bright_mask == 255] = 0

    eyelash_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, eyelash_kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, eyelash_kernel)

    return {
        "inner_circle": {"x": ix, "y": iy, "radius": ir},
        "outer_circle": {"x": ox, "y": oy, "radius": orad},
        "mask": mask
    }


def unwrap_iris(
    eye: np.ndarray,
    inner: Tuple[int, int, int],
    outer: Tuple[int, int, int],
    width: int = 360,
) -> np.ndarray:
    """
    Unwrap iris region between inner and outer circles into a rectangular strip.
    Uses the rubber sheet model with remapping.
    """
    ix, iy, ir = inner
    ox, oy, orad = outer

    height = orad - ir

    if eye.ndim == 3:
        eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)

    # Create θ and r grids
    theta = np.linspace(0, 2 * np.pi, width)
    r = np.linspace(0, 1, height)

    # 2D grid
    theta_grid, r_grid = np.meshgrid(theta, r)

    # Interpolate centers
    cx = ix + r_grid * (ox - ix)
    cy = iy + r_grid * (oy - iy)

    # Interpolate radii
    rad = ir + r_grid * (orad - ir)

    # Convert to cartesian
    map_x = cx + rad * np.cos(theta_grid)
    map_y = cy + rad * np.sin(theta_grid)

    # Map to image
    map_x = map_x.astype(np.float32)
    map_y = map_y.astype(np.float32)

    unwrapped = cv2.remap(eye, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return unwrapped