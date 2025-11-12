"""
System Status API Routes

Endpoints for system status, risk, and health checks.
"""

from fastapi import APIRouter, Depends
from transmission.api.models.system import SystemStatusResponse, RiskStatusResponse
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
    """Get current system status"""
    try:
        risk_status = orch.get_risk_status()
        tripwire = orch.risk_governor.check_tripwires()
        
        # Get mental state info
        mental_info = orch.mental_governor.get_state_info()
        
        return SystemStatusResponse(
            system_state=orch.get_current_state().value,
            current_regime=orch.get_current_regime(),
            active_strategy=orch.get_current_strategy(),
            daily_pnl_r=risk_status['daily_pnl_r'],
            weekly_pnl_r=risk_status['weekly_pnl_r'],
            current_r=risk_status['current_r'],
            consecutive_red_days=risk_status['consecutive_red_days'],
            can_trade=tripwire.can_trade and mental_info['can_trade'],
            risk_reason=tripwire.reason if not tripwire.can_trade else mental_info.get('reason', 'All clear')
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

