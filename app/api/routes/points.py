"""Point extraction endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.api.routes.images import images_db

router = APIRouter()

# Point extraction cache
points_cache: dict[str, dict] = {}


class PointExtractionParams(BaseModel):
    """Point extraction parameters."""
    image_id: str
    density: float = Field(default=1.0, ge=0.1, le=5.0, description="Point density multiplier")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Feature importance threshold")
    min_distance: int = Field(default=10, ge=1, le=100, description="Minimum distance between points")
    weight_edges: float = Field(default=1.0, ge=0.0, le=2.0, description="Edge feature weight")
    weight_intersections: float = Field(default=1.5, ge=0.0, le=2.0, description="Intersection weight")
    weight_symmetry: float = Field(default=1.2, ge=0.0, le=2.0, description="Symmetry point weight")
    max_points: int = Field(default=1000, ge=10, le=10000, description="Maximum number of points")


class Point2D(BaseModel):
    """2D point with metadata."""
    x: float
    y: float
    weight: float
    feature_type: str  # edge, intersection, symmetry_center, contour


class PointExtractionResult(BaseModel):
    """Point extraction response."""
    id: str
    image_id: str
    points: list[Point2D]
    total_points: int
    parameters: PointExtractionParams
    bounding_box: tuple[float, float, float, float]  # min_x, min_y, max_x, max_y


class PointAdjustParams(BaseModel):
    """Parameters for adjusting extracted points."""
    density: float | None = None
    threshold: float | None = None
    min_distance: int | None = None
    weight_edges: float | None = None
    weight_intersections: float | None = None
    weight_symmetry: float | None = None
    max_points: int | None = None


@router.post("/extract", response_model=PointExtractionResult, status_code=status.HTTP_201_CREATED)
async def extract_points(
    params: PointExtractionParams,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Extract significant points from an analyzed image."""
    import uuid
    
    image = images_db.get(params.image_id)
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
    
    if not image.get("analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be analyzed before extracting points",
        )
    
    # Run point extraction
    from app.core.point_extraction import extract_points as run_extraction
    
    try:
        points = await run_extraction(
            image_path=image["file_path"],
            density=params.density,
            threshold=params.threshold,
            min_distance=params.min_distance,
            weight_edges=params.weight_edges,
            weight_intersections=params.weight_intersections,
            weight_symmetry=params.weight_symmetry,
            max_points=params.max_points,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Point extraction failed: {str(e)}",
        )
    
    # Calculate bounding box
    if points:
        min_x = min(p["x"] for p in points)
        max_x = max(p["x"] for p in points)
        min_y = min(p["y"] for p in points)
        max_y = max(p["y"] for p in points)
        bounding_box = (min_x, min_y, max_x, max_y)
    else:
        bounding_box = (0, 0, image.get("width", 0), image.get("height", 0))
    
    extraction_id = str(uuid.uuid4())
    result = {
        "id": extraction_id,
        "image_id": params.image_id,
        "points": points,
        "total_points": len(points),
        "parameters": params.model_dump(),
        "bounding_box": bounding_box,
    }
    
    # Cache the result
    points_cache[extraction_id] = result
    
    return result


@router.get("/{extraction_id}", response_model=PointExtractionResult)
async def get_points(
    extraction_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get extracted points by extraction ID."""
    result = points_cache.get(extraction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point extraction not found",
        )
    
    # Verify access
    image = images_db.get(result["image_id"])
    if image and image["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return result


@router.put("/{extraction_id}/adjust", response_model=PointExtractionResult)
async def adjust_points(
    extraction_id: str,
    params: PointAdjustParams,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Adjust point extraction parameters and re-extract."""
    result = points_cache.get(extraction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point extraction not found",
        )
    
    image = images_db.get(result["image_id"])
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
    
    # Merge with existing parameters
    current_params = result["parameters"]
    new_params = {
        "image_id": result["image_id"],
        "density": params.density if params.density is not None else current_params["density"],
        "threshold": params.threshold if params.threshold is not None else current_params["threshold"],
        "min_distance": params.min_distance if params.min_distance is not None else current_params["min_distance"],
        "weight_edges": params.weight_edges if params.weight_edges is not None else current_params["weight_edges"],
        "weight_intersections": params.weight_intersections if params.weight_intersections is not None else current_params["weight_intersections"],
        "weight_symmetry": params.weight_symmetry if params.weight_symmetry is not None else current_params["weight_symmetry"],
        "max_points": params.max_points if params.max_points is not None else current_params["max_points"],
    }
    
    # Re-extract with new parameters
    from app.core.point_extraction import extract_points as run_extraction
    
    try:
        points = await run_extraction(
            image_path=image["file_path"],
            **{k: v for k, v in new_params.items() if k != "image_id"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Point extraction failed: {str(e)}",
        )
    
    # Calculate bounding box
    if points:
        min_x = min(p["x"] for p in points)
        max_x = max(p["x"] for p in points)
        min_y = min(p["y"] for p in points)
        max_y = max(p["y"] for p in points)
        bounding_box = (min_x, min_y, max_x, max_y)
    else:
        bounding_box = (0, 0, image.get("width", 0), image.get("height", 0))
    
    # Update cache
    result["points"] = points
    result["total_points"] = len(points)
    result["parameters"] = new_params
    result["bounding_box"] = bounding_box
    
    points_cache[extraction_id] = result
    
    return result
