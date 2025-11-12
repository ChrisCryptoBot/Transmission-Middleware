"""
Metrics API Routes

Endpoints for performance metrics and analytics.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from transmission.api.models.metrics import PerformanceMetricsResponse
from transmission.database import Database

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/", response_model=PerformanceMetricsResponse)
async def get_metrics(window: int = Query(default=20, ge=1, le=100)):
    """
    Get performance metrics for recent trades.
    
    Args:
        window: Number of trades to analyze (default 20)
    """
    try:
        analytics = JournalAnalytics()
        metrics = analytics.compute_metrics(window_trades=window)
        
        return PerformanceMetricsResponse(
            window_trades=window,
            profit_factor=metrics.profit_factor,
            expected_r=metrics.expected_r,
            win_rate=metrics.win_rate,
            win_rate_wilson_lb=metrics.win_rate_wilson_lb,
            max_drawdown_r=metrics.max_drawdown_r,
            current_drawdown_r=metrics.current_drawdown_r,
            costs_pct=metrics.costs_pct,
            total_trades=metrics.total_trades,
            total_wins=metrics.total_wins,
            total_losses=metrics.total_losses,
            avg_win_r=metrics.avg_win_r,
            avg_loss_r=metrics.avg_loss_r
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")

