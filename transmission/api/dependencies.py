"""
API Dependencies

Dependency injection for FastAPI routes.
Supports both single-user (MVP) and multi-user (production) modes.
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict
from pathlib import Path
from loguru import logger

from transmission.orchestrator.transmission import TransmissionOrchestrator
from transmission.api.auth import get_auth_manager, User

# Global orchestrator (single-user mode)
_orchestrator: Optional[TransmissionOrchestrator] = None

# User orchestrators (multi-user mode)
_user_orchestrators: Dict[str, TransmissionOrchestrator] = {}

# Multi-tenancy mode flag
_multi_tenant_mode: bool = False


def set_orchestrator(orch: TransmissionOrchestrator):
    """
    Set the global orchestrator instance (single-user mode).

    For backward compatibility with MVP.
    """
    global _orchestrator
    _orchestrator = orch
    logger.info("Orchestrator set (single-user mode)")


def enable_multi_tenant_mode():
    """Enable multi-tenant mode"""
    global _multi_tenant_mode
    _multi_tenant_mode = True
    logger.info("Multi-tenant mode enabled")


def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> User:
    """
    Dependency: Get current user from API key.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        User object

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required (X-API-Key header)",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    auth_manager = get_auth_manager()
    user = auth_manager.validate_api_key(x_api_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key"
        )

    return user


def get_current_user_optional(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[User]:
    """
    Dependency: Get current user (optional).

    Returns None if no API key provided or invalid.
    Useful for endpoints that support both authenticated and unauthenticated access.
    """
    if not x_api_key:
        return None

    auth_manager = get_auth_manager()
    return auth_manager.validate_api_key(x_api_key)


def get_orchestrator_for_user(user: User = Depends(get_current_user)) -> TransmissionOrchestrator:
    """
    Dependency: Get orchestrator for authenticated user.

    In multi-tenant mode, each user gets their own orchestrator instance
    with isolated database and configuration.

    Args:
        user: Authenticated user (from get_current_user dependency)

    Returns:
        TransmissionOrchestrator for the user

    Raises:
        HTTPException: If orchestrator cannot be created
    """
    global _user_orchestrators

    user_id = user.user_id

    # Check if orchestrator already exists for this user
    if user_id in _user_orchestrators:
        return _user_orchestrators[user_id]

    # Create new orchestrator for user
    try:
        # User-specific paths
        user_data_dir = Path(f"data/user_{user_id}")
        user_config_dir = Path(f"config/user_{user_id}")

        # Create directories if they don't exist
        user_data_dir.mkdir(parents=True, exist_ok=True)
        user_config_dir.mkdir(parents=True, exist_ok=True)

        # Database path
        db_path = user_data_dir / "transmission.db"

        # TODO: Load user-specific config from database or file
        # For now, use default config
        orchestrator = TransmissionOrchestrator(
            db_path=str(db_path)
        )

        _user_orchestrators[user_id] = orchestrator
        logger.info(f"Created orchestrator for user {user_id}")

        return orchestrator

    except Exception as e:
        logger.error(f"Failed to create orchestrator for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize user workspace: {str(e)}"
        )


def get_orchestrator() -> TransmissionOrchestrator:
    """
    Dependency: Get orchestrator instance.

    Backward compatible method for single-user mode.
    For multi-user endpoints, use get_orchestrator_for_user() instead.

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

