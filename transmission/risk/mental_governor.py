"""
Mental Governor

Auto-downshifts position size or disables entries when psychology flags trip.
Tracks recent R drawdown, loss streaks, and self-reported mental state.
"""

from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum


class MentalState(Enum):
    """Mental state levels"""
    EXCELLENT = 5
    GOOD = 4
    NEUTRAL = 3
    POOR = 2
    CRITICAL = 1


@dataclass
class MentalStateConfig:
    """Configuration for mental state governor"""
    # Size multipliers by state
    size_multipliers: dict[MentalState, float] = None
    
    # Cooldown periods (minutes)
    cooldown_minutes: dict[MentalState, int] = None
    
    # Auto-disable thresholds
    auto_disable_on_streak: int = 3  # Disable after N consecutive losses
    auto_disable_on_drawdown_r: float = -1.5  # Disable after -1.5R drawdown
    
    def __post_init__(self):
        """Set defaults if not provided"""
        if self.size_multipliers is None:
            self.size_multipliers = {
                MentalState.EXCELLENT: 1.0,
                MentalState.GOOD: 0.9,
                MentalState.NEUTRAL: 0.75,
                MentalState.POOR: 0.5,
                MentalState.CRITICAL: 0.25
            }
        
        if self.cooldown_minutes is None:
            self.cooldown_minutes = {
                MentalState.EXCELLENT: 0,
                MentalState.GOOD: 0,
                MentalState.NEUTRAL: 15,
                MentalState.POOR: 60,
                MentalState.CRITICAL: 240  # 4 hours
            }


@dataclass
class MentalStateResult:
    """Result of mental state evaluation"""
    current_state: MentalState
    size_multiplier: float
    can_trade: bool
    cooldown_until: Optional[datetime]
    reason: str
    auto_detected: bool  # True if auto-detected, False if user-reported


class MentalGovernor:
    """
    Mental state governor.
    
    Tracks:
    - Recent R drawdown
    - Loss streaks
    - Self-reported mental state
    
    Outputs:
    - Position size multiplier
    - Cooldown period
    - Trade enable/disable
    """
    
    def __init__(self, config: Optional[MentalStateConfig] = None):
        """
        Initialize Mental Governor.
        
        Args:
            config: Configuration (uses defaults if None)
        """
        self.config = config or MentalStateConfig()
        self.current_state: MentalState = MentalState.NEUTRAL
        self.user_reported_state: Optional[MentalState] = None
        self.last_trade_time: Optional[datetime] = None
        self.consecutive_losses: int = 0
        self.recent_drawdown_r: float = 0.0
        self.cooldown_until: Optional[datetime] = None
    
    def update_from_trade(
        self,
        trade_result_r: float,
        trade_time: Optional[datetime] = None
    ) -> None:
        """
        Update mental state from trade result.
        
        Args:
            trade_result_r: Trade result in R
            trade_time: Trade timestamp (defaults to now)
        """
        if trade_time is None:
            trade_time = datetime.now()
        
        self.last_trade_time = trade_time
        
        if trade_result_r < 0:
            self.consecutive_losses += 1
            self.recent_drawdown_r += trade_result_r
        else:
            # Reset on win
            self.consecutive_losses = 0
            if self.recent_drawdown_r < 0:
                self.recent_drawdown_r = 0.0
        
        # Auto-detect state based on performance
        self._auto_detect_state()
    
    def set_user_state(self, state: MentalState) -> None:
        """
        Set user-reported mental state.
        
        Args:
            state: User-reported state (1-5)
        """
        self.user_reported_state = state
        self.current_state = state
        logger.info(f"User reported mental state: {state.name}")
    
    def evaluate(
        self,
        current_drawdown_r: float = 0.0,
        time_since_last_trade: Optional[timedelta] = None
    ) -> MentalStateResult:
        """
        Evaluate current mental state and return trading permissions.
        
        Args:
            current_drawdown_r: Current drawdown in R
            time_since_last_trade: Time since last trade (for cooldown)
        
        Returns:
            MentalStateResult with permissions and multipliers
        """
        # Check cooldown
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return MentalStateResult(
                current_state=self.current_state,
                size_multiplier=0.0,
                can_trade=False,
                cooldown_until=self.cooldown_until,
                reason=f"Cooldown active until {self.cooldown_until}",
                auto_detected=True
            )
        
        # Auto-detect if no user override
        if self.user_reported_state is None:
            self._auto_detect_state()
        
        # Check auto-disable conditions
        can_trade = True
        reason = "All clear"
        
        if self.consecutive_losses >= self.config.auto_disable_on_streak:
            can_trade = False
            reason = f"Auto-disable: {self.consecutive_losses} consecutive losses"
            # Set cooldown
            cooldown_mins = self.config.cooldown_minutes.get(self.current_state, 60)
            self.cooldown_until = datetime.now() + timedelta(minutes=cooldown_mins)
        
        if current_drawdown_r <= self.config.auto_disable_on_drawdown_r:
            can_trade = False
            reason = f"Auto-disable: drawdown {current_drawdown_r:.2f}R"
            cooldown_mins = self.config.cooldown_minutes.get(self.current_state, 60)
            self.cooldown_until = datetime.now() + timedelta(minutes=cooldown_mins)
        
        # Get size multiplier
        size_multiplier = self.config.size_multipliers.get(self.current_state, 0.75)
        
        # Reduce multiplier further if in drawdown
        if current_drawdown_r < -0.5:
            size_multiplier *= 0.8
        
        return MentalStateResult(
            current_state=self.current_state,
            size_multiplier=max(0.0, size_multiplier),  # Never negative
            can_trade=can_trade,
            cooldown_until=self.cooldown_until,
            reason=reason,
            auto_detected=self.user_reported_state is None
        )
    
    def _auto_detect_state(self) -> None:
        """Auto-detect mental state from performance metrics"""
        # Start with neutral
        detected = MentalState.NEUTRAL
        
        # Adjust based on consecutive losses
        if self.consecutive_losses >= 3:
            detected = MentalState.CRITICAL
        elif self.consecutive_losses >= 2:
            detected = MentalState.POOR
        elif self.consecutive_losses >= 1:
            detected = MentalState.NEUTRAL
        
        # Adjust based on recent drawdown
        if self.recent_drawdown_r <= -2.0:
            detected = MentalState.CRITICAL
        elif self.recent_drawdown_r <= -1.0:
            detected = MentalState.POOR
        elif self.recent_drawdown_r <= -0.5:
            detected = MentalState.NEUTRAL
        
        # Only update if no user override
        if self.user_reported_state is None:
            self.current_state = detected
    
    def reset_cooldown(self) -> None:
        """Manually reset cooldown (for testing/admin)"""
        self.cooldown_until = None
        logger.info("Mental governor cooldown reset")
    
    def get_current_state(self) -> MentalState:
        """Get current mental state"""
        return self.current_state
    
    def get_state_info(self) -> dict:
        """Get current state information"""
        result = self.evaluate()
        return {
            'state': result.current_state.name,
            'state_value': result.current_state.value,
            'size_multiplier': result.size_multiplier,
            'can_trade': result.can_trade,
            'cooldown_until': result.cooldown_until.isoformat() if result.cooldown_until else None,
            'reason': result.reason,
            'consecutive_losses': self.consecutive_losses,
            'recent_drawdown_r': self.recent_drawdown_r,
            'auto_detected': result.auto_detected
        }

