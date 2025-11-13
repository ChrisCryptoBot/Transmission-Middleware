"""
FastAPI Main Application

Transmission™ API Server
"""

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import uvicorn
import os
from datetime import datetime

from transmission.api.routes import trades, metrics, system, signals, auth, webhooks
from transmission.api.websocket import websocket_endpoint, set_orchestrator as set_ws_orchestrator, manager as ws_manager
from transmission.api.dependencies import set_orchestrator as set_dep_orchestrator
from transmission.api.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from transmission.api.exceptions import APIException
from transmission.orchestrator.transmission import TransmissionOrchestrator, SystemState
from transmission.orchestrator.gear_state import set_websocket_manager

# Initialize FastAPI app
app = FastAPI(
    title="Beyond Candlesticks",
    description="Adaptive Trading Middleware - Transmission™ API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration (environment-based)
# Default includes Vite dev server (5173) and common production ports
default_origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = cors_origins_env.split(",") if cors_origins_env else default_origins

# Allow all in development if explicitly set
if "*" in cors_origins or (not cors_origins_env and os.getenv("ENV") != "production"):
    cors_origins = ["*"]
    logger.warning("CORS is set to allow all origins. Configure CORS_ORIGINS for production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"]
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(auth.router)  # Auth routes have /api/auth prefix in router definition
app.include_router(webhooks.router)  # Webhook routes have /api/webhooks prefix in router definition
app.include_router(trades.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)

# Global orchestrator instance
orchestrator: TransmissionOrchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global orchestrator
    
    try:
        logger.info("Initializing Transmission Orchestrator...")
        orchestrator = TransmissionOrchestrator()
        
        # Set orchestrator in route modules and dependencies
        system.set_orchestrator(orchestrator)
        signals.set_orchestrator(orchestrator)
        set_ws_orchestrator(orchestrator)
        set_dep_orchestrator(orchestrator)

        # Set WebSocket manager in gear state machine
        set_websocket_manager(ws_manager)

        logger.info("Transmission API ready")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator
    
    if orchestrator:
        logger.info("Shutting down Transmission Orchestrator...")
        # Cleanup if needed
        pass


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Beyond Candlesticks",
        "description": "Adaptive Trading Middleware - Transmission™ API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "webhooks": "/api/webhooks",
            "status": "/api/system/status",
            "trades": "/api/trades",
            "metrics": "/api/metrics",
            "risk": "/api/system/risk",
            "health": "/api/system/health",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }


@app.get("/api")
async def api_info():
    """API information"""
    return {
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/system/health"
    }


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code or "API_ERROR",
            "detail": exc.detail,
            "metadata": exc.metadata,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "detail": "Request validation failed",
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload (development)
    """
    uvicorn.run(
        "transmission.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)

