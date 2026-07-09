from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine , Base # Your database engine setup
import app.models  # Ensure all models are imported for Alembic to detect them

from app.Routers.v1 import events
from app.Routers.v1 import tickets 

# 🚀 This will now successfully create all tables inside ticket_db
Base.metadata.create_all(bind=engine)

app = FastAPI(
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