# PlaneBrane

**Geometric Pattern to 3D Transformation API**

A powerful backend system that processes 2D geometric patterns and transforms them into 3D visualizations using computer vision, computational geometry, and 3D graphics algorithms.

![Pattern Examples](docs/images/pattern_examples.jpg)

## Features

### 🔍 Image Analysis Engine

- Multi-algorithm edge detection (Canny, Sobel, combined)
- Symmetry detection (rotational, reflectional)
- Geometric parameter extraction
- Pattern complexity metrics

### 🎯 Pattern Classification

- **Circular/Radial**: Spirals, concentric circles, radial symmetry
- **Polygonal**: Triangles, squares, hexagons, stars
- **Linear**: Grids, stripes, rectilinear structures
- **Mixed**: Complex multi-pattern compositions
- Confidence scoring for all classifications

### 📍 Point Extraction

- Intelligent significant point detection
- Adjustable density and threshold controls
- Feature-weighted point selection
- Non-maximum suppression for optimal spacing

### 🎨 3D Generation

- Pattern-to-3D shape mapping:
  - Circular → Sphere, Torus, Ellipsoid
  - Polygonal → Cube, Hexagonal Prism, Pyramid
  - Spiral → Helix, Twisted Torus
- Parameterized generation (extrusion, curvature, subdivision)
- Mesh transformations (smoothing, twist, taper, bend)

### 📦 Export Formats

- STL (binary and ASCII)
- OBJ
- glTF 2.0
- GLB (binary glTF)

## Quick Start

### Requirements

- Python 3.11+
- PostgreSQL 14+ (optional, for persistence)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/planebrane.git
cd planebrane

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
copy .env.example .env
# Edit .env with your settings
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

### API Documentation

Once running, access the interactive API docs at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |

### Image Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/images/upload` | Upload pattern image |
| POST | `/api/v1/images/{id}/analyze` | Run full analysis |
| GET | `/api/v1/images/{id}/edges` | Get edge detection results |
| GET | `/api/v1/images/{id}/symmetry` | Get symmetry analysis |

### Pattern Classification

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patterns/{id}` | Get classification results |
| GET | `/api/v1/patterns/library` | Browse saved patterns |
| POST | `/api/v1/patterns/library` | Save to library |

### Point Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/points/extract` | Extract significant points |
| PUT | `/api/v1/points/{id}/adjust` | Adjust extraction params |

### 3D Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/models/generate` | Generate 3D model |
| PUT | `/api/v1/models/{id}/params` | Update model params |
| GET | `/api/v1/models/{id}/preview` | Get low-poly preview |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/export/{id}/stl` | Download as STL |
| GET | `/api/v1/export/{id}/obj` | Download as OBJ |
| GET | `/api/v1/export/{id}/gltf` | Download as glTF |
| GET | `/api/v1/export/{id}/glb` | Download as GLB |

## Usage Example

```python
import httpx

# 1. Register and login
client = httpx.Client(base_url="http://localhost:8000")
client.post("/api/v1/auth/register", json={
    "email": "user@example.com",
    "password": "secure123",
    "username": "user"
})
tokens = client.post("/api/v1/auth/login", data={
    "username": "user@example.com",
    "password": "secure123"
}).json()
headers = {"Authorization": f"Bearer {tokens['access_token']}"}

# 2. Upload image
with open("pattern.png", "rb") as f:
    response = client.post(
        "/api/v1/images/upload",
        files={"file": f},
        headers=headers
    )
image_id = response.json()["id"]

# 3. Analyze pattern
analysis = client.post(
    f"/api/v1/images/{image_id}/analyze",
    json={"detect_symmetry": True, "extract_geometry": True},
    headers=headers
).json()

# 4. Get classification
pattern = client.get(
    f"/api/v1/patterns/{image_id}",
    headers=headers
).json()
print(f"Pattern type: {pattern['primary_type']['type']}")

# 5. Extract points
points = client.post(
    "/api/v1/points/extract",
    json={"image_id": image_id, "density": 1.5},
    headers=headers
).json()

# 6. Generate 3D model
model = client.post(
    "/api/v1/models/generate",
    json={
        "points_extraction_id": points["id"],
        "target_shape": "auto",
        "geometry_params": {"subdivision_level": 3}
    },
    headers=headers
).json()

# 7. Export as STL
stl_data = client.get(
    f"/api/v1/export/{model['id']}/stl",
    headers=headers
).content
with open("output.stl", "wb") as f:
    f.write(stl_data)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Project Structure

```
planebrane/
├── app/
│   ├── api/routes/          # REST API endpoints
│   ├── core/
│   │   ├── image_analysis/  # CV algorithms
│   │   ├── classification/  # Pattern classifiers
│   │   ├── point_extraction/# Point extraction
│   │   └── geometry3d/      # 3D generation
│   ├── config.py            # Settings management
│   └── main.py              # FastAPI app
├── tests/                   # Test suite
├── docs/                    # Documentation
└── storage/                 # File storage
```

## Configuration

Key environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size | 50 |
| `DEFAULT_SUBDIVISION_LEVEL` | 3D mesh subdivision | 2 |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

---

Built with ❤️ using FastAPI, OpenCV, NumPy, and Trimesh
