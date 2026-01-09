"""Geometric parameter extraction."""

import cv2
import numpy as np
from typing import List, Tuple


def extract_geometry(image: np.ndarray, edges_result: dict) -> dict:
    """
    Extract geometric parameters from an analyzed image.
    
    Args:
        image: Preprocessed grayscale image
        edges_result: Results from edge detection
    
    Returns:
        Dictionary containing geometric parameters
    """
    height, width = image.shape[:2]
    
    # Get bounding box of content
    bounding_box = _get_content_bounding_box(image)
    
    # Find centroid
    centroid = _compute_centroid(image)
    
    # Estimate radius for circular patterns
    radius = _estimate_radius(image, centroid)
    
    # Get dominant angles from edges
    dominant_angles = edges_result.get("dominant_angles", [])
    
    # Detect repetition frequency
    repetition = _detect_repetition_frequency(image)
    
    # Compute complexity score
    complexity = _compute_complexity_score(image, edges_result)
    
    return {
        "bounding_box": bounding_box,
        "centroid": centroid,
        "estimated_radius": radius,
        "dominant_angles": dominant_angles,
        "repetition_frequency": repetition,
        "complexity_score": complexity,
    }


def _get_content_bounding_box(image: np.ndarray) -> Tuple[int, int, int, int]:
    """
    Get bounding box of non-zero content.
    
    Returns:
        Tuple of (x, y, width, height)
    """
    _, thresh = cv2.threshold(image, 10, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return (0, 0, image.shape[1], image.shape[0])
    
    # Get bounding rect of all contours combined
    all_points = np.vstack(contours)
    x, y, w, h = cv2.boundingRect(all_points)
    
    return (int(x), int(y), int(w), int(h))


def _compute_centroid(image: np.ndarray) -> Tuple[float, float]:
    """Compute the centroid of image content."""
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    moments = cv2.moments(thresh)
    
    if moments["m00"] == 0:
        return (image.shape[1] / 2, image.shape[0] / 2)
    
    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]
    
    return (float(cx), float(cy))


def _estimate_radius(
    image: np.ndarray,
    center: Tuple[float, float],
) -> float | None:
    """
    Estimate the radius of a circular pattern.
    
    Uses the average distance from center to edge pixels.
    """
    # Edge detection
    edges = cv2.Canny(image, 50, 150)
    
    # Find edge pixels
    edge_points = np.argwhere(edges > 0)
    
    if len(edge_points) == 0:
        return None
    
    # Calculate distances from center
    cx, cy = center
    distances = np.sqrt(
        (edge_points[:, 1] - cx) ** 2 + (edge_points[:, 0] - cy) ** 2
    )
    
    # Use median distance as estimated radius
    return float(np.median(distances))


def _detect_repetition_frequency(image: np.ndarray) -> int | None:
    """
    Detect repetition frequency using autocorrelation.
    
    Returns:
        Estimated number of repetitions, or None if not detected
    """
    # Compute 2D autocorrelation
    f = np.fft.fft2(image.astype(np.float64))
    autocorr = np.fft.ifft2(f * np.conj(f)).real
    
    # Normalize
    autocorr = autocorr / autocorr.max()
    
    # Find peaks in autocorrelation
    from scipy.signal import find_peaks
    
    # Look at horizontal and vertical slices through center
    h, w = autocorr.shape
    h_slice = autocorr[h // 2, :]
    v_slice = autocorr[:, w // 2]
    
    # Find peaks
    h_peaks, _ = find_peaks(h_slice, height=0.3, distance=10)
    v_peaks, _ = find_peaks(v_slice, height=0.3, distance=10)
    
    # Estimate frequency from peak spacing
    if len(h_peaks) >= 2:
        h_freq = len(h_peaks)
    else:
        h_freq = 0
    
    if len(v_peaks) >= 2:
        v_freq = len(v_peaks)
    else:
        v_freq = 0
    
    freq = max(h_freq, v_freq)
    
    return freq if freq > 0 else None


def _compute_complexity_score(image: np.ndarray, edges_result: dict) -> float:
    """
    Compute a complexity score for the pattern.
    
    Based on:
    - Edge density
    - Contour count
    - Angle variety
    """
    edge_density = edges_result.get("edge_density", 0)
    contour_count = edges_result.get("contour_count", 0)
    angle_count = len(edges_result.get("dominant_angles", []))
    
    # Normalize components
    density_score = min(edge_density * 10, 1.0)  # Typical density is 0.01-0.1
    contour_score = min(contour_count / 100, 1.0)  # Normalize to 100 contours
    angle_score = min(angle_count / 5, 1.0)  # Normalize to 5 angles
    
    # Weighted combination
    complexity = (
        density_score * 0.3 +
        contour_score * 0.4 +
        angle_score * 0.3
    )
    
    return float(round(complexity, 3))


def detect_polygon_shape(contour: np.ndarray) -> dict:
    """
    Detect polygon shape from a contour.
    
    Args:
        contour: OpenCV contour
    
    Returns:
        Dictionary with shape information
    """
    # Approximate polygon
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    num_vertices = len(approx)
    
    # Classify shape
    if num_vertices == 3:
        shape = "triangle"
    elif num_vertices == 4:
        # Check if it's a square or rectangle
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        if 0.95 <= aspect_ratio <= 1.05:
            shape = "square"
        else:
            shape = "rectangle"
    elif num_vertices == 5:
        shape = "pentagon"
    elif num_vertices == 6:
        shape = "hexagon"
    elif num_vertices > 6 and num_vertices < 10:
        shape = "polygon"
    else:
        shape = "circle" if num_vertices >= 10 else "irregular"
    
    # Compute area and perimeter
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    
    # Circularity (1 for perfect circle)
    circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
    
    return {
        "shape": shape,
        "vertices": num_vertices,
        "area": float(area),
        "perimeter": float(perimeter),
        "circularity": float(circularity),
    }


def find_concentric_circles(image: np.ndarray, center: Tuple[float, float]) -> List[float]:
    """
    Detect concentric circles in an image.
    
    Args:
        image: Grayscale image
        center: Expected center point
    
    Returns:
        List of detected radii
    """
    # Use Hough Circle Transform
    circles = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=30,
        minRadius=10,
        maxRadius=min(image.shape) // 2,
    )
    
    if circles is None:
        return []
    
    circles = np.round(circles[0, :]).astype(int)
    
    # Filter circles near the expected center
    cx, cy = center
    radii = []
    
    for x, y, r in circles:
        distance_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        if distance_from_center < r * 0.3:  # Circle center is near expected center
            radii.append(float(r))
    
    return sorted(radii)
