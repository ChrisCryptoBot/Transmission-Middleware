"""
Webhook Integration Endpoints

Receives signals from external platforms (TradingView, MT5, custom integrations)
and processes them through Transmission's adaptive middleware.

This is the key to the multi-interface strategy - users can send signals from
ANY platform and Transmission adds the intelligence layer.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from transmission.api.auth import User
from transmission.api.dependencies import get_current_user, get_orchestrator_for_user
from transmission.strategies.signal_adapter import get_signal_adapter
from transmission.orchestrator.transmission import TransmissionOrchestrator

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# Response Models
class WebhookResponse(BaseModel):
    """Webhook processing response"""
    status: str  # "received", "processed", "rejected"
    signal_id: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime
    message: str


# Webhook Endpoints

@router.post("/tradingview", response_model=WebhookResponse)
async def tradingview_webhook(
    alert: Dict[str, Any],
    user: User = Depends(get_current_user),
    orchestrator: TransmissionOrchestrator = Depends(get_orchestrator_for_user)
):
    """
    TradingView webhook endpoint.

    Receives TradingView alerts and processes them through Transmission.

    **Required Headers:**
    - X-API-Key: Your Transmission API key

    **Expected Payload:**
    ```json
    {
        "ticker": "MNQ",
        "action": "BUY",  // or "SELL"
        "close": 12345.50,
        "time": 1703001600,  // optional
        "strategy": "VWAP Pullback",  // optional
        "message": "Entry signal"  // optional
    }
    ```

    **TradingView Setup:**
    1. Create alert in TradingView
    2. Set alert message to JSON format above
    3. Set webhook URL: https://your-api.com/api/webhooks/tradingview
    4. Add X-API-Key header in TradingView webhook settings

    **Returns:**
    - status: "received" (acknowledged), "processed" (signal generated), or "rejected"
    - reason: Why signal was accepted or rejected
    """
    try:
        # Get TradingView adapter
        adapter = get_signal_adapter("tradingview")

        # Validate signal format
        if not adapter.validate(alert):
            return WebhookResponse(
                status="rejected",
                reason="Invalid TradingView alert format",
                timestamp=datetime.now(),
                message="Signal rejected - check format"
            )

        # Parse to Transmission Signal
        signal = adapter.parse(alert)

        # Log webhook received
        logger.info(f"TradingView webhook received from user {user.user_id}: {signal.strategy} {signal.direction} on {alert.get('ticker')}")

        # Process signal through orchestrator
        result = await orchestrator.process_signal(signal)

        return WebhookResponse(
            status=result["status"],
            signal_id=result.get("signal_id"),
            reason=result.get("reason"),
            timestamp=datetime.now(),
            message=f"TradingView {signal.direction} signal for {alert.get('ticker')} {result['action'].lower()}"
        )

    except ValueError as e:
        logger.error(f"TradingView webhook parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signal format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"TradingView webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/mt5", response_model=WebhookResponse)
async def mt5_webhook(
    signal: Dict[str, Any],
    user: User = Depends(get_current_user),
    orchestrator: TransmissionOrchestrator = Depends(get_orchestrator_for_user)
):
    """
    MetaTrader 5 webhook endpoint.

    Receives MT5 Expert Advisor signals and processes them through Transmission.

    **Required Headers:**
    - X-API-Key: Your Transmission API key

    **Expected Payload:**
    ```json
    {
        "symbol": "MNQ",
        "type": 0,  // 0=BUY, 1=SELL
        "price": 12345.50,
        "sl": 12300.0,  // stop loss (optional)
        "tp": 12400.0,  // take profit (optional)
        "volume": 1.0,  // lot size
        "comment": "MA Crossover",  // optional
        "magic": 123456  // EA magic number (optional)
    }
    ```

    **MT5 Setup:**
    Use an HTTP library in your EA to POST signals:
    ```mql5
    string url = "https://your-api.com/api/webhooks/mt5";
    string headers = "X-API-Key: your_api_key\r\n";
    string data = "{\"symbol\":\"MNQ\",\"type\":0,\"price\":12345.50}";
    WebRequest("POST", url, headers, 5000, data, result, result_headers);
    ```

    **Returns:**
    - status: "received", "processed", or "rejected"
    - reason: Why signal was accepted or rejected
    """
    try:
        # Get MT5 adapter
        adapter = get_signal_adapter("mt5")

        # Validate signal format
        if not adapter.validate(signal):
            return WebhookResponse(
                status="rejected",
                reason="Invalid MT5 signal format",
                timestamp=datetime.now(),
                message="Signal rejected - check format"
            )

        # Parse to Transmission Signal
        parsed_signal = adapter.parse(signal)

        # Log webhook received
        logger.info(f"MT5 webhook received from user {user.user_id}: {parsed_signal.strategy} {parsed_signal.direction} on {signal.get('symbol')}")

        # Process signal through orchestrator
        result = await orchestrator.process_signal(parsed_signal)

        return WebhookResponse(
            status=result["status"],
            signal_id=result.get("signal_id"),
            reason=result.get("reason"),
            timestamp=datetime.now(),
            message=f"MT5 {parsed_signal.direction} signal for {signal.get('symbol')} {result['action'].lower()}"
        )

    except ValueError as e:
        logger.error(f"MT5 webhook parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signal format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"MT5 webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/generic", response_model=WebhookResponse)
async def generic_webhook(
    signal: Dict[str, Any],
    user: User = Depends(get_current_user),
    orchestrator: TransmissionOrchestrator = Depends(get_orchestrator_for_user)
):
    """
    Generic webhook endpoint for custom integrations.

    Flexible format for any platform or custom signal source.

    **Required Headers:**
    - X-API-Key: Your Transmission API key

    **Expected Payload:**
    ```json
    {
        "symbol": "MNQ",
        "side": "LONG",  // or "SHORT"
        "entry": 12345.50,
        "stop": 12300.0,  // optional
        "target": 12400.0,  // optional
        "contracts": 1,  // optional
        "strategy": "Custom Strategy",  // optional
        "confidence": 0.8,  // optional (0.0-1.0)
        "notes": "Custom signal"  // optional
    }
    ```

    **Example (cURL):**
    ```bash
    curl -X POST https://your-api.com/api/webhooks/generic \
      -H "X-API-Key: your_api_key" \
      -H "Content-Type: application/json" \
      -d '{
        "symbol": "MNQ",
        "side": "LONG",
        "entry": 12345.50,
        "stop": 12300.0,
        "target": 12400.0
      }'
    ```

    **Returns:**
    - status: "received", "processed", or "rejected"
    - reason: Why signal was accepted or rejected
    """
    try:
        # Get generic adapter
        adapter = get_signal_adapter("generic")

        # Validate signal format
        if not adapter.validate(signal):
            return WebhookResponse(
                status="rejected",
                reason="Invalid generic signal format",
                timestamp=datetime.now(),
                message="Signal rejected - check format"
            )

        # Parse to Transmission Signal
        parsed_signal = adapter.parse(signal)

        # Log webhook received
        logger.info(f"Generic webhook received from user {user.user_id}: {parsed_signal.strategy} {parsed_signal.direction} on {signal.get('symbol')}")

        # Process signal through orchestrator
        result = await orchestrator.process_signal(parsed_signal)

        return WebhookResponse(
            status=result["status"],
            signal_id=result.get("signal_id"),
            reason=result.get("reason"),
            timestamp=datetime.now(),
            message=f"Generic {parsed_signal.direction} signal for {signal.get('symbol')} {result['action'].lower()}"
        )

    except ValueError as e:
        logger.error(f"Generic webhook parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signal format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Generic webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.get("/health")
async def webhook_health():
    """
    Webhook system health check.

    Public endpoint (no authentication required).
    Use this to verify webhook infrastructure is operational.
    """
    return {
        "status": "healthy",
        "service": "webhooks",
        "supported_platforms": ["tradingview", "mt5", "generic"],
        "timestamp": datetime.now().isoformat()
    }
