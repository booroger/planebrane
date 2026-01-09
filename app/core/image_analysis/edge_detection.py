"""Edge detection algorithms and metrics."""

import cv2
import numpy as np
from scipy import ndimage


def detect_edges(
    preprocessed: np.ndarray,
    threshold_low: int = 50,
    threshold_high: int = 150,
    method: str = "combined",
) -> np.ndarray:
    """
    Detect edges using multiple algorithms and combine results.
    
    Args:
        preprocessed: Preprocessed grayscale image
        threshold_low: Lower threshold for Canny
        threshold_high: Upper threshold for Canny
        method: 'canny', 'sobel', or 'combined'
    
    Returns:
        Binary edge image
    """
    if method == "canny":
        return cv2.Canny(preprocessed, threshold_low, threshold_high)
    
    elif method == "sobel":
        return _sobel_edges(preprocessed)
    
    else:  # combined
        # Canny edges
        canny = cv2.Canny(preprocessed, threshold_low, threshold_high)
        
        # Sobel edges
        sobel = _sobel_edges(preprocessed)
        
        # Combine with weighted average
        combined = cv2.addWeighted(canny, 0.6, sobel, 0.4, 0)
        
        # Threshold to binary
        _, binary = cv2.threshold(combined, 50, 255, cv2.THRESH_BINARY)
        
        return binary


def _sobel_edges(image: np.ndarray) -> np.ndarray:
    """Compute Sobel edge magnitude."""
    # Compute gradients
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    
    # Compute magnitude
    magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    
    # Normalize to 0-255
    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    
    return magnitude.astype(np.uint8)


def compute_edge_metrics(edges: np.ndarray, original: np.ndarray) -> dict:
    """
    Compute various metrics from edge detection results.
    
    Args:
        edges: Binary edge image
        original: Original preprocessed image
    
    Returns:
        Dictionary of edge metrics
    """
    height, width = edges.shape
    total_pixels = height * width
    
    # Count edge pixels
    edge_count = np.count_nonzero(edges)
    edge_density = edge_count / total_pixels
    
    # Find contours
    contours, _ = cv2.findContours(
        edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contour_count = len(contours)
    
    # Compute dominant angles using Hough transform
    dominant_angles = _compute_dominant_angles(edges)
    
    return {
        "edge_count": edge_count,
        "edge_density": float(edge_density),
        "dominant_angles": dominant_angles,
        "contour_count": contour_count,
    }


def _compute_dominant_angles(edges: np.ndarray, top_n: int = 5) -> list[float]:
    """
    Find dominant edge orientations using Hough line detection.
    
    Args:
        edges: Binary edge image
        top_n: Number of dominant angles to return
    
    Returns:
        List of dominant angles in degrees
    """
    # Detect lines using probabilistic Hough transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=30,
        maxLineGap=10,
    )
    
    if lines is None or len(lines) == 0:
        return []
    
    # Compute angles of all lines
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        # Normalize to 0-180 range
        angle = angle % 180
        angles.append(angle)
    
    if not angles:
        return []
    
    # Find dominant angles using histogram
    hist, bin_edges = np.histogram(angles, bins=36, range=(0, 180))
    
    # Get indices of top peaks
    peak_indices = np.argsort(hist)[-top_n:]
    
    # Convert bin indices to angles
    dominant = []
    for idx in peak_indices:
        if hist[idx] > 0:
            angle = (bin_edges[idx] + bin_edges[idx + 1]) / 2
            dominant.append(float(round(angle, 1)))
    
    return sorted(dominant)


def detect_edge_intersections(edges: np.ndarray, min_distance: int = 10) -> list[tuple[int, int]]:
    """
    Detect intersection points in edge image.
    
    Args:
        edges: Binary edge image
        min_distance: Minimum distance between detected intersections
    
    Returns:
        List of (x, y) intersection points
    """
    # Apply skeleton to get thin edges
    from skimage.morphology import skeletonize
    skeleton = skeletonize(edges > 0)
    
    # Define intersection kernels (3x3 patterns that indicate junctions)
    kernels = [
        np.array([[1, 0, 1], [0, 1, 0], [1, 0, 1]]),  # X
        np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]),  # +
        np.array([[1, 0, 1], [0, 1, 0], [0, 1, 0]]),  # Y variants
        np.array([[0, 1, 0], [0, 1, 1], [1, 0, 0]]),  # T variants
    ]
    
    intersections = []
    
    for kernel in kernels:
        # Find matches using hit-or-miss transform approximation
        result = ndimage.convolve(skeleton.astype(np.float64), kernel.astype(np.float64))
        threshold = np.sum(kernel) - 0.5
        matches = np.argwhere(result >= threshold)
        
        for y, x in matches:
            # Check minimum distance from existing points
            is_far_enough = True
            for ex, ey in intersections:
                if np.sqrt((x - ex)**2 + (y - ey)**2) < min_distance:
                    is_far_enough = False
                    break
            
            if is_far_enough:
                intersections.append((int(x), int(y)))
    
    return intersections


def find_contour_hierarchy(edges: np.ndarray) -> dict:
    """
    Analyze contour hierarchy to understand pattern structure.
    
    Returns:
        Dictionary with contour statistics
    """
    contours, hierarchy = cv2.findContours(
        edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if hierarchy is None:
        return {"depth": 0, "outer_count": 0, "inner_count": 0}
    
    hierarchy = hierarchy[0]
    
    # Count depth levels and contour types
    outer_count = 0
    inner_count = 0
    max_depth = 0
    
    for i, h in enumerate(hierarchy):
        # h = [next, prev, child, parent]
        if h[3] == -1:  # No parent = outer contour
            outer_count += 1
        else:
            inner_count += 1
        
        # Calculate depth by traversing parent chain
        depth = 0
        parent = h[3]
        while parent != -1:
            depth += 1
            parent = hierarchy[parent][3]
        max_depth = max(max_depth, depth)
    
    return {
        "depth": max_depth,
        "outer_count": outer_count,
        "inner_count": inner_count,
        "total_contours": len(contours),
    }
