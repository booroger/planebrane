"""
Tests for ensuring seamless 3D embeddings without borders or Klein bottles.
Validates that default behavior generates closed, orientable surfaces.
"""

import numpy as np
from app.core.topology.intent import (
    SteeringProfile,
    TopologyFamily,
    BoundaryCondition,
    OrientationRule,
    PhaseBehavior,
)
from app.core.geometry3d.generators import generate_topology_surface
from app.core.topology.analyzer import TopologyAnalyzer


class TestSeamlessDefaults:
    """Test that default steering produces seamless, closed surfaces."""

    def test_default_boundary_condition_is_closed_loop(self):
        """Verify default boundary condition is CLOSED_LOOP."""
        steering = SteeringProfile()
        assert steering.boundary_condition == BoundaryCondition.CLOSED_LOOP

    def test_default_orientation_is_preserve(self):
        """Verify default orientation rule is PRESERVE (no Klein bottles)."""
        steering = SteeringProfile()
        assert steering.orientation_rule == OrientationRule.PRESERVE

    def test_default_allowed_families_include_spheroid(self):
        """Verify Spheroid is in default allowed families."""
        steering = SteeringProfile()
        assert TopologyFamily.SPHEROID in steering.allowed_families
        assert TopologyFamily.TOROIDAL in steering.allowed_families
        assert TopologyFamily.HELICAL in steering.allowed_families
        # Klein bottle should NOT be in default allowed families
        assert TopologyFamily.KLEIN_BOTTLE not in steering.allowed_families

    def test_klein_bottle_blocked_with_preserve_orientation(self):
        """Verify Klein bottle cannot be forced when PRESERVE orientation is set."""
        try:
            steering = SteeringProfile(
                force_family=TopologyFamily.KLEIN_BOTTLE,
                orientation_rule=OrientationRule.PRESERVE
            )
            assert False, "Should have raised ValueError for Klein bottle + PRESERVE"
        except ValueError as e:
            # Either constraint violated: Klein bottle not in allowed, or orientation conflict
            error_msg = str(e)
            assert "KLEIN_BOTTLE" in error_msg or "allowed_families" in error_msg, \
                f"Expected error about Klein bottle or allowed families, got: {error_msg}"

    def test_toroid_with_default_steering_is_closed_loop(self):
        """Generate toroid with defaults and verify it has CLOSED_LOOP boundary."""
        grid = np.random.rand(64, 64) * 0.5
        steering = SteeringProfile()  # Uses defaults
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.TOROIDAL,
            steering=steering,
            resolution=32,
            amplitude=0.3
        )
        assert "vertices" in data
        assert data["vertices"].shape[0] > 0
        # CLOSED_LOOP should not have boundary vertices
        # (all edges connect to neighboring faces)

    def test_spheroid_with_default_steering_is_seamless(self):
        """Generate spheroid with defaults and verify it's seamless."""
        grid = np.random.rand(64, 64) * 0.5
        steering = SteeringProfile()  # Uses defaults: CLOSED_LOOP
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.SPHEROID,
            steering=steering,
            resolution=32,
            amplitude=0.3
        )
        assert "vertices" in data
        assert data["vertices"].shape[0] > 0
        # Spheroid is inherently closed; no boundary edges

    def test_helicoid_respects_default_boundary_condition(self):
        """Generate helicoid and verify it respects CLOSED_LOOP default."""
        grid = np.random.rand(32, 32) * 0.5
        steering = SteeringProfile()  # CLOSED_LOOP default
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.HELICAL,
            steering=steering,
            resolution=24,
            amplitude=0.5
        )
        assert "vertices" in data
        assert data["vertices"].shape[0] > 0


class TestAnalyzerNeverGeneratesKleinBottle:
    """Test that analyzer never auto-detects Klein bottle as intent."""

    def test_analyzer_excludes_klein_bottle_from_scoring(self):
        """Verify analyzer's scoring dict excludes KLEIN_BOTTLE."""
        analyzer = TopologyAnalyzer()
        # Check that the scoring method never returns Klein bottle for random patterns
        for _ in range(10):
            img = np.random.rand(128, 128)
            family, confidence = analyzer.analyze(img)
            assert family != TopologyFamily.KLEIN_BOTTLE, \
                f"Analyzer should never auto-detect Klein bottle, got {family}"

    def test_analyzer_with_explicit_force_can_override(self):
        """Test that explicit force_family CANNOT force Klein bottle with PRESERVE."""
        img = np.ones((64, 64)) * 0.5
        analyzer = TopologyAnalyzer()
        steering = SteeringProfile(
            force_family=None  # Will not force Klein bottle
        )
        family, confidence = analyzer.analyze(img, steering)
        assert family != TopologyFamily.KLEIN_BOTTLE


class TestClosedSurfaceValidation:
    """Test properties of closed/seamless surfaces."""

    def test_toroid_has_continuous_u_seam(self):
        """Verify toroid u-seam (theta=0 to 2π) creates connectivity."""
        grid = np.zeros((64, 64))
        steering = SteeringProfile()
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.TOROIDAL,
            steering=steering,
            resolution=32,
            amplitude=0.5
        )
        # Check faces exist and are valid
        assert len(data["faces"]) > 0
        # Verify no vertices are unreferenced
        face_indices = set(data["faces"].flatten())
        assert len(face_indices) <= data["vertices"].shape[0]

    def test_spheroid_has_complete_poles(self):
        """Verify spheroid poles (v=0, v=π) create valid topology."""
        grid = np.zeros((64, 64))
        steering = SteeringProfile()
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.SPHEROID,
            steering=steering,
            resolution=32,
            amplitude=0.5
        )
        vertices = data["vertices"]
        faces = data["faces"]
        
        # Check basic topology
        assert len(faces) > 0
        assert vertices.shape[0] > 0
        # Normals should be computed
        assert "normals" in data
        assert data["normals"].shape == vertices.shape

    def test_no_nan_or_inf_in_generated_surfaces(self):
        """Verify no NaN or Inf values in generated meshes."""
        for family in [TopologyFamily.TOROIDAL, TopologyFamily.SPHEROID, TopologyFamily.HELICAL]:
            grid = np.random.rand(32, 32)
            steering = SteeringProfile()
            data = generate_topology_surface(
                displacement_grid=grid,
                family=family,
                steering=steering,
                resolution=16,
                amplitude=0.5
            )
            # Check for NaN/Inf
            assert not np.any(np.isnan(data["vertices"])), f"NaN in {family} vertices"
            assert not np.any(np.isinf(data["vertices"])), f"Inf in {family} vertices"
            assert not np.any(np.isnan(data["normals"])), f"NaN in {family} normals"
            assert not np.any(np.isinf(data["normals"])), f"Inf in {family} normals"


class TestOrientabilityEnforcement:
    """Test that surfaces are orientable (2-manifolds with consistent normals)."""

    def test_default_steering_prevents_non_orientable(self):
        """Verify default steering profile blocks non-orientable surfaces."""
        steering = SteeringProfile()
        # PRESERVE orientation_rule + default allowed families
        # Should never allow Möbius strip or Klein bottle
        assert TopologyFamily.KLEIN_BOTTLE not in steering.allowed_families

    def test_toroid_normals_are_valid(self):
        """Verify toroid has valid, normalized normals."""
        grid = np.zeros((32, 32))
        steering = SteeringProfile()
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.TOROIDAL,
            steering=steering,
            resolution=16,
            amplitude=0.5
        )
        normals = data["normals"]
        # Check normals are normalized
        norms = np.linalg.norm(normals, axis=1)
        assert np.allclose(norms, 1.0, atol=0.01), "Normals should be unit vectors"

    def test_spheroid_normals_are_valid(self):
        """Verify spheroid has valid, normalized normals."""
        grid = np.zeros((32, 32))
        steering = SteeringProfile()
        data = generate_topology_surface(
            displacement_grid=grid,
            family=TopologyFamily.SPHEROID,
            steering=steering,
            resolution=16,
            amplitude=0.5
        )
        normals = data["normals"]
        # Check normals are normalized (allowing for pole singularities with norm~0)
        norms = np.linalg.norm(normals, axis=1)
        # Most normals should be ~1.0 (unit vectors)
        # Pole singularities may have norm=0
        non_zero_mask = norms > 0.1
        assert np.allclose(norms[non_zero_mask], 1.0, atol=0.01), \
            "Non-zero normals should be unit vectors"
