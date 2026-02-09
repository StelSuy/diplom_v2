"""
FastAPI application entry point.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.router import api_router
from app.ws.routes import router as ws_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.seed import seed_demo_data
from app.db.session import SessionLocal

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.app_name} in {settings.env} mode")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    
    # Seed demo data
    try:
        db = SessionLocal()
        try:
            created = seed_demo_data(db)
            if created:
                logger.info("Demo data seeded successfully")
        finally:
            db.close()
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"Database not ready for seeding: {e}")
    except Exception as e:
        logger.exception(f"Failed to seed data: {e}")
    
    # Debug: Log registered routes
    if settings.debug:
        logger.info("=== Registered Routes ===")
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                methods = ",".join(sorted(route.methods))
                logger.info(f"{methods:15} {route.path}")


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application")


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    Logs the error and returns a generic error response.
    """
    logger.exception(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method,
        },
    )


# Request Logging Middleware (Development only)
if settings.is_development:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests in development mode."""
        logger.debug(f">>> {request.method} {request.url.path}")
        response = await call_next(request)
        logger.debug(f"<<< {response.status_code}")
        return response


# Favicon Endpoint
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon.ico if it exists."""
    favicon_path = Path(__file__).parent.parent / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Favicon not found"}
    )


# Health Check Endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns application status and version.
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.env,
        "version": "1.0.0",
    }


# Root Endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with API information.
    """
    response = {
        "message": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.env,
    }
    
    if settings.is_development:
        response.update({
            "docs": "/docs",
            "redoc": "/redoc",
            "admin": "/admin",
        })
    
    return response


# Include API Router
app.include_router(api_router, prefix="/api")

# WebSocket Router
app.include_router(ws_router)

# Mount Admin Static Files
try:
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/admin", StaticFiles(directory=str(static_path), html=True), name="admin")
        logger.info(f"Admin panel mounted at /admin")
except Exception as e:
    logger.warning(f"Failed to mount admin static files: {e}")
