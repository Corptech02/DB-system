"""
FastAPI application for FMCSA Database Management System.
Main application setup with middleware, routes, and lifespan management.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

from ..database import initialize_database, close_database, test_connection, refresh_statistics
from .models import HealthCheckResponse, ErrorResponse
from .routes import search, export, stats
from .dependencies import db_pool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    Initialize resources on startup, cleanup on shutdown.
    """
    # Startup
    logger.info("Starting FMCSA API server...")
    
    try:
        # Initialize database pool
        await initialize_database()
        app.state.db_pool = db_pool
        
        # Test database connection
        if not await test_connection():
            logger.error("Database connection test failed")
            raise RuntimeError("Database initialization failed")
        
        logger.info("Database initialized successfully")
        
        # Refresh statistics on startup
        try:
            await refresh_statistics()
            logger.info("Statistics refreshed")
        except Exception as e:
            logger.warning(f"Failed to refresh statistics: {e}")
        
        # Store startup time
        app.state.startup_time = datetime.utcnow()
        
        logger.info("FMCSA API server started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FMCSA API server...")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("FMCSA API server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="FMCSA Database Management System",
    description="API for managing FMCSA carrier data with search, export, and lead generation capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code,
            detail=str(exc)
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            status_code=400
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            status_code=500
        ).model_dump()
    )


# Include routers
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "FMCSA Database Management System",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status including database connectivity
    """
    try:
        # Check database
        db_healthy = await test_connection()
        
        # Get carrier count
        carrier_count = None
        if db_healthy:
            try:
                carrier_count = await db_pool.fetchval("SELECT COUNT(*) FROM carriers")
            except:
                pass
        
        # Get last ingestion time (simplified - would need ingestion log table)
        last_ingestion = None
        
        # Determine overall status
        if db_healthy:
            status = "healthy"
        else:
            status = "degraded"
        
        return HealthCheckResponse(
            status=status,
            database=db_healthy,
            last_ingestion=last_ingestion,
            carrier_count=carrier_count
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            database=False
        )


# Metrics endpoint (optional - for Prometheus)
if os.getenv("ENABLE_METRICS", "false").lower() == "true":
    from prometheus_fastapi_instrumentator import Instrumentator
    
    @app.on_event("startup")
    async def startup_metrics():
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# Static files for exports (if configured)
export_dir = os.getenv("EXPORT_TEMP_DIR", "/tmp/fmcsa_exports")
if os.path.exists(export_dir):
    app.mount("/exports", StaticFiles(directory=export_dir), name="exports")


# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"{request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log response
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {duration:.3f}s"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(duration)
    response.headers["X-Server-Version"] = "1.0.0"
    
    return response


def create_app() -> FastAPI:
    """Factory function to create FastAPI app."""
    return app


if __name__ == "__main__":
    # Run with uvicorn for development
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        workers=int(os.getenv("API_WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )