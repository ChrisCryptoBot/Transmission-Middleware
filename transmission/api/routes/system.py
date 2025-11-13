"""
System Status API Routes

Endpoints for system status, risk, and health checks.
"""

from fastapi import APIRouter, Depends
from typing import List
from transmission.api.models.system import (
    SystemStatusResponse,
    RiskStatusResponse,
    GearShiftResponse,
    GearPerformanceResponse
)
from transmission.api.dependencies import get_orchestrator, get_orchestrator_optional
from transmission.api.exceptions import ServiceUnavailableError, InternalServerError
from transmission.orchestrator.transmission import TransmissionOrchestrator
from transmission.database import Database
from datetime import datetime

router = APIRouter(prefix="/system", tags=["system"])

# Keep backward compatibility
orchestrator: TransmissionOrchestrator = None


def set_orchestrator(orch: TransmissionOrchestrator):
    """Set the orchestrator instance (called from main.py)"""
    global orchestrator
    orchestrator = orch


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    orch: TransmissionOrchestrator = Depends(get_orchestrator)
):
    """Get current system status with gear state"""
    try:
        risk_status = orch.get_risk_status()
        tripwire = orch.risk_governor.check_tripwires()

        # Get mental state info
        mental_info = orch.mental_governor.get_state_info()

        # Get gear state (NEW - Transmission visualization)
        gear_context = orch._build_gear_context(regime=orch.get_current_regime())
        current_gear, gear_reason = orch.gear_state_machine.shift(gear_context)
        gear_multiplier = orch.gear_state_machine.get_risk_multiplier()

        return SystemStatusResponse(
            system_state=orch.get_current_state().value,
            current_regime=orch.get_current_regime(),
            active_strategy=orch.get_current_strategy(),
            daily_pnl_r=risk_status['daily_pnl_r'],
            weekly_pnl_r=risk_status['weekly_pnl_r'],
            current_r=risk_status['current_r'],
            consecutive_red_days=risk_status['consecutive_red_days'],
            can_trade=tripwire.can_trade and mental_info['can_trade'],
            risk_reason=tripwire.reason if not tripwire.can_trade else mental_info.get('reason', 'All clear'),
            gear=current_gear.value,
            gear_reason=gear_reason,
            gear_risk_multiplier=gear_multiplier
        )
    except Exception as e:
        raise InternalServerError(f"Error getting system status: {str(e)}")


@router.get("/risk", response_model=RiskStatusResponse)
async def get_risk_status(
    orch: TransmissionOrchestrator = Depends(get_orchestrator)
):
    """Get current risk status"""
    try:
        tripwire = orch.risk_governor.check_tripwires()
        
        return RiskStatusResponse(
            can_trade=tripwire.can_trade,
            reason=tripwire.reason,
            action=tripwire.action,
            daily_pnl_r=tripwire.daily_pnl_r,
            weekly_pnl_r=tripwire.weekly_pnl_r,
            consecutive_red_days=tripwire.consecutive_red_days,
            current_r=orch.risk_governor.get_current_r()
        )
    except Exception as e:
        raise InternalServerError(f"Error getting risk status: {str(e)}")


@router.get("/health")
async def health_check(
    orch: TransmissionOrchestrator = Depends(get_orchestrator_optional)
):
    """Health check endpoint"""
    try:
        # Check database connection
        db = Database()
        db.conn.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "orchestrator": "ready" if orch else "not_initialized",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/flatten_all")
async def flatten_all(
    payload: dict,
    orch: TransmissionOrchestrator = Depends(get_orchestrator)
):
    """
    Flatten all positions (kill switch).
    
    Body:
        reason: Optional reason for flattening
    """
    try:
        reason = payload.get("reason", "manual_button")
        orch.flatten_all_manual(reason)
        
        return {
            "status": "ok",
            "message": f"All positions flattened: {reason}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise InternalServerError(f"Error flattening positions: {str(e)}")


@router.get("/orders")
async def get_open_orders():
    """Get all open orders"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        orders = orchestrator.get_open_orders()
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")


@router.get("/positions")
async def get_positions():
    """Get all active positions"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="System not initialized")

        positions = orchestrator.get_positions()
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")


# ============================================================================
# GEAR STATE ENDPOINTS (NEW - Transmission Visualization)
# ============================================================================

@router.get("/gear/history", response_model=List[GearShiftResponse])
async def get_gear_history(
    limit: int = 20,
    orch: TransmissionOrchestrator = Depends(get_orchestrator)
):
    """
    Get recent gear shift history.

    Query params:
        limit: Number of recent shifts to return (default: 20, max: 100)
    """
    try:
        # Limit to reasonable range
        limit = min(max(limit, 1), 100)

        # Get gear shifts from database
        shifts_raw = orch.database.get_recent_gear_shifts(limit=limit)

        # Convert to response models
        shifts = []
        for shift in shifts_raw:
            shifts.append(GearShiftResponse(
                timestamp=shift['timestamp'],
                from_gear=shift['from_gear'],
                to_gear=shift['to_gear'],
                reason=shift['reason'],
                daily_r=shift['daily_r'],
                weekly_r=shift['weekly_r'],
                consecutive_losses=shift['consecutive_losses'],
                regime=shift.get('regime')
            ))

        return shifts

    except Exception as e:
        raise InternalServerError(f"Error fetching gear history: {str(e)}")


@router.get("/gear/performance", response_model=List[GearPerformanceResponse])
async def get_gear_performance(
    orch: TransmissionOrchestrator = Depends(get_orchestrator)
):
    """
    Get performance metrics broken down by gear.

    Returns win rate, profit factor, and other stats for each gear (P/R/N/D/L).
    """
    try:
        # Get performance by gear from database
        perf_data = orch.database.get_performance_by_gear()

        # Convert to response models
        results = []
        for gear in ['P', 'R', 'N', 'D', 'L']:
            data = perf_data.get(gear, {})
            results.append(GearPerformanceResponse(
                gear=gear,
                trades=data.get('trades', 0),
                wins=data.get('wins', 0),
                losses=data.get('losses', 0),
                win_rate=data.get('win_rate', 0.0),
                avg_win_r=data.get('avg_win_r', 0.0),
                avg_loss_r=data.get('avg_loss_r', 0.0),
                total_r=data.get('total_r', 0.0),
                profit_factor=data.get('profit_factor', 0.0)
            ))

        return results

    except Exception as e:
        raise InternalServerError(f"Error fetching gear performance: {str(e)}")

