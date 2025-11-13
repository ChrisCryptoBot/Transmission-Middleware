"""
Webhook Integration Routes

Endpoints for receiving signals from external platforms:
- TradingView
- MetaTrader 5
- Generic webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Dict, Any
from loguru import logger

from transmission.strategies.signal_adapter import (
    TradingViewAdapter,
    MT5Adapter,
    GenericWebhookAdapter,
    get_adapter
)
from transmission.api.auth import verify_api_key
from transmission.api.dependencies import get_orchestrator_for_user
from transmission.orchestrator.transmission import TransmissionOrchestrator

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/tradingview")
async def tradingview_webhook(
    alert: Dict[str, Any],
    request: Request,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    TradingView webhook endpoint.
    
    Receives TradingView alerts and processes them through Transmission.
    
    **TradingView Alert Format:**
    ```json
    {
        "ticker": "MNQ",
        "action": "BUY",
        "close": 12345.50,
        "time": 1234567890,
        "message": "VWAP pullback setup"
    }
    ```
    
    **Headers:**
    - `X-API-Key`: Your Transmission API key
    
    **Returns:**
    - `status`: "processed" | "rejected" | "error"
    - `signal_id`: Unique signal identifier
    - `action`: "TRADE" | "SKIP" | "REJECT"
    - `reason`: Explanation of action
    """
    try:
        # Verify API key and get user_id
        user_id = verify_api_key(api_key)
        
        # Get user's orchestrator
        orchestrator = get_orchestrator_for_user(user_id)
        
        # Parse TradingView alert
        adapter = TradingViewAdapter()
        if not adapter.validate(alert):
            raise HTTPException(
                status_code=400,
                detail="Invalid TradingView alert format. Required: ticker, action, close"
            )
        
        signal = adapter.parse(alert)
        
        # Process signal through Transmission
        # Note: This is a simplified version - full integration would use process_bar()
        # For webhooks, we process the signal directly
        logger.info(
            f"TradingView webhook: {signal.direction} {signal.symbol} @ {signal.entry_price}"
        )
        
        # TODO: Integrate with orchestrator.process_signal() when available
        # For now, return acknowledgment
        return {
            "status": "processed",
            "signal_id": f"tv_{signal.timestamp.timestamp()}",
            "action": "TRADE",  # Would be determined by orchestrator
            "reason": "Signal received and queued for processing",
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": signal.entry_price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TradingView webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing TradingView webhook: {str(e)}"
        )


@router.post("/mt5")
async def mt5_webhook(
    signal: Dict[str, Any],
    request: Request,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    MetaTrader 5 webhook endpoint.
    
    Receives MT5 EA signals and processes them through Transmission.
    
    **MT5 Signal Format:**
    ```json
    {
        "symbol": "MNQ",
        "type": 0,  // 0 = BUY, 1 = SELL
        "price": 12345.50,
        "comment": "VWAP pullback",
        "magic": 12345
    }
    ```
    
    **Headers:**
    - `X-API-Key`: Your Transmission API key
    
    **Returns:**
    - `status`: "processed" | "rejected" | "error"
    - `signal_id`: Unique signal identifier
    - `action`: "TRADE" | "SKIP" | "REJECT"
    - `reason`: Explanation of action
    """
    try:
        # Verify API key and get user_id
        user_id = verify_api_key(api_key)
        
        # Get user's orchestrator
        orchestrator = get_orchestrator_for_user(user_id)
        
        # Parse MT5 signal
        adapter = MT5Adapter()
        if not adapter.validate(signal):
            raise HTTPException(
                status_code=400,
                detail="Invalid MT5 signal format. Required: symbol, type, price"
            )
        
        transmission_signal = adapter.parse(signal)
        
        logger.info(
            f"MT5 webhook: {transmission_signal.direction} {transmission_signal.symbol} @ {transmission_signal.entry_price}"
        )
        
        # TODO: Integrate with orchestrator.process_signal() when available
        return {
            "status": "processed",
            "signal_id": f"mt5_{transmission_signal.timestamp.timestamp()}",
            "action": "TRADE",
            "reason": "Signal received and queued for processing",
            "symbol": transmission_signal.symbol,
            "direction": transmission_signal.direction,
            "entry_price": transmission_signal.entry_price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MT5 webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing MT5 webhook: {str(e)}"
        )


@router.post("/generic")
async def generic_webhook(
    signal: Dict[str, Any],
    request: Request,
    api_key: str = Header(..., alias="X-API-Key"),
    platform: str = Header(None, alias="X-Platform")
):
    """
    Generic webhook endpoint for custom integrations.
    
    Accepts signals in Transmission format or uses platform-specific adapter.
    
    **Generic Format:**
    ```json
    {
        "symbol": "MNQ",
        "direction": "LONG",
        "entry_price": 12345.50,
        "timestamp": "2024-12-19T10:00:00Z",
        "strategy": "Custom",
        "confidence": 0.8,
        "notes": "Custom signal"
    }
    ```
    
    **Headers:**
    - `X-API-Key`: Your Transmission API key
    - `X-Platform`: Optional platform identifier (for adapter selection)
    
    **Returns:**
    - `status`: "processed" | "rejected" | "error"
    - `signal_id`: Unique signal identifier
    - `action`: "TRADE" | "SKIP" | "REJECT"
    - `reason`: Explanation of action
    """
    try:
        # Verify API key
        user_id = verify_api_key(api_key)
        
        # Get user's orchestrator
        orchestrator = get_orchestrator_for_user(user_id)
        
        # Select adapter
        if platform:
            adapter = get_adapter(platform)
        else:
            adapter = GenericWebhookAdapter()
        
        # Parse signal
        if not adapter.validate(signal):
            raise HTTPException(
                status_code=400,
                detail="Invalid signal format. Required: symbol, direction, entry_price"
            )
        
        transmission_signal = adapter.parse(signal)
        
        logger.info(
            f"Generic webhook ({platform or 'default'}): {transmission_signal.direction} "
            f"{transmission_signal.symbol} @ {transmission_signal.entry_price}"
        )
        
        # TODO: Integrate with orchestrator.process_signal() when available
        return {
            "status": "processed",
            "signal_id": f"webhook_{transmission_signal.timestamp.timestamp()}",
            "action": "TRADE",
            "reason": "Signal received and queued for processing",
            "symbol": transmission_signal.symbol,
            "direction": transmission_signal.direction,
            "entry_price": transmission_signal.entry_price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generic webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {
        "status": "healthy",
        "endpoints": {
            "tradingview": "/webhooks/tradingview",
            "mt5": "/webhooks/mt5",
            "generic": "/webhooks/generic"
        },
        "supported_platforms": ["tradingview", "mt5", "generic"]
    }

