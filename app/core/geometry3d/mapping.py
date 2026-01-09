"""Map 2D pattern points to 3D surfaces."""

import numpy as np
from typing import List


def map_points_to_surface(
    vertices: np.ndarray,
    points_2d: List[dict],
    curvature: float = 0.0,
) -> np.ndarray:
    """
    Map 2D pattern points to modulate a 3D surface.
    
    Uses the 2D pattern to create displacement on the 3D surface.
    
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
    
    # Create a displacement field from 2D points
    displacement_field = _create_displacement_field(points_2d)
    
    # For each 3D vertex, sample the displacement field
    for i, vertex in enumerate(vertices):
        # Project vertex to 2D (using x, y for simplicity)
        # This works well for shapes that have clear projection planes
        x_2d, y_2d = vertex[0], vertex[1]
        
        # Sample displacement
        displacement = _sample_displacement(displacement_field, x_2d, y_2d)
        
        # Apply displacement along vertex normal
        # For simple case, displace along z-axis modulated by curvature
        z_offset = displacement * (1 + curvature)
        
        modified[i, 2] += z_offset * 0.1  # Scale factor
    
    return modified


def _create_displacement_field(points_2d: List[dict]) -> dict:
    """
    Create a displacement field from 2D points.
    
    Uses weighted Gaussian interpolation.
    """
    if not points_2d:
        return {"points": [], "weights": [], "sigma": 0.1}
    
    points = np.array([[p["x"], p["y"]] for p in points_2d])
    weights = np.array([p.get("weight", 1.0) for p in points_2d])
    
    # Compute characteristic distance for Gaussian kernel
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
    """
    Sample displacement at a 2D location using RBF interpolation.
    """
    points = field["points"]
    weights = field["weights"]
    sigma = field["sigma"]
    
    if len(points) == 0:
        return 0.0
    
    # Compute weighted sum of Gaussians
    query = np.array([x, y])
    
    total_weight = 0.0
    total_value = 0.0
    
    for point, weight in zip(points, weights):
        distance_sq = np.sum((query - point) ** 2)
        gaussian = np.exp(-distance_sq / (2 * sigma ** 2))
        
        total_weight += gaussian
        total_value += gaussian * weight
    
    if total_weight > 0:
        return total_value / total_weight
    return 0.0


def project_pattern_to_sphere(
    points_2d: List[dict],
    radius: float = 1.0,
) -> List[tuple]:
    """
    Project 2D pattern points onto a sphere surface.
    
    Uses stereographic projection.
    
    Args:
        points_2d: List of 2D points with x, y in [-1, 1] range
        radius: Sphere radius
    
    Returns:
        List of 3D (x, y, z) coordinates on sphere
    """
    points_3d = []
    
    for p in points_2d:
        x, y = p["x"], p["y"]
        
        # Stereographic projection
        # Maps plane to sphere (north pole at infinity)
        denom = 1 + x**2 + y**2
        
        x3d = 2 * x / denom
        y3d = 2 * y / denom
        z3d = (x**2 + y**2 - 1) / denom
        
        # Scale to radius
        points_3d.append((x3d * radius, y3d * radius, z3d * radius))
    
    return points_3d


def project_pattern_to_torus(
    points_2d: List[dict],
    major_radius: float = 1.0,
    minor_radius: float = 0.3,
) -> List[tuple]:
    """
    Project 2D pattern points onto a torus surface.
    
    Uses angular mapping: x -> theta, y -> phi
    
    Args:
        points_2d: List of 2D points with x, y in [-1, 1] range
        major_radius: Distance from center to ring center
        minor_radius: Ring tube radius
    
    Returns:
        List of 3D (x, y, z) coordinates on torus
    """
    points_3d = []
    
    for p in points_2d:
        # Map x to theta (around major axis)
        theta = (p["x"] + 1) * np.pi  # Maps [-1, 1] to [0, 2π]
        
        # Map y to phi (around minor axis)
        phi = (p["y"] + 1) * np.pi  # Maps [-1, 1] to [0, 2π]
        
        # Torus parametric equations
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
    """
    Project 2D pattern points onto a cylinder surface.
    
    Args:
        points_2d: List of 2D points with x, y in [-1, 1] range
        radius: Cylinder radius
        height: Cylinder height
    
    Returns:
        List of 3D (x, y, z) coordinates on cylinder
    """
    points_3d = []
    
    for p in points_2d:
        # Map x to theta (angle around cylinder)
        theta = (p["x"] + 1) * np.pi  # Maps [-1, 1] to [0, 2π]
        
        # Map y to z (height)
        z = p["y"] * height / 2  # Maps [-1, 1] to [-h/2, h/2]
        
        # Cylinder parametric equations
        x3d = radius * np.cos(theta)
        y3d = radius * np.sin(theta)
        z3d = z
        
        points_3d.append((x3d, y3d, z3d))
    
    return points_3d
