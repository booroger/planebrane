"""Circular and radial pattern detection."""

import cv2
import numpy as np
from typing import Tuple


def detect_circular_pattern(
    image: np.ndarray,
    symmetry: dict,
    center: Tuple[float, float],
) -> dict:
    """
    Detect circular patterns: spirals, concentric circles, radial symmetry.
    
    Args:
        image: Preprocessed grayscale image
        symmetry: Symmetry analysis results
        center: Detected center point
    
    Returns:
        Detection result with confidence and subtype
    """
    confidence = 0.0
    subtype = "circular"
    description = ""
    
    # Check for rotational symmetry
    has_rotational = symmetry.get("has_rotational", False)
    rotational_order = symmetry.get("rotational_order", 0)
    
    if has_rotational:
        confidence += 0.3
    
    if rotational_order and rotational_order >= 3:
        confidence += 0.2
        description = f"{rotational_order}-fold rotational symmetry"
    
    # Detect concentric circles
    num_circles = _count_concentric_circles(image, center)
    if num_circles >= 2:
        confidence += 0.2
        subtype = "radial"
        description = f"Concentric pattern with {num_circles} rings"
    
    # Detect spiral
    is_spiral, spiral_conf = _detect_spiral(image, center)
    if is_spiral:
        confidence = max(confidence, spiral_conf)
        subtype = "spiral"
        description = "Spiral pattern detected"
    
    # Check circularity of main contour
    circularity = _compute_main_circularity(image)
    if circularity > 0.7:
        confidence += 0.15
    
    # Normalize confidence
    confidence = min(confidence, 1.0)
    
    if not description:
        description = "Circular pattern with radial characteristics"
    
    return {
        "type": "circular",
        "subtype": subtype,
        "confidence": float(round(confidence, 3)),
        "description": description,
        "details": {
            "rotational_order": rotational_order,
            "num_concentric_circles": num_circles,
            "is_spiral": is_spiral,
            "circularity": circularity,
        },
    }


def _count_concentric_circles(
    image: np.ndarray,
    center: Tuple[float, float],
    max_circles: int = 20,
) -> int:
    """Count concentric circles using radial profile analysis."""
    height, width = image.shape[:2]
    cx, cy = center
    
    # Maximum radius
    max_radius = int(min(cx, cy, width - cx, height - cy) * 0.9)
    if max_radius < 20:
        return 0
    
    # Sample radial profile (average intensity at each radius)
    radii = np.arange(5, max_radius)
    profile = []
    
    for r in radii:
        # Sample points around circle
        angles = np.linspace(0, 2 * np.pi, 36, endpoint=False)
        values = []
        for angle in angles:
            x = int(cx + r * np.cos(angle))
            y = int(cy + r * np.sin(angle))
            if 0 <= x < width and 0 <= y < height:
                values.append(image[y, x])
        if values:
            profile.append(np.mean(values))
        else:
            profile.append(0)
    
    profile = np.array(profile)
    
    # Find peaks and valleys (transitions indicate circles)
    from scipy.signal import find_peaks
    
    # Smooth profile
    from scipy.ndimage import gaussian_filter1d
    smoothed = gaussian_filter1d(profile, sigma=2)
    
    # Find peaks
    peaks, _ = find_peaks(smoothed, distance=5, prominence=10)
    valleys, _ = find_peaks(-smoothed, distance=5, prominence=10)
    
    # Number of circles is approximately number of transitions
    num_circles = min(len(peaks), len(valleys), max_circles)
    
    return num_circles


def _detect_spiral(
    image: np.ndarray,
    center: Tuple[float, float],
    threshold: float = 0.6,
) -> Tuple[bool, float]:
    """
    Detect spiral patterns using angle-radius relationship.
    
    Spirals show increasing radius with angle.
    """
    height, width = image.shape[:2]
    cx, cy = center
    
    # Edge detection
    edges = cv2.Canny(image, 50, 150)
    
    # Get edge points
    edge_points = np.argwhere(edges > 0)
    if len(edge_points) < 50:
        return False, 0.0
    
    # Convert to polar coordinates relative to center
    y_coords = edge_points[:, 0]
    x_coords = edge_points[:, 1]
    
    dx = x_coords - cx
    dy = y_coords - cy
    
    radii = np.sqrt(dx**2 + dy**2)
    angles = np.arctan2(dy, dx)
    
    # Sort by angle
    sorted_indices = np.argsort(angles)
    sorted_radii = radii[sorted_indices]
    sorted_angles = angles[sorted_indices]
    
    # Check for monotonic increase/decrease in radius with angle
    # This is characteristic of spirals
    
    # Compute correlation between angle and radius
    if len(sorted_radii) < 10:
        return False, 0.0
    
    # Use Spearman correlation (monotonic relationship)
    from scipy.stats import spearmanr
    correlation, p_value = spearmanr(sorted_angles, sorted_radii)
    
    # Strong correlation indicates spiral
    spiral_confidence = abs(correlation)
    is_spiral = spiral_confidence > threshold
    
    return is_spiral, float(spiral_confidence)


def _compute_main_circularity(image: np.ndarray) -> float:
    """Compute circularity of the main contour."""
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return 0.0
    
    # Get largest contour
    largest = max(contours, key=cv2.contourArea)
    
    area = cv2.contourArea(largest)
    perimeter = cv2.arcLength(largest, True)
    
    if perimeter == 0:
        return 0.0
    
    # Circularity formula: 4πA/P²
    circularity = 4 * np.pi * area / (perimeter ** 2)
    
    return float(min(circularity, 1.0))
