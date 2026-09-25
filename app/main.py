from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import contextlib
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine , Base # Your database engine setup
import app.models  # Ensure all models are imported for Alembic to detect them
import asyncio
import sys
import os
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.Routers.v1 import events
from app.Routers.v1 import tickets 
from app.Routers.v1 import tenant
from app.Routers.v1 import checkout
from app.Routers.v1 import auth

# 1. This function hooks directly into Uvicorn's event loop
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Uvicorn's loop handles the 'async with' and 'await' smoothly here
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_instance = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # Attempt to ping Redis to check if it's alive
        await redis_instance.ping()
        await FastAPILimiter.init(redis_instance)
        print("🟢 Redis Rate Limiter Connected Successfully!")
    except Exception as e:
        print(f"🟡 Redis is offline ({e}). Running without Rate Limiter!")
        redis_instance = None
    
    yield 
    
    if redis_instance:
        await redis_instance.close()


app = FastAPI(
    lifespan=lifespan,
    title="High-Concurrency Ticketing Engine",
    description="Multi-tenant event management and atomic reservation MVP.",
    version="1.0.0",
    docs_url="/docs",     # Swagger UI endpoint
    redoc_url="/redoc"    # ReDoc endpoint
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all origins. Lock this down in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(tenant.router, prefix="/api/v1")
app.include_router(checkout.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

# 4. System Health Check Endpoint
@app.get("/health", tags=["System Maintenance"])
async def health_check():
    """
    A lightweight, stateless endpoint for Docker and Load Balancers 
    to verify that the FastAPI worker is currently running and accepting traffic.
    """
    return {
        "status": "healthy",
        "engine": "online",
        "version": "1.0.0"
    }

from app.websockets import manager

@app.websocket("/ws/events/{event_id}")
async def websocket_event_endpoint(websocket: WebSocket, event_id: int):
    """
    WebSocket endpoint for real-time seat map updates.
    """
    await manager.connect(websocket, event_id)
    try:
        while True:
            # We don't expect the client to send messages, but we keep the socket open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, event_id)