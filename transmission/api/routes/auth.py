"""
Authentication and API Key Management Routes

Endpoints for user authentication and API key management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from transmission.api.auth import get_auth_manager, User, APIKey
from transmission.api.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Request/Response Models
class CreateUserRequest(BaseModel):
    """Create user request"""
    email: EmailStr
    tier: str = "free"


class CreateAPIKeyRequest(BaseModel):
    """Create API key request"""
    name: str
    scopes: Optional[list[str]] = None


class CreateAPIKeyResponse(BaseModel):
    """Create API key response"""
    api_key: str
    key_id: str
    name: str
    created_at: datetime
    warning: str = "⚠️ Store this key securely. It will not be shown again."


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)"""
    key_id: str
    name: str
    scopes: list[str]
    created_at: datetime
    last_used: Optional[datetime]
    active: bool


class UserInfo(BaseModel):
    """User information"""
    user_id: str
    email: str
    tier: str
    created_at: datetime
    active: bool


# Routes

@router.post("/users", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest):
    """
    Create new user account.

    **NOTE:** In production, this should be behind admin authentication
    or integrated with a proper user registration flow.
    """
    auth_manager = get_auth_manager()

    try:
        user = auth_manager.create_user(
            email=request.email,
            tier=request.tier
        )
        return UserInfo(
            user_id=user.user_id,
            email=user.email,
            tier=user.tier,
            created_at=user.created_at,
            active=user.active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires: X-API-Key header
    """
    return UserInfo(
        user_id=user.user_id,
        email=user.email,
        tier=user.tier,
        created_at=user.created_at,
        active=user.active
    )


@router.post("/keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: User = Depends(get_current_user)
):
    """
    Create new API key for authenticated user.

    The API key is returned ONLY ONCE. Store it securely.

    Requires: X-API-Key header (existing key to create new one)
    """
    auth_manager = get_auth_manager()

    try:
        api_key, key_obj = auth_manager.create_api_key(
            user_id=user.user_id,
            name=request.name,
            scopes=request.scopes
        )

        return CreateAPIKeyResponse(
            api_key=api_key,
            key_id=key_obj.key_id,
            name=key_obj.name,
            created_at=key_obj.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/keys", response_model=list[APIKeyInfo])
async def list_api_keys(user: User = Depends(get_current_user)):
    """
    List all API keys for authenticated user.

    Returns key metadata only (not the actual keys).

    Requires: X-API-Key header
    """
    auth_manager = get_auth_manager()
    keys = auth_manager.list_api_keys(user.user_id)

    return [
        APIKeyInfo(
            key_id=key.key_id,
            name=key.name,
            scopes=key.scopes,
            created_at=key.created_at,
            last_used=key.last_used,
            active=key.active
        )
        for key in keys
    ]


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user)
):
    """
    Revoke API key.

    The key will no longer be valid for authentication.

    Requires: X-API-Key header (must use a different key, not the one being revoked)
    """
    auth_manager = get_auth_manager()
    success = auth_manager.revoke_api_key(key_id, user.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or unauthorized"
        )

    return None


@router.get("/health")
async def auth_health():
    """
    Health check for authentication system.

    Public endpoint (no authentication required).
    """
    auth_manager = get_auth_manager()
    return {
        "status": "healthy",
        "users": len(auth_manager.users),
        "api_keys": len(auth_manager.api_keys)
    }
