"""Mixed and complex pattern handling."""

import numpy as np


def classify_mixed_pattern(
    image: np.ndarray,
    symmetry: dict,
    edge_metrics: dict,
    candidates: list[dict],
) -> dict:
    """
    Classify complex patterns that don't fit simple categories.
    
    Args:
        image: Preprocessed grayscale image
        symmetry: Symmetry analysis results
        edge_metrics: Edge detection metrics
        candidates: List of other pattern candidates
    
    Returns:
        Classification result for mixed pattern
    """
    # Analyze complexity
    edge_density = edge_metrics.get("edge_density", 0)
    contour_count = edge_metrics.get("contour_count", 0)
    symmetry_score = symmetry.get("symmetry_score", 0)
    
    # Determine description based on features
    features = []
    
    if symmetry.get("has_rotational", False):
        order = symmetry.get("rotational_order", 0)
        if order:
            features.append(f"{order}-fold rotational symmetry")
    
    if symmetry.get("has_reflectional", False):
        axes = symmetry.get("reflection_axes", [])
        if axes:
            features.append(f"reflectional symmetry ({len(axes)} axes)")
    
    if edge_density > 0.05:
        features.append("high detail density")
    
    if contour_count > 50:
        features.append("many structural elements")
    
    # Combine candidate patterns
    if candidates:
        pattern_names = [c.get("type", "unknown") for c in candidates[:2]]
        features.append(f"combines {' and '.join(pattern_names)} elements")
    
    # Build description
    if features:
        description = "Complex pattern with " + ", ".join(features)
    else:
        description = "Complex or abstract pattern"
    
    # Confidence based on our ability to describe it
    confidence = 0.5 + len(features) * 0.1
    confidence = min(confidence, 0.85)
    
    return {
        "type": "mixed",
        "confidence": float(round(confidence, 3)),
        "description": description,
        "details": {
            "symmetry_score": symmetry_score,
            "edge_density": edge_density,
            "contour_count": contour_count,
            "features": features,
        },
    }


def analyze_pattern_complexity(
    image: np.ndarray,
    symmetry: dict,
    edge_metrics: dict,
) -> dict:
    """
    Analyze overall pattern complexity.
    
    Returns metrics useful for 3D generation decisions.
    """
    # Compute various complexity metrics
    
    # Structural complexity
    contour_count = edge_metrics.get("contour_count", 0)
    structural = min(contour_count / 100, 1.0)
    
    # Detail complexity
    edge_density = edge_metrics.get("edge_density", 0)
    detail = min(edge_density * 20, 1.0)
    
    # Geometric complexity (inverse of symmetry)
    symmetry_score = symmetry.get("symmetry_score", 0.5)
    geometric = 1 - symmetry_score
    
    # Angular complexity
    angles = edge_metrics.get("dominant_angles", [])
    angular = min(len(angles) / 6, 1.0)
    
    # Overall complexity
    overall = (
        structural * 0.3 +
        detail * 0.25 +
        geometric * 0.25 +
        angular * 0.2
    )
    
    return {
        "overall": float(round(overall, 3)),
        "structural": float(round(structural, 3)),
        "detail": float(round(detail, 3)),
        "geometric": float(round(geometric, 3)),
        "angular": float(round(angular, 3)),
        "recommended_subdivision": _recommend_subdivision(overall),
        "recommended_smoothing": _recommend_smoothing(detail, symmetry_score),
    }


def _recommend_subdivision(complexity: float) -> int:
    """Recommend subdivision level based on complexity."""
    if complexity < 0.3:
        return 1
    elif complexity < 0.5:
        return 2
    elif complexity < 0.7:
        return 3
    else:
        return 4


def _recommend_smoothing(detail: float, symmetry: float) -> int:
    """Recommend smoothing iterations."""
    # High detail + high symmetry = more smoothing makes sense
    # High detail + low symmetry = less smoothing to preserve features
    
    if symmetry > 0.7:
        base = 3
    elif symmetry > 0.4:
        base = 2
    else:
        base = 1
    
    if detail > 0.6:
        base += 1
    
    return min(base, 5)
