"""
Gear State Machine - The "Transmission" Core

Formalizes the system's adaptive behavior into explicit gear states.

Gears (like a vehicle transmission):
- P (PARK): Trading locked - emergency stop, tripwires hit, kill switch
- R (REVERSE): Recovery mode - drawdown recovery, cooldown active
- N (NEUTRAL): Standby - engine on but not trading (news blackout, outside session)
- D (DRIVE): Normal trading - all systems go, full risk allocation
- L (LOW): Risk downshifted - reduced size/frequency due to volatility/losses/mental state

The gear is derived from real-time data, not arbitrary:
- Risk status (daily/weekly R)
- Mental state (psychology)
- Regime (market conditions)
- Volatility (ATR spikes)
- Constraints (DLL, consistency rules)
- Session (time of day, news events)
"""

from enum import Enum
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from loguru import logger


# WebSocket manager (imported globally, set from orchestrator)
websocket_manager = None


def set_websocket_manager(manager):
    """Set the WebSocket manager instance"""
    global websocket_manager
    websocket_manager = manager


class GearState(Enum):
    """
    Transmission gear states.

    Think of this like a vehicle transmission:
    - P = Emergency brake
    - R = Backing up carefully
    - N = Idling
    - D = Normal driving
    - L = Low gear (cautious)
    """
    PARK = "P"      # Trading locked
    REVERSE = "R"   # Recovery mode
    NEUTRAL = "N"   # Standby (not trading)
    DRIVE = "D"     # Normal trading
    LOW = "L"       # Risk downshifted


@dataclass
class GearContext:
    """Context used to determine gear state"""
    # Risk metrics
    daily_r: float
    weekly_r: float
    consecutive_losses: int
    current_drawdown: float

    # Market conditions
    regime: str  # TREND, RANGE, VOLATILE, NOTRADE
    volatility_percentile: float  # 0-1 (current ATR vs historical)

    # Psychology
    mental_state: int  # 1-5 (1=CRITICAL, 5=EXCELLENT)

    # Constraints
    dll_remaining: float  # Daily loss limit remaining (%)
    tripwire_active: bool

    # Session
    in_trading_session: bool
    news_blackout_active: bool

    # System
    kill_switch_active: bool
    positions_open: int


@dataclass
class GearShift:
    """Record of a gear change"""
    timestamp: datetime
    from_gear: GearState
    to_gear: GearState
    reason: str
    context: Dict


class GearStateMachine:
    """
    Main gear state machine.

    Determines current gear based on real-time context.
    Logs every shift with reason and context.
    """

    def __init__(self, database=None, initial_gear: GearState = GearState.NEUTRAL):
        """
        Initialize gear state machine

        Args:
            database: Database instance for logging gear shifts
            initial_gear: Starting gear (default: NEUTRAL)
        """
        self.current_gear = initial_gear
        self.shift_history: List[GearShift] = []
        self.database = database

        # Configuration (thresholds for gear shifts)
        self.config = {
            # PARK thresholds
            'park_daily_r_limit': -2.0,      # -2R daily = PARK
            'park_weekly_r_limit': -5.0,     # -5R weekly = PARK
            'park_drawdown_limit': -0.10,    # -10% DD = PARK

            # REVERSE thresholds (recovery mode)
            'reverse_daily_r_trigger': -1.5,  # -1.5R = enter recovery
            'reverse_exit_daily_r': -0.5,     # Back to -0.5R = exit recovery

            # LOW thresholds (risk downshift)
            'low_loss_streak': 2,             # 2 consecutive losses = LOW
            'low_volatility_percentile': 0.8, # 80th percentile ATR = LOW
            'low_mental_state': 3,            # Mental state < 3 = LOW
            'low_dll_remaining': 0.3,         # < 30% DLL remaining = LOW

            # NEUTRAL triggers (standby)
            # news_blackout_active, outside session handled automatically
        }

    def determine_gear(self, context: GearContext) -> Tuple[GearState, str]:
        """
        Determine appropriate gear based on current context.

        Priority order (top = highest):
        1. PARK - Emergency conditions
        2. REVERSE - Recovery mode
        3. NEUTRAL - Not trading (session/news)
        4. LOW - Risk downshift
        5. DRIVE - Normal trading

        Returns:
            (new_gear, reason)
        """

        # PRIORITY 1: PARK (Emergency)
        if context.kill_switch_active:
            return (GearState.PARK, "Kill switch activated")

        if context.tripwire_active:
            return (GearState.PARK, "Risk tripwire triggered")

        if context.daily_r <= self.config['park_daily_r_limit']:
            return (GearState.PARK, f"Daily loss limit reached ({context.daily_r:.2f}R)")

        if context.weekly_r <= self.config['park_weekly_r_limit']:
            return (GearState.PARK, f"Weekly loss limit reached ({context.weekly_r:.2f}R)")

        if context.current_drawdown <= self.config['park_drawdown_limit']:
            return (GearState.PARK, f"Maximum drawdown reached ({context.current_drawdown:.1%})")

        # PRIORITY 2: REVERSE (Recovery Mode)
        # Enter REVERSE if we're in drawdown but not at PARK limits
        if context.daily_r <= self.config['reverse_daily_r_trigger']:
            return (GearState.REVERSE, f"Recovery mode: {context.daily_r:.2f}R daily drawdown")

        # Exit REVERSE once we recover to -0.5R
        if self.current_gear == GearState.REVERSE:
            if context.daily_r >= self.config['reverse_exit_daily_r']:
                return (GearState.DRIVE, f"Recovered to {context.daily_r:.2f}R")
            else:
                return (GearState.REVERSE, "Still in recovery mode")

        # PRIORITY 3: NEUTRAL (Standby)
        if not context.in_trading_session:
            return (GearState.NEUTRAL, "Outside trading session")

        if context.news_blackout_active:
            return (GearState.NEUTRAL, "News blackout window")

        if context.regime == "NOTRADE":
            return (GearState.NEUTRAL, "Market regime: NOTRADE")

        # PRIORITY 4: LOW (Risk Downshift)
        reasons = []

        if context.consecutive_losses >= self.config['low_loss_streak']:
            reasons.append(f"Loss streak ({context.consecutive_losses})")

        if context.volatility_percentile >= self.config['low_volatility_percentile']:
            reasons.append(f"High volatility ({context.volatility_percentile:.0%})")

        if context.mental_state < self.config['low_mental_state']:
            reasons.append(f"Mental state: {context.mental_state}/5")

        if context.dll_remaining < self.config['low_dll_remaining']:
            reasons.append(f"DLL low ({context.dll_remaining:.0%} remaining)")

        if reasons:
            return (GearState.LOW, " | ".join(reasons))

        # PRIORITY 5: DRIVE (Normal Trading)
        return (GearState.DRIVE, "All systems nominal")

    def shift(self, context: GearContext) -> Tuple[GearState, str]:
        """
        Check if gear should shift, execute shift if needed, and return current gear.

        Args:
            context: Current system context

        Returns:
            Tuple of (current_gear, reason)
        """
        new_gear, reason = self.determine_gear(context)

        if new_gear != self.current_gear:
            # Gear shift detected
            shift = GearShift(
                timestamp=datetime.now(timezone.utc),
                from_gear=self.current_gear,
                to_gear=new_gear,
                reason=reason,
                context={
                    'daily_r': context.daily_r,
                    'weekly_r': context.weekly_r,
                    'consecutive_losses': context.consecutive_losses,
                    'regime': context.regime,
                    'mental_state': context.mental_state,
                    'volatility_percentile': context.volatility_percentile,
                }
            )

            logger.info(
                f"⚙️ GEAR SHIFT: {self.current_gear.value} → {new_gear.value} | {reason}"
            )

            # Log shift to database if available
            if self.database:
                try:
                    self.database.log_gear_shift(
                        from_gear=self.current_gear.value,
                        to_gear=new_gear.value,
                        reason=reason,
                        daily_r=context.daily_r,
                        weekly_r=context.weekly_r,
                        consecutive_losses=context.consecutive_losses,
                        current_drawdown=context.current_drawdown,
                        regime=context.regime,
                        volatility_percentile=context.volatility_percentile,
                        mental_state=context.mental_state,
                        dll_remaining=context.dll_remaining,
                        tripwire_active=context.tripwire_active,
                        in_trading_session=context.in_trading_session,
                        news_blackout_active=context.news_blackout_active,
                        kill_switch_active=context.kill_switch_active,
                        positions_open=context.positions_open
                    )
                except Exception as e:
                    logger.error(f"Failed to log gear shift to database: {e}")

            # Broadcast gear change via WebSocket
            if websocket_manager:
                try:
                    from transmission.api.websocket import broadcast_gear_change
                    broadcast_gear_change(
                        from_gear=self.current_gear.value,
                        to_gear=new_gear.value,
                        reason=reason,
                        context={
                            'daily_r': context.daily_r,
                            'weekly_r': context.weekly_r,
                            'consecutive_losses': context.consecutive_losses,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to broadcast gear change via WebSocket: {e}")

            self.current_gear = new_gear
            self.shift_history.append(shift)

            # Keep only last 100 shifts
            if len(self.shift_history) > 100:
                self.shift_history = self.shift_history[-100:]

        return (self.current_gear, reason)

    def get_current_gear(self) -> GearState:
        """Get current gear state"""
        return self.current_gear

    def get_shift_history(self, limit: int = 20) -> List[GearShift]:
        """Get recent gear shifts"""
        return self.shift_history[-limit:]

    def can_trade(self) -> bool:
        """Check if trading is allowed in current gear"""
        return self.current_gear in [GearState.DRIVE, GearState.LOW, GearState.REVERSE]

    def get_risk_multiplier(self) -> float:
        """
        Get position size multiplier based on current gear.

        Returns:
            Multiplier for position sizing (0.0 - 1.0)
        """
        multipliers = {
            GearState.PARK: 0.0,      # No trading
            GearState.REVERSE: 0.5,   # 50% size (recovery mode)
            GearState.NEUTRAL: 0.0,   # No trading (standby)
            GearState.DRIVE: 1.0,     # Full size
            GearState.LOW: 0.65,      # 65% size (risk downshift)
        }
        return multipliers.get(self.current_gear, 0.0)

    def get_state_info(self) -> Dict:
        """Get current gear state information"""
        return {
            'current_gear': self.current_gear.value,
            'can_trade': self.can_trade(),
            'risk_multiplier': self.get_risk_multiplier(),
            'shift_count': len(self.shift_history),
            'last_shift': self.shift_history[-1] if self.shift_history else None
        }
