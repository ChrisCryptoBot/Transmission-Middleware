"""
API Dependencies

Dependency injection for FastAPI routes.
"""

from fastapi import Depends, HTTPException, status
from typing import Optional
from transmission.orchestrator.transmission import TransmissionOrchestrator

# Global orchestrator (set during startup)
_orchestrator: Optional[TransmissionOrchestrator] = None


def set_orchestrator(orch: TransmissionOrchestrator):
    """Set the global orchestrator instance"""
    global _orchestrator
    _orchestrator = orch


def get_orchestrator() -> TransmissionOrchestrator:
    """
    Dependency: Get orchestrator instance.
    
    Raises:
        HTTPException: If orchestrator is not initialized
    """
    if _orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized"
        )
    return _orchestrator


def get_orchestrator_optional() -> Optional[TransmissionOrchestrator]:
    """
    Dependency: Get orchestrator instance (optional).
    
    Returns None if not initialized (for health checks, etc.)
    """
    return _orchestrator

