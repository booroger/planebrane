"""Image tracing module for Pixel-to-Vertex Mapping.

Converts 2D crop circle images into binary grids and extracts
plot point coordinates for 3D mesh displacement.
"""

import cv2
import numpy as np
from typing import Literal


def threshold_image(
    image: np.ndarray,
    threshold_value: int = 128,
    method: Literal["binary", "adaptive", "otsu"] = "binary",
    invert: bool = False,
) -> np.ndarray:
    """
    Convert image to binary (black/white) for plot point extraction.

    Args:
        image: Input image (grayscale or BGR)
        threshold_value: Threshold cutoff for binary method (0-255)
        method: Thresholding method:
            - 'binary': Simple threshold
            - 'adaptive': Adaptive thresholding for varying lighting
            - 'otsu': Automatic threshold using Otsu's method
        invert: If True, invert result (background=white, lines=black)

    Returns:
        Binary image where 255 = line pixels, 0 = background
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply thresholding based on method
    if method == "binary":
        _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    elif method == "adaptive":
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )
    elif method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        raise ValueError(f"Unknown threshold method: {method}")

    # Invert if requested (useful when lines are dark on light background)
    if invert:
        binary = cv2.bitwise_not(binary)

    return binary


def extract_plot_points(
    binary_image: np.ndarray,
    normalize: bool = True,
    sample_step: int = 1,
) -> list[tuple[float, float]]:
    """
    Extract coordinates of all non-black pixels (the "ink" lines).

    Args:
        binary_image: Binary image from threshold_image()
        normalize: If True, normalize coordinates to [-1, 1] range
        sample_step: Sample every Nth pixel (for performance on large images)

    Returns:
        List of (x, y) coordinates where lines exist
    """
    height, width = binary_image.shape[:2]

    # Find all non-zero (line) pixels
    # np.argwhere returns (row, col) = (y, x), so we flip
    points_yx = np.argwhere(binary_image > 0)

    if len(points_yx) == 0:
        return []

    # Sample if step > 1
    if sample_step > 1:
        points_yx = points_yx[::sample_step]

    # Convert to (x, y) format
    points = []
    for y, x in points_yx:
        if normalize:
            # Normalize to [-1, 1] range
            nx = (x / (width - 1)) * 2 - 1 if width > 1 else 0.0
            ny = (y / (height - 1)) * 2 - 1 if height > 1 else 0.0
            points.append((float(nx), float(ny)))
        else:
            points.append((float(x), float(y)))

    return points


def create_plot_grid(
    binary_image: np.ndarray,
    grid_resolution: int = 256,
) -> np.ndarray:
    """
    Create a normalized 2D grid of hit/miss values for mesh mapping.

    Resizes the binary image to match mesh resolution for direct lookup.

    Args:
        binary_image: Binary image from threshold_image()
        grid_resolution: Target grid size (e.g., 256x256)

    Returns:
        Float grid [0.0, 1.0] where 1.0 = line pixel
    """
    # Resize to target resolution
    resized = cv2.resize(
        binary_image,
        (grid_resolution, grid_resolution),
        interpolation=cv2.INTER_LINEAR,
    )

    # Normalize to [0, 1] range
    grid = resized.astype(np.float32) / 255.0

    return grid


def apply_distance_falloff(
    binary_image: np.ndarray,
    falloff_radius: int = 5,
) -> np.ndarray:
    """
    Apply distance-based falloff from line pixels.

    Creates a gradient around lines for smoother displacement transitions.

    Args:
        binary_image: Binary image from threshold_image()
        falloff_radius: Maximum distance for falloff effect

    Returns:
        Float image [0.0, 1.0] with gradient falloff from lines
    """
    # Compute distance transform from background to nearest line
    # Invert binary so lines are 0 (foreground for distance transform)
    inverted = cv2.bitwise_not(binary_image)

    # Distance transform gives distance from each pixel to nearest 0 pixel
    distance = cv2.distanceTransform(inverted, cv2.DIST_L2, 5)

    # Normalize and invert: pixels on lines = 1.0, falloff to 0.0
    normalized = 1.0 - np.clip(distance / falloff_radius, 0.0, 1.0)

    return normalized.astype(np.float32)
