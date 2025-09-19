from fastapi import APIRouter
from datetime import datetime
from app.models.schemas import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )
