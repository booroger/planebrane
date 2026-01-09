"""Image preprocessing utilities."""

import cv2
import numpy as np


def preprocess_image(
    image: np.ndarray,
    blur_kernel_size: int = 5,
    normalize: bool = True,
) -> np.ndarray:
    """
    Preprocess image for analysis.
    
    Steps:
    1. Convert to grayscale if color
    2. Apply Gaussian blur to reduce noise
    3. Optionally normalize intensity
    4. Apply histogram equalization for better contrast
    
    Args:
        image: Input image (BGR or grayscale)
        blur_kernel_size: Size of Gaussian blur kernel (must be odd)
        normalize: Whether to normalize pixel intensities
    
    Returns:
        Preprocessed grayscale image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Ensure kernel size is odd
    if blur_kernel_size % 2 == 0:
        blur_kernel_size += 1
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
    
    # Normalize intensity
    if normalize:
        blurred = cv2.normalize(blurred, None, 0, 255, cv2.NORM_MINMAX)
    
    # Histogram equalization for better contrast
    equalized = cv2.equalizeHist(blurred)
    
    return equalized


def resize_for_processing(
    image: np.ndarray,
    max_dimension: int = 1024,
) -> tuple[np.ndarray, float]:
    """
    Resize image for faster processing while maintaining aspect ratio.
    
    Args:
        image: Input image
        max_dimension: Maximum width or height
    
    Returns:
        Tuple of (resized image, scale factor)
    """
    height, width = image.shape[:2]
    
    if max(height, width) <= max_dimension:
        return image, 1.0
    
    if width > height:
        scale = max_dimension / width
        new_width = max_dimension
        new_height = int(height * scale)
    else:
        scale = max_dimension / height
        new_height = max_dimension
        new_width = int(width * scale)
    
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return resized, scale


def apply_morphological_cleanup(
    binary_image: np.ndarray,
    operation: str = "close",
    kernel_size: int = 3,
    iterations: int = 1,
) -> np.ndarray:
    """
    Apply morphological operations to clean up binary images.
    
    Args:
        binary_image: Binary (edge/threshold) image
        operation: One of 'open', 'close', 'dilate', 'erode'
        kernel_size: Size of morphological kernel
        iterations: Number of times to apply operation
    
    Returns:
        Cleaned binary image
    """
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    
    if operation == "open":
        result = cv2.morphologyEx(
            binary_image, cv2.MORPH_OPEN, kernel, iterations=iterations
        )
    elif operation == "close":
        result = cv2.morphologyEx(
            binary_image, cv2.MORPH_CLOSE, kernel, iterations=iterations
        )
    elif operation == "dilate":
        result = cv2.dilate(binary_image, kernel, iterations=iterations)
    elif operation == "erode":
        result = cv2.erode(binary_image, kernel, iterations=iterations)
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return result


def extract_roi(
    image: np.ndarray,
    margin_percent: float = 0.05,
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """
    Extract region of interest by finding non-zero content area.
    
    Args:
        image: Grayscale image
        margin_percent: Margin to add around ROI as percentage of dimensions
    
    Returns:
        Tuple of (cropped image, bounding box as (x, y, w, h))
    """
    # Threshold to find content
    _, thresh = cv2.threshold(image, 10, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return image, (0, 0, image.shape[1], image.shape[0])
    
    # Get bounding box of all contours
    x_min = min(cv2.boundingRect(c)[0] for c in contours)
    y_min = min(cv2.boundingRect(c)[1] for c in contours)
    x_max = max(cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] for c in contours)
    y_max = max(cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] for c in contours)
    
    # Add margin
    height, width = image.shape[:2]
    margin_x = int(width * margin_percent)
    margin_y = int(height * margin_percent)
    
    x_min = max(0, x_min - margin_x)
    y_min = max(0, y_min - margin_y)
    x_max = min(width, x_max + margin_x)
    y_max = min(height, y_max + margin_y)
    
    cropped = image[y_min:y_max, x_min:x_max]
    
    return cropped, (x_min, y_min, x_max - x_min, y_max - y_min)
