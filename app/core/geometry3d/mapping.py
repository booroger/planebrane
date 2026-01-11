"""Map 2D pattern points to 3D surfaces."""

from typing import List, Literal, Dict, Any, Optional
import numpy as np


def map_points_to_surface(
    vertices: np.ndarray,
    points_2d: List[dict],
    curvature: float = 0.0,
) -> np.ndarray:
    """
    Map 2D pattern points to modulate a 3D surface.

    Args:
        vertices: 3D mesh vertices
        points_2d: List of 2D points with x, y, weight
        curvature: Curvature factor (-1 to 1)

    Returns:
        Modified vertices
    """
    if not points_2d or len(points_2d) == 0:
        return vertices

    modified = vertices.copy()
    displacement_field = _create_displacement_field(points_2d)

    for i, vertex in enumerate(vertices):
        x_2d, y_2d = vertex[0], vertex[1]
        displacement = _sample_displacement(displacement_field, x_2d, y_2d)
        z_offset = displacement * (1 + curvature)
        modified[i, 2] += z_offset * 0.1

    return modified


def _create_displacement_field(points_2d: List[dict]) -> dict:
    """Create a displacement field from 2D points."""
    if not points_2d:
        return {"points": [], "weights": [], "sigma": 0.1}

    points = np.array([[p["x"], p["y"]] for p in points_2d])
    weights = np.array([p.get("weight", 1.0) for p in points_2d])

    if len(points) > 1:
        from scipy.spatial import distance

        dists = distance.pdist(points)
        sigma = np.median(dists) / 2 if len(dists) > 0 else 0.1
    else:
        sigma = 0.1

    return {
        "points": points,
        "weights": weights,
        "sigma": max(sigma, 0.05),
    }


def _sample_displacement(field: dict, x: float, y: float) -> float:
    """Sample displacement at a 2D location using RBF interpolation."""
    points = field["points"]
    weights = field["weights"]
    sigma = field["sigma"]

    if len(points) == 0:
        return 0.0

    query = np.array([x, y])
    total_weight = 0.0
    total_value = 0.0

    for point, weight in zip(points, weights):
        distance_sq = np.sum((query - point) ** 2)
        gaussian = np.exp(-distance_sq / (2 * sigma**2))
        total_weight += gaussian
        total_value += gaussian * weight

    if total_weight > 0:
        return total_value / total_weight
    return 0.0


def project_pattern_to_sphere(
    points_2d: List[dict],
    radius: float = 1.0,
) -> List[tuple]:
    """Project 2D pattern points onto a sphere surface."""
    points_3d = []
    for p in points_2d:
        x, y = p["x"], p["y"]
        denom = 1 + x**2 + y**2
        x3d = 2 * x / denom
        y3d = 2 * y / denom
        z3d = (x**2 + y**2 - 1) / denom
        points_3d.append((x3d * radius, y3d * radius, z3d * radius))
    return points_3d


def project_pattern_to_torus(
    points_2d: List[dict],
    major_radius: float = 1.0,
    minor_radius: float = 0.3,
) -> List[tuple]:
    """Project 2D pattern points onto a torus surface."""
    points_3d = []
    for p in points_2d:
        theta = (p["x"] + 1) * np.pi
        phi = (p["y"] + 1) * np.pi
        x3d = (major_radius + minor_radius * np.cos(phi)) * np.cos(theta)
        y3d = (major_radius + minor_radius * np.cos(phi)) * np.sin(theta)
        z3d = minor_radius * np.sin(phi)
        points_3d.append((x3d, y3d, z3d))
    return points_3d


def project_pattern_to_cylinder(
    points_2d: List[dict],
    radius: float = 1.0,
    height: float = 2.0,
) -> List[tuple]:
    """Project 2D pattern points onto a cylinder surface."""
    points_3d = []
    for p in points_2d:
        theta = (p["x"] + 1) * np.pi
        z = p["y"] * height / 2
        x3d = radius * np.cos(theta)
        y3d = radius * np.sin(theta)
        z3d = z
        points_3d.append((x3d, y3d, z3d))
    return points_3d


def map_image_to_3d(
    image_path: str,
    resolution: int = 128,
    amplitude: float = 1.0,
    threshold_value: int = 128,
    threshold_method: Literal["binary", "adaptive", "otsu"] = "otsu",
    invert: bool = True,
    smoothing_method: Literal["gaussian", "bilinear", "none"] = "gaussian",
    smoothing_strength: float = 2.0,
    use_distance_falloff: bool = True,
    falloff_radius: int = 5,
    steering: Optional[Dict] = None,
) -> dict:
    """
    Convert a 2D image to a 3D topological surface.

    Analyzes the image to determine the best topological family unless overridden.
    """
    import cv2
    from app.core.image_analysis.tracer import (
        threshold_image,
        apply_distance_falloff,
    )
    from app.core.topology.intent import SteeringProfile
    from app.core.topology.analyzer import TopologyAnalyzer
    from app.core.geometry3d.generators import generate_topology_surface

    # Parse Steering Profile
    if steering is None:
        steering_profile = SteeringProfile()
    elif isinstance(steering, dict):
        steering_profile = SteeringProfile(**steering)
    else:
        steering_profile = steering

    # Analyze Intent
    analyzer = TopologyAnalyzer()
    family, confidence = analyzer.analyze(image_path, steering_profile)

    # Load image for displacement map
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Convert to binary
    binary = threshold_image(
        img,
        threshold_value=threshold_value,
        method=threshold_method,
        invert=invert,
    )

    # Create displacement grid
    if use_distance_falloff:
        displacement_grid = apply_distance_falloff(binary, falloff_radius)
    else:
        displacement_grid = binary.astype(np.float32) / 255.0

    # Resize Grid
    if displacement_grid.shape[0] != resolution or displacement_grid.shape[1] != resolution:
        from scipy.ndimage import zoom

        zoom_factors = (
            resolution / displacement_grid.shape[0],
            resolution / displacement_grid.shape[1],
        )
        displacement_grid = zoom(displacement_grid, zoom_factors, order=1)

    # Apply smoothing
    if smoothing_method == "gaussian":
        from scipy import ndimage

        displacement_grid = ndimage.gaussian_filter(displacement_grid, sigma=smoothing_strength)

    # Generate Mesh
    mesh_data = generate_topology_surface(
        displacement_grid=displacement_grid,
        family=family,
        steering=steering_profile,
        resolution=resolution,
        amplitude=amplitude,
    )

    mesh_data["topology_family"] = family
    mesh_data["intent_confidence"] = confidence

    return mesh_data


# Backwards compatibility alias
map_image_to_relief = map_image_to_3d
