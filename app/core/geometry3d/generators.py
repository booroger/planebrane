"""
3D Mesh Generators for Topology Intent Layer.
"""

import numpy as np
from typing import Dict, Any, Tuple

from app.core.topology.intent import (
    TopologyFamily,
    SteeringProfile,
    PhaseBehavior,
    BoundaryCondition,
)


def generate_topology_surface(
    displacement_grid: np.ndarray,
    family: TopologyFamily,
    steering: SteeringProfile,
    resolution: int = 128,
    amplitude: float = 1.0,
) -> Dict[str, np.ndarray]:
    """
    Dispatcher for generating 3D surfaces based on topology family.
    """

    if family == TopologyFamily.TOROIDAL:
        return generate_toroid(displacement_grid, steering, resolution, amplitude)
    elif family == TopologyFamily.SPHEROID:
        return generate_spheroid(displacement_grid, steering, resolution, amplitude)
    elif family == TopologyFamily.HELICAL:
        return generate_helicoid(displacement_grid, steering, resolution, amplitude)
    elif family == TopologyFamily.LATTICE_RESONATOR:
        return generate_lattice(displacement_grid, steering, resolution, amplitude)
    elif family == TopologyFamily.COMPACTIFIED_FOLDED:
        # Fallback to Toroid with twist or custom logic for now?
        # Or maybe a specific folded plane. Let's do a folded plane.
        return generate_compactified(displacement_grid, steering, resolution, amplitude)
    else:
        # Default Planar
        return generate_planar_relief(displacement_grid, steering, resolution, amplitude)


def generate_planar_relief(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """Standard Planar Relief Map."""
    # This logic is similar to existing vertex_mapper but adapted here for uniformity
    from app.core.geometry3d.vertex_mapper import create_mesh_grid, compute_vertex_normals

    vertices, faces = create_mesh_grid(resolution=resolution)

    # Map displacement to Z
    # Assumes grid matches resolution (handled by caller or wrapper usually)
    # We'll do a quick sampling here to be safe

    modified = vertices.copy()
    grid_h, grid_w = displacement_grid.shape

    for i, v in enumerate(vertices):
        # geometry3d creates grid from -1 to 1
        vx, vy = v[0], v[1]
        gx = int((vx + 1) / 2 * (grid_w - 1))
        gy = int((vy + 1) / 2 * (grid_h - 1))

        # Clamp
        gx = max(0, min(gx, grid_w - 1))
        gy = max(0, min(gy, grid_h - 1))

        d = displacement_grid[gy, gx]
        modified[i, 2] = d * amplitude

    normals = compute_vertex_normals(modified, faces)
    return {"vertices": modified, "faces": faces, "normals": normals}


def generate_toroid(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """
    Generate a Toroidal Surface.
    X-axis maps to Major Angle (Theta).
    Y-axis maps to Minor Angle (Phi).
    Displacement maps to Surface Normal (Minor Radius variance).
    """
    major_r = 1.0
    minor_r = 0.4

    # Grid generation
    # We generate a grid of (u, v) from 0 to 1
    u = np.linspace(0, 1, resolution)
    v = np.linspace(0, 1, resolution)
    uu, vv = np.meshgrid(u, v)

    points_u = uu.flatten()
    points_v = vv.flatten()

    vertices = []
    grid_h, grid_w = displacement_grid.shape

    for i in range(len(points_u)):
        u_val = points_u[i]
        v_val = points_v[i]

        # Sample displacement
        gx = int(u_val * (grid_w - 1))
        gy = int(v_val * (grid_h - 1))
        gx = max(0, min(gx, grid_w - 1))
        gy = max(0, min(gy, grid_h - 1))
        disp = displacement_grid[gy, gx]

        # Map to angles
        theta = u_val * 2 * np.pi  # Major circle
        phi = v_val * 2 * np.pi  # Minor circle

        # Apply displacement to minor radius (ballooning effect)
        local_minor = minor_r + (disp * amplitude * 0.3)

        # Torus formula
        x = (major_r + local_minor * np.cos(phi)) * np.cos(theta)
        y = (major_r + local_minor * np.cos(phi)) * np.sin(theta)
        z = local_minor * np.sin(phi)

        vertices.append([x, y, z])

    vertices = np.array(vertices)

    # Faces generation (Standard Grid Topology)
    faces = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            v0 = i * resolution + j
            v1 = v0 + 1
            v2 = (i + 1) * resolution + j
            v3 = v2 + 1
            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    # Enforce seam closure for CLOSED_LOOP boundary condition
    # Connect last column (u=1) back to first column (u=0)
    if steering.boundary_condition == BoundaryCondition.CLOSED_LOOP:
        # Stitch U-seam: merge duplicate vertices at u=0 and u=1
        seam_faces = []
        for i in range(resolution - 1):
            # Last col wraps to first col
            v_last_col = i * resolution + (resolution - 1)
            v_first_col = i * resolution + 0
            v_next_last = (i + 1) * resolution + (resolution - 1)
            v_next_first = (i + 1) * resolution + 0
            # Create seam face
            seam_faces.append([v_last_col, v_next_last, v_first_col])
            seam_faces.append([v_first_col, v_next_last, v_next_first])
        faces.extend(seam_faces)

    from app.core.geometry3d.vertex_mapper import compute_vertex_normals

    faces = np.array(faces)
    normals = compute_vertex_normals(vertices, faces)

    return {"vertices": vertices, "faces": faces, "normals": normals}


def generate_spheroid(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """
    Generate a Spheroid (Elongated or Oblate Ellipsoid).
    X-axis maps to Latitude (Phi).
    Y-axis maps to Longitude (Theta).
    Inherently closed surface with no boundaries (CLOSED_LOOP by nature).
    
    Spheroid parameters:
    - Semi-major axis (a) along Z: 1.2
    - Semi-minor axes (b, c) in XY plane: 0.8
    """
    a = 1.2  # Z semi-axis (vertical extent)
    b = 0.8  # X,Y semi-axes (horizontal extent)

    # Grid generation using latitude/longitude
    # v maps to latitude (phi): 0 to pi
    # u maps to longitude (theta): 0 to 2*pi
    u = np.linspace(0, 1, resolution)
    v = np.linspace(0, 1, resolution)
    uu, vv = np.meshgrid(u, v)

    points_u = uu.flatten()
    points_v = vv.flatten()

    vertices = []
    grid_h, grid_w = displacement_grid.shape

    for i in range(len(points_u)):
        u_val = points_u[i]
        v_val = points_v[i]

        # Sample displacement
        gx = int(u_val * (grid_w - 1))
        gy = int(v_val * (grid_h - 1))
        gx = max(0, min(gx, grid_w - 1))
        gy = max(0, min(gy, grid_h - 1))
        disp = displacement_grid[gy, gx]

        # Map to spherical angles
        theta = u_val * 2 * np.pi  # Longitude: 0 to 2π
        phi = v_val * np.pi  # Latitude: 0 to π

        # Apply displacement to radii (ballooning effect)
        local_a = a + (disp * amplitude * 0.3)
        local_b = b + (disp * amplitude * 0.2)

        # Prolate/Oblate Spheroid formula
        x = local_b * np.sin(phi) * np.cos(theta)
        y = local_b * np.sin(phi) * np.sin(theta)
        z = local_a * np.cos(phi)

        vertices.append([x, y, z])

    vertices = np.array(vertices)

    # Faces generation (Standard Grid Topology)
    faces = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            v0 = i * resolution + j
            v1 = v0 + 1
            v2 = (i + 1) * resolution + j
            v3 = v2 + 1
            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    # Note: Spheroid is inherently CLOSED_LOOP (poles are continuous singularities)
    # No seam stitching needed; it's topologically complete
    # Handle pole collapsing if needed (currently v=0 and v=1 collapse to single points)
    
    from app.core.geometry3d.vertex_mapper import compute_vertex_normals

    faces = np.array(faces)
    normals = compute_vertex_normals(vertices, faces)

    return {"vertices": vertices, "faces": faces, "normals": normals}


def generate_helicoid(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """
    Generate a Helicoid Surface.
    X-axis -> Rotation (Theta).
    Y-axis -> Radial distance + Vertical height.
    """
    turns = 3
    height = 3.0
    max_r = 1.0

    u = np.linspace(0, 1, resolution)
    v = np.linspace(0, 1, resolution)
    uu, vv = np.meshgrid(u, v)

    points_u = uu.flatten()
    points_v = vv.flatten()

    vertices = []
    grid_h, grid_w = displacement_grid.shape

    for i in range(len(points_u)):
        u_val = points_u[i]
        v_val = points_v[i]

        gx = int(u_val * (grid_w - 1))
        gy = int(v_val * (grid_h - 1))
        disp = displacement_grid[gy, gx]

        theta = u_val * turns * 2 * np.pi

        # Map v to radius (0 to 1)
        r = v_val * max_r

        # z is periodic with theta
        z = (theta / (2 * np.pi)) * (height / turns)

        # Apply displacement to Z or R
        z += disp * amplitude

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        vertices.append([x, y, z])

    vertices = np.array(vertices)

    # Faces (Standard Grid)
    faces = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            v0 = i * resolution + j
            v1 = v0 + 1
            v2 = (i + 1) * resolution + j
            v3 = v2 + 1
            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    # Enforce FLOWING phase behavior: add twist or extra rotation
    if steering.phase_behavior == PhaseBehavior.FLOWING:
        # Apply mild twist along the helix for visual effect
        for i in range(len(vertices)):
            z = vertices[i, 2]
            theta = np.arctan2(vertices[i, 1], vertices[i, 0])
            # Add phase-dependent rotation
            twist_angle = z * 0.2
            r = np.sqrt(vertices[i, 0] ** 2 + vertices[i, 1] ** 2)
            vertices[i, 0] = r * np.cos(theta + twist_angle)
            vertices[i, 1] = r * np.sin(theta + twist_angle)

    from app.core.geometry3d.vertex_mapper import compute_vertex_normals

    faces = np.array(faces)
    normals = compute_vertex_normals(vertices, faces)

    return {"vertices": vertices, "faces": faces, "normals": normals}


def generate_lattice(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """
    Generate a Lattice Resonator.
    Discretized/Quantized vertices based on phase_behavior.
    """
    # Get base planar relief first
    data = generate_planar_relief(displacement_grid, steering, resolution, amplitude)
    verts = data["vertices"]

    # Apply quantization if QUANTIZED phase
    if steering.phase_behavior == PhaseBehavior.QUANTIZED:
        quantize_step = 0.1
        verts = np.round(verts / quantize_step) * quantize_step
    else:
        # For STATIC or FLOWING, apply grid alignment with softer snapping
        grid_spacing = 0.15
        verts = np.round(verts / grid_spacing) * grid_spacing + 0.02 * (verts % grid_spacing)

    # Recompute normals (will look faceted for quantized)
    from app.core.geometry3d.vertex_mapper import compute_vertex_normals

    normals = compute_vertex_normals(verts, data["faces"])

    data["vertices"] = verts
    data["normals"] = normals

    return data


def generate_compactified(
    displacement_grid: np.ndarray, steering: SteeringProfile, resolution: int, amplitude: float
) -> Dict[str, np.ndarray]:
    """
    Generate a Calabi-Yau-like folded surface.
    Uses complex coordinate mapping:
    z1 = z^k + ...
    For simplicity, we modulate a sphere with high frequency folding.
    """
    # Base: Sphere

    u = np.linspace(0, 1, resolution)
    v = np.linspace(0, 1, resolution)
    uu, vv = np.meshgrid(u, v)
    points_u = uu.flatten()
    points_v = vv.flatten()

    vertices = []
    grid_h, grid_w = displacement_grid.shape

    for i in range(len(points_u)):
        u_val = points_u[i]
        v_val = points_v[i]

        gx = int(u_val * (grid_w - 1))
        gy = int(v_val * (grid_h - 1))
        disp = displacement_grid[gy, gx]

        # Sphere mapping
        theta = u_val * 2 * np.pi
        phi = v_val * np.pi

        r = 1.0 + (disp * amplitude * 0.5)

        # Introduce "folding" based on 2nd harmonics of u, v
        fold = np.sin(u_val * 6 * np.pi) * np.cos(v_val * 6 * np.pi) * 0.2
        r += fold

        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)

        vertices.append([x, y, z])

    vertices = np.array(vertices)

    faces = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            v0 = i * resolution + j
            v1 = v0 + 1
            v2 = (i + 1) * resolution + j
            v3 = v2 + 1
            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    from app.core.geometry3d.vertex_mapper import compute_vertex_normals

    faces = np.array(faces)
    normals = compute_vertex_normals(vertices, faces)

    return {"vertices": vertices, "faces": faces, "normals": normals}
