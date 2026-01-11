"""Symmetry detection algorithms."""

import cv2
import numpy as np
from scipy import ndimage
from typing import Tuple, List


def detect_symmetry(image: np.ndarray) -> dict:
    """
    Detect various types of symmetry in an image.
    
    Detects:
    - Rotational symmetry (and order)
    - Reflectional symmetry (horizontal, vertical, diagonal)
    - Center of rotation
    
    Args:
        image: Preprocessed grayscale image
    
    Returns:
        Dictionary containing symmetry analysis results
    """
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    
    # Detect rotational symmetry
    has_rotational, rotational_order, rot_center, rot_score = _detect_rotational_symmetry(image)
    
    # Detect reflectional symmetry
    has_reflectional, reflection_axes = _detect_reflectional_symmetry(image)
    
    # Compute overall symmetry score
    symmetry_score = _compute_symmetry_score(rot_score, len(reflection_axes))
    
    return {
        "has_rotational": has_rotational,
        "rotational_order": rotational_order,
        "rotational_center": rot_center,
        "has_reflectional": has_reflectional,
        "reflection_axes": reflection_axes,
        "symmetry_score": symmetry_score,
    }


def _detect_rotational_symmetry(
    image: np.ndarray,
    angles_to_test: list[int] = [30, 45, 60, 72, 90, 120, 180],
    threshold: float = 0.85,
) -> Tuple[bool, int | None, Tuple[float, float] | None, float]:
    """
    Detect rotational symmetry by comparing image with rotated versions.
    
    Args:
        image: Grayscale image
        angles_to_test: Rotation angles to test (divisors of 360)
        threshold: Correlation threshold for symmetry detection
    
    Returns:
        Tuple of (has_symmetry, order, center, best_score)
    """
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    
    # Ensure uint8 input for OpenCV thresholding
    img_u8 = _to_uint8(image)

    # Find centroid of content as potential center
    _, thresh = cv2.threshold(img_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    moments = cv2.moments(thresh)

    if moments["m00"] != 0:
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        content_center = (cx, cy)
    else:
        content_center = center
    
    best_order = None
    best_score = 0.0
    
    for angle in angles_to_test:
        # Compute how many rotations of this angle fit in 360
        order = 360 // angle

        # Rotate image (use uint8 input for warpAffine)
        rotation_matrix = cv2.getRotationMatrix2D(content_center, angle, 1.0)
        rotated_u8 = cv2.warpAffine(
            img_u8, rotation_matrix, (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

        # Convert back to float for correlation
        rotated = rotated_u8.astype(np.float64)

        # Compute correlation
        correlation = _compute_image_correlation(image.astype(np.float64), rotated)

        if correlation > best_score:
            best_score = correlation
            best_order = order
    
    has_symmetry = best_score >= threshold
    
    return (
        has_symmetry,
        best_order if has_symmetry else None,
        content_center if has_symmetry else None,
        float(best_score),
    )


def _detect_reflectional_symmetry(
    image: np.ndarray,
    threshold: float = 0.85,
) -> Tuple[bool, List[float]]:
    img_u8 = _to_uint8(image)
    """
    Detect reflectional (mirror) symmetry.
    
    Tests horizontal, vertical, and diagonal axes.
    
    Args:
        image: Grayscale image
        threshold: Correlation threshold
    
    Returns:
        Tuple of (has_symmetry, list of axis angles in degrees)
    """
    axes = []
    
    # Test horizontal axis (flip vertically)
    flipped_h = cv2.flip(img_u8, 0)
    if _compute_image_correlation(image.astype(np.float64), flipped_h.astype(np.float64)) >= threshold:
        axes.append(0.0)  # Horizontal axis

    # Test vertical axis (flip horizontally)
    flipped_v = cv2.flip(img_u8, 1)
    if _compute_image_correlation(image.astype(np.float64), flipped_v.astype(np.float64)) >= threshold:
        axes.append(90.0)  # Vertical axis
    
    # Test diagonal axes
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    
    for angle in [45, 135]:
        # Rotate, flip, rotate back
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rot_back_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        
        rotated = cv2.warpAffine(image, rot_matrix, (width, height))
        flipped = cv2.flip(rotated, 1)
        rotated_back = cv2.warpAffine(flipped, rot_back_matrix, (width, height))
        
        if _compute_image_correlation(image, rotated_back) >= threshold:
            axes.append(float(angle))
    
    return len(axes) > 0, axes


def _compute_image_correlation(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compute normalized cross-correlation between two images.
    
    Args:
        img1, img2: Grayscale images of same size
    
    Returns:
        Correlation coefficient in range [0, 1]
    """
    # Convert to float
    f1 = img1.astype(np.float64)
    f2 = img2.astype(np.float64)
    
    # Guard against zero-variance images
    if f1.std() < 1e-8 or f2.std() < 1e-8:
        return 0.0
    
    # Normalize
    f1 = (f1 - f1.mean()) / (f1.std() + 1e-10)
    f2 = (f2 - f2.mean()) / (f2.std() + 1e-10)
    
    # Compute correlation
    correlation = np.mean(f1 * f2)
    
    # Clamp to [0, 1]
    return float(max(0, min(1, (correlation + 1) / 2)))



def _to_uint8(image: np.ndarray) -> np.ndarray:
    """Convert image to uint8 safely for OpenCV operations."""
    if image.dtype == np.uint8:
        return image
    im = image.copy()
    if im.max() <= 1.0:
        im = (im * 255.0).clip(0, 255).astype(np.uint8)
    else:
        im = im.clip(0, 255).astype(np.uint8)
    return im


def _compute_symmetry_score(rotation_score: float, num_reflection_axes: int) -> float:
    """
    Compute overall symmetry score.
    
    Args:
        rotation_score: Rotational symmetry correlation
        num_reflection_axes: Number of detected reflection axes
    
    Returns:
        Overall symmetry score in [0, 1]
    """
    # Weight rotational symmetry more heavily
    rot_component = rotation_score * 0.6
    
    # Reflection contribution (max 4 axes: h, v, 2 diagonals)
    ref_component = (num_reflection_axes / 4) * 0.4
    
    return float(rot_component + ref_component)


def find_center_of_rotation(image: np.ndarray) -> Tuple[float, float]:
    """
    Find the center of rotation for radial patterns.
    
    Uses moment-based centroid detection.
    
    Args:
        image: Grayscale image
    
    Returns:
        (x, y) coordinates of rotation center
    """
    # Threshold to binary
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Compute moments
    moments = cv2.moments(thresh)
    
    if moments["m00"] == 0:
        # Fall back to image center
        return (image.shape[1] / 2, image.shape[0] / 2)
    
    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]
    
    return (float(cx), float(cy))


def detect_radial_pattern(image: np.ndarray, center: Tuple[float, float]) -> dict:
    """
    Analyze radial characteristics of a pattern.
    
    Args:
        image: Grayscale image
        center: Center point for radial analysis
    
    Returns:
        Dictionary with radial pattern analysis
    """
    height, width = image.shape[:2]
    cx, cy = center
    
    # Convert to polar coordinates
    max_radius = int(min(cx, cy, width - cx, height - cy))
    
    if max_radius < 10:
        return {"is_radial": False, "num_arms": 0, "periodicity": 0}
    
    # Sample along radial lines
    num_angles = 360
    angles = np.linspace(0, 2 * np.pi, num_angles, endpoint=False)
    
    radial_profiles = []
    for angle in angles:
        profile = []
        for r in range(1, max_radius):
            x = int(cx + r * np.cos(angle))
            y = int(cy + r * np.sin(angle))
            if 0 <= x < width and 0 <= y < height:
                profile.append(image[y, x])
        radial_profiles.append(profile)
    
    # Analyze angular periodicity
    min_len = min(len(p) for p in radial_profiles)
    profiles_array = np.array([p[:min_len] for p in radial_profiles])
    
    # Compute autocorrelation of angular samples
    mean_profile = profiles_array.mean(axis=1)
    autocorr = np.correlate(mean_profile, mean_profile, mode="full")
    autocorr = autocorr[len(autocorr) // 2:]
    
    # Find peaks in autocorrelation
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(autocorr, height=autocorr.max() * 0.5, distance=10)
    
    num_arms = len(peaks) if len(peaks) > 0 else 0
    periodicity = 360 // num_arms if num_arms > 0 else 0
    
    return {
        "is_radial": num_arms >= 2,
        "num_arms": num_arms,
        "periodicity": periodicity,
    }
