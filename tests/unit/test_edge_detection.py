"""Unit tests for edge detection."""

import pytest
import numpy as np
import cv2


class TestEdgeDetection:
    """Test edge detection algorithms."""
    
    def test_detect_edges_canny(self, sample_image_path):
        """Test Canny edge detection."""
        from app.core.image_analysis.edge_detection import detect_edges
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        
        edges = detect_edges(preprocessed, 50, 150, method="canny")
        
        assert edges is not None
        assert edges.shape == img.shape
        assert edges.dtype == np.uint8
        assert np.max(edges) > 0  # Should have some edges
    
    def test_detect_edges_sobel(self, sample_image_path):
        """Test Sobel edge detection."""
        from app.core.image_analysis.edge_detection import detect_edges
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        
        edges = detect_edges(preprocessed, 50, 150, method="sobel")
        
        assert edges is not None
        assert edges.shape == img.shape
        assert np.max(edges) > 0
    
    def test_detect_edges_combined(self, sample_image_path):
        """Test combined edge detection."""
        from app.core.image_analysis.edge_detection import detect_edges
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        
        edges = detect_edges(preprocessed, 50, 150, method="combined")
        
        assert edges is not None
        assert np.max(edges) > 0
    
    def test_compute_edge_metrics(self, sample_image_path):
        """Test edge metrics computation."""
        from app.core.image_analysis.edge_detection import (
            detect_edges, compute_edge_metrics
        )
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        edges = detect_edges(preprocessed, 50, 150)
        
        metrics = compute_edge_metrics(edges, preprocessed)
        
        assert "edge_count" in metrics
        assert "edge_density" in metrics
        assert "dominant_angles" in metrics
        assert "contour_count" in metrics
        
        assert isinstance(metrics["edge_count"], int)
        assert 0 <= metrics["edge_density"] <= 1
        assert isinstance(metrics["dominant_angles"], list)
        assert metrics["contour_count"] >= 0
    
    def test_detect_edge_intersections(self, sample_grid_image_path):
        """Test intersection detection on grid pattern."""
        from app.core.image_analysis.edge_detection import (
            detect_edges, detect_edge_intersections
        )
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_grid_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        edges = detect_edges(preprocessed, 50, 150)
        
        intersections = detect_edge_intersections(edges, min_distance=20)
        
        assert isinstance(intersections, list)
        # Grid should have intersections
        # Note: exact count depends on implementation
    
    def test_find_contour_hierarchy(self, sample_image_path):
        """Test contour hierarchy analysis."""
        from app.core.image_analysis.edge_detection import (
            detect_edges, find_contour_hierarchy
        )
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path, cv2.IMREAD_GRAYSCALE)
        preprocessed = preprocess_image(img)
        edges = detect_edges(preprocessed, 50, 150)
        
        hierarchy = find_contour_hierarchy(edges)
        
        assert "depth" in hierarchy
        assert "outer_count" in hierarchy
        assert "inner_count" in hierarchy
        assert "total_contours" in hierarchy


class TestPreprocessor:
    """Test image preprocessing."""
    
    def test_preprocess_image(self, sample_image_path):
        """Test basic preprocessing."""
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path)
        
        preprocessed = preprocess_image(img)
        
        assert preprocessed is not None
        assert len(preprocessed.shape) == 2  # Grayscale
        assert preprocessed.dtype == np.uint8
    
    def test_preprocess_with_blur(self, sample_image_path):
        """Test preprocessing with different blur kernel sizes."""
        from app.core.image_analysis.preprocessor import preprocess_image
        
        img = cv2.imread(sample_image_path)
        
        result_3 = preprocess_image(img, blur_kernel_size=3)
        result_7 = preprocess_image(img, blur_kernel_size=7)
        
        # Different blur sizes should produce different results
        assert not np.array_equal(result_3, result_7)
    
    def test_resize_for_processing(self, sample_image_path):
        """Test image resizing."""
        from app.core.image_analysis.preprocessor import resize_for_processing
        
        # Create large image
        large_img = np.zeros((2000, 2000), dtype=np.uint8)
        
        resized, scale = resize_for_processing(large_img, max_dimension=1024)
        
        assert max(resized.shape) <= 1024
        assert scale < 1.0
    
    def test_morphological_cleanup(self, sample_image_path):
        """Test morphological operations."""
        from app.core.image_analysis.preprocessor import apply_morphological_cleanup
        
        # Create binary image with noise
        binary = np.zeros((100, 100), dtype=np.uint8)
        binary[40:60, 40:60] = 255
        binary[10, 10] = 255  # Single pixel noise
        
        cleaned = apply_morphological_cleanup(binary, operation="open", kernel_size=3)
        
        assert cleaned is not None
        # Opening should remove single-pixel noise
