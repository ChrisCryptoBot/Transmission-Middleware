"""
Custom API Exceptions

Standardized exception handling for the API.
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class APIException(HTTPException):
    """Base API exception with standardized format"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.metadata = metadata or {}


class ValidationError(APIException):
    """Validation error (400)"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            metadata={"field": field} if field else {}
        )


class NotFoundError(APIException):
    """Resource not found (404)"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        detail = f"{resource} not found"
        if identifier:
            detail += f": {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            metadata={"resource": resource, "identifier": identifier}
        )


class UnauthorizedError(APIException):
    """Unauthorized access (401)"""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(APIException):
    """Forbidden access (403)"""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ServiceUnavailableError(APIException):
    """Service unavailable (503)"""
    
    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE"
        )


class InternalServerError(APIException):
    """Internal server error (500)"""
    
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_ERROR"
        )

