"""3D model generation endpoints."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.api.routes.points import points_cache

router = APIRouter()

# Model storage
models_db: dict[str, dict] = {}


class GeometryParams(BaseModel):
    """3D geometry generation parameters."""
    extrusion_depth: float = Field(default=1.0, ge=0.1, le=10.0)
    curvature: float = Field(default=0.0, ge=-1.0, le=1.0)
    subdivision_level: int = Field(default=2, ge=0, le=5)
    smoothing_iterations: int = Field(default=3, ge=0, le=10)
    pattern_scale: float = Field(default=1.0, ge=0.1, le=10.0)
    hollow: bool = False
    wall_thickness: float = Field(default=0.1, ge=0.01, le=1.0)


class ModelGenerationRequest(BaseModel):
    """3D model generation request."""
    points_extraction_id: str
    target_shape: Literal[
        "sphere", "torus", "ellipsoid", "cone",
        "cube", "cuboid", "hexagonal_prism", "pyramid",
        "helix", "twisted_torus", "wireframe_surface",
        "auto"  # Automatically select based on pattern classification
    ] = "auto"
    geometry_params: GeometryParams = Field(default_factory=GeometryParams)


class Model3DMetadata(BaseModel):
    """3D model metadata."""
    id: str
    points_extraction_id: str
    image_id: str
    target_shape: str
    actual_shape: str
    vertex_count: int
    face_count: int
    geometry_params: GeometryParams
    created_at: datetime
    bounding_box: tuple[float, float, float, float, float, float]  # min/max x,y,z


class ModelPreview(BaseModel):
    """Low-poly preview data for 3D visualization."""
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]
    normals: list[tuple[float, float, float]]


class ModelUpdateParams(BaseModel):
    """Parameters for updating model generation."""
    target_shape: str | None = None
    geometry_params: GeometryParams | None = None


@router.post("/generate", response_model=Model3DMetadata, status_code=status.HTTP_201_CREATED)
async def generate_model(
    request: ModelGenerationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Generate a 3D model from extracted points."""
    # Get point extraction
    points_result = points_cache.get(request.points_extraction_id)
    if not points_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point extraction not found",
        )
    
    # Import and verify image access
    from app.api.routes.images import images_db
    image = images_db.get(points_result["image_id"])
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original image not found",
        )
    
    if image["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Determine actual shape if auto
    actual_shape = request.target_shape
    if request.target_shape == "auto":
        from app.core.classification import get_cached_classification
        classification = get_cached_classification(points_result["image_id"])
        if classification:
            # Map pattern type to 3D shape
            shape_mapping = {
                "circular": "sphere",
                "radial": "torus",
                "spiral": "helix",
                "polygonal": "pyramid",
                "hexagonal": "hexagonal_prism",
                "linear": "cuboid",
                "mixed": "wireframe_surface",
            }
            primary_type = classification.get("primary_type", {}).get("type", "mixed")
            actual_shape = shape_mapping.get(primary_type, "sphere")
        else:
            actual_shape = "sphere"  # Default fallback
    
    # Generate 3D model
    from app.core.geometry3d import generate_3d_model
    
    try:
        mesh_data = await generate_3d_model(
            points=points_result["points"],
            shape=actual_shape,
            params=request.geometry_params.model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"3D generation failed: {str(e)}",
        )
    
    model_id = str(uuid.uuid4())
    model = {
        "id": model_id,
        "points_extraction_id": request.points_extraction_id,
        "image_id": points_result["image_id"],
        "target_shape": request.target_shape,
        "actual_shape": actual_shape,
        "vertex_count": mesh_data["vertex_count"],
        "face_count": mesh_data["face_count"],
        "geometry_params": request.geometry_params.model_dump(),
        "created_at": datetime.utcnow(),
        "bounding_box": mesh_data["bounding_box"],
        "mesh_data": mesh_data,  # Store for export
        "user_id": current_user["id"],
    }
    
    models_db[model_id] = model
    
    return {
        "id": model_id,
        "points_extraction_id": request.points_extraction_id,
        "image_id": points_result["image_id"],
        "target_shape": request.target_shape,
        "actual_shape": actual_shape,
        "vertex_count": mesh_data["vertex_count"],
        "face_count": mesh_data["face_count"],
        "geometry_params": request.geometry_params,
        "created_at": model["created_at"],
        "bounding_box": mesh_data["bounding_box"],
    }


@router.get("/{model_id}", response_model=Model3DMetadata)
async def get_model(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get 3D model metadata."""
    model = models_db.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return {
        "id": model["id"],
        "points_extraction_id": model["points_extraction_id"],
        "image_id": model["image_id"],
        "target_shape": model["target_shape"],
        "actual_shape": model["actual_shape"],
        "vertex_count": model["vertex_count"],
        "face_count": model["face_count"],
        "geometry_params": model["geometry_params"],
        "created_at": model["created_at"],
        "bounding_box": model["bounding_box"],
    }


@router.put("/{model_id}/params", response_model=Model3DMetadata)
async def update_model_params(
    model_id: str,
    params: ModelUpdateParams,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Update model parameters and regenerate."""
    model = models_db.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Get points
    points_result = points_cache.get(model["points_extraction_id"])
    if not points_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point extraction not found",
        )
    
    # Merge parameters
    new_shape = params.target_shape if params.target_shape else model["target_shape"]
    new_geometry = params.geometry_params.model_dump() if params.geometry_params else model["geometry_params"]
    
    # Determine actual shape if auto
    actual_shape = new_shape
    if new_shape == "auto":
        from app.core.classification import get_cached_classification
        classification = get_cached_classification(model["image_id"])
        if classification:
            shape_mapping = {
                "circular": "sphere",
                "radial": "torus",
                "spiral": "helix",
                "polygonal": "pyramid",
                "hexagonal": "hexagonal_prism",
                "linear": "cuboid",
                "mixed": "wireframe_surface",
            }
            primary_type = classification.get("primary_type", {}).get("type", "mixed")
            actual_shape = shape_mapping.get(primary_type, "sphere")
        else:
            actual_shape = "sphere"
    
    # Regenerate
    from app.core.geometry3d import generate_3d_model
    
    try:
        mesh_data = await generate_3d_model(
            points=points_result["points"],
            shape=actual_shape,
            params=new_geometry,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"3D regeneration failed: {str(e)}",
        )
    
    # Update model
    model["target_shape"] = new_shape
    model["actual_shape"] = actual_shape
    model["geometry_params"] = new_geometry
    model["vertex_count"] = mesh_data["vertex_count"]
    model["face_count"] = mesh_data["face_count"]
    model["bounding_box"] = mesh_data["bounding_box"]
    model["mesh_data"] = mesh_data
    
    models_db[model_id] = model
    
    return {
        "id": model["id"],
        "points_extraction_id": model["points_extraction_id"],
        "image_id": model["image_id"],
        "target_shape": model["target_shape"],
        "actual_shape": model["actual_shape"],
        "vertex_count": model["vertex_count"],
        "face_count": model["face_count"],
        "geometry_params": model["geometry_params"],
        "created_at": model["created_at"],
        "bounding_box": model["bounding_box"],
    }


@router.get("/{model_id}/preview", response_model=ModelPreview)
async def get_model_preview(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    max_vertices: int = 1000,
) -> dict:
    """Get a low-poly preview of the 3D model for visualization."""
    model = models_db.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    mesh_data = model.get("mesh_data")
    if not mesh_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mesh data not available",
        )
    
    # Simplify mesh for preview if needed
    from app.core.geometry3d import simplify_mesh
    
    preview = simplify_mesh(mesh_data, max_vertices)
    
    return preview
