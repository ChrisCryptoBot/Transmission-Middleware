"""
In-Trade Manager

Manages positions after fill:
- Trailing stops (ATR-trail, swing-low/high, break-even)
- Scale-out rules (partial exits at targets)
- Time stops (max bars in trade)
"""

from typing import Optional, Literal, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import pandas as pd

from transmission.execution.adapter import Position
from transmission.telemetry.market_data import MarketFeatures


class TrailingStopMode(Enum):
    """Trailing stop modes"""
    ATR_TRAIL = "atr_trail"
    SWING_LOW_HIGH = "swing_low_high"
    BREAK_EVEN = "break_even"
    FIXED = "fixed"


@dataclass
class TrailingStopConfig:
    """Configuration for trailing stop"""
    mode: TrailingStopMode
    atr_multiplier: float = 2.0  # For ATR_TRAIL
    activation_r: float = 1.0  # Activate trailing after +1R
    min_trail_ticks: float = 4.0  # Minimum trail distance


@dataclass
class ScaleOutRule:
    """Scale-out rule configuration"""
    target_r: float  # Exit X% at this R target
    exit_percent: float  # Percentage to exit (0.0-1.0)


@dataclass
class InTradeState:
    """State of an in-trade position"""
    position_id: str
    symbol: str
    direction: Literal["LONG", "SHORT"]
    entry_price: float
    entry_time: datetime
    initial_stop: float
    initial_target: float
    contracts: int
    filled_contracts: int
    current_stop: float
    current_target: Optional[float]
    trailing_stop: Optional[TrailingStopConfig]
    scale_out_rules: list[ScaleOutRule]
    max_bars: Optional[int] = None
    bars_in_trade: int = 0
    highest_price: float  # For longs
    lowest_price: float  # For shorts
    unrealized_pnl_r: float = 0.0
    realized_pnl_r: float = 0.0


class InTradeManager:
    """
    Manages positions after fill.
    
    Handles:
    - Trailing stops (ATR, swing, break-even)
    - Scale-out rules (partial exits)
    - Time stops (max bars)
    """
    
    def __init__(self, tick_size: float = 0.25):
        """
        Initialize In-Trade Manager.
        
        Args:
            tick_size: Minimum price increment
        """
        self.tick_size = tick_size
        self.active_positions: Dict[str, InTradeState] = {}
    
    def register_position(
        self,
        position_id: str,
        symbol: str,
        direction: Literal["LONG", "SHORT"],
        entry_price: float,
        initial_stop: float,
        initial_target: Optional[float],
        contracts: int,
        trailing_stop: Optional[TrailingStopConfig] = None,
        scale_out_rules: Optional[list[ScaleOutRule]] = None,
        max_bars: Optional[int] = None
    ) -> InTradeState:
        """
        Register a new position for management.
        
        Args:
            position_id: Unique position identifier
            symbol: Trading symbol
            direction: LONG or SHORT
            entry_price: Entry price
            initial_stop: Initial stop loss
            initial_target: Initial take profit (optional)
            contracts: Position size
            trailing_stop: Trailing stop configuration
            scale_out_rules: Scale-out rules
            max_bars: Maximum bars to hold (time stop)
        
        Returns:
            InTradeState for the position
        """
        state = InTradeState(
            position_id=position_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_time=datetime.now(),
            initial_stop=initial_stop,
            initial_target=initial_target,
            contracts=contracts,
            filled_contracts=contracts,
            current_stop=initial_stop,
            current_target=initial_target,
            trailing_stop=trailing_stop,
            scale_out_rules=scale_out_rules or [],
            max_bars=max_bars,
            bars_in_trade=0,
            highest_price=entry_price if direction == "LONG" else float('inf'),
            lowest_price=entry_price if direction == "SHORT" else 0.0
        )
        
        self.active_positions[position_id] = state
        logger.info(
            f"Registered position {position_id}: {direction} {contracts} {symbol} @ {entry_price}, "
            f"stop={initial_stop}, target={initial_target}"
        )
        
        return state
    
    def update_position(
        self,
        position_id: str,
        current_price: float,
        features: MarketFeatures,
        bars_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Update position state and check for exit conditions.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            features: Market features (ATR, VWAP, etc.)
            bars_data: Recent bar data for swing detection
        
        Returns:
            Dict with updates: {
                'stop_moved': bool,
                'new_stop': Optional[float],
                'scale_out': Optional[Dict],
                'time_exit': bool,
                'should_exit': bool,
                'exit_reason': Optional[str]
            }
        """
        if position_id not in self.active_positions:
            return {'should_exit': False}
        
        state = self.active_positions[position_id]
        state.bars_in_trade += 1
        
        # Update highest/lowest prices
        if state.direction == "LONG":
            state.highest_price = max(state.highest_price, current_price)
        else:
            state.lowest_price = min(state.lowest_price, current_price)
        
        # Calculate unrealized P&L in R
        if state.direction == "LONG":
            price_diff = current_price - state.entry_price
        else:
            price_diff = state.entry_price - current_price
        
        # Calculate R (risk per contract)
        risk_per_contract = abs(state.entry_price - state.initial_stop)
        if risk_per_contract > 0:
            state.unrealized_pnl_r = (price_diff / risk_per_contract) * (state.filled_contracts / state.contracts)
        
        updates = {
            'stop_moved': False,
            'new_stop': None,
            'scale_out': None,
            'time_exit': False,
            'should_exit': False,
            'exit_reason': None
        }
        
        # Check time stop
        if state.max_bars and state.bars_in_trade >= state.max_bars:
            updates['time_exit'] = True
            updates['should_exit'] = True
            updates['exit_reason'] = f"Time stop: {state.bars_in_trade} bars"
            logger.info(f"Position {position_id}: Time stop triggered at {state.bars_in_trade} bars")
            return updates
        
        # Check trailing stop
        if state.trailing_stop:
            new_stop = self._calculate_trailing_stop(state, current_price, features, bars_data)
            if new_stop and new_stop != state.current_stop:
                updates['stop_moved'] = True
                updates['new_stop'] = new_stop
                state.current_stop = new_stop
                logger.info(f"Position {position_id}: Stop moved to {new_stop}")
        
        # Check scale-out rules
        for rule in state.scale_out_rules:
            if state.unrealized_pnl_r >= rule.target_r:
                # Check if we've already scaled out at this target
                if not hasattr(state, '_scaled_out_at') or rule.target_r not in getattr(state, '_scaled_out_at', []):
                    exit_contracts = int(state.filled_contracts * rule.exit_percent)
                    if exit_contracts > 0:
                        updates['scale_out'] = {
                            'target_r': rule.target_r,
                            'exit_contracts': exit_contracts,
                            'exit_price': current_price
                        }
                        state.filled_contracts -= exit_contracts
                        if not hasattr(state, '_scaled_out_at'):
                            state._scaled_out_at = []
                        state._scaled_out_at.append(rule.target_r)
                        logger.info(
                            f"Position {position_id}: Scale-out {exit_contracts} contracts at {rule.target_r}R"
                        )
                        break
        
        # Check if stop hit
        if state.direction == "LONG" and current_price <= state.current_stop:
            updates['should_exit'] = True
            updates['exit_reason'] = "Stop loss hit"
        elif state.direction == "SHORT" and current_price >= state.current_stop:
            updates['should_exit'] = True
            updates['exit_reason'] = "Stop loss hit"
        
        # Check if target hit
        if state.current_target and state.filled_contracts > 0:
            if state.direction == "LONG" and current_price >= state.current_target:
                updates['should_exit'] = True
                updates['exit_reason'] = "Take profit hit"
            elif state.direction == "SHORT" and current_price <= state.current_target:
                updates['should_exit'] = True
                updates['exit_reason'] = "Take profit hit"
        
        return updates
    
    def _calculate_trailing_stop(
        self,
        state: InTradeState,
        current_price: float,
        features: MarketFeatures,
        bars_data: Optional[pd.DataFrame]
    ) -> Optional[float]:
        """
        Calculate new trailing stop price.
        
        Args:
            state: Position state
            current_price: Current market price
            features: Market features
            bars_data: Recent bar data
        
        Returns:
            New stop price or None if no update
        """
        if not state.trailing_stop:
            return None
        
        config = state.trailing_stop
        
        # Check if trailing is activated (need +1R profit)
        if state.unrealized_pnl_r < config.activation_r:
            return None
        
        if config.mode == TrailingStopMode.BREAK_EVEN:
            # Move stop to break-even
            new_stop = state.entry_price
            if state.direction == "LONG":
                return max(state.current_stop, new_stop)
            else:
                return min(state.current_stop, new_stop)
        
        elif config.mode == TrailingStopMode.ATR_TRAIL:
            # Trail by ATR multiplier
            if not features.atr:
                return None
            
            trail_distance = features.atr * config.atr_multiplier
            min_trail = config.min_trail_ticks * self.tick_size
            
            if state.direction == "LONG":
                new_stop = current_price - max(trail_distance, min_trail)
                # Only move up
                return max(state.current_stop, new_stop)
            else:
                new_stop = current_price + max(trail_distance, min_trail)
                # Only move down
                return min(state.current_stop, new_stop)
        
        elif config.mode == TrailingStopMode.SWING_LOW_HIGH:
            # Trail to swing low (longs) or swing high (shorts)
            if bars_data is None or len(bars_data) < 5:
                return None
            
            if state.direction == "LONG":
                # Find swing low (lowest low in recent bars)
                swing_low = bars_data['low'].tail(5).min()
                new_stop = swing_low - (self.tick_size * 2)  # 2 ticks below swing
                return max(state.current_stop, new_stop)
            else:
                # Find swing high
                swing_high = bars_data['high'].tail(5).max()
                new_stop = swing_high + (self.tick_size * 2)  # 2 ticks above swing
                return min(state.current_stop, new_stop)
        
        return None
    
    def get_position_state(self, position_id: str) -> Optional[InTradeState]:
        """Get current state of a position"""
        return self.active_positions.get(position_id)
    
    def close_position(self, position_id: str, exit_price: float, exit_reason: str) -> Optional[InTradeState]:
        """
        Close a position and return final state.
        
        Args:
            position_id: Position identifier
            exit_price: Exit price
            exit_reason: Reason for exit
        
        Returns:
            Final position state or None if not found
        """
        if position_id not in self.active_positions:
            return None
        
        state = self.active_positions[position_id]
        
        # Calculate final P&L
        if state.direction == "LONG":
            price_diff = exit_price - state.entry_price
        else:
            price_diff = state.entry_price - exit_price
        
        risk_per_contract = abs(state.entry_price - state.initial_stop)
        if risk_per_contract > 0:
            state.realized_pnl_r = (price_diff / risk_per_contract) * (state.filled_contracts / state.contracts)
        
        logger.info(
            f"Position {position_id} closed: {exit_reason}, "
            f"P&L={state.realized_pnl_r:.2f}R, "
            f"bars={state.bars_in_trade}"
        )
        
        # Remove from active
        del self.active_positions[position_id]
        
        return state
    
    def list_active_positions(self) -> list[InTradeState]:
        """Get all active positions"""
        return list(self.active_positions.values())

