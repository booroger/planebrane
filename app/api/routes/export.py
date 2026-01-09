"""Export endpoints for 3D models."""

import io
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.routes.auth import get_current_user
from app.api.routes.models3d import models_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def get_content_type(format: str) -> str:
    """Get MIME type for export format."""
    types = {
        "stl": "model/stl",
        "obj": "model/obj",
        "gltf": "model/gltf+json",
        "glb": "model/gltf-binary",
    }
    return types.get(format, "application/octet-stream")


async def export_model(
    model_id: str,
    format: Literal["stl", "obj", "gltf", "glb"],
    current_user: dict,
    binary: bool = False,
) -> tuple[bytes, str]:
    """Export model to specified format."""
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
    
    from app.core.geometry3d.exporters import export_to_format
    
    try:
        data = export_to_format(mesh_data, format, binary=binary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )
    
    # Generate filename
    filename = f"planebrane_{model_id[:8]}.{format}"
    
    return data, filename


@router.get("/{model_id}/stl")
async def export_stl(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    binary: bool = True,
) -> StreamingResponse:
    """Export model as STL file."""
    data, filename = await export_model(model_id, "stl", current_user, binary)
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type=get_content_type("stl"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/{model_id}/obj")
async def export_obj(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Export model as OBJ file."""
    data, filename = await export_model(model_id, "obj", current_user)
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type=get_content_type("obj"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/{model_id}/gltf")
async def export_gltf(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Export model as GLTF file (JSON format)."""
    data, filename = await export_model(model_id, "gltf", current_user)
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type=get_content_type("gltf"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/{model_id}/glb")
async def export_glb(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Export model as GLB file (binary GLTF)."""
    data, filename = await export_model(model_id, "glb", current_user, binary=True)
    
    return StreamingResponse(
        io.BytesIO(data),
        media_type=get_content_type("glb"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/{model_id}/save")
async def save_to_disk(
    model_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    format: Literal["stl", "obj", "gltf", "glb"] = "stl",
) -> dict:
    """Save exported model to server storage."""
    data, filename = await export_model(
        model_id, format, current_user, binary=(format in ["stl", "glb"])
    )
    
    # Ensure export directory exists
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = settings.export_dir / filename
    mode = "wb" if isinstance(data, bytes) else "w"
    
    with open(file_path, mode) as f:
        f.write(data)
    
    return {
        "message": "Model saved successfully",
        "filename": filename,
        "path": str(file_path),
        "size_bytes": len(data),
    }
