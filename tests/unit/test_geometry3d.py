"""Unit tests for 3D geometry generation."""

import pytest
import numpy as np


class TestPrimitives:
    """Test 3D primitive shape generators."""
    
    def test_create_sphere(self):
        """Test sphere generation."""
        from app.core.geometry3d.primitives import create_sphere
        
        vertices, faces, normals = create_sphere(radius=1.0, subdivisions=2)
        
        assert len(vertices) > 0
        assert len(faces) > 0
        assert len(normals) == len(vertices)
        
        # Check vertices are on sphere surface
        distances = np.linalg.norm(vertices, axis=1)
        np.testing.assert_array_almost_equal(distances, 1.0, decimal=5)
    
    def test_create_torus(self):
        """Test torus generation."""
        from app.core.geometry3d.primitives import create_torus
        
        vertices, faces, normals = create_torus(
            major_radius=1.0, minor_radius=0.3, segments=16, ring_segments=8
        )
        
        assert len(vertices) == 16 * 8
        assert len(faces) == 16 * 8 * 2  # 2 triangles per quad
        assert len(normals) == len(vertices)
    
    def test_create_cube(self):
        """Test cube generation."""
        from app.core.geometry3d.primitives import create_cube
        
        vertices, faces, normals = create_cube(size=2.0)
        
        assert len(vertices) == 8
        assert len(faces) == 12  # 6 faces * 2 triangles
        
        # Check bounds
        assert np.allclose(vertices.min(), -1.0)
        assert np.allclose(vertices.max(), 1.0)
    
    def test_create_hexagonal_prism(self):
        """Test hexagonal prism generation."""
        from app.core.geometry3d.primitives import create_hexagonal_prism
        
        vertices, faces, normals = create_hexagonal_prism(radius=1.0, height=2.0)
        
        assert len(vertices) > 0
        assert len(faces) > 0
        
        # Should have 14 vertices: 6 top + 6 bottom + 2 centers
        assert len(vertices) == 14
    
    def test_create_pyramid(self):
        """Test pyramid generation."""
        from app.core.geometry3d.primitives import create_pyramid
        
        vertices, faces, normals = create_pyramid(
            base_radius=1.0, height=2.0, sides=4
        )
        
        assert len(vertices) == 6  # 4 base + apex + base center
        assert len(faces) == 8  # 4 base + 4 sides
    
    def test_create_helix(self):
        """Test helix generation."""
        from app.core.geometry3d.primitives import create_helix
        
        vertices, faces, normals = create_helix(
            radius=1.0, height=3.0, turns=2,
            tube_radius=0.1, segments_per_turn=16, tube_segments=8
        )
        
        assert len(vertices) > 0
        assert len(faces) > 0
        assert len(normals) == len(vertices)


class TestTransformations:
    """Test mesh transformation operations."""
    
    @pytest.fixture
    def simple_mesh(self):
        """Create a simple mesh for testing."""
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ], dtype=np.float64)
        
        faces = np.array([
            [0, 1, 2],
            [0, 1, 3],
            [0, 2, 3],
            [1, 2, 3],
        ])
        
        return vertices, faces
    
    def test_apply_extrusion(self, simple_mesh):
        """Test extrusion transformation."""
        from app.core.geometry3d.transformations import apply_extrusion
        
        vertices, faces = simple_mesh
        normals = np.array([
            [-1, -1, -1],
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
        ], dtype=np.float64)
        normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
        
        extruded = apply_extrusion(vertices, normals, depth=2.0)
        
        assert extruded.shape == vertices.shape
        # Vertices should have moved along normals
        assert not np.allclose(extruded, vertices)
    
    def test_apply_subdivision(self, simple_mesh):
        """Test mesh subdivision."""
        from app.core.geometry3d.transformations import apply_subdivision
        
        vertices, faces = simple_mesh
        
        new_vertices, new_faces = apply_subdivision(vertices, faces, levels=1)
        
        # Subdivision increases vertex and face count
        assert len(new_vertices) > len(vertices)
        assert len(new_faces) > len(faces)
    
    def test_apply_smoothing(self, simple_mesh):
        """Test Laplacian smoothing."""
        from app.core.geometry3d.transformations import apply_smoothing
        
        vertices, faces = simple_mesh
        
        smoothed = apply_smoothing(vertices, faces, iterations=3, factor=0.5)
        
        assert smoothed.shape == vertices.shape
        # Smoothing should move vertices toward neighbors
    
    def test_apply_twist(self, simple_mesh):
        """Test twist deformation."""
        from app.core.geometry3d.transformations import apply_twist
        
        vertices, _ = simple_mesh
        
        twisted = apply_twist(vertices, axis="z", angle_per_unit=0.5)
        
        assert twisted.shape == vertices.shape
        # Twisted should differ from original
        assert not np.allclose(twisted, vertices)
    
    def test_apply_taper(self, simple_mesh):
        """Test taper deformation."""
        from app.core.geometry3d.transformations import apply_taper
        
        vertices, _ = simple_mesh
        
        tapered = apply_taper(
            vertices, axis="z", start_scale=1.0, end_scale=0.5
        )
        
        assert tapered.shape == vertices.shape


class TestExporters:
    """Test mesh export functionality."""
    
    @pytest.fixture
    def mesh_data(self):
        """Create mesh data for export testing."""
        from app.core.geometry3d.primitives import create_cube
        
        vertices, faces, normals = create_cube(size=2.0)
        
        return {
            "vertices": vertices.tolist(),
            "faces": faces.tolist(),
            "normals": normals.tolist(),
        }
    
    def test_export_stl_binary(self, mesh_data):
        """Test binary STL export."""
        from app.core.geometry3d.exporters import export_to_format
        
        data = export_to_format(mesh_data, "stl", binary=True)
        
        assert isinstance(data, bytes)
        assert len(data) > 0
        # Binary STL has 80-byte header + 4-byte count + 50 bytes per triangle
        expected_size = 80 + 4 + 50 * len(mesh_data["faces"])
        assert len(data) == expected_size
    
    def test_export_stl_ascii(self, mesh_data):
        """Test ASCII STL export."""
        from app.core.geometry3d.exporters import export_to_format
        
        data = export_to_format(mesh_data, "stl", binary=False)
        
        assert isinstance(data, bytes)
        text = data.decode('utf-8')
        assert text.startswith("solid planebrane")
        assert text.strip().endswith("endsolid planebrane")
    
    def test_export_obj(self, mesh_data):
        """Test OBJ export."""
        from app.core.geometry3d.exporters import export_to_format
        
        data = export_to_format(mesh_data, "obj")
        
        assert isinstance(data, bytes)
        text = data.decode('utf-8')
        
        # Should have vertex lines
        assert "v " in text
        # Should have face lines
        assert "f " in text
        # Should have normal lines
        assert "vn " in text
    
    def test_export_gltf(self, mesh_data):
        """Test glTF export."""
        import json
        from app.core.geometry3d.exporters import export_to_format
        
        data = export_to_format(mesh_data, "gltf")
        
        assert isinstance(data, bytes)
        gltf = json.loads(data.decode('utf-8'))
        
        assert "asset" in gltf
        assert gltf["asset"]["version"] == "2.0"
        assert "meshes" in gltf
        assert "buffers" in gltf
    
    def test_export_glb(self, mesh_data):
        """Test GLB binary export."""
        from app.core.geometry3d.exporters import export_to_format
        
        data = export_to_format(mesh_data, "glb", binary=True)
        
        assert isinstance(data, bytes)
        # GLB magic number
        assert data[:4] == b'glTF'
        # Version 2
        assert data[4:8] == b'\x02\x00\x00\x00'


class TestMapping:
    """Test 2D to 3D mapping."""
    
    def test_map_points_to_surface(self, sample_points):
        """Test surface mapping."""
        from app.core.geometry3d.primitives import create_sphere
        from app.core.geometry3d.mapping import map_points_to_surface
        
        vertices, _, _ = create_sphere(radius=1.0, subdivisions=1)
        
        modified = map_points_to_surface(vertices, sample_points, curvature=0.5)
        
        assert modified.shape == vertices.shape
    
    def test_project_pattern_to_sphere(self, sample_points):
        """Test spherical projection."""
        from app.core.geometry3d.mapping import project_pattern_to_sphere
        
        points_3d = project_pattern_to_sphere(sample_points, radius=1.0)
        
        assert len(points_3d) == len(sample_points)
        
        for p in points_3d:
            assert len(p) == 3
            # All points should be on or near sphere
            distance = np.sqrt(sum(c**2 for c in p))
            assert distance <= 1.1  # Allow small tolerance
    
    def test_project_pattern_to_torus(self, sample_points):
        """Test toroidal projection."""
        from app.core.geometry3d.mapping import project_pattern_to_torus
        
        points_3d = project_pattern_to_torus(
            sample_points, major_radius=1.0, minor_radius=0.3
        )
        
        assert len(points_3d) == len(sample_points)
        
        for p in points_3d:
            assert len(p) == 3
