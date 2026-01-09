"""API router aggregation."""

from fastapi import APIRouter

from app.api.routes import auth, images, patterns, points, models3d, export

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(images.router, prefix="/images", tags=["Image Processing"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["Pattern Classification"])
api_router.include_router(points.router, prefix="/points", tags=["Point Extraction"])
api_router.include_router(models3d.router, prefix="/models", tags=["3D Generation"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
