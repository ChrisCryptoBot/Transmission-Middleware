"""
Opening Range Breakout (ORB) Retest Strategy

Designed for RANGE regimes. Trades retests of opening range breakouts.

Logic:
1. Define opening range (first 15-30 minutes): OR_high, OR_low
2. Wait for breakout above OR_high (bullish) or below OR_low (bearish)
3. Wait for retest of breakout level
4. Enter when price bounces off the retest level
5. Stop: opposite side of OR
6. Target: 2x OR range size

This strategy profits from range expansion after consolidation.
"""

from typing import Optional
from datetime import time
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal
from transmission.telemetry.market_data import MarketFeatures
from transmission.config.instrument_specs import InstrumentSpecService


class ORBRetestStrategy(BaseStrategy):
    """
    Opening Range Breakout Retest Strategy

    Best for: RANGE → TREND transitions
    Timeframe: 1-5 minute bars, 15-30 min opening range
    Win Rate: 55-60% (fewer trades, high quality)
    Risk-Reward: 2:1 or better
    """

    def __init__(
        self,
        or_duration_minutes: int = 30,
        retest_tolerance_atr: float = 0.3,
        min_or_range_atr: float = 0.5,
        max_or_range_atr: float = 3.0,
        bounce_confirmation_bars: int = 2,
        instrument_spec_service: Optional[InstrumentSpecService] = None
    ):
        """
        Initialize ORB Retest strategy.

        Args:
            or_duration_minutes: Opening range duration (15, 30, 60 minutes)
            retest_tolerance_atr: How close to OR level counts as retest (in ATR)
            min_or_range_atr: Minimum OR range size to trade (filters tight ranges)
            max_or_range_atr: Maximum OR range size to trade (filters gaps/volatility)
            bounce_confirmation_bars: Bars to confirm bounce before entry
            instrument_spec_service: For multi-asset tick size lookups
        """
        super().__init__()

        self.or_duration_minutes = or_duration_minutes
        self.retest_tolerance_atr = retest_tolerance_atr
        self.min_or_range_atr = min_or_range_atr
        self.max_or_range_atr = max_or_range_atr
        self.bounce_confirmation_bars = bounce_confirmation_bars
        self.instrument_spec = instrument_spec_service or InstrumentSpecService()

        # State tracking
        self.or_high: Optional[float] = None
        self.or_low: Optional[float] = None
        self.or_established = False
        self.breakout_direction: Optional[str] = None  # 'LONG' or 'SHORT'
        self.retest_in_progress = False
        self.bounce_bars = 0

    def generate_signal(
        self,
        data: pd.DataFrame,
        features: MarketFeatures,
        symbol: str = "MNQ"
    ) -> Optional[Signal]:
        """
        Generate ORB Retest signal.

        Process:
        1. Establish opening range (if not set)
        2. Detect breakout above OR high or below OR low
        3. Wait for retest of breakout level
        4. Confirm bounce (2+ bars moving away from level)
        5. Generate signal with stop at opposite OR boundary

        Args:
            data: OHLCV DataFrame with at least OR duration + retest bars
            features: Market features from Telemetry
            symbol: Trading symbol

        Returns:
            Signal if valid setup, None otherwise
        """
        if len(data) < self.or_duration_minutes + 10:
            return None  # Not enough data

        current_price = data['close'].iloc[-1]
        current_time = data.index[-1].time()
        atr = features.atr

        # Step 1: Establish opening range
        if not self.or_established:
            self._establish_opening_range(data)
            if not self.or_established:
                return None  # OR not ready yet

        # Validate OR range size (not too tight, not too wide)
        or_range = self.or_high - self.or_low
        or_range_atr = or_range / atr if atr > 0 else 0

        if or_range_atr < self.min_or_range_atr:
            # Range too tight - likely choppy, skip
            return None

        if or_range_atr > self.max_or_range_atr:
            # Range too wide - gap or volatile open, skip
            return None

        # Step 2: Detect breakout
        if self.breakout_direction is None:
            self._detect_breakout(data, current_price, atr)
            if self.breakout_direction is None:
                return None  # No breakout yet

        # Step 3: Detect retest
        if not self.retest_in_progress:
            self._detect_retest(data, current_price, atr)
            if not self.retest_in_progress:
                return None  # No retest yet

        # Step 4: Confirm bounce
        bounce_confirmed = self._confirm_bounce(data, current_price)
        if not bounce_confirmed:
            return None  # No bounce yet

        # Step 5: Generate signal
        return self._generate_entry_signal(
            data=data,
            current_price=current_price,
            symbol=symbol,
            atr=atr,
            features=features
        )

    def _establish_opening_range(self, data: pd.DataFrame) -> None:
        """
        Calculate opening range high/low from first N minutes.

        Sets:
            self.or_high, self.or_low, self.or_established
        """
        # Get bars from market open to OR duration
        # Assuming 930am ET market open (for futures, adjust as needed)
        market_open_time = time(9, 30)
        or_end_time = time(9, 30 + self.or_duration_minutes // 60, self.or_duration_minutes % 60)

        # Filter data for OR period
        or_data = data[
            (data.index.time >= market_open_time) &
            (data.index.time < or_end_time)
        ]

        if len(or_data) < self.or_duration_minutes:
            return  # Not enough OR data yet

        self.or_high = or_data['high'].max()
        self.or_low = or_data['low'].min()
        self.or_established = True

    def _detect_breakout(self, data: pd.DataFrame, current_price: float, atr: float) -> None:
        """
        Detect breakout above OR high or below OR low.

        Sets:
            self.breakout_direction ('LONG' or 'SHORT')
        """
        # Check recent bars for close above OR high (bullish) or below OR low (bearish)
        recent_closes = data['close'].iloc[-5:]

        # Bullish breakout: close above OR high
        if (recent_closes > self.or_high).any():
            self.breakout_direction = 'LONG'

        # Bearish breakout: close below OR low
        elif (recent_closes < self.or_low).any():
            self.breakout_direction = 'SHORT'

    def _detect_retest(self, data: pd.DataFrame, current_price: float, atr: float) -> None:
        """
        Detect retest of breakout level.

        Retest = price returns within retest_tolerance of breakout level.

        Sets:
            self.retest_in_progress (True if retest detected)
        """
        tolerance = self.retest_tolerance_atr * atr

        if self.breakout_direction == 'LONG':
            # Check if price retested OR high from above
            if abs(current_price - self.or_high) <= tolerance and current_price >= self.or_high:
                self.retest_in_progress = True

        elif self.breakout_direction == 'SHORT':
            # Check if price retested OR low from below
            if abs(current_price - self.or_low) <= tolerance and current_price <= self.or_low:
                self.retest_in_progress = True

    def _confirm_bounce(self, data: pd.DataFrame, current_price: float) -> bool:
        """
        Confirm bounce off retest level.

        Bounce = price moves away from retest level for N bars.

        Returns:
            True if bounce confirmed
        """
        if not self.retest_in_progress:
            return False

        # Check if price is moving away from retest level
        recent_closes = data['close'].iloc[-(self.bounce_confirmation_bars + 1):]

        if self.breakout_direction == 'LONG':
            # Bullish bounce: recent bars closing above OR high
            if (recent_closes.iloc[-self.bounce_confirmation_bars:] > self.or_high).all():
                self.bounce_bars += 1
            else:
                self.bounce_bars = 0

        elif self.breakout_direction == 'SHORT':
            # Bearish bounce: recent bars closing below OR low
            if (recent_closes.iloc[-self.bounce_confirmation_bars:] < self.or_low).all():
                self.bounce_bars += 1
            else:
                self.bounce_bars = 0

        return self.bounce_bars >= self.bounce_confirmation_bars

    def _generate_entry_signal(
        self,
        data: pd.DataFrame,
        current_price: float,
        symbol: str,
        atr: float,
        features: MarketFeatures
    ) -> Signal:
        """
        Generate entry signal with stops and targets.

        Stop: Opposite side of OR (OR low for longs, OR high for shorts)
        Target: 2x OR range from entry
        """
        or_range = self.or_high - self.or_low

        if self.breakout_direction == 'LONG':
            entry_price = current_price
            stop_price = self.or_low  # Stop at OR low
            target_price = entry_price + (2 * or_range)  # 2x OR range target
            direction = 'LONG'

        else:  # SHORT
            entry_price = current_price
            stop_price = self.or_high  # Stop at OR high
            target_price = entry_price - (2 * or_range)  # 2x OR range target
            direction = 'SHORT'

        # Calculate confidence (higher for cleaner setups)
        confidence = self._calculate_confidence(features, or_range, atr)

        # Get asset class
        asset_class = self.instrument_spec.get_asset_class(symbol)

        # Create signal
        signal = Signal(
            symbol=symbol,
            asset_class=asset_class,
            direction=direction,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            confidence=confidence,
            strategy='ORB_RETEST',
            regime='RANGE',
            setup_quality=self._score_setup_quality(features, or_range, atr),
            notes=f"OR: {self.or_low:.2f}-{self.or_high:.2f} | Range: {or_range:.2f} | Retest bounce confirmed"
        )

        # Reset state for next setup
        self._reset_state()

        return signal

    def _calculate_confidence(self, features: MarketFeatures, or_range: float, atr: float) -> float:
        """
        Calculate setup confidence (0.0-1.0).

        Higher confidence for:
        - Clean OR range (not too tight/wide)
        - Strong volume on breakout
        - Clean retest (no whipsaw)
        """
        confidence = 0.5  # Base confidence

        # OR range quality (prefer 0.75-1.5 ATR ranges)
        or_range_atr = or_range / atr if atr > 0 else 1.0
        if 0.75 <= or_range_atr <= 1.5:
            confidence += 0.15

        # Volume above average (indicates breakout strength)
        if features.relative_volume > 1.2:
            confidence += 0.15

        # Low spread (good liquidity)
        if features.bid_ask_spread <= 1.0:
            confidence += 0.10

        # ADX rising (trend emerging after range)
        if features.adx >= 20:
            confidence += 0.10

        return min(confidence, 1.0)

    def _score_setup_quality(self, features: MarketFeatures, or_range: float, atr: float) -> str:
        """
        Score setup quality: EXCELLENT, GOOD, FAIR, POOR.
        """
        or_range_atr = or_range / atr if atr > 0 else 1.0

        # Excellent: clean range, strong volume, low spread
        if (
            0.75 <= or_range_atr <= 1.5 and
            features.relative_volume > 1.3 and
            features.bid_ask_spread <= 1.0
        ):
            return 'EXCELLENT'

        # Good: decent range, above avg volume
        elif (
            0.5 <= or_range_atr <= 2.0 and
            features.relative_volume > 1.1
        ):
            return 'GOOD'

        # Fair: acceptable but not ideal
        elif or_range_atr >= self.min_or_range_atr:
            return 'FAIR'

        # Poor: marginal setup
        return 'POOR'

    def _reset_state(self) -> None:
        """Reset strategy state after signal generation."""
        self.or_established = False
        self.breakout_direction = None
        self.retest_in_progress = False
        self.bounce_bars = 0
        self.or_high = None
        self.or_low = None

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            f"ORB Retest Strategy:\n"
            f"  OR Duration: {self.or_duration_minutes} minutes\n"
            f"  Min OR Range: {self.min_or_range_atr} ATR\n"
            f"  Max OR Range: {self.max_or_range_atr} ATR\n"
            f"  Retest Tolerance: {self.retest_tolerance_atr} ATR\n"
            f"  Bounce Confirmation: {self.bounce_confirmation_bars} bars\n"
            f"  Risk-Reward: 2:1 (2x OR range target)\n"
        )
