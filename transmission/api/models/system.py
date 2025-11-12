"""
Pydantic Models for System Status API

System status and state response models.
"""

from pydantic import BaseModel
from typing import Optional, Literal


class SystemStatusResponse(BaseModel):
    """System status response"""
    system_state: Literal[
        "initializing", "ready", "analyzing", 
        "signal_generated", "trading", "paused", "error"
    ]
    current_regime: Optional[str] = None
    active_strategy: Optional[str] = None
    daily_pnl_r: float
    weekly_pnl_r: float
    current_r: float
    consecutive_red_days: int
    can_trade: bool
    risk_reason: str


class RiskStatusResponse(BaseModel):
    """Risk status response"""
    can_trade: bool
    reason: str
    action: Literal["TRADE", "FLAT", "PAUSE"]
    daily_pnl_r: float
    weekly_pnl_r: float
    consecutive_red_days: int
    current_r: float

