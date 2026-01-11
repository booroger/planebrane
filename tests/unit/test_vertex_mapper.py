"""Unit tests for vertex mapper module."""

import pytest
import numpy as np


class TestCreateMeshGrid:
    """Test mesh grid creation."""

    def test_create_mesh_grid_default(self):
        """Test default mesh grid creation."""
        from app.core.geometry3d.vertex_mapper import create_mesh_grid

        vertices, faces = create_mesh_grid(resolution=10)

        assert vertices.shape == (100, 3)  # 10x10 = 100 vertices
        assert faces.shape[1] == 3  # Triangular faces
        # Vertices should span [-1, 1] range
        assert np.min(vertices[:, 0]) == pytest.approx(-1.0)
        assert np.max(vertices[:, 0]) == pytest.approx(1.0)
        # Z should be 0 (flat plane)
        assert np.all(vertices[:, 2] == 0.0)

    def test_create_mesh_grid_custom_size(self):
        """Test custom mesh size."""
        from app.core.geometry3d.vertex_mapper import create_mesh_grid

        vertices, faces = create_mesh_grid(resolution=5, size=4.0)

        assert vertices.shape == (25, 3)
        # Should span [-2, 2] for size 4
        assert np.min(vertices[:, 0]) == pytest.approx(-2.0)
        assert np.max(vertices[:, 0]) == pytest.approx(2.0)


class TestMapPixelsToVertices:
    """Test pixel-to-vertex mapping."""

    def test_map_pixels_to_vertices_hit(self):
        """Test Z-displacement for hit pixels."""
        from app.core.geometry3d.vertex_mapper import (
            create_mesh_grid,
            map_pixels_to_vertices,
        )

        vertices, _ = create_mesh_grid(resolution=5)

        # Create displacement grid with center hit
        grid = np.zeros((5, 5), dtype=np.float32)
        grid[2, 2] = 1.0  # Center hit

        modified = map_pixels_to_vertices(vertices, grid, amplitude=2.0, base_height=0.0)

        # Center vertex should have max Z
        center_idx = 2 * 5 + 2  # Row 2, col 2
        assert modified[center_idx, 2] == pytest.approx(2.0)

        # Edge vertices should have base height
        assert modified[0, 2] == pytest.approx(0.0)

    def test_map_pixels_to_vertices_miss(self):
        """Test base height for miss pixels."""
        from app.core.geometry3d.vertex_mapper import (
            create_mesh_grid,
            map_pixels_to_vertices,
        )

        vertices, _ = create_mesh_grid(resolution=4)
        grid = np.zeros((4, 4), dtype=np.float32)  # All zeros

        modified = map_pixels_to_vertices(vertices, grid, amplitude=1.0, base_height=0.5)

        # All vertices should have base height
        assert np.all(modified[:, 2] == pytest.approx(0.5))


class TestSmoothing:
    """Test mesh smoothing functions."""

    def test_apply_gaussian_smoothing(self):
        """Test Gaussian smoothing reduces peaks."""
        from app.core.geometry3d.vertex_mapper import (
            create_mesh_grid,
            apply_gaussian_smoothing,
        )

        vertices, _ = create_mesh_grid(resolution=10)

        # Create spike in center
        center_idx = 5 * 10 + 5
        vertices[center_idx, 2] = 10.0

        smoothed = apply_gaussian_smoothing(vertices, resolution=10, sigma=1.0)

        # Peak should be reduced
        assert smoothed[center_idx, 2] < 10.0
        # Neighbors should have some height
        neighbor_idx = 5 * 10 + 4
        assert smoothed[neighbor_idx, 2] > 0.0

    def test_apply_bilinear_interpolation(self):
        """Test bilinear interpolation smoothing."""
        from app.core.geometry3d.vertex_mapper import (
            create_mesh_grid,
            apply_bilinear_interpolation,
        )

        vertices, _ = create_mesh_grid(resolution=5)

        # Create spike
        vertices[12, 2] = 5.0  # Center of 5x5

        smoothed = apply_bilinear_interpolation(vertices, resolution=5, iterations=1)

        # Peak should be reduced
        assert smoothed[12, 2] < 5.0


class TestGenerateReliefMesh:
    """Test complete relief mesh generation."""

    def test_generate_relief_mesh_basic(self):
        """Test basic relief mesh generation."""
        from app.core.geometry3d.vertex_mapper import generate_relief_mesh

        # Create simple displacement grid
        grid = np.zeros((50, 50), dtype=np.float32)
        grid[20:30, 20:30] = 1.0  # Square in center

        result = generate_relief_mesh(
            displacement_grid=grid,
            resolution=32,
            amplitude=1.0,
            smoothing_method="gaussian",
            smoothing_strength=2.0,
        )

        assert "vertices" in result
        assert "faces" in result
        assert "normals" in result
        assert result["vertices"].shape[0] == 32 * 32
        assert result["vertices"].shape[1] == 3

    def test_generate_relief_mesh_no_smoothing(self):
        """Test mesh with no smoothing."""
        from app.core.geometry3d.vertex_mapper import generate_relief_mesh

        grid = np.zeros((10, 10), dtype=np.float32)
        grid[5, 5] = 1.0

        result = generate_relief_mesh(
            displacement_grid=grid,
            resolution=10,
            smoothing_method="none",
        )

        assert result["vertices"].shape == (100, 3)


class TestVertexNormals:
    """Test normal computation."""

    def test_compute_vertex_normals(self):
        """Test vertex normal computation."""
        from app.core.geometry3d.vertex_mapper import (
            create_mesh_grid,
            compute_vertex_normals,
        )

        vertices, faces = create_mesh_grid(resolution=3)
        normals = compute_vertex_normals(vertices, faces)

        assert normals.shape == vertices.shape
        # For flat plane, normals should point up (0, 0, 1)
        for normal in normals:
            length = np.linalg.norm(normal)
            if length > 0:
                assert length == pytest.approx(1.0, abs=0.01)
