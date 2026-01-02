from fastapi import APIRouter
from app.api.v1 import auth, geography, candidates, elections, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(geography.router, prefix="/geography", tags=["geography"])
# api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(elections.router, prefix="/elections", tags=["elections"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}