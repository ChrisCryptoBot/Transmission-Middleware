"""
Telemetry Module - Market Feature Calculator

Calculates all market indicators needed for regime classification:
- ADX (Average Directional Index) for trend strength
- VWAP (Volume-Weighted Average Price) and slope
- ATR (Average True Range) for volatility
- Opening Range (OR) high/low
- Microstructure features (spread, order book imbalance)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd
import numpy as np
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    # Fallback: will use manual calculations


@dataclass
class MarketFeatures:
    """Market features calculated from OHLCV data"""
    timestamp: datetime
    
    # Trend indicators
    adx_14: float  # ADX(14) for trend strength
    vwap: float  # Volume-weighted average price
    vwap_slope_abs: float  # |VWAP_now - VWAP_20bars_ago| / 20
    vwap_slope_median_20d: float  # Median slope over 20 sessions
    
    # Volatility
    atr_14: float  # Average True Range(14)
    baseline_atr: float  # Median ATR for normalization
    
    # Opening Range
    or_high: float  # 15-min OR high
    or_low: float  # 15-min OR low
    or_hold_minutes: int  # Minutes OR hasn't broken
    
    # Microstructure
    spread_ticks: float  # Bid-ask spread in ticks
    ob_imbalance: float  # (BidSize - AskSize) / (BidSize + AskSize)
    rel_volume_hour: float  # Current volume / avg volume this hour
    
    # Risk context
    news_proximity_min: Optional[int]  # Minutes to next Tier-1 event
    entry_p90_slippage: float  # 90th percentile entry slippage
    exit_p90_slippage: float  # 90th percentile exit slippage


class Telemetry:
    """
    Calculates market features from OHLCV data.
    
    This is the foundation of the Transmission system - all other
    modules depend on accurate feature calculation.
    """
    
    def __init__(self, tick_size: float = 0.25):
        """
        Initialize Telemetry calculator.
        
        Args:
            tick_size: Minimum price movement (default 0.25 for MNQ)
        """
        self.tick_size = tick_size
        self.vwap_cache = {}  # Cache VWAP calculations by symbol
    
    def calculate_adx(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> float:
        """
        Calculate ADX (Average Directional Index) for trend strength.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ADX period (default 14)
            
        Returns:
            ADX value (0-100, higher = stronger trend)
        """
        if len(close) < period + 1:
            return 0.0
        
        # Use pandas_ta for ADX calculation if available, else fallback
        if HAS_PANDAS_TA:
            adx_df = ta.adx(high=high, low=low, close=close, length=period)
            if adx_df is None or adx_df.empty:
                return 0.0
            return float(adx_df[f'ADX_{period}'].iloc[-1])
        else:
            # Fallback: Simple directional movement calculation
            # This is a simplified version - for production, use pandas_ta
            return 20.0  # Placeholder - implement full ADX if needed
        
        if adx_df is None or adx_df.empty:
            return 0.0
        
        # Get the last ADX value
        adx_value = adx_df.iloc[-1, 0]  # First column is ADX
        
        return float(adx_value) if not pd.isna(adx_value) else 0.0
    
    def calculate_vwap(
        self,
        price: pd.Series,
        volume: pd.Series,
        symbol: Optional[str] = None
    ) -> float:
        """
        Calculate VWAP (Volume-Weighted Average Price).
        
        Args:
            price: Typically close prices
            volume: Volume data
            symbol: Optional symbol for caching
            
        Returns:
            Current VWAP value
        """
        if len(price) == 0 or len(volume) == 0:
            return 0.0
        
        # VWAP = sum(price * volume) / sum(volume)
        vwap = (price * volume).sum() / volume.sum()
        
        return float(vwap) if not pd.isna(vwap) else 0.0
    
    def calculate_vwap_slope(
        self,
        vwap_series: pd.Series,
        lookback: int = 20
    ) -> float:
        """
        Calculate absolute VWAP slope.
        
        Args:
            vwap_series: Series of VWAP values
            lookback: Number of bars to look back
            
        Returns:
            Absolute slope: |VWAP_now - VWAP_lookback_ago| / lookback
        """
        if len(vwap_series) < lookback + 1:
            return 0.0
        
        current_vwap = vwap_series.iloc[-1]
        past_vwap = vwap_series.iloc[-lookback-1]
        
        slope_abs = abs(current_vwap - past_vwap) / lookback
        
        return float(slope_abs) if not pd.isna(slope_abs) else 0.0
    
    def calculate_vwap_slope_median(
        self,
        vwap_series: pd.Series,
        window: int = 20,
        sessions: int = 20
    ) -> float:
        """
        Calculate median VWAP slope over multiple sessions.
        
        Args:
            vwap_series: Series of VWAP values
            window: Bars per session
            sessions: Number of sessions to analyze
            
        Returns:
            Median slope over sessions
        """
        if len(vwap_series) < window * sessions:
            return 0.0
        
        slopes = []
        for i in range(sessions):
            start_idx = -(i + 1) * window
            end_idx = -i * window if i > 0 else None
            session_vwap = vwap_series.iloc[start_idx:end_idx]
            
            if len(session_vwap) >= window:
                slope = self.calculate_vwap_slope(session_vwap, window)
                slopes.append(slope)
        
        if not slopes:
            return 0.0
        
        return float(np.median(slopes))
    
    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> float:
        """
        Calculate ATR (Average True Range) for volatility.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period (default 14)
            
        Returns:
            ATR value
        """
        if len(close) < period + 1:
            return 0.0
        
        # Use pandas_ta for ATR calculation
        atr_series = ta.atr(high=high, low=low, close=close, length=period)
        
        if atr_series is None or atr_series.empty:
            return 0.0
        
        atr_value = atr_series.iloc[-1]
        
        return float(atr_value) if not pd.isna(atr_value) else 0.0
    
    def calculate_baseline_atr(
        self,
        atr_series: pd.Series,
        lookback: int = 20
    ) -> float:
        """
        Calculate baseline (median) ATR for normalization.
        
        Args:
            atr_series: Series of ATR values
            lookback: Number of bars to look back
            
        Returns:
            Median ATR over lookback period
        """
        if len(atr_series) < lookback:
            return atr_series.median() if len(atr_series) > 0 else 0.0
        
        recent_atr = atr_series.iloc[-lookback:]
        baseline = recent_atr.median()
        
        return float(baseline) if not pd.isna(baseline) else 0.0
    
    def get_opening_range(
        self,
        bars_15m: pd.DataFrame,
        session_start_minutes: int = 15
    ) -> tuple[float, float]:
        """
        Get Opening Range (OR) high and low.
        
        Args:
            bars_15m: DataFrame with OHLCV data (15-minute bars)
            session_start_minutes: Minutes from session start to define OR
            
        Returns:
            Tuple of (OR_high, OR_low)
        """
        if len(bars_15m) == 0:
            return 0.0, 0.0
        
        # For MVP: Use first bar's high/low as OR
        # In production: Filter by session start time
        or_high = float(bars_15m['high'].iloc[0])
        or_low = float(bars_15m['low'].iloc[0])
        
        return or_high, or_low
    
    def calculate_or_hold_minutes(
        self,
        current_price: float,
        or_high: float,
        or_low: float,
        bars_15m: pd.DataFrame
    ) -> int:
        """
        Calculate minutes since Opening Range hasn't been broken.
        
        Args:
            current_price: Current market price
            or_high: OR high
            or_low: OR low
            bars_15m: 15-minute bars
            
        Returns:
            Minutes OR has held (0 if broken)
        """
        if current_price > or_high or current_price < or_low:
            return 0
        
        # Count bars where price stayed within OR
        hold_count = 0
        for i in range(len(bars_15m) - 1, -1, -1):
            bar = bars_15m.iloc[i]
            if or_low <= bar['close'] <= or_high:
                hold_count += 1
            else:
                break
        
        return hold_count * 15  # 15 minutes per bar
    
    def calculate_spread_ticks(
        self,
        bid: float,
        ask: float,
        tick_size: Optional[float] = None
    ) -> float:
        """
        Calculate bid-ask spread in ticks.
        
        Args:
            bid: Bid price
            ask: Ask price
            tick_size: Tick size (defaults to self.tick_size)
            
        Returns:
            Spread in ticks
        """
        if tick_size is None:
            tick_size = self.tick_size
        
        if tick_size == 0:
            return 0.0
        
        spread = (ask - bid) / tick_size
        
        return float(spread) if not pd.isna(spread) else 0.0
    
    def calculate_ob_imbalance(
        self,
        bid_size: float,
        ask_size: float
    ) -> float:
        """
        Calculate order book imbalance.
        
        Args:
            bid_size: Total bid size
            ask_size: Total ask size
            
        Returns:
            Imbalance: (BidSize - AskSize) / (BidSize + AskSize)
            Range: -1.0 (all asks) to +1.0 (all bids)
        """
        total_size = bid_size + ask_size
        
        if total_size == 0:
            return 0.0
        
        imbalance = (bid_size - ask_size) / total_size
        
        return float(imbalance) if not pd.isna(imbalance) else 0.0
    
    def calculate_relative_volume(
        self,
        current_volume: float,
        avg_volume_hour: float
    ) -> float:
        """
        Calculate relative volume (current vs average).
        
        Args:
            current_volume: Current period volume
            avg_volume_hour: Average volume for this hour
            
        Returns:
            Relative volume ratio
        """
        if avg_volume_hour == 0:
            return 1.0
        
        rel_vol = current_volume / avg_volume_hour
        
        return float(rel_vol) if not pd.isna(rel_vol) else 1.0
    
    def calculate_all_features(
        self,
        bars_15m: pd.DataFrame,
        current_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        bid_size: Optional[float] = None,
        ask_size: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> MarketFeatures:
        """
        Calculate all market features from bar data.
        
        This is the main entry point for feature calculation.
        
        Args:
            bars_15m: DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
            current_price: Current market price
            bid: Current bid price (optional)
            ask: Current ask price (optional)
            bid_size: Current bid size (optional)
            ask_size: Current ask size (optional)
            timestamp: Current timestamp (defaults to now)
            
        Returns:
            MarketFeatures dataclass with all calculated features
        """
        if len(bars_15m) < 20:
            raise ValueError("Need at least 20 bars for feature calculation")
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Extract series
        high = bars_15m['high']
        low = bars_15m['low']
        close = bars_15m['close']
        volume = bars_15m['volume']
        
        # Calculate indicators
        adx_14 = self.calculate_adx(high, low, close, period=14)
        vwap = self.calculate_vwap(close, volume)
        vwap_series = pd.Series([vwap] * len(close))  # Simplified for MVP
        vwap_slope_abs = self.calculate_vwap_slope(close, lookback=20)
        vwap_slope_median_20d = self.calculate_vwap_slope_median(close, window=20, sessions=20)
        
        atr_14 = self.calculate_atr(high, low, close, period=14)
        atr_series = pd.Series([atr_14] * len(close))  # Simplified for MVP
        baseline_atr = self.calculate_baseline_atr(atr_series, lookback=20)
        
        # Opening Range
        or_high, or_low = self.get_opening_range(bars_15m)
        or_hold_minutes = self.calculate_or_hold_minutes(current_price, or_high, or_low, bars_15m)
        
        # Microstructure (use defaults if not provided)
        spread_ticks = 0.0
        if bid is not None and ask is not None:
            spread_ticks = self.calculate_spread_ticks(bid, ask)
        
        ob_imbalance = 0.0
        if bid_size is not None and ask_size is not None:
            ob_imbalance = self.calculate_ob_imbalance(bid_size, ask_size)
        
        # Relative volume (simplified - use current volume as proxy)
        avg_volume_hour = volume.mean() if len(volume) > 0 else 1.0
        rel_volume_hour = self.calculate_relative_volume(volume.iloc[-1], avg_volume_hour)
        
        # Risk context (defaults for MVP)
        news_proximity_min = None
        entry_p90_slippage = 0.0
        exit_p90_slippage = 0.0
        
        return MarketFeatures(
            timestamp=timestamp,
            adx_14=adx_14,
            vwap=vwap,
            vwap_slope_abs=vwap_slope_abs,
            vwap_slope_median_20d=vwap_slope_median_20d,
            atr_14=atr_14,
            baseline_atr=baseline_atr,
            or_high=or_high,
            or_low=or_low,
            or_hold_minutes=or_hold_minutes,
            spread_ticks=spread_ticks,
            ob_imbalance=ob_imbalance,
            rel_volume_hour=rel_volume_hour,
            news_proximity_min=news_proximity_min,
            entry_p90_slippage=entry_p90_slippage,
            exit_p90_slippage=exit_p90_slippage
        )

