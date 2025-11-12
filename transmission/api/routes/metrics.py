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
        db = Database()
        trades = db.get_trades_for_metrics(window=window)
        db.close()
        
        if not trades:
            return PerformanceMetricsResponse(
                window_trades=0,
                total_trades=0,
                total_wins=0,
                total_losses=0
            )
        
        # Calculate metrics
        wins = [t for t in trades if t.get('win_loss') == 'Win']
        losses = [t for t in trades if t.get('win_loss') == 'Loss']
        
        total_wins = len(wins)
        total_losses = len(losses)
        total_trades = len(trades)
        
        # Profit Factor
        profit_factor = None
        if total_losses > 0:
            total_win_r = sum(t.get('result_r', 0) for t in wins if t.get('result_r'))
            total_loss_r = abs(sum(t.get('result_r', 0) for t in losses if t.get('result_r')))
            if total_loss_r > 0:
                profit_factor = total_win_r / total_loss_r
        
        # Expected R
        expected_r = None
        if total_trades > 0:
            total_r = sum(t.get('result_r', 0) for t in trades if t.get('result_r'))
            expected_r = total_r / total_trades
        
        # Win Rate
        win_rate = None
        if total_trades > 0:
            win_rate = total_wins / total_trades
        
        # Average Win/Loss
        avg_win_r = None
        if wins:
            avg_win_r = sum(t.get('result_r', 0) for t in wins if t.get('result_r')) / len(wins)
        
        avg_loss_r = None
        if losses:
            avg_loss_r = sum(t.get('result_r', 0) for t in losses if t.get('result_r')) / len(losses)
        
        # Drawdown (simplified - would need equity curve)
        max_drawdown_r = None
        current_drawdown_r = None
        
        # Costs percentage (simplified)
        costs_pct = None
        if trades:
            total_gross = sum(t.get('pl_amount_gross', 0) for t in trades if t.get('pl_amount_gross'))
            total_fees = sum(t.get('fees_paid', 0) for t in trades if t.get('fees_paid'))
            if total_gross > 0:
                costs_pct = (total_fees / total_gross) * 100
        
        # Wilson Lower Bound (simplified - would need proper calculation)
        win_rate_wilson_lb = None
        if total_trades > 0 and win_rate:
            # Simplified Wilson score - full implementation in analytics module
            z = 1.96  # 95% confidence
            p = win_rate
            n = total_trades
            denominator = 1 + z**2 / n
            centre = (p + z**2 / (2 * n)) / denominator
            margin = z * ((p * (1 - p) + z**2 / (4 * n)) / n)**0.5 / denominator
            win_rate_wilson_lb = centre - margin
        
        return PerformanceMetricsResponse(
            window_trades=window,
            profit_factor=profit_factor,
            expected_r=expected_r,
            win_rate=win_rate,
            win_rate_wilson_lb=win_rate_wilson_lb,
            max_drawdown_r=max_drawdown_r,
            current_drawdown_r=current_drawdown_r,
            costs_pct=costs_pct,
            total_trades=total_trades,
            total_wins=total_wins,
            total_losses=total_losses,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")

