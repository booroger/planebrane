"""
Verification script for Topology Intent Layer.
"""

import cv2
import numpy as np
import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.topology.intent import TopologyFamily, SteeringProfile, OrientationRule
from app.core.topology.analyzer import TopologyAnalyzer
from app.core.geometry3d.mapping import map_image_to_3d


def create_synthetic_image(type_name: str, size: int = 128) -> np.ndarray:
    """Create synthetic test images."""
    img = np.zeros((size, size), dtype=np.uint8)
    center = (size // 2, size // 2)

    if type_name == "circle":
        # Concentric circles
        for r in range(10, 60, 10):
            cv2.circle(img, center, r, 255, 2)
    elif type_name == "stripes":
        # Vertical stripes
        for x in range(0, size, 20):
            cv2.line(img, (x, 0), (x, size), 255, 5)
    elif type_name == "grid":
        # Grid
        for x in range(0, size, 20):
            cv2.line(img, (x, 0), (x, size), 255, 2)
        for y in range(0, size, 20):
            cv2.line(img, (0, y), (size, y), 255, 2)
    elif type_name == "noise":
        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, (size, size), dtype=np.uint8)

    return img


def test_analysis():
    print("Testing Analysis...")
    analyzer = TopologyAnalyzer()

    # 1. Toroid Check
    circle_img = create_synthetic_image("circle")
    cv2.imwrite("temp_circle.png", circle_img)
    family, conf = analyzer.analyze("temp_circle.png")
    print(f"Circle Image -> {family} (Confidence: {conf})")

    # DEBUG: Inspect features manually if needed
    if family != TopologyFamily.TOROIDAL:
        print("DEBUG: Circle Classification Failed. Dumping Features:")
        features = analyzer._extract_features(circle_img)  # HACK: Access protected method
        print(f"Symmetry: {features.get('symmetry')}")
        print(f"Radial: {features.get('radial')}")
        print(f"Concentric: {features.get('concentric_circles')}")

    if family != TopologyFamily.TOROIDAL:
        print("FAILED: Circle was not Toroidal.")
        sys.exit(1)

    # 2. Lattice Check
    grid_img = create_synthetic_image("grid")
    cv2.imwrite("temp_grid.png", grid_img)
    family, conf = analyzer.analyze("temp_grid.png")
    print(f"Grid Image -> {family} (Confidence: {conf})")
    assert family == TopologyFamily.LATTICE_RESONATOR, f"Grid should be Lattice, got {family}"

    # 3. Planar/Helical Check (Stripes often ambiguous but definitely not Toroid)
    stripes_img = create_synthetic_image("stripes")
    cv2.imwrite("temp_stripes.png", stripes_img)
    family, conf = analyzer.analyze("temp_stripes.png")
    print(f"Stripes Image -> {family} (Confidence: {conf})")
    # Stripes usually mapped to Helical (linear periodicity) or Planar
    assert family in [TopologyFamily.HELICAL, TopologyFamily.PLANAR_RELIEF], (
        f"Stripes should be Helical or Planar, got {family}"
    )


def test_generation():
    print("\nTesting Generation...")

    # Force Toroid
    steering = {"force_family": "toroidal"}
    result = map_image_to_3d("temp_circle.png", steering=steering)
    verts = result["vertices"]
    print(f"Generated Toroid Vertices: {len(verts)}")
    assert result["topology_family"] == TopologyFamily.TOROIDAL

    # Check bounds (Toroid usually roughly within -1 to 1 unless scaled)
    # Just check it ran
    assert len(verts) > 0


def test_negative_klein():
    print("\nTesting Negative Klein Bottle Safety...")
    # Even if we strictly preserve orientation, we should NEVER get Klein Bottle automatically
    analyzer = TopologyAnalyzer()

    # Create ambiguous image
    img = create_synthetic_image("noise")
    cv2.imwrite("temp_noise.png", img)

    steering = SteeringProfile(orientation_rule=OrientationRule.PRESERVE)
    family, conf = analyzer.analyze("temp_noise.png", steering)

    print(f"Noise Image + Preserve Orientation -> {family}")
    assert family != TopologyFamily.KLEIN_BOTTLE, "Should never auto-detect Klein Bottle"


if __name__ == "__main__":
    try:
        test_analysis()
        test_generation()
        test_negative_klein()
        print("\nALL VERIFICATION TESTS PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if os.path.exists("temp_circle.png"):
            os.remove("temp_circle.png")
        if os.path.exists("temp_grid.png"):
            os.remove("temp_grid.png")
        if os.path.exists("temp_stripes.png"):
            os.remove("temp_stripes.png")
        if os.path.exists("temp_noise.png"):
            os.remove("temp_noise.png")
