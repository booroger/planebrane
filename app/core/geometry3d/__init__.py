"""3D geometry generation package."""

from typing import Any
import numpy as np


async def generate_3d_model(
    points: list[dict],
    shape: str,
    params: dict,
) -> dict[str, Any]:
    """
    Generate a 3D model from extracted 2D points.

    Args:
        points: List of 2D points with x, y, weight, feature_type
        shape: Target 3D shape type
        params: Generation parameters

    Returns:
        Mesh data dictionary
    """
    from app.core.geometry3d.primitives import (
        create_sphere,
        create_torus,
        create_cube,
        create_hexagonal_prism,
        create_helix,
        create_pyramid,
    )
    from app.core.geometry3d.mapping import map_points_to_surface, map_image_to_relief
    from app.core.geometry3d.transformations import (
        apply_extrusion,
        apply_subdivision,
        apply_smoothing,
    )

    # Extract parameters
    extrusion_depth = params.get("extrusion_depth", 1.0)
    curvature = params.get("curvature", 0.0)
    subdivision_level = params.get("subdivision_level", 2)
    smoothing_iterations = params.get("smoothing_iterations", 3)
    pattern_scale = params.get("pattern_scale", 1.0)
    hollow = params.get("hollow", False)
    wall_thickness = params.get("wall_thickness", 0.1)

    # Normalize points to [-1, 1] range
    if points:
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        center_x = (max(xs) + min(xs)) / 2
        center_y = (max(ys) + min(ys)) / 2
        scale = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
        if scale == 0:
            scale = 1

        normalized_points = [
            {
                "x": (p["x"] - center_x) / scale,
                "y": (p["y"] - center_y) / scale,
                "weight": p["weight"],
                "feature_type": p["feature_type"],
            }
            for p in points
        ]
    else:
        normalized_points = []

    # Create base geometry based on shape
    shape_creators = {
        "sphere": lambda: create_sphere(radius=pattern_scale, subdivisions=subdivision_level),
        "torus": lambda: create_torus(
            major_radius=pattern_scale,
            minor_radius=pattern_scale * 0.3,
            segments=32 * (subdivision_level + 1),
        ),
        "ellipsoid": lambda: create_sphere(radius=pattern_scale, subdivisions=subdivision_level),
        "cone": lambda: create_pyramid(
            base_radius=pattern_scale, height=pattern_scale * 2, sides=32
        ),
        "cube": lambda: create_cube(size=pattern_scale * 2),
        "cuboid": lambda: create_cube(size=pattern_scale * 2),
        "hexagonal_prism": lambda: create_hexagonal_prism(
            radius=pattern_scale, height=pattern_scale * 2
        ),
        "pyramid": lambda: create_pyramid(
            base_radius=pattern_scale, height=pattern_scale * 2, sides=4
        ),
        "helix": lambda: create_helix(
            radius=pattern_scale,
            height=pattern_scale * 3,
            turns=3,
            tube_radius=pattern_scale * 0.1,
        ),
        "twisted_torus": lambda: create_torus(
            major_radius=pattern_scale,
            minor_radius=pattern_scale * 0.2,
            segments=64,
        ),
        "wireframe_surface": lambda: create_sphere(
            radius=pattern_scale, subdivisions=subdivision_level
        ),
    }

    creator = shape_creators.get(shape, shape_creators["sphere"])
    vertices, faces, normals = creator()

    # Apply point-based surface modulation
    if normalized_points:
        vertices = map_points_to_surface(vertices, normalized_points, curvature)

    # Apply extrusion/displacement
    if extrusion_depth != 1.0:
        vertices = apply_extrusion(vertices, normals, extrusion_depth)

    # Apply subdivision for smoother surface
    if subdivision_level > 0:
        vertices, faces = apply_subdivision(vertices, faces, subdivision_level)
        # Recompute normals after subdivision
        normals = _compute_normals(vertices, faces)

    # Apply smoothing
    if smoothing_iterations > 0:
        vertices = apply_smoothing(vertices, faces, smoothing_iterations)
        normals = _compute_normals(vertices, faces)

    # Handle hollow geometry
    if hollow:
        vertices, faces, normals = _make_hollow(vertices, faces, normals, wall_thickness)

    # Compute bounding box
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    bounding_box = tuple(min_coords.tolist() + max_coords.tolist())

    return {
        "vertices": vertices.tolist(),
        "faces": faces.tolist(),
        "normals": normals.tolist(),
        "vertex_count": len(vertices),
        "face_count": len(faces),
        "bounding_box": bounding_box,
    }


def _compute_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Compute vertex normals from mesh."""
    normals = np.zeros_like(vertices)

    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)

        for idx in face:
            normals[idx] += face_normal

    # Normalize
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    normals = normals / lengths

    return normals


def _make_hollow(
    vertices: np.ndarray,
    faces: np.ndarray,
    normals: np.ndarray,
    thickness: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create hollow geometry by insetting and connecting."""
    # Create inner surface by moving vertices inward along normals
    inner_vertices = vertices - normals * thickness

    # Combine vertices
    num_outer = len(vertices)
    all_vertices = np.vstack([vertices, inner_vertices])

    # Create inner faces (flipped)
    inner_faces = faces.copy() + num_outer
    inner_faces = inner_faces[:, ::-1]  # Flip winding

    # Combine faces
    all_faces = np.vstack([faces, inner_faces])

    # Recompute normals
    all_normals = _compute_normals(all_vertices, all_faces)

    return all_vertices, all_faces, all_normals


def simplify_mesh(mesh_data: dict, max_vertices: int = 1000) -> dict:
    """Simplify mesh for preview."""
    vertices = np.array(mesh_data["vertices"])
    faces = np.array(mesh_data["faces"])
    normals = np.array(mesh_data["normals"])

    if len(vertices) <= max_vertices:
        return {
            "vertices": [tuple(v) for v in vertices],
            "faces": [tuple(f) for f in faces],
            "normals": [tuple(n) for n in normals],
        }

    # Simple decimation: skip vertices uniformly
    step = len(vertices) // max_vertices
    if step < 2:
        step = 2

    # Create vertex mapping
    keep_indices = np.arange(0, len(vertices), step)
    new_indices = {old: new for new, old in enumerate(keep_indices)}

    # Filter vertices
    new_vertices = vertices[keep_indices]
    new_normals = normals[keep_indices]

    # Filter and remap faces
    new_faces = []
    for face in faces:
        if all(idx in new_indices for idx in face):
            new_faces.append([new_indices[idx] for idx in face])

    new_faces = np.array(new_faces) if new_faces else np.array([]).reshape(0, 3)

    return {
        "vertices": [tuple(v) for v in new_vertices],
        "faces": [tuple(f) for f in new_faces],
        "normals": [tuple(n) for n in new_normals],
    }
