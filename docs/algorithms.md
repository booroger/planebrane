# PlaneBrane Algorithm Documentation

This document provides detailed mathematical explanations of the algorithms used in PlaneBrane.

## Table of Contents

1. [Edge Detection](#edge-detection)
2. [Symmetry Detection](#symmetry-detection)
3. [Pattern Classification](#pattern-classification)
4. [Point Extraction](#point-extraction)
5. [3D Geometry Generation](#3d-geometry-generation)

---

## Edge Detection

### Canny Edge Detection

The Canny algorithm is a multi-stage edge detector:

1. **Noise Reduction**: Apply Gaussian blur

   ```
   G(x,y) = (1/2πσ²) × e^(-(x²+y²)/2σ²)
   ```

2. **Gradient Calculation**: Using Sobel operators

   ```
   Gx = [-1 0 +1]     Gy = [-1 -2 -1]
        [-2 0 +2]          [ 0  0  0]
        [-1 0 +1]          [+1 +2 +1]
   ```

3. **Gradient Magnitude and Direction**:

   ```
   |G| = √(Gx² + Gy²)
   θ = atan2(Gy, Gx)
   ```

4. **Non-Maximum Suppression**: Thin edges to 1-pixel width

5. **Hysteresis Thresholding**: Connect strong edges

### Combined Edge Detection

We combine Canny and Sobel results with weighted averaging:

```python
combined = 0.6 × canny_edges + 0.4 × sobel_magnitude
```

This captures both fine detail (Canny) and gradient strength (Sobel).

---

## Symmetry Detection

### Rotational Symmetry

We detect rotational symmetry by comparing the image with rotated versions:

```python
for angle in [30°, 45°, 60°, 72°, 90°, 120°, 180°]:
    rotated = rotate(image, angle, center)
    correlation = normalized_cross_correlation(image, rotated)
```

**Normalized Cross-Correlation (NCC)**:

```
NCC = Σ[(I₁ - μ₁)(I₂ - μ₂)] / (σ₁ × σ₂ × N)
```

The **rotational order** is `360° / angle` for the best matching angle.

### Reflectional Symmetry

We test mirror symmetry across four axes:

| Axis | Transformation |
|------|----------------|
| Horizontal (0°) | Vertical flip |
| Vertical (90°) | Horizontal flip |
| Diagonal (45°) | Rotate 45° → flip → rotate -45° |
| Diagonal (135°) | Rotate 135° → flip → rotate -135° |

### Symmetry Score

Combined score weighing rotation and reflection:

```
score = 0.6 × rotation_correlation + 0.4 × (num_axes / 4)
```

---

## Pattern Classification

### Classification Decision Tree

```
                    Input Image
                         │
                         ▼
              ┌──────────────────────┐
              │ Has center of rotation? │
              └──────────────────────┘
                    │          │
                   Yes         No
                    │          │
                    ▼          ▼
            ┌────────────┐  ┌────────────┐
            │ Concentric? │  │ Grid pattern? │
            └────────────┘  └────────────┘
                 │  │            │   │
                Yes No          Yes  No
                 │  │            │   │
                 ▼  ▼            ▼   ▼
             Radial Spiral?   Analyze  Mixed
                      │       angles
                     Yes/No
                      │
                 ▼         ▼
              Spiral    Radial Symmetry
```

### Spiral Detection

Spirals exhibit a monotonic relationship between angle and radius:

```python
# Convert edge points to polar coordinates
r = √(x² + y²)
θ = atan2(y, x)

# Compute Spearman correlation
ρ = spearman_correlation(θ, r)

# Spiral confidence = |ρ|
is_spiral = |ρ| > 0.6
```

### Polygonal Classification

We analyze contours using polygon approximation:

```python
epsilon = 0.02 × perimeter
approximated = cv2.approxPolyDP(contour, epsilon, closed=True)
num_vertices = len(approximated)
```

**Circularity** distinguishes polygons from circles:

```
circularity = 4π × area / perimeter²
```

- Circle: circularity ≈ 1.0
- Square: circularity ≈ 0.785
- Triangle: circularity ≈ 0.604

---

## Point Extraction

### Feature Detection

We extract points from multiple feature types:

| Feature | Method | Weight |
|---------|--------|--------|
| Edge contours | Contour sampling | 1.0 |
| Corners | Shi-Tomasi detector | 1.5 |
| Intersections | Skeleton junction detection | 1.5 |
| Symmetry center | Moment centroid | 2.0 |

### Non-Maximum Suppression

To ensure minimum spacing between points:

```python
Algorithm: Greedy NMS
1. Sort points by weight (descending)
2. For each point P in sorted order:
   a. If distance(P, all selected points) >= min_distance:
      - Add P to selected set
3. Return selected points
```

### Adaptive Point Density

Point density is controlled by:

```python
effective_points = base_points × density_multiplier
step = max(1, total_contour_points / effective_points)
```

---

## 3D Geometry Generation

### Icosphere Generation

We use icosahedron subdivision for uniform vertex distribution:

1. **Base Icosahedron** (12 vertices, 20 faces):

   ```
   φ = (1 + √5) / 2  (golden ratio)
   
   Vertices at:
   (±1, ±φ, 0), (0, ±1, ±φ), (±φ, 0, ±1)
   ```

2. **Subdivision**: For each triangle, create 4 new triangles by inserting midpoints on each edge, then project all vertices onto the unit sphere.

### Torus Parametric Equations

```
x(θ, φ) = (R + r·cos(φ)) × cos(θ)
y(θ, φ) = (R + r·cos(φ)) × sin(θ)
z(θ, φ) = r × sin(φ)

where:
  R = major radius (center to tube center)
  r = minor radius (tube radius)
  θ ∈ [0, 2π] (around torus)
  φ ∈ [0, 2π] (around tube)
```

### Helix Parametric Equations

```
x(t) = r × cos(2πnt)
y(t) = r × sin(2πnt)
z(t) = h × t

where:
  r = helix radius
  n = number of turns
  h = total height
  t ∈ [0, 1]
```

### Laplacian Smoothing

For each vertex, move toward the average of its neighbors:

```
v'ᵢ = (1 - λ)vᵢ + λ × (1/|N(i)|) × Σⱼ∈N(i) vⱼ

where:
  λ = smoothing factor (0.0 to 1.0)
  N(i) = set of neighboring vertices
```

### Loop Subdivision

Increases mesh density while smoothing:

1. Insert midpoint vertices on each edge
2. For interior vertices, apply mask:

   ```
   β = 3/(8 × n)  [for n neighbors]
   v' = (1 - n×β)×v + β×Σneighbors
   ```

3. For edge vertices, average endpoints

### Stereographic Projection (2D → Sphere)

Maps a plane to a sphere (north pole at infinity):

```
x₃ = 2x / (1 + x² + y²)
y₃ = 2y / (1 + x² + y²)  
z₃ = (x² + y² - 1) / (1 + x² + y²)
```

---

## Export Formats

### STL (Stereolithography)

Binary format (per triangle):

- Normal vector: 3 × float32
- Vertex 1, 2, 3: 3 × 3 × float32
- Attribute byte count: uint16

### OBJ (Wavefront)

Text format:

```
v x y z          # vertex positions
vn nx ny nz      # vertex normals
f v1//n1 v2//n2 v3//n3  # faces with normals
```

### glTF 2.0

JSON structure with embedded or external binary buffers:

- `accessors`: typed views into buffer data
- `bufferViews`: byte ranges in buffers
- `meshes`: geometry with primitives
- `nodes`: scene hierarchy
