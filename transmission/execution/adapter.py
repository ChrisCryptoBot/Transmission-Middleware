"""
Broker Adapter Interface

Protocol-based broker abstraction for mock, paper, and live trading.
Any broker that implements this interface can be used.

Based on user requirements for clean adapter pattern.
"""

from typing import Protocol, Optional, List, Literal, TypedDict
from datetime import datetime


# Type definitions
Side = Literal["BUY", "SELL"]
OrderType = Literal["MKT", "LMT", "STP", "STP_LMT"]
TimeInForce = Literal["DAY", "GTC", "IOC", "FOK"]
OrderStatus = Literal["ACCEPTED", "REJECTED", "PENDING_NEW", "FILLED", "PARTIALLY_FILLED", "CANCELED"]


class OrderReq(TypedDict):
    """Order request"""
    symbol: str
    side: Side
    qty: float
    order_type: OrderType
    limit_price: Optional[float]
    stop_price: Optional[float]
    tif: TimeInForce
    client_order_id: Optional[str]


class OrderResp(TypedDict):
    """Order response"""
    client_order_id: str
    broker_order_id: str
    status: OrderStatus
    reason: Optional[str]
    timestamp: float


class Fill(TypedDict):
    """Fill information"""
    broker_order_id: str
    filled_qty: float
    avg_price: float
    timestamp: float
    commission: float


class Position(TypedDict):
    """Position information"""
    symbol: str
    qty: float
    avg_price: float
    unrealized_pnl: float
    side: Side


class BrokerAdapter(Protocol):
    """
    Broker adapter protocol.
    
    Any broker implementation must satisfy this interface.
    """
    
    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open for symbol"""
        ...
    
    def get_price(self, symbol: str) -> float:
        """Get current market price"""
        ...
    
    def get_bid_ask(self, symbol: str) -> tuple[float, float]:
        """Get current bid/ask prices"""
        ...
    
    def submit(self, order: OrderReq) -> OrderResp:
        """Submit order to broker"""
        ...
    
    def cancel(self, broker_order_id: str) -> bool:
        """Cancel an order"""
        ...
    
    def get_open_orders(self) -> List[OrderResp]:
        """Get all open orders"""
        ...
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        ...
    
    def get_fills(self, broker_order_id: str) -> List[Fill]:
        """Get fills for an order"""
        ...

