"""
Mock Broker Adapter

Deterministic mock broker for testing and development.
Simulates order execution with configurable slippage and latency.
"""

from typing import List, Optional
import time
from datetime import datetime
from loguru import logger

from transmission.execution.adapter import (
    BrokerAdapter, OrderReq, OrderResp, Fill, Position,
    Side, OrderType, OrderStatus
)


class MockBrokerAdapter:
    """
    Mock broker adapter for testing.
    
    Features:
    - Deterministic fills
    - Configurable slippage
    - Configurable latency
    - Order state tracking
    """
    
    def __init__(
        self,
        slippage_ticks: float = 0.5,
        latency_ms: float = 50.0,
        fill_probability: float = 1.0
    ):
        """
        Initialize Mock Broker.
        
        Args:
            slippage_ticks: Average slippage in ticks
            latency_ms: Average latency in milliseconds
            fill_probability: Probability of fill (0.0-1.0)
        """
        self.slippage_ticks = slippage_ticks
        self.latency_ms = latency_ms
        self.fill_probability = fill_probability
        
        # State tracking
        self.orders: dict[str, OrderResp] = {}
        self.fills: dict[str, List[Fill]] = {}
        self.positions: dict[str, Position] = {}
        self.current_prices: dict[str, float] = {"MNQ": 15000.0}  # Default price
        self.market_open = True
        self.order_counter = 0
    
    def is_market_open(self, symbol: str) -> bool:
        """Check if market is open"""
        return self.market_open
    
    def set_market_open(self, open: bool) -> None:
        """Set market open status"""
        self.market_open = open
    
    def get_price(self, symbol: str) -> float:
        """Get current market price"""
        return self.current_prices.get(symbol, 15000.0)
    
    def set_price(self, symbol: str, price: float) -> None:
        """Set current market price (for testing)"""
        self.current_prices[symbol] = price
    
    def get_bid_ask(self, symbol: str) -> tuple[float, float]:
        """Get bid/ask prices"""
        price = self.get_price(symbol)
        tick_size = 0.25
        spread = tick_size * 2  # 2 tick spread
        return (price - tick_size, price + tick_size)
    
    def submit(self, order: OrderReq) -> OrderResp:
        """Submit order (mock execution)"""
        import random
        
        self.order_counter += 1
        client_order_id = order.get("client_order_id") or f"MOCK_{self.order_counter}"
        broker_order_id = f"BROKER_{self.order_counter}"
        
        # Simulate latency
        time.sleep(self.latency_ms / 1000.0)
        
        # Check market open
        if not self.is_market_open(order["symbol"]):
            return OrderResp(
                client_order_id=client_order_id,
                broker_order_id=broker_order_id,
                status="REJECTED",
                reason="Market closed",
                timestamp=time.time()
            )
        
        # Check fill probability
        if random.random() > self.fill_probability:
            return OrderResp(
                client_order_id=client_order_id,
                broker_order_id=broker_order_id,
                status="REJECTED",
                reason="Fill probability check failed",
                timestamp=time.time()
            )
        
        # Determine fill price
        current_price = self.get_price(order["symbol"])
        fill_price = self._calculate_fill_price(order, current_price)
        
        # Create order response
        order_resp = OrderResp(
            client_order_id=client_order_id,
            broker_order_id=broker_order_id,
            status="ACCEPTED",
            reason=None,
            timestamp=time.time()
        )
        
        self.orders[broker_order_id] = order_resp
        
        # Immediately fill (mock broker fills instantly)
        if order["order_type"] == "MKT":
            self._create_fill(broker_order_id, order, fill_price)
            order_resp["status"] = "FILLED"
        elif order["order_type"] == "LMT":
            # Limit order: fill if price is favorable
            if self._should_fill_limit(order, current_price):
                self._create_fill(broker_order_id, order, fill_price)
                order_resp["status"] = "FILLED"
            else:
                order_resp["status"] = "PENDING_NEW"
        
        logger.info(
            f"Mock order submitted: {order['side']} {order['qty']} {order['symbol']} "
            f"@ {fill_price:.2f} (status: {order_resp['status']})"
        )
        
        return order_resp
    
    def _calculate_fill_price(self, order: OrderReq, current_price: float) -> float:
        """Calculate fill price with slippage"""
        tick_size = 0.25
        
        if order["order_type"] == "MKT":
            # Market order: fill at current price + slippage
            slippage = self.slippage_ticks * tick_size
            if order["side"] == "BUY":
                return current_price + slippage  # Pay more on buy
            else:
                return current_price - slippage  # Get less on sell
        
        elif order["order_type"] == "LMT" and order.get("limit_price"):
            # Limit order: fill at limit price (no slippage)
            return order["limit_price"]
        
        return current_price
    
    def _should_fill_limit(self, order: OrderReq, current_price: float) -> bool:
        """Check if limit order should fill"""
        if order["order_type"] != "LMT" or not order.get("limit_price"):
            return False
        
        limit_price = order["limit_price"]
        
        if order["side"] == "BUY":
            # Buy limit: fill if price is at or below limit
            return current_price <= limit_price
        else:
            # Sell limit: fill if price is at or above limit
            return current_price >= limit_price
    
    def _create_fill(self, broker_order_id: str, order: OrderReq, fill_price: float) -> None:
        """Create a fill for an order"""
        fill = Fill(
            broker_order_id=broker_order_id,
            filled_qty=order["qty"],
            avg_price=fill_price,
            timestamp=time.time(),
            commission=order["qty"] * 0.50  # $0.50 per contract round trip
        )
        
        if broker_order_id not in self.fills:
            self.fills[broker_order_id] = []
        self.fills[broker_order_id].append(fill)
        
        # Update position
        self._update_position(order["symbol"], order["side"], order["qty"], fill_price)
    
    def _update_position(self, symbol: str, side: Side, qty: float, price: float) -> None:
        """Update position after fill"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                qty=0.0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                side="BUY"
            )
        
        pos = self.positions[symbol]
        
        if side == "BUY":
            # Adding to long or reducing short
            if pos["qty"] >= 0:
                # Long position
                total_cost = (pos["qty"] * pos["avg_price"]) + (qty * price)
                pos["qty"] += qty
                pos["avg_price"] = total_cost / pos["qty"] if pos["qty"] > 0 else 0.0
                pos["side"] = "BUY"
            else:
                # Reducing short
                pos["qty"] += qty
                if pos["qty"] > 0:
                    pos["side"] = "BUY"
                    pos["avg_price"] = price
        else:
            # Adding to short or reducing long
            if pos["qty"] <= 0:
                # Short position
                total_cost = abs((pos["qty"] * pos["avg_price"]) + (qty * price))
                pos["qty"] -= qty
                pos["avg_price"] = total_cost / abs(pos["qty"]) if pos["qty"] < 0 else 0.0
                pos["side"] = "SELL"
            else:
                # Reducing long
                pos["qty"] -= qty
                if pos["qty"] < 0:
                    pos["side"] = "SELL"
                    pos["avg_price"] = price
        
        # Update unrealized P&L
        current_price = self.get_price(symbol)
        if pos["qty"] > 0:
            pos["unrealized_pnl"] = (current_price - pos["avg_price"]) * pos["qty"] * 2.0  # $2/point
        elif pos["qty"] < 0:
            pos["unrealized_pnl"] = (pos["avg_price"] - current_price) * abs(pos["qty"]) * 2.0
        else:
            pos["unrealized_pnl"] = 0.0
    
    def cancel(self, broker_order_id: str) -> bool:
        """Cancel an order"""
        if broker_order_id in self.orders:
            self.orders[broker_order_id]["status"] = "CANCELED"
            logger.info(f"Order {broker_order_id} canceled")
            return True
        return False
    
    def get_open_orders(self) -> List[OrderResp]:
        """Get all open orders"""
        return [
            order for order in self.orders.values()
            if order["status"] in ["PENDING_NEW", "PARTIALLY_FILLED"]
        ]
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return [pos for pos in self.positions.values() if pos["qty"] != 0.0]
    
    def get_fills(self, broker_order_id: str) -> List[Fill]:
        """Get fills for an order"""
        return self.fills.get(broker_order_id, [])

