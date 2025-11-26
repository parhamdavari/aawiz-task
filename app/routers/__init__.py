from fastapi import APIRouter
from app.routers import auth, evaluations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])

__all__ = ["api_router"]

