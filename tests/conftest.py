"""Test fixtures and configuration."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import cv2


@pytest.fixture
def sample_image_path():
    """Create a sample geometric pattern image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Create a simple circular pattern
        img = np.zeros((256, 256), dtype=np.uint8)
        cv2.circle(img, (128, 128), 50, 255, 2)
        cv2.circle(img, (128, 128), 80, 255, 2)
        cv2.circle(img, (128, 128), 110, 255, 2)
        cv2.imwrite(f.name, img)
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_spiral_image_path():
    """Create a sample spiral pattern image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = np.zeros((256, 256), dtype=np.uint8)
        
        # Draw a simple spiral
        cx, cy = 128, 128
        for i in range(1000):
            t = i / 100
            r = 5 + t * 10
            x = int(cx + r * np.cos(t * 2))
            y = int(cy + r * np.sin(t * 2))
            if 0 <= x < 256 and 0 <= y < 256:
                cv2.circle(img, (x, y), 2, 255, -1)
        
        cv2.imwrite(f.name, img)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_grid_image_path():
    """Create a sample grid pattern image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = np.zeros((256, 256), dtype=np.uint8)
        
        # Draw grid lines
        for i in range(0, 256, 32):
            cv2.line(img, (i, 0), (i, 255), 255, 1)
            cv2.line(img, (0, i), (255, i), 255, 1)
        
        cv2.imwrite(f.name, img)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_hexagon_image_path():
    """Create a sample hexagonal pattern image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = np.zeros((256, 256), dtype=np.uint8)
        
        # Draw hexagon
        cx, cy = 128, 128
        radius = 80
        pts = []
        for i in range(6):
            angle = np.pi / 3 * i - np.pi / 6
            x = int(cx + radius * np.cos(angle))
            y = int(cy + radius * np.sin(angle))
            pts.append((x, y))
        
        for i in range(6):
            cv2.line(img, pts[i], pts[(i + 1) % 6], 255, 2)
        
        cv2.imwrite(f.name, img)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_points():
    """Sample 2D points for testing."""
    return [
        {"x": 0.0, "y": 0.0, "weight": 1.0, "feature_type": "center"},
        {"x": 0.5, "y": 0.0, "weight": 0.8, "feature_type": "edge"},
        {"x": 0.0, "y": 0.5, "weight": 0.8, "feature_type": "edge"},
        {"x": -0.5, "y": 0.0, "weight": 0.8, "feature_type": "edge"},
        {"x": 0.0, "y": -0.5, "weight": 0.8, "feature_type": "edge"},
        {"x": 0.35, "y": 0.35, "weight": 0.6, "feature_type": "corner"},
        {"x": -0.35, "y": 0.35, "weight": 0.6, "feature_type": "corner"},
        {"x": -0.35, "y": -0.35, "weight": 0.6, "feature_type": "corner"},
        {"x": 0.35, "y": -0.35, "weight": 0.6, "feature_type": "corner"},
    ]
