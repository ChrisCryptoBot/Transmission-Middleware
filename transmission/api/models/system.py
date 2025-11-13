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

    # Gear state (Transmission visualization)
    gear: Optional[Literal["P", "R", "N", "D", "L"]] = None
    gear_reason: Optional[str] = None
    gear_risk_multiplier: Optional[float] = None


class RiskStatusResponse(BaseModel):
    """Risk status response"""
    can_trade: bool
    reason: str
    action: Literal["TRADE", "FLAT", "PAUSE"]
    daily_pnl_r: float
    weekly_pnl_r: float
    consecutive_red_days: int
    current_r: float


class GearShiftResponse(BaseModel):
    """Gear shift event response"""
    timestamp: str
    from_gear: Literal["P", "R", "N", "D", "L"]
    to_gear: Literal["P", "R", "N", "D", "L"]
    reason: str
    daily_r: float
    weekly_r: float
    consecutive_losses: int
    regime: Optional[str] = None


class GearPerformanceResponse(BaseModel):
    """Performance metrics by gear"""
    gear: Literal["P", "R", "N", "D", "L"]
    trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    total_r: float
    profit_factor: float

