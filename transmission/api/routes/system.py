"""
System Status API Routes

Endpoints for system status, risk, and health checks.
"""

from fastapi import APIRouter, HTTPException
from transmission.api.models.system import SystemStatusResponse, RiskStatusResponse
from transmission.orchestrator.transmission import TransmissionOrchestrator
from transmission.database import Database

router = APIRouter(prefix="/system", tags=["system"])

# Global orchestrator instance (will be initialized in main.py)
orchestrator: TransmissionOrchestrator = None


def set_orchestrator(orch: TransmissionOrchestrator):
    """Set the orchestrator instance (called from main.py)"""
    global orchestrator
    orchestrator = orch


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get current system status"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        risk_status = orchestrator.get_risk_status()
        tripwire = orchestrator.risk_governor.check_tripwires()
        
        return SystemStatusResponse(
            system_state=orchestrator.get_current_state().value,
            current_regime=orchestrator.get_current_regime(),
            active_strategy=orchestrator.get_current_strategy(),
            daily_pnl_r=risk_status['daily_pnl_r'],
            weekly_pnl_r=risk_status['weekly_pnl_r'],
            current_r=risk_status['current_r'],
            consecutive_red_days=risk_status['consecutive_red_days'],
            can_trade=tripwire.can_trade,
            risk_reason=tripwire.reason
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")


@router.get("/risk", response_model=RiskStatusResponse)
async def get_risk_status():
    """Get current risk status"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        tripwire = orchestrator.risk_governor.check_tripwires()
        
        return RiskStatusResponse(
            can_trade=tripwire.can_trade,
            reason=tripwire.reason,
            action=tripwire.action,
            daily_pnl_r=tripwire.daily_pnl_r,
            weekly_pnl_r=tripwire.weekly_pnl_r,
            consecutive_red_days=tripwire.consecutive_red_days,
            current_r=orchestrator.risk_governor.get_current_r()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting risk status: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db = Database()
        db.conn.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "orchestrator": "ready" if orchestrator else "not_initialized"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

