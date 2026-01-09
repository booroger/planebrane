"""Pattern classification system."""

from typing import Any
import numpy as np

# Cache for classification results
_classification_cache: dict[str, dict] = {}


async def classify_pattern(image_id: str, image_path: str) -> dict:
    """
    Classify a pattern into predefined categories.
    
    Args:
        image_id: Unique identifier for the image
        image_path: Path to the image file
    
    Returns:
        Classification result with primary and secondary types
    """
    import cv2
    from app.core.image_analysis.preprocessor import preprocess_image
    from app.core.image_analysis.symmetry import detect_symmetry, find_center_of_rotation
    from app.core.image_analysis.edge_detection import detect_edges, compute_edge_metrics
    
    # Load and preprocess
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    preprocessed = preprocess_image(img)
    
    # Get analysis data
    edges = detect_edges(preprocessed, 50, 150)
    edge_metrics = compute_edge_metrics(edges, preprocessed)
    symmetry = detect_symmetry(preprocessed)
    center = find_center_of_rotation(preprocessed)
    
    # Run classifiers
    from app.core.classification.circular import detect_circular_pattern
    from app.core.classification.polygonal import detect_polygonal_pattern
    from app.core.classification.linear import detect_linear_pattern
    from app.core.classification.mixed import classify_mixed_pattern
    
    # Detect each pattern type
    circular_result = detect_circular_pattern(preprocessed, symmetry, center)
    polygonal_result = detect_polygonal_pattern(preprocessed, edge_metrics)
    linear_result = detect_linear_pattern(preprocessed, edge_metrics)
    
    # Collect all results with confidence
    candidates = []
    
    if circular_result["confidence"] > 0.3:
        candidates.append({
            "type": circular_result["subtype"],
            "confidence": circular_result["confidence"],
            "description": circular_result["description"],
        })
    
    if polygonal_result["confidence"] > 0.3:
        candidates.append({
            "type": polygonal_result["subtype"],
            "confidence": polygonal_result["confidence"],
            "description": polygonal_result["description"],
        })
    
    if linear_result["confidence"] > 0.3:
        candidates.append({
            "type": "linear",
            "confidence": linear_result["confidence"],
            "description": linear_result["description"],
        })
    
    # Sort by confidence
    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    
    # If no strong candidates, classify as mixed
    if not candidates or candidates[0]["confidence"] < 0.5:
        mixed_result = classify_mixed_pattern(
            preprocessed, symmetry, edge_metrics, candidates
        )
        candidates = [mixed_result] + candidates
    
    # Build result
    primary = candidates[0] if candidates else {
        "type": "mixed",
        "confidence": 0.5,
        "description": "Complex or unrecognized pattern",
    }
    
    secondary = candidates[1:4] if len(candidates) > 1 else []
    
    result = {
        "image_id": image_id,
        "primary_type": primary,
        "secondary_types": secondary,
        "symmetry_order": symmetry.get("rotational_order"),
        "complexity_score": _compute_complexity(edge_metrics, symmetry),
        "features": {
            "has_rotational_symmetry": symmetry.get("has_rotational", False),
            "has_reflectional_symmetry": symmetry.get("has_reflectional", False),
            "edge_density": edge_metrics.get("edge_density", 0),
            "contour_count": edge_metrics.get("contour_count", 0),
        },
    }
    
    # Cache the result
    _classification_cache[image_id] = result
    
    return result


def get_cached_classification(image_id: str) -> dict | None:
    """Get cached classification result."""
    return _classification_cache.get(image_id)


def _compute_complexity(edge_metrics: dict, symmetry: dict) -> float:
    """Compute overall pattern complexity score."""
    edge_density = edge_metrics.get("edge_density", 0)
    contour_count = edge_metrics.get("contour_count", 0)
    symmetry_score = symmetry.get("symmetry_score", 0)
    
    # Higher symmetry = more structured = slightly less complex
    complexity = (
        min(edge_density * 10, 0.4) +
        min(contour_count / 50, 0.4) +
        (1 - symmetry_score) * 0.2
    )
    
    return float(round(min(complexity, 1.0), 3))
