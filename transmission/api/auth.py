"""
API Key Authentication

Manages API key creation, validation, and user authentication.
MVP: In-memory storage. Production: Database-backed.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import hashlib
from dataclasses import dataclass
from loguru import logger
from fastapi import Header, HTTPException, status


@dataclass
class User:
    """User account"""
    user_id: str
    email: str
    tier: str  # "free", "pro", "enterprise"
    created_at: datetime
    active: bool = True


@dataclass
class APIKey:
    """API key"""
    key_id: str
    user_id: str
    key_hash: str  # SHA256 hash of the key
    name: str
    scopes: list[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    active: bool = True


class AuthManager:
    """
    API key authentication manager.

    MVP: In-memory storage
    Production: Replace with database queries
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.key_to_user: Dict[str, str] = {}  # key_hash -> user_id

        # Create default user for MVP (backward compatibility)
        self._create_default_user()

    def _create_default_user(self):
        """Create default user for single-user mode"""
        default_user = User(
            user_id="default_user",
            email="default@localhost",
            tier="pro",
            created_at=datetime.now()
        )
        self.users["default_user"] = default_user

        # Create default API key
        api_key, key_obj = self.create_api_key(
            user_id="default_user",
            name="Default API Key",
            scopes=["read", "write", "admin"]
        )
        logger.info(f"Default API key created: {api_key}")
        logger.info("⚠️ In production, store this securely!")

    def create_user(
        self,
        email: str,
        tier: str = "free"
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            tier: Subscription tier (free, pro, enterprise)

        Returns:
            User object
        """
        user_id = f"user_{secrets.token_hex(8)}"
        user = User(
            user_id=user_id,
            email=email,
            tier=tier,
            created_at=datetime.now()
        )
        self.users[user_id] = user
        logger.info(f"User created: {user_id} ({email})")
        return user

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[list[str]] = None
    ) -> tuple[str, APIKey]:
        """
        Create new API key for user.

        Args:
            user_id: User ID
            name: Key name (e.g., "Production", "Testing")
            scopes: Permissions (default: ["read", "write"])

        Returns:
            Tuple of (api_key, APIKey object)

        Note:
            The api_key is returned ONLY ONCE. Store it securely.
            Only the hash is stored internally.
        """
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")

        # Generate secure API key: "sk_" prefix + 32 random bytes
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(api_key)

        key_id = f"key_{secrets.token_hex(8)}"
        api_key_obj = APIKey(
            key_id=key_id,
            user_id=user_id,
            key_hash=key_hash,
            name=name,
            scopes=scopes or ["read", "write"],
            created_at=datetime.now()
        )

        self.api_keys[key_id] = api_key_obj
        self.key_to_user[key_hash] = user_id

        logger.info(f"API key created: {key_id} for user {user_id}")
        return api_key, api_key_obj

    def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        Validate API key and return user.

        Args:
            api_key: API key from request header

        Returns:
            User object if valid, None if invalid
        """
        if not api_key or not api_key.startswith("sk_"):
            return None

        key_hash = self._hash_key(api_key)
        user_id = self.key_to_user.get(key_hash)

        if not user_id:
            logger.warning(f"Invalid API key attempted")
            return None

        user = self.users.get(user_id)
        if not user or not user.active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            return None

        # Update last used timestamp
        for key_obj in self.api_keys.values():
            if key_obj.key_hash == key_hash:
                key_obj.last_used = datetime.now()
                break

        return user

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """
        Revoke API key.

        Args:
            key_id: Key ID to revoke
            user_id: User ID (for authorization check)

        Returns:
            True if revoked, False if not found or unauthorized
        """
        key = self.api_keys.get(key_id)
        if not key or key.user_id != user_id:
            return False

        key.active = False
        # Remove from lookup table
        if key.key_hash in self.key_to_user:
            del self.key_to_user[key.key_hash]

        logger.info(f"API key revoked: {key_id}")
        return True

    def list_api_keys(self, user_id: str) -> list[APIKey]:
        """
        List all API keys for user.

        Args:
            user_id: User ID

        Returns:
            List of APIKey objects (without key_hash)
        """
        return [
            key for key in self.api_keys.values()
            if key.user_id == user_id
        ]

    def _hash_key(self, api_key: str) -> str:
        """Hash API key using SHA256"""
        return hashlib.sha256(api_key.encode()).hexdigest()


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def verify_api_key(api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Verify API key and return user_id.
    
    FastAPI dependency for API key authentication.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        user_id: User ID associated with the API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    auth_manager = get_auth_manager()
    user = auth_manager.validate_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    
    return user.user_id
