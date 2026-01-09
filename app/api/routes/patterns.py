"""Pattern classification endpoints."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.api.routes.images import images_db

router = APIRouter()

# Pattern library storage
pattern_library: dict[str, dict] = {}


class PatternType(BaseModel):
    """Individual pattern type with confidence."""
    type: Literal["circular", "radial", "spiral", "polygonal", "hexagonal", "linear", "mixed"]
    confidence: float
    description: str


class ClassificationResult(BaseModel):
    """Pattern classification response."""
    image_id: str
    primary_type: PatternType
    secondary_types: list[PatternType]
    symmetry_order: int | None = None
    complexity_score: float
    features: dict


class PatternLibraryEntry(BaseModel):
    """Pattern library entry."""
    id: str
    name: str
    description: str
    image_id: str
    classification: ClassificationResult
    tags: list[str]
    created_at: datetime
    user_id: int


class PatternLibrarySave(BaseModel):
    """Request to save pattern to library."""
    name: str
    description: str
    image_id: str
    tags: list[str] = []


@router.get("/{image_id}", response_model=ClassificationResult)
async def get_classification(
    image_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get pattern classification results for an analyzed image."""
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
    
    if not image.get("analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet. Call /images/{id}/analyze first.",
        )
    
    # Run classification
    from app.core.classification import classify_pattern
    
    try:
        result = await classify_pattern(image_id, image["file_path"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )
    
    return result


@router.get("/library", response_model=list[PatternLibraryEntry])
async def browse_library(
    current_user: Annotated[dict, Depends(get_current_user)],
    tag: str | None = None,
    pattern_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Browse the pattern library."""
    results = []
    
    for entry in pattern_library.values():
        # Filter by user
        if entry["user_id"] != current_user["id"]:
            continue
        
        # Filter by tag
        if tag and tag not in entry["tags"]:
            continue
        
        # Filter by pattern type
        if pattern_type and entry["classification"]["primary_type"]["type"] != pattern_type:
            continue
        
        results.append(entry)
    
    # Sort by creation date (newest first)
    results.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    return results[offset : offset + limit]


@router.post("/library", response_model=PatternLibraryEntry, status_code=status.HTTP_201_CREATED)
async def save_to_library(
    data: PatternLibrarySave,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Save a classified pattern to the library."""
    import uuid
    
    image = images_db.get(data.image_id)
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
            detail="Image must be analyzed before saving to library",
        )
    
    # Get classification
    from app.core.classification import get_cached_classification
    classification = get_cached_classification(data.image_id)
    
    if not classification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pattern must be classified before saving to library",
        )
    
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "name": data.name,
        "description": data.description,
        "image_id": data.image_id,
        "classification": classification,
        "tags": data.tags,
        "created_at": datetime.utcnow(),
        "user_id": current_user["id"],
    }
    
    pattern_library[entry_id] = entry
    
    return entry


@router.get("/library/{entry_id}", response_model=PatternLibraryEntry)
async def get_library_entry(
    entry_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get a specific pattern library entry."""
    entry = pattern_library.get(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library entry not found",
        )
    
    if entry["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return entry


@router.delete("/library/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library_entry(
    entry_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """Delete a pattern library entry."""
    entry = pattern_library.get(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library entry not found",
        )
    
    if entry["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    del pattern_library[entry_id]
