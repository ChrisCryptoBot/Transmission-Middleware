"""
WebSocket Handler for Real-Time Updates

Broadcasts system state changes, signals, and risk updates.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
from loguru import logger
import json
from datetime import datetime


# Global orchestrator (set from main.py)
orchestrator = None


def set_orchestrator(orch):
    """Set orchestrator instance"""
    global orchestrator
    orchestrator = orch


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    Clients receive:
    - System state changes
    - Regime changes
    - Signal generation
    - Risk limit updates
    - Trade execution
    """
    await manager.connect(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Transmission WebSocket"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages (ping/pong, subscriptions, etc.)
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from WebSocket: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def broadcast_regime_change(regime: str):
    """Broadcast regime change to all clients"""
    manager.broadcast({
        "type": "regime_change",
        "regime": regime,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_signal(signal: dict):
    """Broadcast signal generation to all clients"""
    manager.broadcast({
        "type": "signal",
        "signal": signal,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_risk_update(risk_status: dict):
    """Broadcast risk status update to all clients"""
    manager.broadcast({
        "type": "risk_update",
        "risk": risk_status,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_trade_execution(trade: dict):
    """Broadcast trade execution to all clients"""
    manager.broadcast({
        "type": "trade_execution",
        "trade": trade,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_rejection(rejection_type: str, reason: str):
    """Broadcast rejection event (constraint violation or guard reject)"""
    manager.broadcast({
        "type": rejection_type,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_order_submitted(order_id: str, signal: dict):
    """Broadcast order submitted event"""
    manager.broadcast({
        "type": "order_submitted",
        "order_id": order_id,
        "signal": signal,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_fill(fill: dict):
    """Broadcast fill event"""
    manager.broadcast({
        "type": "fill",
        "fill": fill,
        "timestamp": datetime.now().isoformat()
    })


def broadcast_flatten_all(reason: str):
    """Broadcast flatten all event"""
    manager.broadcast({
        "type": "flatten_all",
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })

