"""
Fill Simulator

Deterministic fill simulation for testing.
Provides realistic fill behavior for backtesting and unit tests.
"""

from typing import Optional
from datetime import datetime
import random
from loguru import logger

from transmission.execution.adapter import OrderReq, Fill, Side, OrderType


class FillSimulator:
    """
    Deterministic fill simulator.
    
    Rules:
    - MKT orders: Fill at next tick with slippage
    - LMT orders: Fill when price touches/crosses limit
    - STP orders: Trigger then use LMT/MKT logic
    """
    
    def __init__(
        self,
        slippage_model: str = "fixed",  # "fixed", "random", "volume_based"
        slippage_ticks: float = 0.5,
        latency_ms: float = 50.0,
        fill_probability: float = 1.0
    ):
        """
        Initialize Fill Simulator.
        
        Args:
            slippage_model: Slippage calculation model
            slippage_ticks: Base slippage in ticks
            latency_ms: Execution latency in milliseconds
            fill_probability: Probability of fill (0.0-1.0)
        """
        self.slippage_model = slippage_model
        self.slippage_ticks = slippage_ticks
        self.latency_ms = latency_ms
        self.fill_probability = fill_probability
    
    def simulate_fill(
        self,
        order: OrderReq,
        current_price: float,
        current_volume: float = 100.0,
        tick_size: float = 0.25
    ) -> Optional[Fill]:
        """
        Simulate order fill.
        
        Args:
            order: Order request
            current_price: Current market price
            current_volume: Current volume (for volume-based slippage)
            tick_size: Tick size for the instrument
            
        Returns:
            Fill if order should fill, None otherwise
        """
        # Check fill probability
        if random.random() > self.fill_probability:
            return None
        
        # Calculate fill price based on order type
        fill_price = self._calculate_fill_price(
            order, current_price, current_volume, tick_size
        )
        
        if fill_price is None:
            return None  # Order shouldn't fill yet
        
        # Create fill
        fill = Fill(
            broker_order_id=order.get("client_order_id", "SIM"),
            filled_qty=order["qty"],
            avg_price=fill_price,
            timestamp=datetime.now().timestamp(),
            commission=order["qty"] * 0.50  # $0.50 per contract
        )
        
        return fill
    
    def _calculate_fill_price(
        self,
        order: OrderReq,
        current_price: float,
        volume: float,
        tick_size: float
    ) -> Optional[float]:
        """Calculate fill price based on order type"""
        
        if order["order_type"] == "MKT":
            # Market order: fill immediately with slippage
            slippage = self._calculate_slippage(volume, tick_size)
            
            if order["side"] == "BUY":
                return current_price + slippage  # Pay more
            else:
                return current_price - slippage  # Get less
        
        elif order["order_type"] == "LMT":
            # Limit order: fill if price is favorable
            limit_price = order.get("limit_price")
            if limit_price is None:
                return None
            
            if order["side"] == "BUY":
                # Buy limit: fill if price <= limit
                if current_price <= limit_price:
                    return limit_price  # Fill at limit (no slippage)
            else:
                # Sell limit: fill if price >= limit
                if current_price >= limit_price:
                    return limit_price  # Fill at limit (no slippage)
            
            return None  # Don't fill yet
        
        elif order["order_type"] == "STP":
            # Stop order: trigger then fill
            stop_price = order.get("stop_price")
            if stop_price is None:
                return None
            
            if order["side"] == "BUY":
                # Buy stop: trigger if price >= stop
                if current_price >= stop_price:
                    # Fill as market order
                    slippage = self._calculate_slippage(volume, tick_size)
                    return current_price + slippage
            else:
                # Sell stop: trigger if price <= stop
                if current_price <= stop_price:
                    # Fill as market order
                    slippage = self._calculate_slippage(volume, tick_size)
                    return current_price - slippage
            
            return None  # Stop not triggered
        
        return None
    
    def _calculate_slippage(self, volume: float, tick_size: float) -> float:
        """Calculate slippage based on model"""
        if self.slippage_model == "fixed":
            return self.slippage_ticks * tick_size
        
        elif self.slippage_model == "random":
            # Random slippage between 0 and 2x base
            slippage_ticks = random.uniform(0, self.slippage_ticks * 2)
            return slippage_ticks * tick_size
        
        elif self.slippage_model == "volume_based":
            # Higher volume = more slippage
            volume_factor = min(volume / 100.0, 2.0)  # Cap at 2x
            slippage_ticks = self.slippage_ticks * volume_factor
            return slippage_ticks * tick_size
        
        return self.slippage_ticks * tick_size

