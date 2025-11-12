"""
FastAPI Main Application

Transmission™ API Server
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from transmission.api.routes import trades, metrics, system, signals
from transmission.api.websocket import websocket_endpoint, set_orchestrator as set_ws_orchestrator
from transmission.orchestrator.transmission import TransmissionOrchestrator, SystemState

# Initialize FastAPI app
app = FastAPI(
    title="Beyond Candlesticks",
    description="Adaptive Trading Middleware - Transmission™ API",
    version="0.1.0"
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trades.router)
app.include_router(metrics.router)
app.include_router(system.router)
app.include_router(signals.router)

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
        
        # Set orchestrator in route modules
        system.set_orchestrator(orchestrator)
        signals.set_orchestrator(orchestrator)
        set_ws_orchestrator(orchestrator)
        
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
        "name": "Transmission™ API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "status": "/api/system/status",
            "trades": "/api/trades",
            "metrics": "/api/metrics",
            "risk": "/api/system/risk",
            "websocket": "/ws"
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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
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

