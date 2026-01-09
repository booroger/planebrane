"""Polygonal pattern detection."""

import cv2
import numpy as np
from collections import Counter


def detect_polygonal_pattern(image: np.ndarray, edge_metrics: dict) -> dict:
    """
    Detect polygonal patterns: triangles, squares, hexagons, stars.
    
    Args:
        image: Preprocessed grayscale image
        edge_metrics: Edge detection metrics
    
    Returns:
        Detection result with confidence and subtype
    """
    confidence = 0.0
    subtype = "polygonal"
    description = ""
    
    # Find contours
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return {
            "type": "polygonal",
            "subtype": subtype,
            "confidence": 0.0,
            "description": "No polygonal structures detected",
            "details": {},
        }
    
    # Analyze polygon shapes
    shape_counts = Counter()
    vertex_counts = []
    
    for contour in contours:
        if cv2.contourArea(contour) < 100:  # Skip small contours
            continue
        
        shape_info = _classify_contour_shape(contour)
        if shape_info:
            shape_counts[shape_info["shape"]] += 1
            vertex_counts.append(shape_info["vertices"])
    
    # Determine dominant shape
    if shape_counts:
        dominant_shape, count = shape_counts.most_common(1)[0]
        
        # Map shapes to pattern types
        shape_to_subtype = {
            "triangle": "triangular",
            "square": "square",
            "rectangle": "rectangular",
            "pentagon": "pentagonal",
            "hexagon": "hexagonal",
            "star": "star",
            "polygon": "polygonal",
        }
        
        subtype = shape_to_subtype.get(dominant_shape, "polygonal")
        
        # Confidence based on dominance and count
        total_shapes = sum(shape_counts.values())
        dominance_ratio = count / total_shapes if total_shapes > 0 else 0
        
        confidence = min(0.5 + dominance_ratio * 0.4, 0.9)
        
        description = f"{dominant_shape.capitalize()} pattern with {count} instances"
    
    # Check for star patterns specifically
    star_conf = _detect_star_pattern(image, edge_metrics)
    if star_conf > confidence:
        confidence = star_conf
        subtype = "star"
        description = "Star pattern detected"
    
    # Analyze dominant angles
    dominant_angles = edge_metrics.get("dominant_angles", [])
    angle_signature = _analyze_angle_signature(dominant_angles)
    
    if angle_signature:
        confidence = max(confidence, angle_signature["confidence"])
        if angle_signature["pattern"] and not description:
            description = angle_signature["description"]
    
    return {
        "type": "polygonal",
        "subtype": subtype,
        "confidence": float(round(confidence, 3)),
        "description": description or "Polygonal pattern detected",
        "details": {
            "shape_counts": dict(shape_counts),
            "dominant_angles": dominant_angles,
            "average_vertices": np.mean(vertex_counts) if vertex_counts else 0,
        },
    }


def _classify_contour_shape(contour: np.ndarray) -> dict | None:
    """Classify a contour as a specific polygon shape."""
    # Approximate polygon
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    num_vertices = len(approx)
    
    if num_vertices < 3:
        return None
    
    # Compute convexity
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    contour_area = cv2.contourArea(contour)
    
    solidity = contour_area / hull_area if hull_area > 0 else 0
    
    # Classify
    if num_vertices == 3:
        shape = "triangle"
    elif num_vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        if 0.9 <= aspect_ratio <= 1.1:
            shape = "square"
        else:
            shape = "rectangle"
    elif num_vertices == 5:
        shape = "pentagon"
    elif num_vertices == 6:
        shape = "hexagon"
    elif num_vertices >= 8 and solidity < 0.7:
        # Star shapes have low solidity (concave)
        shape = "star"
    elif num_vertices < 12:
        shape = "polygon"
    else:
        return None  # Too many vertices, likely a circle
    
    return {
        "shape": shape,
        "vertices": num_vertices,
        "solidity": solidity,
    }


def _detect_star_pattern(image: np.ndarray, edge_metrics: dict) -> float:
    """
    Detect star patterns using corner detection and radial analysis.
    """
    # Use Harris corner detection
    corners = cv2.cornerHarris(image.astype(np.float32), 2, 3, 0.04)
    corners = cv2.dilate(corners, None)
    
    # Threshold corners
    threshold = 0.01 * corners.max()
    corner_points = np.argwhere(corners > threshold)
    
    if len(corner_points) < 5:
        return 0.0
    
    # Check if corners are arranged radially
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    
    # Calculate angles from center
    angles = []
    for y, x in corner_points:
        angle = np.arctan2(y - center[1], x - center[0])
        angles.append(angle)
    
    angles = np.array(angles)
    
    # Check for regular angular spacing (indicative of star)
    angles_sorted = np.sort(angles)
    diffs = np.diff(angles_sorted)
    
    if len(diffs) < 4:
        return 0.0
    
    # Regular star has consistent angle differences
    std_dev = np.std(diffs)
    mean_diff = np.mean(diffs)
    
    if mean_diff == 0:
        return 0.0
    
    regularity = 1 - min(std_dev / mean_diff, 1.0)
    
    # Star confidence based on regularity and number of points
    num_points = len(corner_points)
    point_factor = min(num_points / 10, 1.0)  # Normalize to 10 points
    
    confidence = regularity * 0.7 + point_factor * 0.3
    
    return float(confidence)


def _analyze_angle_signature(dominant_angles: list[float]) -> dict | None:
    """
    Analyze dominant angles to identify pattern type.
    
    Common signatures:
    - 90° dominant: Square/rectangular
    - 60°/120°: Hexagonal
    - 72°: Pentagonal
    - 45°: Diagonal/diamond
    """
    if not dominant_angles:
        return None
    
    angles = np.array(dominant_angles)
    
    # Check for specific angle patterns
    patterns = [
        (90, "square", "Square/grid pattern - 90° angles dominant"),
        (60, "hexagonal", "Hexagonal pattern - 60° angles dominant"),
        (120, "hexagonal", "Hexagonal pattern - 120° angles dominant"),
        (72, "pentagonal", "Pentagonal pattern - 72° angles dominant"),
        (45, "diagonal", "Diagonal/diamond pattern - 45° angles dominant"),
    ]
    
    for target_angle, pattern, description in patterns:
        # Check if any dominant angle is close to target
        close_angles = np.abs(angles - target_angle) < 10  # 10° tolerance
        close_angles |= np.abs(angles - (180 - target_angle)) < 10
        
        if np.any(close_angles):
            return {
                "pattern": pattern,
                "confidence": 0.6,
                "description": description,
            }
    
    return None
