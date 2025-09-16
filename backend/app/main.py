from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import socketio
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import init_db
from app.api import auth, agents, calls, webhooks
from app.core.security import get_current_user


# Socket.IO server for real-time updates
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.SOCKET_CORS_ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True
)

socket_app = socketio.ASGIApp(sio)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("🔄 Attempting database initialization...")
        await init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("🚀 Starting server without database connection...")
        print("📝 Note: Database-dependent endpoints will not work until connection is fixed")
    
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI Voice Agent Tool - Logistics Communication System",
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.railway.app"]
)

# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    agents.router,
    prefix="/api/v1/agents",
    tags=["agents"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    calls.router,
    prefix="/api/v1/calls",
    tags=["calls"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    webhooks.router,
    prefix="/api/v1/webhooks",
    tags=["webhooks"]
)

# Mount Socket.IO app
app.mount("/socket.io", socket_app)


@app.get("/")
async def root():
    return {
        "message": "AI Voice Agent API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-voice-agent-api"}


# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    print(f"Client {sid} connected")
    await sio.emit("connected", {"message": "Connected to voice agent server"}, room=sid)


@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")


@sio.event
async def join_call_room(sid, data):
    """Join a room for call-specific updates"""
    call_id = data.get("call_id")
    if call_id:
        await sio.enter_room(sid, f"call_{call_id}")
        await sio.emit("joined_call_room", {"call_id": call_id}, room=sid)
