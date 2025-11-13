"""
API Authentication & Multi-Tenancy

Handles API key validation and user isolation.
"""

from typing import Optional
from fastapi import HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
from loguru import logger
import os
import hashlib
import hmac

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory API key store (MVP)
# Production: Use database with encryption
API_KEYS: dict[str, str] = {}  # api_key -> user_id


def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate API key and return user_id.
    
    Args:
        api_key: API key from header
    
    Returns:
        user_id if valid, None otherwise
    """
    if not api_key:
        return None
    
    # Check in-memory store
    if api_key in API_KEYS:
        return API_KEYS[api_key]
    
    # Check environment variable (for development)
    # Format: API_KEY_USER_ID=key_value
    env_key = os.getenv(f"API_KEY_{api_key[:8].upper()}")
    if env_key and env_key == api_key:
        # Extract user_id from env var name or use default
        user_id = os.getenv(f"USER_ID_{api_key[:8].upper()}", "default")
        return user_id
    
    # TODO: Check database for production
    return None


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    FastAPI dependency to verify API key.
    
    Args:
        api_key: API key from X-API-Key header
    
    Returns:
        user_id if valid
    
    Raises:
        HTTPException if invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header."
        )
    
    user_id = validate_api_key(api_key)
    if not user_id:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return user_id


def create_api_key(user_id: str) -> str:
    """
    Create a new API key for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Generated API key
    """
    # Generate API key (simple implementation)
    # Production: Use proper key generation (secrets.token_urlsafe)
    import secrets
    api_key = f"tr_{secrets.token_urlsafe(32)}"
    
    # Store mapping
    API_KEYS[api_key] = user_id
    
    logger.info(f"Created API key for user {user_id}")
    return api_key


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        api_key: API key to revoke
    
    Returns:
        True if revoked, False if not found
    """
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        logger.info(f"Revoked API key: {api_key[:8]}...")
        return True
    return False


def get_user_from_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Get user_id from API key (alias for verify_api_key).
    
    Args:
        api_key: API key from header
    
    Returns:
        user_id
    """
    return verify_api_key(api_key)

