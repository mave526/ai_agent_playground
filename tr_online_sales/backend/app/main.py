"""
FastAPI application entry point.
Configures app, includes routers, and sets up lifecycle events.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Database
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await Database.connect()
    yield
    # Shutdown
    await Database.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
TR Online Sales - Multi-sided Marketplace Platform

## Features
- Multi-role authentication (Consumer, Merchant, Delivery Agent, Influencer, Advertiser, Admin)
- JWT-based authentication with refresh tokens
- Product catalog and management
- Order processing and tracking
- Delivery job management
- Affiliate and advertising systems

## Architecture
- FastAPI async framework
- MongoDB database
- JWT authentication
""",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "TR Online Sales API is running",
        "version": settings.app_version
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    # Check MongoDB connection
    db_status = "connected"
    try:
        await Database.get_database().command("ping")
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": settings.app_version
    }