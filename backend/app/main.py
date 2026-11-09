"""
StockVision AI - FastAPI Application Entry Point

This is the main application file that:
1. Creates the FastAPI app instance
2. Configures CORS middleware
3. Initializes the database
4. Registers API routers
5. Provides a health check endpoint
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_PATH, settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup (before yield) and shutdown (after yield).
    """
    # Startup: create database tables
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    print("[OK] Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("[STOP] Shutting down")


# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="StockVision product, inventory, cashier point-of-sale, and shelf-vision APIs.",
    lifespan=lifespan,
)

# Configure CORS to allow the React frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# ──────────────────────────────────────────────
# Register API Routers
# ──────────────────────────────────────────────

from app.routers import entries, vision

app.include_router(entries.router, prefix="/api", tags=["Products, inventory, and sales"])
app.include_router(vision.router, prefix="/api/vision", tags=["Shelf vision"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")
