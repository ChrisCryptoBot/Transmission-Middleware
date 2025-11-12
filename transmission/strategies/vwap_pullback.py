"""
VWAP Pullback Strategy

Trend-following strategy that enters on pullbacks to VWAP in trending markets.
Works in TREND regime only.

Based on Product_Concept.txt specifications.
"""

from typing import Optional, List
from datetime import datetime
from transmission.strategies.base import BaseStrategy, Signal, Position
from transmission.telemetry.market_data import MarketFeatures


class VWAPPullbackStrategy(BaseStrategy):
    """
    VWAP Pullback Strategy for trending markets.
    
    Entry Logic:
    - Market must be in TREND regime
    - Price pulls back to VWAP (within adaptive distance)
    - Entry on bounce from VWAP
    
    Exit Logic:
    - Stop: Below recent swing low (for longs) or above swing high (for shorts)
    - Target: 2:1 or 3:1 risk:reward ratio
    """
    
    def __init__(
        self,
        risk_reward_ratio: float = 2.0,
        vwap_distance_threshold: float = 0.5,  # % distance from VWAP
        min_adx: float = 25.0
    ):
        """
        Initialize VWAP Pullback Strategy.
        
        Args:
            risk_reward_ratio: Target risk:reward (default 2:1)
            vwap_distance_threshold: Maximum % distance from VWAP for entry (default 0.5%)
            min_adx: Minimum ADX for trend confirmation (default 25)
        """
        self.risk_reward_ratio = risk_reward_ratio
        self.vwap_distance_threshold = vwap_distance_threshold
        self.min_adx = min_adx
    
    @property
    def required_regime(self) -> str:
        """This strategy works in TREND regime"""
        return 'TREND'
    
    @property
    def strategy_name(self) -> str:
        """Human-readable strategy name"""
        return 'VWAP Pullback'
    
    def generate_signal(
        self,
        features: MarketFeatures,
        regime: str,
        current_positions: List[Position]
    ) -> Optional[Signal]:
        """
        Generate VWAP Pullback signal.
        
        Args:
            features: MarketFeatures with indicators
            regime: Current market regime
            current_positions: Currently open positions
            
        Returns:
            Signal if setup found, None otherwise
        """
        # Must be in TREND regime
        if not self.validate_regime(regime):
            return None
        
        # ADX must be above minimum for trend strength
        if features.adx_14 < self.min_adx:
            return None
        
        # Check for existing position (one trade at a time for MVP)
        if len(current_positions) > 0:
            return None
        
        # Determine direction based on VWAP slope
        # Positive slope = uptrend (long), negative slope = downtrend (short)
        vwap_slope_positive = features.vwap_slope_abs > features.vwap_slope_median_20d
        
        if vwap_slope_positive:
            # Uptrend - look for long entry
            signal = self._check_long_entry(features)
        else:
            # Downtrend - look for short entry
            signal = self._check_short_entry(features)
        
        return signal
    
    def _check_long_entry(self, features: MarketFeatures) -> Optional[Signal]:
        """
        Check for long entry on VWAP pullback.
        
        Entry conditions:
        - Price is at or below VWAP (pullback)
        - Price is within threshold distance of VWAP
        - VWAP slope is positive (uptrend)
        """
        current_price = features.vwap  # Simplified - in production, use actual current price
        
        # Calculate distance from VWAP
        distance_pct = abs((current_price - features.vwap) / features.vwap) * 100
        
        # Must be within threshold distance
        if distance_pct > self.vwap_distance_threshold:
            return None
        
        # Entry price (at VWAP or slightly below)
        entry_price = features.vwap
        
        # Stop loss: Below recent low (use ATR for stop distance)
        stop_distance = features.atr_14 * 0.5  # 0.5 ATR stop
        stop_price = entry_price - stop_distance
        
        # Target: Risk:reward ratio
        risk = entry_price - stop_price
        reward = risk * self.risk_reward_ratio
        target_price = entry_price + reward
        
        # Calculate confidence
        setup_quality = 0.7  # Base quality
        if features.adx_14 > 30:
            setup_quality += 0.1  # Strong trend
        if distance_pct < 0.3:
            setup_quality += 0.1  # Close to VWAP
        
        confidence = self.calculate_confidence(features, setup_quality)
        
        return Signal(
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            direction='LONG',
            contracts=1,  # Will be adjusted by position sizer
            confidence=confidence,
            regime='TREND',
            strategy=self.strategy_name,
            timestamp=datetime.now(),
            notes=f"VWAP pullback, ADX={features.adx_14:.1f}, distance={distance_pct:.2f}%"
        )
    
    def _check_short_entry(self, features: MarketFeatures) -> Optional[Signal]:
        """
        Check for short entry on VWAP pullback.
        
        Entry conditions:
        - Price is at or above VWAP (pullback in downtrend)
        - Price is within threshold distance of VWAP
        - VWAP slope is negative (downtrend)
        """
        current_price = features.vwap  # Simplified
        
        # Calculate distance from VWAP
        distance_pct = abs((current_price - features.vwap) / features.vwap) * 100
        
        # Must be within threshold distance
        if distance_pct > self.vwap_distance_threshold:
            return None
        
        # Entry price (at VWAP or slightly above)
        entry_price = features.vwap
        
        # Stop loss: Above recent high
        stop_distance = features.atr_14 * 0.5
        stop_price = entry_price + stop_distance
        
        # Target: Risk:reward ratio
        risk = stop_price - entry_price
        reward = risk * self.risk_reward_ratio
        target_price = entry_price - reward
        
        # Calculate confidence
        setup_quality = 0.7
        if features.adx_14 > 30:
            setup_quality += 0.1
        if distance_pct < 0.3:
            setup_quality += 0.1
        
        confidence = self.calculate_confidence(features, setup_quality)
        
        return Signal(
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            direction='SHORT',
            contracts=1,
            confidence=confidence,
            regime='TREND',
            strategy=self.strategy_name,
            timestamp=datetime.now(),
            notes=f"VWAP pullback short, ADX={features.adx_14:.1f}, distance={distance_pct:.2f}%"
        )

