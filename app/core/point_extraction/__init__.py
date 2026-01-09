"""Point extraction module."""

import cv2
import numpy as np
from typing import Any


async def extract_points(
    image_path: str,
    density: float = 1.0,
    threshold: float = 0.5,
    min_distance: int = 10,
    weight_edges: float = 1.0,
    weight_intersections: float = 1.5,
    weight_symmetry: float = 1.2,
    max_points: int = 1000,
) -> list[dict[str, Any]]:
    """
    Extract significant points from an image.
    
    Args:
        image_path: Path to the image file
        density: Point density multiplier
        threshold: Feature importance threshold
        min_distance: Minimum distance between points
        weight_edges: Weight for edge points
        weight_intersections: Weight for intersection points
        weight_symmetry: Weight for symmetry points
        max_points: Maximum number of points to return
    
    Returns:
        List of extracted points with coordinates and metadata
    """
    from app.core.image_analysis.preprocessor import preprocess_image
    from app.core.image_analysis.edge_detection import detect_edges, detect_edge_intersections
    from app.core.image_analysis.symmetry import find_center_of_rotation
    
    # Load and preprocess
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    preprocessed = preprocess_image(img)
    height, width = preprocessed.shape[:2]
    
    # Edge detection
    edges = detect_edges(preprocessed, 50, 150)
    
    # Collect candidate points with weights
    candidates: list[dict] = []
    
    # 1. Edge contour points
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Sample points along contour based on density
        total_points = len(contour)
        step = max(1, int(total_points / (10 * density)))
        
        for i in range(0, total_points, step):
            point = contour[i][0]
            candidates.append({
                "x": float(point[0]),
                "y": float(point[1]),
                "weight": weight_edges,
                "feature_type": "edge",
            })
    
    # 2. Corner points (high importance)
    corners = cv2.goodFeaturesToTrack(
        preprocessed,
        maxCorners=int(200 * density),
        qualityLevel=0.01,
        minDistance=min_distance,
    )
    
    if corners is not None:
        for corner in corners:
            x, y = corner.ravel()
            candidates.append({
                "x": float(x),
                "y": float(y),
                "weight": weight_edges * 1.5,  # Corners are high-value edges
                "feature_type": "corner",
            })
    
    # 3. Intersection points
    intersections = detect_edge_intersections(edges, min_distance)
    for x, y in intersections:
        candidates.append({
            "x": float(x),
            "y": float(y),
            "weight": weight_intersections,
            "feature_type": "intersection",
        })
    
    # 4. Symmetry center point
    center = find_center_of_rotation(preprocessed)
    candidates.append({
        "x": float(center[0]),
        "y": float(center[1]),
        "weight": weight_symmetry * 2,  # Center is very important
        "feature_type": "symmetry_center",
    })
    
    # 5. Radial sample points (if pattern has rotational symmetry)
    radial_points = _sample_radial_points(preprocessed, center, int(50 * density))
    for x, y in radial_points:
        candidates.append({
            "x": float(x),
            "y": float(y),
            "weight": weight_symmetry,
            "feature_type": "radial",
        })
    
    # Apply threshold - filter by weight
    max_weight = max(c["weight"] for c in candidates) if candidates else 1
    threshold_value = threshold * max_weight
    filtered = [c for c in candidates if c["weight"] >= threshold_value]
    
    # Apply minimum distance constraint using non-maximum suppression
    final_points = _non_max_suppression(filtered, min_distance)
    
    # Limit to max_points, prioritizing by weight
    final_points.sort(key=lambda p: p["weight"], reverse=True)
    final_points = final_points[:max_points]
    
    # Normalize weights to [0, 1]
    if final_points:
        max_w = max(p["weight"] for p in final_points)
        for p in final_points:
            p["weight"] = round(p["weight"] / max_w, 3)
    
    return final_points


def _sample_radial_points(
    image: np.ndarray,
    center: tuple[float, float],
    num_points: int,
) -> list[tuple[float, float]]:
    """Sample points along radial lines from center."""
    height, width = image.shape[:2]
    cx, cy = center
    
    max_radius = min(cx, cy, width - cx, height - cy) * 0.9
    if max_radius < 20:
        return []
    
    points = []
    num_angles = max(8, int(num_points / 5))
    points_per_ray = max(3, num_points // num_angles)
    
    for i in range(num_angles):
        angle = 2 * np.pi * i / num_angles
        
        for j in range(points_per_ray):
            r = max_radius * (j + 1) / points_per_ray
            x = cx + r * np.cos(angle)
            y = cy + r * np.sin(angle)
            
            if 0 <= x < width and 0 <= y < height:
                points.append((x, y))
    
    return points


def _non_max_suppression(
    points: list[dict],
    min_distance: int,
) -> list[dict]:
    """Apply non-maximum suppression to enforce minimum distance."""
    if not points:
        return []
    
    # Sort by weight descending
    sorted_points = sorted(points, key=lambda p: p["weight"], reverse=True)
    
    selected = []
    for point in sorted_points:
        # Check distance to all selected points
        is_far_enough = True
        for selected_point in selected:
            dx = point["x"] - selected_point["x"]
            dy = point["y"] - selected_point["y"]
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                is_far_enough = False
                break
        
        if is_far_enough:
            selected.append(point)
    
    return selected
