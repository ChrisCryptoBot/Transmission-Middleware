"""
Execution Guard Module

Safeguards around order execution quality:
- Spread checks (reject if too wide)
- Slippage monitoring
- Liquidity checks (order book depth)
- Order type selection (limit vs market)

Based on ACTION_PLAN_CONCEPT.txt and Product_Concept.txt.
"""

from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime
from loguru import logger


@dataclass
class ExecutionCheck:
    """Result of execution guard check"""
    approved: bool
    reason: str
    recommended_order_type: Literal['LIMIT', 'MARKET', 'POST_ONLY']
    max_slippage_ticks: float


class ExecutionGuard:
    """
    Guards order execution quality.
    
    Checks:
    - Spread width (reject if > 2 ticks)
    - Order book depth
    - Slippage risk
    - Liquidity conditions
    """
    
    def __init__(
        self,
        max_spread_ticks: float = 2.0,
        min_orderbook_depth: float = 3.0,  # 3x order size
        max_slippage_ticks: float = 1.0,
        prefer_limit: bool = True
    ):
        """
        Initialize Execution Guard.
        
        Args:
            max_spread_ticks: Maximum spread for trading (default 2 ticks)
            min_orderbook_depth: Minimum order book depth (default 3x order size)
            max_slippage_ticks: Maximum acceptable slippage (default 1 tick)
            prefer_limit: Prefer limit orders over market (default True)
        """
        self.max_spread_ticks = max_spread_ticks
        self.min_orderbook_depth = min_orderbook_depth
        self.max_slippage_ticks = max_slippage_ticks
        self.prefer_limit = prefer_limit
    
    def validate_execution(
        self,
        spread_ticks: float,
        order_size: int,
        orderbook_bid_size: Optional[float] = None,
        orderbook_ask_size: Optional[float] = None,
        current_slippage_p90: Optional[float] = None
    ) -> ExecutionCheck:
        """
        Validate if execution conditions are acceptable.
        
        Args:
            spread_ticks: Current bid-ask spread in ticks
            order_size: Number of contracts to trade
            orderbook_bid_size: Size at best bid (optional)
            orderbook_ask_size: Size at best ask (optional)
            current_slippage_p90: 90th percentile slippage (optional)
            
        Returns:
            ExecutionCheck with approval status and recommendations
        """
        # Check spread
        if spread_ticks > self.max_spread_ticks:
            return ExecutionCheck(
                approved=False,
                reason=f"Spread {spread_ticks:.1f} ticks > limit {self.max_spread_ticks}",
                recommended_order_type='LIMIT',
                max_slippage_ticks=0.0
            )
        
        # Check order book depth (if available)
        if orderbook_bid_size is not None and orderbook_ask_size is not None:
            min_depth = order_size * self.min_orderbook_depth
            if orderbook_bid_size < min_depth or orderbook_ask_size < min_depth:
                return ExecutionCheck(
                    approved=False,
                    reason=f"Insufficient order book depth: bid={orderbook_bid_size}, ask={orderbook_ask_size}, required={min_depth}",
                    recommended_order_type='LIMIT',
                    max_slippage_ticks=0.0
                )
        
        # Check slippage history (if available)
        if current_slippage_p90 is not None:
            if current_slippage_p90 > self.max_slippage_ticks:
                # Still approve but recommend limit order
                return ExecutionCheck(
                    approved=True,
                    reason=f"High slippage risk (P90={current_slippage_p90:.1f} ticks), use limit order",
                    recommended_order_type='LIMIT',
                    max_slippage_ticks=self.max_slippage_ticks
                )
        
        # Determine order type
        if self.prefer_limit:
            order_type = 'LIMIT'
        elif spread_ticks <= 1.0:
            order_type = 'MARKET'  # Tight spread, market OK
        else:
            order_type = 'LIMIT'  # Wide spread, use limit
        
        return ExecutionCheck(
            approved=True,
            reason="Execution conditions acceptable",
            recommended_order_type=order_type,
            max_slippage_ticks=self.max_slippage_ticks
        )
    
    def should_cancel_order(
        self,
        order_age_seconds: float,
        fill_percentage: float,
        max_wait_seconds: float = 2.0
    ) -> bool:
        """
        Determine if an unfilled order should be cancelled.
        
        Args:
            order_age_seconds: How long order has been pending
            fill_percentage: Percentage of order filled (0.0 to 1.0)
            max_wait_seconds: Maximum wait time before cancel (default 2s)
            
        Returns:
            True if order should be cancelled
        """
        # Cancel if order is old and not filled
        if order_age_seconds > max_wait_seconds and fill_percentage < 0.5:
            logger.warning(
                f"Order cancellation recommended: age={order_age_seconds:.1f}s, "
                f"fill={fill_percentage:.1%}"
            )
            return True
        
        return False
    
    def calculate_expected_slippage(
        self,
        spread_ticks: float,
        order_type: Literal['LIMIT', 'MARKET'],
        order_size: int,
        historical_slippage_p50: Optional[float] = None
    ) -> float:
        """
        Estimate expected slippage for an order.
        
        Args:
            spread_ticks: Current spread
            order_type: LIMIT or MARKET
            order_size: Number of contracts
            historical_slippage_p50: Historical median slippage (optional)
            
        Returns:
            Expected slippage in ticks
        """
        if order_type == 'LIMIT':
            # Limit orders: slippage is typically 0 if filled, or spread if not
            return spread_ticks * 0.5  # Assume 50% of spread
        
        # Market orders: slippage is spread + market impact
        base_slippage = spread_ticks * 0.5  # Half the spread
        
        # Add market impact (simplified - larger orders = more impact)
        if order_size > 5:
            market_impact = 0.5  # Additional slippage for large orders
        else:
            market_impact = 0.0
        
        # Use historical data if available
        if historical_slippage_p50 is not None:
            return max(base_slippage + market_impact, historical_slippage_p50)
        
        return base_slippage + market_impact

