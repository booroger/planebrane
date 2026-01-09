"""Image analysis engine - main module."""

from typing import Any

import cv2
import numpy as np

from app.core.image_analysis.edge_detection import detect_edges, compute_edge_metrics
from app.core.image_analysis.symmetry import detect_symmetry
from app.core.image_analysis.geometry_extractor import extract_geometry
from app.core.image_analysis.preprocessor import preprocess_image

# Cache for analysis results
_edges_cache: dict[str, dict] = {}
_symmetry_cache: dict[str, dict] = {}
_geometry_cache: dict[str, dict] = {}


async def analyze_image(
    image_path: str,
    edge_threshold_low: int = 50,
    edge_threshold_high: int = 150,
    blur_kernel_size: int = 5,
    detect_symmetry: bool = True,
    extract_geometry: bool = True,
) -> dict[str, Any]:
    """
    Run full analysis pipeline on an image.
    
    Args:
        image_path: Path to the image file
        edge_threshold_low: Lower threshold for Canny edge detection
        edge_threshold_high: Upper threshold for Canny edge detection
        blur_kernel_size: Kernel size for Gaussian blur
        detect_symmetry: Whether to run symmetry detection
        extract_geometry: Whether to extract geometric parameters
    
    Returns:
        Dictionary containing edges, symmetry, and geometry results
    """
    # Load and preprocess image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    preprocessed = preprocess_image(img, blur_kernel_size)
    
    # Edge detection
    edges_result = await run_edge_detection(
        preprocessed,
        edge_threshold_low,
        edge_threshold_high,
    )
    
    results: dict[str, Any] = {"edges": edges_result}
    
    # Symmetry detection
    if detect_symmetry:
        symmetry_result = await run_symmetry_detection(preprocessed)
        results["symmetry"] = symmetry_result
    
    # Geometry extraction
    if extract_geometry:
        geometry_result = await run_geometry_extraction(preprocessed, edges_result)
        results["geometry"] = geometry_result
    
    # Cache results by generating a hash from the path
    import hashlib
    image_id = hashlib.md5(image_path.encode()).hexdigest()[:16]
    _edges_cache[image_id] = edges_result
    if detect_symmetry:
        _symmetry_cache[image_id] = results["symmetry"]
    if extract_geometry:
        _geometry_cache[image_id] = results["geometry"]
    
    return results


async def run_edge_detection(
    preprocessed: np.ndarray,
    threshold_low: int,
    threshold_high: int,
) -> dict:
    """Run edge detection algorithms."""
    # Get edges using Canny
    edges = detect_edges(preprocessed, threshold_low, threshold_high)
    
    # Compute metrics
    metrics = compute_edge_metrics(edges, preprocessed)
    
    return metrics


async def run_symmetry_detection(preprocessed: np.ndarray) -> dict:
    """Run symmetry detection."""
    from app.core.image_analysis.symmetry import detect_symmetry as symmetry_detect
    return symmetry_detect(preprocessed)


async def run_geometry_extraction(
    preprocessed: np.ndarray,
    edges_result: dict,
) -> dict:
    """Extract geometric parameters."""
    from app.core.image_analysis.geometry_extractor import extract_geometry as geo_extract
    return geo_extract(preprocessed, edges_result)


def get_cached_edges(image_id: str) -> dict | None:
    """Get cached edge detection results."""
    return _edges_cache.get(image_id)


def get_cached_symmetry(image_id: str) -> dict | None:
    """Get cached symmetry results."""
    return _symmetry_cache.get(image_id)


def get_cached_geometry(image_id: str) -> dict | None:
    """Get cached geometry results."""
    return _geometry_cache.get(image_id)
