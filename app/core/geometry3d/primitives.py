"""3D primitive shape generators."""

import numpy as np
from typing import Tuple


def create_sphere(
    radius: float = 1.0,
    subdivisions: int = 2,
    center: Tuple[float, float, float] = (0, 0, 0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create an icosphere mesh.
    
    Uses icosahedron subdivision for uniform vertex distribution.
    
    Args:
        radius: Sphere radius
        subdivisions: Number of subdivision iterations
        center: Center point
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    # Golden ratio for icosahedron
    phi = (1 + np.sqrt(5)) / 2
    
    # Icosahedron vertices
    vertices = np.array([
        [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
        [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
        [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
    ], dtype=np.float64)
    
    # Normalize to unit sphere
    vertices = vertices / np.linalg.norm(vertices[0])
    
    # Icosahedron faces
    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ])
    
    # Subdivide
    for _ in range(subdivisions):
        vertices, faces = _subdivide_icosphere(vertices, faces)
    
    # Scale and translate
    vertices = vertices * radius + np.array(center)
    
    # Normals point outward from center
    normals = vertices - np.array(center)
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
    
    return vertices, faces, normals


def _subdivide_icosphere(
    vertices: np.ndarray,
    faces: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Subdivide icosphere faces."""
    edge_midpoints = {}
    new_vertices = list(vertices)
    new_faces = []
    
    def get_midpoint(i1: int, i2: int) -> int:
        key = (min(i1, i2), max(i1, i2))
        if key in edge_midpoints:
            return edge_midpoints[key]
        
        midpoint = (vertices[i1] + vertices[i2]) / 2
        midpoint = midpoint / np.linalg.norm(midpoint)  # Project to sphere
        
        new_idx = len(new_vertices)
        new_vertices.append(midpoint)
        edge_midpoints[key] = new_idx
        
        return new_idx
    
    for v0, v1, v2 in faces:
        a = get_midpoint(v0, v1)
        b = get_midpoint(v1, v2)
        c = get_midpoint(v2, v0)
        
        new_faces.append([v0, a, c])
        new_faces.append([v1, b, a])
        new_faces.append([v2, c, b])
        new_faces.append([a, b, c])
    
    return np.array(new_vertices), np.array(new_faces)


def create_torus(
    major_radius: float = 1.0,
    minor_radius: float = 0.3,
    segments: int = 32,
    ring_segments: int = 16,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a torus mesh.
    
    Args:
        major_radius: Distance from center to ring center
        minor_radius: Ring tube radius
        segments: Number of segments around the ring
        ring_segments: Number of segments in each ring
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    vertices = []
    normals = []
    
    for i in range(segments):
        theta = 2 * np.pi * i / segments
        
        # Center of this ring segment
        ring_center = np.array([
            major_radius * np.cos(theta),
            major_radius * np.sin(theta),
            0,
        ])
        
        for j in range(ring_segments):
            phi = 2 * np.pi * j / ring_segments
            
            # Offset from ring center
            local = np.array([
                minor_radius * np.cos(phi) * np.cos(theta),
                minor_radius * np.cos(phi) * np.sin(theta),
                minor_radius * np.sin(phi),
            ])
            
            vertex = ring_center + local
            vertices.append(vertex)
            
            # Normal points from ring center to vertex
            normal = local / minor_radius
            normals.append(normal)
    
    vertices = np.array(vertices)
    normals = np.array(normals)
    
    # Create faces
    faces = []
    for i in range(segments):
        next_i = (i + 1) % segments
        
        for j in range(ring_segments):
            next_j = (j + 1) % ring_segments
            
            v0 = i * ring_segments + j
            v1 = i * ring_segments + next_j
            v2 = next_i * ring_segments + next_j
            v3 = next_i * ring_segments + j
            
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])
    
    return vertices, np.array(faces), normals


def create_cube(
    size: float = 2.0,
    center: Tuple[float, float, float] = (0, 0, 0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a cube mesh.
    
    Args:
        size: Side length of the cube
        center: Center point
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    half = size / 2
    cx, cy, cz = center
    
    vertices = np.array([
        [cx - half, cy - half, cz - half],
        [cx + half, cy - half, cz - half],
        [cx + half, cy + half, cz - half],
        [cx - half, cy + half, cz - half],
        [cx - half, cy - half, cz + half],
        [cx + half, cy - half, cz + half],
        [cx + half, cy + half, cz + half],
        [cx - half, cy + half, cz + half],
    ])
    
    # Faces (triangulated)
    faces = np.array([
        # Front
        [0, 1, 2], [0, 2, 3],
        # Back
        [5, 4, 7], [5, 7, 6],
        # Left
        [4, 0, 3], [4, 3, 7],
        # Right
        [1, 5, 6], [1, 6, 2],
        # Top
        [3, 2, 6], [3, 6, 7],
        # Bottom
        [4, 5, 1], [4, 1, 0],
    ])
    
    # Compute normals
    normals = np.zeros((8, 3))
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)
        for idx in face:
            normals[idx] += face_normal
    
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
    
    return vertices, faces, normals


def create_hexagonal_prism(
    radius: float = 1.0,
    height: float = 2.0,
    center: Tuple[float, float, float] = (0, 0, 0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a hexagonal prism mesh.
    
    Args:
        radius: Distance from center to vertices
        height: Height of the prism
        center: Center point
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    cx, cy, cz = center
    half_h = height / 2
    
    vertices = []
    
    # Bottom hexagon
    for i in range(6):
        angle = np.pi / 3 * i
        x = cx + radius * np.cos(angle)
        y = cy + radius * np.sin(angle)
        vertices.append([x, y, cz - half_h])
    
    # Top hexagon
    for i in range(6):
        angle = np.pi / 3 * i
        x = cx + radius * np.cos(angle)
        y = cy + radius * np.sin(angle)
        vertices.append([x, y, cz + half_h])
    
    # Center points for top and bottom caps
    vertices.append([cx, cy, cz - half_h])  # index 12
    vertices.append([cx, cy, cz + half_h])  # index 13
    
    vertices = np.array(vertices)
    
    faces = []
    
    # Bottom cap (fan from center)
    for i in range(6):
        next_i = (i + 1) % 6
        faces.append([12, next_i, i])  # Reversed for outward normals
    
    # Top cap
    for i in range(6):
        next_i = (i + 1) % 6
        faces.append([13, i + 6, next_i + 6])
    
    # Side faces
    for i in range(6):
        next_i = (i + 1) % 6
        # Two triangles per side
        faces.append([i, next_i, next_i + 6])
        faces.append([i, next_i + 6, i + 6])
    
    faces = np.array(faces)
    
    # Compute normals
    normals = np.zeros((len(vertices), 3))
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)
        for idx in face:
            normals[idx] += face_normal
    
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    normals = normals / lengths
    
    return vertices, faces, normals


def create_pyramid(
    base_radius: float = 1.0,
    height: float = 2.0,
    sides: int = 4,
    center: Tuple[float, float, float] = (0, 0, 0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a pyramid mesh.
    
    Args:
        base_radius: Radius of the base
        height: Height of the pyramid
        sides: Number of sides
        center: Center of the base
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    cx, cy, cz = center
    
    vertices = []
    
    # Base vertices
    for i in range(sides):
        angle = 2 * np.pi * i / sides
        x = cx + base_radius * np.cos(angle)
        y = cy + base_radius * np.sin(angle)
        vertices.append([x, y, cz])
    
    # Apex
    apex_idx = len(vertices)
    vertices.append([cx, cy, cz + height])
    
    # Base center
    base_center_idx = len(vertices)
    vertices.append([cx, cy, cz])
    
    vertices = np.array(vertices)
    
    faces = []
    
    # Base (fan from center)
    for i in range(sides):
        next_i = (i + 1) % sides
        faces.append([base_center_idx, next_i, i])
    
    # Sides (triangles to apex)
    for i in range(sides):
        next_i = (i + 1) % sides
        faces.append([i, next_i, apex_idx])
    
    faces = np.array(faces)
    
    # Compute normals
    normals = np.zeros((len(vertices), 3))
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)
        for idx in face:
            normals[idx] += face_normal
    
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    normals = normals / lengths
    
    return vertices, faces, normals


def create_helix(
    radius: float = 1.0,
    height: float = 3.0,
    turns: int = 3,
    tube_radius: float = 0.1,
    segments_per_turn: int = 32,
    tube_segments: int = 8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a helical tube mesh.
    
    Args:
        radius: Helix radius
        height: Total height
        turns: Number of turns
        tube_radius: Radius of the tube
        segments_per_turn: Resolution around each turn
        tube_segments: Resolution of tube cross-section
    
    Returns:
        Tuple of (vertices, faces, normals)
    """
    total_segments = turns * segments_per_turn
    
    vertices = []
    normals = []
    
    for i in range(total_segments + 1):
        t = i / total_segments
        theta = 2 * np.pi * turns * t
        z = height * t - height / 2
        
        # Center of tube at this point
        center = np.array([radius * np.cos(theta), radius * np.sin(theta), z])
        
        # Tangent direction (helix curve derivative)
        tangent = np.array([
            -radius * np.sin(theta) * 2 * np.pi * turns,
            radius * np.cos(theta) * 2 * np.pi * turns,
            height,
        ])
        tangent = tangent / np.linalg.norm(tangent)
        
        # Perpendicular vectors for tube cross-section
        up = np.array([0, 0, 1])
        binormal = np.cross(tangent, up)
        if np.linalg.norm(binormal) < 0.1:
            binormal = np.cross(tangent, np.array([1, 0, 0]))
        binormal = binormal / np.linalg.norm(binormal)
        normal_vec = np.cross(binormal, tangent)
        
        for j in range(tube_segments):
            phi = 2 * np.pi * j / tube_segments
            offset = tube_radius * (np.cos(phi) * binormal + np.sin(phi) * normal_vec)
            vertex = center + offset
            vertices.append(vertex)
            normals.append(offset / tube_radius)
    
    vertices = np.array(vertices)
    normals = np.array(normals)
    
    # Create faces
    faces = []
    for i in range(total_segments):
        for j in range(tube_segments):
            next_j = (j + 1) % tube_segments
            
            v0 = i * tube_segments + j
            v1 = i * tube_segments + next_j
            v2 = (i + 1) * tube_segments + next_j
            v3 = (i + 1) * tube_segments + j
            
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])
    
    return vertices, np.array(faces), normals
