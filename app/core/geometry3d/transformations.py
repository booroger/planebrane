"""Mesh transformation operations."""

import numpy as np
from typing import Tuple


def apply_extrusion(
    vertices: np.ndarray,
    normals: np.ndarray,
    depth: float,
) -> np.ndarray:
    """
    Apply extrusion by displacing vertices along their normals.
    
    Args:
        vertices: Mesh vertices
        normals: Vertex normals
        depth: Extrusion depth (multiplier)
    
    Returns:
        Modified vertices
    """
    # Depth of 1.0 means no change
    offset = (depth - 1.0) * 0.5
    return vertices + normals * offset


def apply_subdivision(
    vertices: np.ndarray,
    faces: np.ndarray,
    levels: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Loop subdivision to smooth the mesh.
    
    Args:
        vertices: Mesh vertices
        faces: Mesh faces (triangles)
        levels: Number of subdivision iterations
    
    Returns:
        Tuple of (new_vertices, new_faces)
    """
    current_vertices = vertices.copy()
    current_faces = faces.copy()
    
    for _ in range(levels):
        current_vertices, current_faces = _subdivide_once(
            current_vertices, current_faces
        )
    
    return current_vertices, current_faces


def _subdivide_once(
    vertices: np.ndarray,
    faces: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Perform one iteration of subdivision."""
    edge_midpoints = {}
    new_vertices = list(vertices)
    new_faces = []
    
    def get_midpoint(i1: int, i2: int) -> int:
        key = (min(i1, i2), max(i1, i2))
        if key in edge_midpoints:
            return edge_midpoints[key]
        
        midpoint = (vertices[i1] + vertices[i2]) / 2
        new_idx = len(new_vertices)
        new_vertices.append(midpoint)
        edge_midpoints[key] = new_idx
        
        return new_idx
    
    for face in faces:
        v0, v1, v2 = face
        
        # Get midpoints of edges
        a = get_midpoint(v0, v1)
        b = get_midpoint(v1, v2)
        c = get_midpoint(v2, v0)
        
        # Create 4 new triangles
        new_faces.append([v0, a, c])
        new_faces.append([a, v1, b])
        new_faces.append([c, b, v2])
        new_faces.append([a, b, c])
    
    return np.array(new_vertices), np.array(new_faces)


def apply_smoothing(
    vertices: np.ndarray,
    faces: np.ndarray,
    iterations: int = 3,
    factor: float = 0.5,
) -> np.ndarray:
    """
    Apply Laplacian smoothing to the mesh.
    
    Args:
        vertices: Mesh vertices
        faces: Mesh faces
        iterations: Number of smoothing passes
        factor: Smoothing strength (0-1)
    
    Returns:
        Smoothed vertices
    """
    # Build adjacency information
    adjacency = _build_adjacency(vertices, faces)
    
    smoothed = vertices.copy()
    
    for _ in range(iterations):
        new_positions = np.zeros_like(smoothed)
        
        for i, neighbors in enumerate(adjacency):
            if not neighbors:
                new_positions[i] = smoothed[i]
                continue
            
            # Compute average of neighbors
            neighbor_avg = np.mean(smoothed[list(neighbors)], axis=0)
            
            # Blend between current position and neighbor average
            new_positions[i] = (1 - factor) * smoothed[i] + factor * neighbor_avg
        
        smoothed = new_positions
    
    return smoothed


def _build_adjacency(
    vertices: np.ndarray,
    faces: np.ndarray,
) -> list[set]:
    """Build vertex adjacency list from faces."""
    adjacency = [set() for _ in range(len(vertices))]
    
    for face in faces:
        for i in range(3):
            v = face[i]
            for j in range(3):
                if i != j:
                    adjacency[v].add(face[j])
    
    return adjacency


def apply_twist(
    vertices: np.ndarray,
    axis: str = "z",
    angle_per_unit: float = 0.5,
) -> np.ndarray:
    """
    Apply twist deformation around an axis.
    
    Args:
        vertices: Mesh vertices
        axis: Twist axis ('x', 'y', or 'z')
        angle_per_unit: Radians of twist per unit along axis
    
    Returns:
        Twisted vertices
    """
    twisted = vertices.copy()
    
    axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
    other_axes = [i for i in range(3) if i != axis_idx]
    
# Compute axis center to make twist noticeable for centered meshes
    axis_values = vertices[:, axis_idx]
    axis_min = axis_values.min()
    axis_max = axis_values.max()
    axis_center = (axis_min + axis_max) / 2.0

    for i, vertex in enumerate(vertices):
        # Distance along twist axis determines rotation relative to center
        dist = vertex[axis_idx] - axis_center
        angle = dist * angle_per_unit
        
        # Rotate in the plane perpendicular to axis
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        x = vertex[other_axes[0]]
        y = vertex[other_axes[1]]
        
        twisted[i, other_axes[0]] = x * cos_a - y * sin_a
        twisted[i, other_axes[1]] = x * sin_a + y * cos_a
    
    return twisted


def apply_taper(
    vertices: np.ndarray,
    axis: str = "z",
    start_scale: float = 1.0,
    end_scale: float = 0.5,
) -> np.ndarray:
    """
    Apply taper deformation along an axis.
    
    Args:
        vertices: Mesh vertices
        axis: Taper axis
        start_scale: Scale at axis minimum
        end_scale: Scale at axis maximum
    
    Returns:
        Tapered vertices
    """
    tapered = vertices.copy()
    
    axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
    other_axes = [i for i in range(3) if i != axis_idx]
    
    # Get axis range
    axis_values = vertices[:, axis_idx]
    axis_min = axis_values.min()
    axis_max = axis_values.max()
    axis_range = axis_max - axis_min
    
    if axis_range == 0:
        return vertices
    
    for i, vertex in enumerate(vertices):
        # Interpolation factor (0 at min, 1 at max)
        t = (vertex[axis_idx] - axis_min) / axis_range
        
        # Scale factor
        scale = start_scale + t * (end_scale - start_scale)
        
        # Scale perpendicular components
        for ax in other_axes:
            tapered[i, ax] = vertex[ax] * scale
    
    return tapered


def apply_bend(
    vertices: np.ndarray,
    axis: str = "z",
    bend_angle: float = np.pi / 4,
) -> np.ndarray:
    """
    Apply bend deformation.
    
    Bends the mesh around a perpendicular axis.
    
    Args:
        vertices: Mesh vertices
        axis: Axis along which bending occurs
        bend_angle: Total bend angle in radians
    
    Returns:
        Bent vertices
    """
    bent = vertices.copy()
    
    axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
    
    # Get axis range
    axis_values = vertices[:, axis_idx]
    axis_min = axis_values.min()
    axis_max = axis_values.max()
    axis_range = axis_max - axis_min
    
    if axis_range == 0:
        return vertices
    
    # Bending radius
    radius = axis_range / bend_angle
    
    for i, vertex in enumerate(vertices):
        # Position along bend axis (0 to 1)
        t = (vertex[axis_idx] - axis_min) / axis_range
        
        # Current angle
        angle = t * bend_angle
        
        # New position
        # Bend primarily affects the axis and one perpendicular
        if axis == "z":
            x = vertex[0] + radius * (np.cos(angle) - 1)
            z = axis_min + radius * np.sin(angle)
            bent[i, 0] = x
            bent[i, 2] = z
        elif axis == "y":
            x = vertex[0] + radius * (np.cos(angle) - 1)
            y = axis_min + radius * np.sin(angle)
            bent[i, 0] = x
            bent[i, 1] = y
        else:  # x
            y = vertex[1] + radius * (np.cos(angle) - 1)
            x = axis_min + radius * np.sin(angle)
            bent[i, 1] = y
            bent[i, 0] = x
    
    return bent
