"""Vertex mapper for Pixel-to-Vertex displacement.

Maps 2D image pixel data directly to 3D mesh vertex Z-heights,
creating relief surfaces from crop circle patterns.
"""

import numpy as np
from scipy import ndimage
from typing import Literal


def create_mesh_grid(
    resolution: int = 128,
    size: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create a flat plane mesh grid with specified resolution.

    Args:
        resolution: Number of vertices per axis (e.g., 128 = 128x128 grid)
        size: Total size of the mesh (default 2.0 spans [-1, 1])

    Returns:
        Tuple of (vertices, faces) where:
            - vertices: Nx3 array of (x, y, z) coordinates
            - faces: Mx3 array of triangle indices
    """
    half_size = size / 2

    # Create grid of x, y coordinates
    x = np.linspace(-half_size, half_size, resolution)
    y = np.linspace(-half_size, half_size, resolution)
    xx, yy = np.meshgrid(x, y)

    # Initialize z to 0 (flat plane)
    zz = np.zeros_like(xx)

    # Flatten to vertex list
    vertices = np.column_stack(
        [
            xx.flatten(),
            yy.flatten(),
            zz.flatten(),
        ]
    )

    # Generate triangle faces
    faces = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            # Vertex indices in the grid
            v0 = i * resolution + j
            v1 = v0 + 1
            v2 = (i + 1) * resolution + j
            v3 = v2 + 1

            # Two triangles per grid cell
            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    return vertices, np.array(faces, dtype=np.int32)


def map_pixels_to_vertices(
    vertices: np.ndarray,
    displacement_grid: np.ndarray,
    amplitude: float = 1.0,
    base_height: float = 0.0,
) -> np.ndarray:
    """
    Map pixel displacement values to mesh vertex Z-heights.

    For each vertex (vx, vy), sample the displacement grid and set Z.

    Args:
        vertices: Nx3 array of mesh vertices
        displacement_grid: 2D grid of displacement values [0, 1]
        amplitude: Maximum Z-height for "hit" pixels
        base_height: Z-height for "miss" pixels

    Returns:
        Modified vertices with Z-displacement applied
    """
    modified = vertices.copy()
    grid_height, grid_width = displacement_grid.shape

    for i, vertex in enumerate(vertices):
        vx, vy = vertex[0], vertex[1]

        # Map vertex coordinates [-1, 1] to grid indices [0, size-1]
        # Assuming vertex coords are normalized to [-1, 1]
        grid_x = int((vx + 1) / 2 * (grid_width - 1))
        grid_y = int((vy + 1) / 2 * (grid_height - 1))

        # Clamp to grid bounds
        grid_x = np.clip(grid_x, 0, grid_width - 1)
        grid_y = np.clip(grid_y, 0, grid_height - 1)

        # Sample displacement and apply
        displacement = displacement_grid[grid_y, grid_x]
        modified[i, 2] = base_height + displacement * amplitude

    return modified


def apply_gaussian_smoothing(
    vertices: np.ndarray,
    resolution: int,
    sigma: float = 2.0,
) -> np.ndarray:
    """
    Apply Gaussian blur to vertex Z-heights for smooth curves.

    Args:
        vertices: Nx3 array of mesh vertices
        resolution: Original grid resolution (to reshape Z values)
        sigma: Gaussian blur sigma (larger = smoother)

    Returns:
        Vertices with smoothed Z-heights
    """
    modified = vertices.copy()

    # Extract Z values and reshape to grid
    z_values = modified[:, 2].reshape(resolution, resolution)

    # Apply Gaussian blur
    smoothed_z = ndimage.gaussian_filter(z_values, sigma=sigma)

    # Update vertices
    modified[:, 2] = smoothed_z.flatten()

    return modified


def apply_bilinear_interpolation(
    vertices: np.ndarray,
    resolution: int,
    iterations: int = 3,
) -> np.ndarray:
    """
    Smooth mesh using iterative bilinear interpolation.

    Each vertex Z-height is averaged with its neighbors.

    Args:
        vertices: Nx3 array of mesh vertices
        resolution: Grid resolution
        iterations: Number of smoothing passes

    Returns:
        Vertices with smoothed Z-heights
    """
    modified = vertices.copy()

    for _ in range(iterations):
        z_grid = modified[:, 2].reshape(resolution, resolution)
        smoothed = z_grid.copy()

        # Average each interior vertex with its 4 neighbors
        for i in range(1, resolution - 1):
            for j in range(1, resolution - 1):
                neighbors = (
                    z_grid[i - 1, j] + z_grid[i + 1, j] + z_grid[i, j - 1] + z_grid[i, j + 1]
                )
                smoothed[i, j] = (z_grid[i, j] + neighbors) / 5.0

        modified[:, 2] = smoothed.flatten()

    return modified


def compute_vertex_normals(
    vertices: np.ndarray,
    faces: np.ndarray,
) -> np.ndarray:
    """
    Compute vertex normals for proper lighting/shading.

    Args:
        vertices: Nx3 array of vertices
        faces: Mx3 array of face indices

    Returns:
        Nx3 array of normalized vertex normals
    """
    normals = np.zeros_like(vertices)

    # Compute face normals and accumulate at vertices
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

        # Edge vectors
        e1 = v1 - v0
        e2 = v2 - v0

        # Face normal (cross product)
        face_normal = np.cross(e1, e2)

        # Accumulate at each vertex
        normals[face[0]] += face_normal
        normals[face[1]] += face_normal
        normals[face[2]] += face_normal

    # Normalize
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1  # Avoid division by zero
    normals = normals / lengths

    return normals


def generate_relief_mesh(
    displacement_grid: np.ndarray,
    resolution: int = 128,
    amplitude: float = 1.0,
    smoothing_method: Literal["gaussian", "bilinear", "none"] = "gaussian",
    smoothing_strength: float = 2.0,
) -> dict:
    """
    Complete pipeline: generate a relief mesh from a displacement grid.

    Args:
        displacement_grid: 2D array of displacement values [0, 1]
        resolution: Mesh resolution (vertices per axis)
        amplitude: Max Z-height displacement
        smoothing_method: 'gaussian', 'bilinear', or 'none'
        smoothing_strength: Sigma for gaussian, iterations for bilinear

    Returns:
        Dict with 'vertices', 'faces', 'normals'
    """
    # Create base mesh
    vertices, faces = create_mesh_grid(resolution=resolution)

    # Resize displacement grid to match mesh resolution
    from scipy.ndimage import zoom

    if displacement_grid.shape != (resolution, resolution):
        zoom_factors = (
            resolution / displacement_grid.shape[0],
            resolution / displacement_grid.shape[1],
        )
        displacement_grid = zoom(displacement_grid, zoom_factors, order=1)

    # Apply displacement
    vertices = map_pixels_to_vertices(vertices, displacement_grid, amplitude=amplitude)

    # Apply smoothing
    if smoothing_method == "gaussian":
        vertices = apply_gaussian_smoothing(vertices, resolution, sigma=smoothing_strength)
    elif smoothing_method == "bilinear":
        vertices = apply_bilinear_interpolation(
            vertices, resolution, iterations=int(smoothing_strength)
        )

    # Compute normals
    normals = compute_vertex_normals(vertices, faces)

    return {
        "vertices": vertices,
        "faces": faces,
        "normals": normals,
    }
