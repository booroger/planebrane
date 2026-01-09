"""Linear pattern detection."""

import cv2
import numpy as np


def detect_linear_pattern(image: np.ndarray, edge_metrics: dict) -> dict:
    """
    Detect linear patterns: grids, stripes, rectilinear structures.
    
    Args:
        image: Preprocessed grayscale image
        edge_metrics: Edge detection metrics
    
    Returns:
        Detection result with confidence
    """
    confidence = 0.0
    description = ""
    
    # Detect lines using Hough transform
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=30,
        maxLineGap=10,
    )
    
    if lines is None or len(lines) < 3:
        return {
            "type": "linear",
            "subtype": "linear",
            "confidence": 0.0,
            "description": "No significant linear structures detected",
            "details": {},
        }
    
    # Analyze line orientations
    angles = []
    lengths = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        angles.append(angle)
        lengths.append(length)
    
    angles = np.array(angles)
    lengths = np.array(lengths)
    
    # Check for grid pattern (orthogonal lines)
    is_grid, grid_conf = _detect_grid_pattern(angles, lengths)
    
    # Check for stripes (parallel lines)
    is_stripes, stripe_conf, stripe_angle = _detect_stripe_pattern(angles, lengths)
    
    # Determine pattern type
    if is_grid and grid_conf > stripe_conf:
        confidence = grid_conf
        description = "Grid/mesh pattern with orthogonal lines"
        subtype = "grid"
    elif is_stripes:
        confidence = stripe_conf
        orientation = "horizontal" if abs(stripe_angle) < 30 else (
            "vertical" if abs(stripe_angle - 90) < 30 else "diagonal"
        )
        description = f"Stripe pattern with {orientation} orientation"
        subtype = "stripes"
    else:
        # General linear pattern
        confidence = min(len(lines) / 20, 0.6)  # Normalize to 20 lines
        description = f"Linear pattern with {len(lines)} detected lines"
        subtype = "linear"
    
    return {
        "type": "linear",
        "subtype": subtype,
        "confidence": float(round(confidence, 3)),
        "description": description,
        "details": {
            "line_count": len(lines),
            "is_grid": is_grid,
            "is_stripes": is_stripes,
            "dominant_angles": edge_metrics.get("dominant_angles", []),
        },
    }


def _detect_grid_pattern(
    angles: np.ndarray,
    lengths: np.ndarray,
    tolerance: float = 15,
) -> tuple[bool, float]:
    """
    Detect grid pattern by finding orthogonal line groups.
    """
    # Separate lines into horizontal-ish and vertical-ish
    horizontal = np.abs(angles) < tolerance  # Near 0°
    horizontal |= np.abs(angles - 180) < tolerance
    
    vertical = np.abs(angles - 90) < tolerance  # Near 90°
    
    h_count = np.sum(horizontal)
    v_count = np.sum(vertical)
    
    total = len(angles)
    
    # Grid pattern should have both horizontal and vertical lines
    if h_count >= 2 and v_count >= 2:
        # Confidence based on how many lines fit the grid pattern
        grid_ratio = (h_count + v_count) / total
        balance = 1 - abs(h_count - v_count) / (h_count + v_count)
        
        confidence = grid_ratio * 0.6 + balance * 0.4
        return True, float(confidence)
    
    return False, 0.0


def _detect_stripe_pattern(
    angles: np.ndarray,
    lengths: np.ndarray,
    tolerance: float = 15,
) -> tuple[bool, float, float]:
    """
    Detect stripe pattern by finding parallel lines.
    """
    # Cluster angles
    if len(angles) < 3:
        return False, 0.0, 0.0
    
    # Find the most common angle range
    hist, bin_edges = np.histogram(angles, bins=12, range=(0, 180))
    dominant_bin = np.argmax(hist)
    dominant_angle = (bin_edges[dominant_bin] + bin_edges[dominant_bin + 1]) / 2
    
    # Count lines near dominant angle
    near_dominant = np.abs(angles - dominant_angle) < tolerance
    near_dominant |= np.abs(angles - dominant_angle - 180) < tolerance
    near_dominant |= np.abs(angles - dominant_angle + 180) < tolerance
    
    parallel_count = np.sum(near_dominant)
    parallel_ratio = parallel_count / len(angles)
    
    # Stripe pattern needs many parallel lines
    if parallel_ratio > 0.6 and parallel_count >= 3:
        # Weight by line lengths
        parallel_lengths = lengths[near_dominant]
        length_factor = np.mean(parallel_lengths) / (np.mean(lengths) + 1e-10)
        
        confidence = parallel_ratio * 0.7 + min(length_factor, 1.0) * 0.3
        return True, float(confidence), float(dominant_angle)
    
    return False, 0.0, 0.0
