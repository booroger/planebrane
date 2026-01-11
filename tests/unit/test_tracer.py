"""Unit tests for tracer module."""

import pytest
import numpy as np
import cv2


class TestThresholdImage:
    """Test image thresholding functions."""

    def test_threshold_image_binary(self):
        """Test binary thresholding."""
        from app.core.image_analysis.tracer import threshold_image

        # Create test image with gradient
        img = np.zeros((100, 100), dtype=np.uint8)
        img[:, 50:] = 255  # Right half is white

        binary = threshold_image(img, threshold_value=128, method="binary")

        assert binary is not None
        assert binary.shape == img.shape
        assert binary.dtype == np.uint8
        # Check that left half is 0 and right half is 255
        assert np.all(binary[:, :50] == 0)
        assert np.all(binary[:, 50:] == 255)

    def test_threshold_image_otsu(self):
        """Test Otsu's thresholding."""
        from app.core.image_analysis.tracer import threshold_image

        # Create bimodal image
        img = np.zeros((100, 100), dtype=np.uint8)
        img[25:75, 25:75] = 200  # Bright center

        binary = threshold_image(img, method="otsu")

        assert binary is not None
        assert np.max(binary) == 255 or np.max(binary) == 0  # Binary values

    def test_threshold_image_adaptive(self):
        """Test adaptive thresholding."""
        from app.core.image_analysis.tracer import threshold_image

        # Create image with varying intensity
        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img, (50, 50), 30, 200, -1)

        binary = threshold_image(img, method="adaptive")

        assert binary is not None
        assert binary.shape == img.shape

    def test_threshold_image_invert(self):
        """Test image inversion."""
        from app.core.image_analysis.tracer import threshold_image

        img = np.zeros((50, 50), dtype=np.uint8)
        img[10:40, 10:40] = 255

        normal = threshold_image(img, method="binary", invert=False)
        inverted = threshold_image(img, method="binary", invert=True)

        # Inverted should be opposite
        assert not np.array_equal(normal, inverted)
        assert np.array_equal(normal, cv2.bitwise_not(inverted))


class TestExtractPlotPoints:
    """Test plot point extraction."""

    def test_extract_plot_points_basic(self):
        """Test basic point extraction."""
        from app.core.image_analysis.tracer import extract_plot_points

        # Create simple binary image with known points
        binary = np.zeros((10, 10), dtype=np.uint8)
        binary[5, 5] = 255

        points = extract_plot_points(binary, normalize=False)

        assert len(points) == 1
        assert points[0] == (5.0, 5.0)

    def test_extract_plot_points_normalized(self):
        """Test normalized point extraction."""
        from app.core.image_analysis.tracer import extract_plot_points

        # Create binary image with corners marked
        binary = np.zeros((11, 11), dtype=np.uint8)
        binary[0, 0] = 255  # Top-left
        binary[10, 10] = 255  # Bottom-right

        points = extract_plot_points(binary, normalize=True)

        assert len(points) == 2
        # Top-left should be near (-1, -1)
        # Bottom-right should be near (1, 1)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        assert min(xs) == pytest.approx(-1.0)
        assert max(xs) == pytest.approx(1.0)

    def test_extract_plot_points_empty(self):
        """Test empty image returns no points."""
        from app.core.image_analysis.tracer import extract_plot_points

        binary = np.zeros((10, 10), dtype=np.uint8)
        points = extract_plot_points(binary)

        assert len(points) == 0

    def test_extract_plot_points_sampling(self):
        """Test point sampling for performance."""
        from app.core.image_analysis.tracer import extract_plot_points

        # Create image with many points
        binary = np.ones((100, 100), dtype=np.uint8) * 255

        all_points = extract_plot_points(binary, sample_step=1)
        sampled = extract_plot_points(binary, sample_step=10)

        assert len(sampled) < len(all_points)


class TestCreatePlotGrid:
    """Test plot grid creation."""

    def test_create_plot_grid_resize(self):
        """Test grid resizing."""
        from app.core.image_analysis.tracer import create_plot_grid

        binary = np.zeros((200, 200), dtype=np.uint8)
        binary[50:150, 50:150] = 255

        grid = create_plot_grid(binary, grid_resolution=64)

        assert grid.shape == (64, 64)
        assert grid.dtype == np.float32
        assert np.max(grid) <= 1.0
        assert np.min(grid) >= 0.0


class TestDistanceFalloff:
    """Test distance falloff function."""

    def test_apply_distance_falloff(self):
        """Test distance-based falloff."""
        from app.core.image_analysis.tracer import apply_distance_falloff

        # Create binary image with line
        binary = np.zeros((50, 50), dtype=np.uint8)
        binary[25, :] = 255  # Horizontal line

        falloff = apply_distance_falloff(binary, falloff_radius=5)

        assert falloff.shape == binary.shape
        assert falloff.dtype == np.float32
        # Line pixels should be 1.0
        assert falloff[25, 25] == pytest.approx(1.0)
        # Far away pixels should be 0.0
        assert falloff[0, 0] == pytest.approx(0.0)
        # Adjacent pixels should have gradient
        assert 0.0 < falloff[24, 25] < 1.0
