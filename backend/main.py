"""
AI Voice Agent FastAPI Application
Main entry point for the FastAPI backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

try:
    from app.core.config import settings
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Create basic settings for development
    class BasicSettings:
        CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
        LOG_TO_FILE = False
    settings = BasicSettings()

# Create FastAPI app
app = FastAPI(
    title="AI Voice Agent API",
    description="Backend API for AI Voice Agent logistics application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (only if they exist)
try:
    from app.api.routes import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    logger.info("Auth routes loaded")
except ImportError as e:
    logger.warning(f"Auth routes not available: {e}")

try:
    from app.api.routes import agents
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    logger.info("Agent routes loaded")
except ImportError as e:
    logger.warning(f"Agent routes not available: {e}")

try:
    from app.api.routes import calls
    app.include_router(calls.router, prefix="/api/calls", tags=["calls"])
    logger.info("Call routes loaded")
except ImportError as e:
    logger.warning(f"Call routes not available: {e}")

try:
    from app.api.routes import retell
    app.include_router(retell.router, prefix="/api/retell", tags=["retell"])
    logger.info("Retell routes loaded")
except ImportError as e:
    logger.warning(f"Retell routes not available: {e}")

try:
    from app.api.routes import scenarios
    app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
    logger.info("Scenario routes loaded")
except ImportError as e:
    logger.warning(f"Scenario routes not available: {e}")

try:
    from app.api.routes import webhooks
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
    logger.info("Webhook routes loaded")
except ImportError as e:
    logger.warning(f"Webhook routes not available: {e}")


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    try:
        logger.info("Starting AI Voice Agent API...")

        # Try to ensure admin user exists if auth service is available
        try:
            from app.services.supabase_auth_service import SupabaseAuthService
            await SupabaseAuthService.ensure_admin_user()
            logger.info("Admin user verification completed")
        except ImportError:
            logger.warning("Supabase auth service not available - skipping admin user setup")
        except Exception as e:
            logger.warning(f"Admin user setup failed: {e}")

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        # Don't raise to allow the server to start anyway


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Voice Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-voice-agent-api",
        "version": "1.0.0"
    }


# Global exception handler is now handled by setup_exception_handlers


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )