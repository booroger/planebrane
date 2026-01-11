"""
Analyzer for determining Topological Intent from 2D patterns.
Based on image features (symmetry, geometry), maps a 2D pattern
to a target 3D manifold family with a confidence score.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any

from app.core.topology.intent import TopologyFamily, SteeringProfile, PhaseBehavior
from app.core.image_analysis import symmetry
from app.core.image_analysis import geometry_extractor
from app.core.image_analysis import preprocessor


class TopologyAnalyzer:
    """
    Analyzes 2D patterns to suggest a 3D topology family.
    """

    def __init__(self):
        pass

    def analyze(
        self, input_obj, steering: SteeringProfile = None
    ) -> Tuple[TopologyFamily, float]:
        """
        Analyze an image or array and determine the best fit topology family.

        Args:
            input_obj: Path to the image file OR a numpy ndarray representing grayscale image.
            steering: Optional steering profile to constrain or force results.

        Returns:
            Tuple of (TopologyFamily, confidence_score [0.0 - 1.0]).
        """
        # Default steering if None
        if steering is None:
            steering = SteeringProfile()
        elif isinstance(steering, dict):
            # Construct a SteeringProfile-like object from dict without raising validation errors
            steering_obj = SteeringProfile()
            for k, v in steering.items():
                try:
                    setattr(steering_obj, k, v)
                except Exception:
                    # best-effort assignment; ignore attributes that can't be set
                    pass
            steering = steering_obj


        # 1. Force Family Override
        if steering.force_family:
            # Safety: compare orientation safely
            orientation = getattr(steering, "orientation_rule", None)
            orientation_value = orientation.value if hasattr(orientation, "value") else str(orientation)
            force_family_value = steering.force_family.value if hasattr(steering.force_family, "value") else str(steering.force_family)
            if force_family_value == TopologyFamily.KLEIN_BOTTLE.value and orientation_value == "preserve":
                raise ValueError("KLEIN_BOTTLE cannot be produced when orientation_rule == PRESERVE")
            return steering.force_family, 1.0

        # 2. Load and Preprocess Image (accept numpy arrays for tests)
        try:
            if isinstance(input_obj, np.ndarray):
                img = input_obj
            else:
                img = cv2.imread(input_obj, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError(f"Could not load image: {input_obj}")

            # Simple normalization
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

        except Exception as e:
            # Fallback on error
            print(f"Analysis error: {e}")
            return TopologyFamily.PLANAR_RELIEF, 0.0

        # 3. Extract Features
        features = self._extract_features(img)

        # Quick heuristics override: concentric circles -> TOROIDAL (require 3+ peaks to avoid noise)
        if features.get("concentric_circles") and len(features.get("concentric_circles", [])) >= 3:
            return TopologyFamily.TOROIDAL, 0.8

        # 4. Calculate Family Scores
        scores: Dict[TopologyFamily, float] = {
            TopologyFamily.TOROIDAL: self._score_toroidal(features),
            TopologyFamily.HELICAL: self._score_helical(features),
            TopologyFamily.LATTICE_RESONATOR: self._score_lattice(features),
            TopologyFamily.COMPACTIFIED_FOLDED: self._score_compactified(features),
            TopologyFamily.PLANAR_RELIEF: 0.5,  # Baseline
            # KLEIN_BOTTLE: Never auto-detect; only via explicit force_family
        }

        # 5. Filter by Steering Constraints
        if steering.allowed_families:
            for family in scores:
                if (
                    family not in steering.allowed_families
                    and family != TopologyFamily.PLANAR_RELIEF
                ):
                    scores[family] = 0.0

        # 6. Safety Checks (e.g. Klein Bottle)
        # We generally do not suggest Klein Bottle automatically unless very specific conditions met
        # or manually requested, so we keep it out of the auto-scoring for now.

        # 7. Select Best Fit
        best_family = TopologyFamily.PLANAR_RELIEF
        best_score = 0.0

        for family, score in scores.items():
            if score > best_score:
                best_score = score
                best_family = family

        # 8. Threshold Fallback
        # If the best non-planar score is weak, fallback to planar
        if best_family != TopologyFamily.PLANAR_RELIEF and best_score < 0.6:
            return TopologyFamily.PLANAR_RELIEF, 0.5

        return best_family, best_score

    def _extract_features(self, img: np.ndarray) -> Dict[str, Any]:
        """Run standard image analysis tools."""

        # Symmetry Analysis
        sym_result = symmetry.detect_symmetry(img)

        # Radial Analysis
        center = sym_result.get("rotational_center")
        if center is None:
            center = (img.shape[1] / 2, img.shape[0] / 2)

        radial_result = symmetry.detect_radial_pattern(img, center)

        # Geometric Analysis (requires "edges_result" usually, we'll mock or compute minimum)
        # Ensure uint8 for edge detection
        if img.dtype != np.uint8:
            img_u8 = (img / img.max() * 255).astype(np.uint8) if img.max() > 1 else (img * 255).astype(np.uint8)
        else:
            img_u8 = img
        edges = cv2.Canny(img_u8, 50, 150)
        edges_result = {
            "edge_density": np.count_nonzero(edges) / edges.size,
            "dominant_angles": [],  # Simplified for now
        }
        geo_result = geometry_extractor.extract_geometry(img_u8, edges_result)

        # Concentric Circles: prefer geometry_extractor result but try HoughCircles then radial peaks as fallback
        circles = geometry_extractor.find_concentric_circles(img, center)
        if not circles:
            # Hough Circle detection (more robust for explicit rings)
            try:
                img_blur = cv2.medianBlur(img, 5)
                detected = cv2.HoughCircles(
                    img_blur,
                    cv2.HOUGH_GRADIENT,
                    dp=1.2,
                    minDist=10,
                    param1=50,
                    param2=30,
                    minRadius=2,
                    maxRadius=min(img.shape) // 2,
                )
                if detected is not None:
                    circles = detected[0].tolist()
            except Exception:
                pass

        if not circles:
            # quick radial peak detection on a downsampled grid
            try:
                from scipy.signal import find_peaks
                h, w = img.shape
                cy, cx = int(h / 2), int(w / 2)
                y, x = np.indices(img.shape)
                r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                maxr = int(r.max())
                bins = np.linspace(0, maxr, min(128, maxr) + 1)
                radial = np.zeros(len(bins) - 1)
                for i in range(len(radial)):
                    mask = (r >= bins[i]) & (r < bins[i + 1])
                    if mask.sum() > 0:
                        radial[i] = img[mask].mean()
                # smooth
                from scipy.ndimage import gaussian_filter1d
                radial_s = gaussian_filter1d(radial, sigma=1)
                peaks, _ = find_peaks(radial_s, height=radial_s.mean() + radial_s.std() * 0.25, distance=3)
                circles = [float(p) for p in peaks]
            except Exception:
                circles = []

        return {
            "symmetry": sym_result,
            "radial": radial_result,
            "geometry": geo_result,
            "concentric_circles": circles,
            "img_shape": img.shape,
        }

    def _score_toroidal(self, features: Dict[str, Any]) -> float:
        """
        Score for Toroidal Topology.
        Heuristics:
        - High Rotational Symmetry
        - Concentric Circles present
        - Radial pattern
        """
        score = 0.0

        sym = features["symmetry"]
        radial = features["radial"]
        circles = features["concentric_circles"]

        # 1. Rotational Symmetry is key for toroids
        if sym.get("has_rotational"):
            score += 0.4
            if sym.get("rotational_order", 0) > 2:
                score += 0.1

        # 2. Concentric Circles (strong indicator of donut/ring structure)
        # Allow even 1 circle to contribute slightly, but prefer >1
        if len(circles) > 0:
            score += 0.2
        if len(circles) > 1:
            score += 0.2

        # 3. Radial definition
        if radial.get("is_radial"):
            score += 0.2

        return min(score, 1.0)

    def _score_helical(self, features: Dict[str, Any]) -> float:
        """
        Score for Helical/Solenoid Topology.
        Heuristics:
        - Rotational symmetry
        - BUT with angular drift or spiral arms (difficult to detect perfectly,
          but usually lacks perfect concentric circles)
        - High aspect ratio in bounding box can sometimes hint, but mostly we look for
          rotational symmetry WTHOUT concentric rings.
        """
        score = 0.0

        sym = features["symmetry"]
        circles = features["concentric_circles"]
        radial = features["radial"]

        # 1. Rotational Symmetry
        if sym.get("has_rotational"):
            score += 0.3

        # 2. Lack of concentric circles (differentiates from Toroid)
        if len(circles) <= 1:
            score += 0.2

        # 3. Radial arms (spirals often read as radial arms)
        if radial.get("is_radial") and radial.get("num_arms", 0) > 0:
            score += 0.2

        # 4. Periodicity (if we implemented linear stripe detection, would go here)
        # For now, we piggyback on Repetition Frequency
        freq = features["geometry"].get("repetition_frequency")
        if freq and freq > 0:
            score += 0.1

        return min(score, 1.0)

    def _score_lattice(self, features: Dict[str, Any]) -> float:
        """
        Score for Lattice/Resonator Topology.
        Heuristics:
        - High repetition frequency (grid-like)
        - High reflectional symmetry (mirror axes)
        """
        score = 0.0

        geo = features["geometry"]
        sym = features["symmetry"]

        # 1. Repetition Frequency
        freq = geo.get("repetition_frequency")
        if freq and freq > 2:
            score += 0.5
            if freq > 5:
                score += 0.2

        # 2. Reflectional Symmetry (Boxes/Grids have 2+ axes)
        axes = sym.get("reflection_axes", [])
        if len(axes) >= 2:
            score += 0.3

        return min(score, 1.0)

    def _score_compactified(self, features: Dict[str, Any]) -> float:
        """
        Score for Compactified (Calabi-Yau) Topology.
        Heuristics:
        - High geometric complexity
        - Low symmetry (organic/folded look)
        - Irregular shapes
        """
        score = 0.0

        geo = features["geometry"]
        sym = features["symmetry"]

        # 1. Complexity
        complexity = geo.get("complexity_score", 0.0)
        if complexity > 0.7:
            score += 0.4
        elif complexity > 0.5:
            score += 0.2

        # 2. Low Symmetry (Chaos often implies complex manifolds)
        if not sym.get("has_rotational") and not sym.get("has_reflectional"):
            score += 0.3

        # 3. Baseline for mysterious shapes
        if complexity > 0.3:
            score += 0.1

        return min(score, 1.0)
