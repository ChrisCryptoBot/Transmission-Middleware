"""
Pydantic Models for Metrics API

Performance metrics response models.
"""

from pydantic import BaseModel
from typing import Optional


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response"""
    window_trades: int
    profit_factor: Optional[float] = None
    expected_r: Optional[float] = None
    win_rate: Optional[float] = None
    win_rate_wilson_lb: Optional[float] = None
    max_drawdown_r: Optional[float] = None
    current_drawdown_r: Optional[float] = None
    costs_pct: Optional[float] = None
    total_trades: int
    total_wins: int
    total_losses: int
    avg_win_r: Optional[float] = None
    avg_loss_r: Optional[float] = None
    
    class Config:
        from_attributes = True

