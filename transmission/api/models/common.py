"""
Common API Models

Shared request/response models used across multiple endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    error_code: Optional[str] = None
    detail: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """Standardized success response"""
    status: str = "ok"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list
    total: int
    limit: int
    offset: int
    has_more: bool
    
    @property
    def has_more(self) -> bool:
        """Check if there are more items"""
        return (self.offset + self.limit) < self.total


class FilterParams(BaseModel):
    """Common filter parameters"""
    strategy: Optional[str] = None
    regime: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

