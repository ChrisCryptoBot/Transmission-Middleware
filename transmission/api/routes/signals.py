"""
Signal API Routes

Endpoints for signal generation (testing/validation).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from transmission.api.models.trade import TradeResponse
from transmission.orchestrator.transmission import TransmissionOrchestrator

router = APIRouter(prefix="/signals", tags=["signals"])

# Global orchestrator instance
orchestrator: TransmissionOrchestrator = None


def set_orchestrator(orch: TransmissionOrchestrator):
    """Set the orchestrator instance"""
    global orchestrator
    orchestrator = orch


class SignalRequest(BaseModel):
    """Request to generate a signal"""
    bars_data: dict  # OHLCV data as dict
    current_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None


class SignalResponse(BaseModel):
    """Signal generation response"""
    signal_generated: bool
    signal: Optional[dict] = None
    reason: str
    regime: Optional[str] = None
    active_strategy: Optional[str] = None


@router.post("/generate", response_model=SignalResponse)
async def generate_signal(request: SignalRequest):
    """
    Generate a trading signal (for testing/validation).
    
    This endpoint allows manual signal generation for testing.
    """
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Convert bars_data dict to DataFrame
        bars_df = pd.DataFrame(request.bars_data)
        
        # Generate signal
        signal = orchestrator.process_bar(
            bars_15m=bars_df,
            current_price=request.current_price,
            bid=request.bid,
            ask=request.ask
        )
        
        if signal:
            signal_dict = {
                "entry_price": signal.entry_price,
                "stop_price": signal.stop_price,
                "target_price": signal.target_price,
                "direction": signal.direction,
                "contracts": signal.contracts,
                "confidence": signal.confidence,
                "regime": signal.regime,
                "strategy": signal.strategy,
                "notes": signal.notes
            }
            
            return SignalResponse(
                signal_generated=True,
                signal=signal_dict,
                reason="Signal generated successfully",
                regime=orchestrator.get_current_regime(),
                active_strategy=orchestrator.get_current_strategy()
            )
        else:
            return SignalResponse(
                signal_generated=False,
                signal=None,
                reason="No signal generated - conditions not met",
                regime=orchestrator.get_current_regime(),
                active_strategy=orchestrator.get_current_strategy()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")

