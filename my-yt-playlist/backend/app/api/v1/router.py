from fastapi import APIRouter
from app.api.v1 import collections, auth, health, tags, users, videos

api_router = APIRouter()

# Include endpoints
api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(videos.router, prefix="/videos", tags=["Video Library"])
api_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
