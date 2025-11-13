"""
API Dependencies

Dependency injection for FastAPI routes.
Supports multi-tenancy with user-isolated orchestrators.
"""

from fastapi import Depends, HTTPException, status, Request
from typing import Optional, Dict
from transmission.orchestrator.transmission import TransmissionOrchestrator
from transmission.api.auth import verify_api_key
from loguru import logger
from pathlib import Path

# Global orchestrator (set during startup - backward compatibility)
_orchestrator: Optional[TransmissionOrchestrator] = None

# User-isolated orchestrators (multi-tenancy)
_user_orchestrators: Dict[str, TransmissionOrchestrator] = {}


def set_orchestrator(orch: TransmissionOrchestrator):
    """Set the global orchestrator instance (backward compatibility)"""
    global _orchestrator
    _orchestrator = orch


def get_orchestrator() -> TransmissionOrchestrator:
    """
    Dependency: Get orchestrator instance (backward compatibility).
    
    For single-user MVP, returns global orchestrator.
    For multi-tenant, use get_orchestrator_for_user().
    
    Raises:
        HTTPException: If orchestrator is not initialized
    """
    if _orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized"
        )
    return _orchestrator


def get_orchestrator_for_user(user_id: str) -> TransmissionOrchestrator:
    """
    Get or create user-specific orchestrator (multi-tenancy).
    
    Args:
        user_id: User identifier from API key
    
    Returns:
        User's TransmissionOrchestrator instance
    """
    # Check cache first
    if user_id in _user_orchestrators:
        return _user_orchestrators[user_id]
    
    # Create isolated orchestrator for user
    # Each user gets their own database and config
    user_data_dir = Path("data") / f"user_{user_id}"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    user_config_dir = Path("config") / f"user_{user_id}"
    user_config_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = user_data_dir / "transmission.db"
    
    logger.info(f"Creating orchestrator for user {user_id}")
    
    # Create orchestrator with user-specific paths
    orchestrator = TransmissionOrchestrator(
        db_path=str(db_path),
        config_path=str(user_config_dir)
    )
    
    # Cache it
    _user_orchestrators[user_id] = orchestrator
    
    return orchestrator


def get_orchestrator_optional() -> Optional[TransmissionOrchestrator]:
    """
    Dependency: Get orchestrator instance (optional).
    
    Returns None if not initialized (for health checks, etc.)
    """
    return _orchestrator


def get_orchestrator_with_auth(
    request: Request,
    user_id: str = Depends(verify_api_key)
) -> TransmissionOrchestrator:
    """
    Get orchestrator with API key authentication.
    
    For write routes that require authentication.
    Automatically uses user-specific orchestrator if API key provided.
    
    Args:
        request: FastAPI request object
        user_id: User ID from verified API key
    
    Returns:
        User's TransmissionOrchestrator instance
    """
    return get_orchestrator_for_user(user_id)

