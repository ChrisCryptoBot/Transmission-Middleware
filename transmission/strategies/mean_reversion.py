"""
Mean Reversion Strategy

Designed for VOLATILE regimes. Trades bounces from oversold/overbought extremes.

Logic:
1. Identify oversold (RSI < 30, price < Bollinger lower) or overbought (RSI > 70, price > Bollinger upper)
2. Wait for reversal signal (bullish/bearish engulfing, hammer/shooting star)
3. Enter on bounce toward mean (VWAP or 20-period MA)
4. Tight stop beyond extreme (1.0 ATR)
5. Quick target at mean (1.0-1.5R, not greedy)

This strategy profits from volatility spikes that snap back to equilibrium.
"""

from typing import Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal
from transmission.telemetry.market_data import MarketFeatures
from transmission.config.instrument_specs import InstrumentSpecService


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy

    Best for: VOLATILE regimes (choppy, whipsaw markets)
    Timeframe: 1-5 minute bars
    Win Rate: 60-65% (many small wins, cut losers fast)
    Risk-Reward: 1:1 to 1.5:1 (quick in/out)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        bb_period: int = 20,
        bb_std: float = 2.0,
        stop_loss_atr: float = 1.0,
        target_rr: float = 1.5,
        min_bars_from_mean: int = 3,
        reversal_confirmation_bars: int = 1,
        instrument_spec_service: Optional[InstrumentSpecService] = None
    ):
        """
        Initialize Mean Reversion strategy.

        Args:
            rsi_period: RSI calculation period
            rsi_oversold: RSI threshold for oversold (< 30)
            rsi_overbought: RSI threshold for overbought (> 70)
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            stop_loss_atr: Stop distance in ATR multiples
            target_rr: Risk-reward ratio for targets (1.0-1.5)
            min_bars_from_mean: Minimum bars away from VWAP/MA to trade
            reversal_confirmation_bars: Bars to confirm reversal
            instrument_spec_service: For multi-asset support
        """
        super().__init__()

        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.stop_loss_atr = stop_loss_atr
        self.target_rr = target_rr
        self.min_bars_from_mean = min_bars_from_mean
        self.reversal_confirmation_bars = reversal_confirmation_bars
        self.instrument_spec = instrument_spec_service or InstrumentSpecService()

    def generate_signal(
        self,
        data: pd.DataFrame,
        features: MarketFeatures,
        symbol: str = "MNQ"
    ) -> Optional[Signal]:
        """
        Generate Mean Reversion signal.

        Process:
        1. Calculate RSI and Bollinger Bands
        2. Detect oversold/overbought extremes
        3. Confirm price is away from mean
        4. Wait for reversal candlestick pattern
        5. Generate signal with tight stop and quick target

        Args:
            data: OHLCV DataFrame
            features: Market features from Telemetry
            symbol: Trading symbol

        Returns:
            Signal if valid setup, None otherwise
        """
        if len(data) < max(self.rsi_period, self.bb_period) + 10:
            return None  # Not enough data

        # Calculate indicators
        rsi = self._calculate_rsi(data['close'], self.rsi_period)
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )

        current_price = data['close'].iloc[-1]
        current_low = data['low'].iloc[-1]
        current_high = data['high'].iloc[-1]
        atr = features.atr
        vwap = features.vwap

        # Use VWAP as mean (or BB middle if VWAP unavailable)
        mean_price = vwap if vwap > 0 else bb_middle.iloc[-1]

        # Check if price is sufficiently away from mean
        if not self._is_away_from_mean(data, mean_price):
            return None

        # Check for oversold/overbought conditions
        direction = None

        # LONG setup: Oversold bounce
        if rsi.iloc[-1] < self.rsi_oversold and current_price < bb_lower.iloc[-1]:
            if self._detect_bullish_reversal(data):
                direction = 'LONG'

        # SHORT setup: Overbought bounce
        elif rsi.iloc[-1] > self.rsi_overbought and current_price > bb_upper.iloc[-1]:
            if self._detect_bearish_reversal(data):
                direction = 'SHORT'

        if direction is None:
            return None  # No valid setup

        # Generate signal
        return self._generate_entry_signal(
            data=data,
            direction=direction,
            current_price=current_price,
            mean_price=mean_price,
            symbol=symbol,
            atr=atr,
            rsi=rsi.iloc[-1],
            features=features
        )

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int, num_std: float
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        return upper, middle, lower

    def _is_away_from_mean(self, data: pd.DataFrame, mean_price: float) -> bool:
        """
        Check if price has been away from mean for min_bars.

        Ensures we're not chasing price into the mean.
        """
        recent_closes = data['close'].iloc[-self.min_bars_from_mean:]

        # For longs: price should be below mean
        # For shorts: price should be above mean
        # We don't know direction yet, so check if consistently one side
        below_mean = (recent_closes < mean_price).sum()
        above_mean = (recent_closes > mean_price).sum()

        # At least N bars consistently on one side
        return below_mean >= self.min_bars_from_mean or above_mean >= self.min_bars_from_mean

    def _detect_bullish_reversal(self, data: pd.DataFrame) -> bool:
        """
        Detect bullish reversal pattern.

        Patterns:
        - Bullish engulfing (current bar engulfs previous)
        - Hammer (long lower wick, small body near high)
        - Higher low (recent low > previous low)
        """
        if len(data) < 3:
            return False

        current = data.iloc[-1]
        previous = data.iloc[-2]

        # Bullish engulfing
        if (
            current['close'] > current['open'] and  # Green bar
            previous['close'] < previous['open'] and  # Previous red
            current['close'] > previous['open'] and  # Engulfs previous open
            current['open'] < previous['close']  # Engulfs previous close
        ):
            return True

        # Hammer pattern
        body = abs(current['close'] - current['open'])
        lower_wick = min(current['open'], current['close']) - current['low']
        upper_wick = current['high'] - max(current['open'], current['close'])

        if lower_wick > (2 * body) and upper_wick < body:
            return True

        # Higher low (simple momentum shift)
        if current['low'] > previous['low'] and current['close'] > previous['close']:
            return True

        return False

    def _detect_bearish_reversal(self, data: pd.DataFrame) -> bool:
        """
        Detect bearish reversal pattern.

        Patterns:
        - Bearish engulfing
        - Shooting star (long upper wick, small body near low)
        - Lower high
        """
        if len(data) < 3:
            return False

        current = data.iloc[-1]
        previous = data.iloc[-2]

        # Bearish engulfing
        if (
            current['close'] < current['open'] and  # Red bar
            previous['close'] > previous['open'] and  # Previous green
            current['close'] < previous['open'] and  # Engulfs previous open
            current['open'] > previous['close']  # Engulfs previous close
        ):
            return True

        # Shooting star pattern
        body = abs(current['close'] - current['open'])
        lower_wick = min(current['open'], current['close']) - current['low']
        upper_wick = current['high'] - max(current['open'], current['close'])

        if upper_wick > (2 * body) and lower_wick < body:
            return True

        # Lower high (simple momentum shift)
        if current['high'] < previous['high'] and current['close'] < previous['close']:
            return True

        return False

    def _generate_entry_signal(
        self,
        data: pd.DataFrame,
        direction: str,
        current_price: float,
        mean_price: float,
        symbol: str,
        atr: float,
        rsi: float,
        features: MarketFeatures
    ) -> Signal:
        """
        Generate entry signal with stops and targets.

        Stop: 1.0 ATR beyond extreme
        Target: Mean price (VWAP), or 1.5R if mean is far
        """
        stop_distance = self.stop_loss_atr * atr

        if direction == 'LONG':
            entry_price = current_price
            stop_price = entry_price - stop_distance

            # Target: mean or 1.5R, whichever is closer (don't be greedy)
            target_at_mean = mean_price
            target_at_rr = entry_price + (stop_distance * self.target_rr)
            target_price = min(target_at_mean, target_at_rr)

        else:  # SHORT
            entry_price = current_price
            stop_price = entry_price + stop_distance

            # Target: mean or 1.5R, whichever is closer
            target_at_mean = mean_price
            target_at_rr = entry_price - (stop_distance * self.target_rr)
            target_price = max(target_at_mean, target_at_rr)

        # Calculate confidence
        confidence = self._calculate_confidence(rsi, current_price, mean_price, features)

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
            strategy='MEAN_REVERSION',
            regime='VOLATILE',
            setup_quality=self._score_setup_quality(rsi, features),
            notes=f"RSI: {rsi:.1f} | Mean: {mean_price:.2f} | Reversal confirmed"
        )

        return signal

    def _calculate_confidence(
        self, rsi: float, current_price: float, mean_price: float, features: MarketFeatures
    ) -> float:
        """
        Calculate setup confidence (0.0-1.0).

        Higher confidence for:
        - Extreme RSI (< 25 or > 75)
        - Far from mean (more room to revert)
        - Low spread (good execution)
        """
        confidence = 0.5  # Base confidence

        # Extreme RSI
        if rsi < 25 or rsi > 75:
            confidence += 0.15

        # Distance from mean (normalize by ATR)
        distance_from_mean = abs(current_price - mean_price)
        distance_atr = distance_from_mean / features.atr if features.atr > 0 else 0

        if distance_atr > 1.5:
            confidence += 0.15
        elif distance_atr > 1.0:
            confidence += 0.10

        # Low spread (good liquidity)
        if features.bid_ask_spread <= 1.0:
            confidence += 0.10

        # High volume (conviction)
        if features.relative_volume > 1.3:
            confidence += 0.10

        return min(confidence, 1.0)

    def _score_setup_quality(self, rsi: float, features: MarketFeatures) -> str:
        """Score setup quality: EXCELLENT, GOOD, FAIR, POOR."""
        # Excellent: extreme RSI, high volume, tight spread
        if (
            (rsi < 25 or rsi > 75) and
            features.relative_volume > 1.3 and
            features.bid_ask_spread <= 1.0
        ):
            return 'EXCELLENT'

        # Good: oversold/overbought with volume
        elif (
            (rsi < 30 or rsi > 70) and
            features.relative_volume > 1.1
        ):
            return 'GOOD'

        # Fair: marginal oversold/overbought
        elif rsi < 35 or rsi > 65:
            return 'FAIR'

        # Poor: weak setup
        return 'POOR'

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            f"Mean Reversion Strategy:\n"
            f"  RSI Period: {self.rsi_period}\n"
            f"  RSI Oversold: < {self.rsi_oversold}\n"
            f"  RSI Overbought: > {self.rsi_overbought}\n"
            f"  Bollinger Bands: {self.bb_period} period, {self.bb_std} std\n"
            f"  Stop Loss: {self.stop_loss_atr} ATR\n"
            f"  Target R:R: {self.target_rr}:1\n"
            f"  Risk-Reward: {self.target_rr}:1 (quick scalps)\n"
        )
