"""Image upload and processing endpoints."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.config import get_settings
from app.api.routes.auth import get_current_user

router = APIRouter()
settings = get_settings()

# In-memory image store (replace with database)
images_db: dict[str, dict] = {}


class ImageMetadata(BaseModel):
    """Image metadata schema."""
    id: str
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    uploaded_at: datetime
    analyzed: bool = False
    user_id: int


class ImageUploadResponse(BaseModel):
    """Image upload response."""
    id: str
    filename: str
    message: str


class ImageAnalysisRequest(BaseModel):
    """Image analysis parameters."""
    edge_threshold_low: int = 50
    edge_threshold_high: int = 150
    blur_kernel_size: int = 5
    detect_symmetry: bool = True
    extract_geometry: bool = True


class EdgeDetectionResult(BaseModel):
    """Edge detection results."""
    edge_count: int
    edge_density: float
    dominant_angles: list[float]
    contour_count: int


class SymmetryResult(BaseModel):
    """Symmetry detection results."""
    has_rotational: bool
    rotational_order: int | None = None
    rotational_center: tuple[float, float] | None = None
    has_reflectional: bool
    reflection_axes: list[float] = []
    symmetry_score: float


class GeometryResult(BaseModel):
    """Geometric parameter extraction results."""
    bounding_box: tuple[int, int, int, int]
    centroid: tuple[float, float]
    estimated_radius: float | None = None
    dominant_angles: list[float]
    repetition_frequency: int | None = None
    complexity_score: float


class ImageAnalysisResponse(BaseModel):
    """Complete image analysis response."""
    image_id: str
    edges: EdgeDetectionResult | None = None
    symmetry: SymmetryResult | None = None
    geometry: GeometryResult | None = None
    processing_time_ms: float


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: Annotated[UploadFile, File(description="Geometric pattern image")],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Upload a geometric pattern image for processing."""
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )
    
    # Generate unique filename
    image_id = str(uuid.uuid4())
    filename = f"{image_id}{file_ext}"
    file_path = settings.upload_dir / filename
    
    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # Get image dimensions using PIL
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        width, height = img.size
    except Exception:
        width, height = None, None
    
    # Store metadata
    images_db[image_id] = {
        "id": image_id,
        "filename": filename,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "width": width,
        "height": height,
        "uploaded_at": datetime.utcnow(),
        "analyzed": False,
        "user_id": current_user["id"],
        "file_path": str(file_path),
    }
    
    return {
        "id": image_id,
        "filename": filename,
        "message": "Image uploaded successfully",
    }


@router.get("/{image_id}", response_model=ImageMetadata)
async def get_image(
    image_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get image metadata by ID."""
    image = images_db.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if image["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return image


@router.post("/{image_id}/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    image_id: str,
    params: ImageAnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Trigger full analysis on an uploaded image."""
    import time
    start_time = time.time()
    
    image = images_db.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if image["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Import analysis modules
    from app.core.image_analysis import analyze_image as run_analysis
    
    try:
        results = await run_analysis(
            image_path=image["file_path"],
            edge_threshold_low=params.edge_threshold_low,
            edge_threshold_high=params.edge_threshold_high,
            blur_kernel_size=params.blur_kernel_size,
            detect_symmetry=params.detect_symmetry,
            extract_geometry=params.extract_geometry,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
    
    # Mark as analyzed
    images_db[image_id]["analyzed"] = True
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "image_id": image_id,
        "edges": results.get("edges"),
        "symmetry": results.get("symmetry"),
        "geometry": results.get("geometry"),
        "processing_time_ms": processing_time,
    }


@router.get("/{image_id}/edges", response_model=EdgeDetectionResult)
async def get_edges(
    image_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get edge detection results for an image."""
    image = images_db.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if not image.get("analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet. Call /analyze first.",
        )
    
    # Return cached edge results
    from app.core.image_analysis import get_cached_edges
    edges = get_cached_edges(image_id)
    
    if not edges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge detection results not found",
        )
    
    return edges


@router.get("/{image_id}/symmetry", response_model=SymmetryResult)
async def get_symmetry(
    image_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get symmetry analysis results for an image."""
    image = images_db.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if not image.get("analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet. Call /analyze first.",
        )
    
    from app.core.image_analysis import get_cached_symmetry
    symmetry = get_cached_symmetry(image_id)
    
    if not symmetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symmetry analysis results not found",
        )
    
    return symmetry
