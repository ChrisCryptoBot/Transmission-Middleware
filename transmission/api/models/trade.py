"""
Pydantic Models for Trade API

Request and response models for trade endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class TradeResponse(BaseModel):
    """Trade response model"""
    trade_id: int
    timestamp_entry: datetime
    timestamp_exit: Optional[datetime] = None
    symbol: str
    trade_type: Literal["Long", "Short"]
    strategy_used: str
    regime_at_entry: Optional[str] = None
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss_price: float
    take_profit_price: Optional[float] = None
    position_size: int
    result_r: Optional[float] = None
    win_loss: Optional[str] = None
    exit_reason: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    """List of trades response"""
    trades: list[TradeResponse]
    total: int
    limit: int
    offset: int


class TradeCreateRequest(BaseModel):
    """Request to create a trade (for testing)"""
    symbol: str = "MNQ"
    trade_type: Literal["Long", "Short"]
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    position_size: int = Field(gt=0)
    strategy_used: str = "VWAP Pullback"
    regime_at_entry: str = "TREND"
    notes: Optional[str] = None

