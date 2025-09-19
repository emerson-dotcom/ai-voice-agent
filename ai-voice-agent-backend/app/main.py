from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import health, calls, retell_webhook, agents, users
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Voice Agent Tool API",
    description="Backend API for AI Voice Agent Tool - Configure, test, and review calls made by adaptive AI voice agents for logistics management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(calls.router, prefix="/api", tags=["calls"])
app.include_router(retell_webhook.router, prefix="/api", tags=["webhooks"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting AI Voice Agent Tool API...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Allowed origins: {settings.allowed_origins_list}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down AI Voice Agent Tool API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
