"""
Regime Classifier Module

Classifies market conditions into regimes:
- TREND: Strong directional movement
- RANGE: Sideways consolidation  
- VOLATILE: High volatility, unclear direction
- NOTRADE: Unsuitable conditions (news, wide spreads)

Based on Product_Concept.txt specifications.
"""

from typing import Literal
from dataclasses import dataclass
from transmission.telemetry.market_data import MarketFeatures


@dataclass
class RegimeResult:
    """Result of regime classification"""
    regime: Literal['TREND', 'RANGE', 'VOLATILE', 'NOTRADE']
    confidence: float  # 0.0 to 1.0
    reason: str  # Explanation of classification


class RegimeClassifier:
    """
    Classifies market regime based on technical indicators.
    
    Classification Rules (from Product_Concept.txt):
    - TREND: ADX > 25 AND (VWAP_slope > median OR OR_hold > 30min)
    - RANGE: ADX < 20 AND VWAP_slope <= median
    - VOLATILE: Neither TREND nor RANGE conditions met
    - NOTRADE: News within 30min OR spread > 2 ticks
    """
    
    def __init__(
        self,
        adx_trend_threshold: float = 25.0,
        adx_range_threshold: float = 20.0,
        spread_limit_ticks: float = 2.0,
        news_blackout_minutes: int = 30,
        or_hold_minutes_trend: int = 30
    ):
        """
        Initialize Regime Classifier.
        
        Args:
            adx_trend_threshold: ADX value above which trend is detected (default 25)
            adx_range_threshold: ADX value below which range is detected (default 20)
            spread_limit_ticks: Maximum spread for trading (default 2 ticks)
            news_blackout_minutes: Minutes before/after news to avoid trading (default 30)
            or_hold_minutes_trend: OR hold duration for trend confirmation (default 30)
        """
        self.adx_trend_threshold = adx_trend_threshold
        self.adx_range_threshold = adx_range_threshold
        self.spread_limit_ticks = spread_limit_ticks
        self.news_blackout_minutes = news_blackout_minutes
        self.or_hold_minutes_trend = or_hold_minutes_trend
    
    def classify(self, features: MarketFeatures) -> RegimeResult:
        """
        Classify market regime from market features.
        
        Args:
            features: MarketFeatures dataclass with all calculated indicators
            
        Returns:
            RegimeResult with regime, confidence, and reason
        """
        # First check for NOTRADE conditions
        notrade_result = self._check_notrade(features)
        if notrade_result:
            return notrade_result
        
        # Check for TREND regime
        trend_result = self._check_trend(features)
        if trend_result:
            return trend_result
        
        # Check for RANGE regime
        range_result = self._check_range(features)
        if range_result:
            return range_result
        
        # Default to VOLATILE if no other regime matches
        return RegimeResult(
            regime='VOLATILE',
            confidence=0.6,
            reason=f"ADX={features.adx_14:.1f} between thresholds, unclear direction"
        )
    
    def _check_notrade(self, features: MarketFeatures) -> RegimeResult | None:
        """
        Check if market conditions are unsuitable for trading.
        
        Returns:
            RegimeResult if NOTRADE, None otherwise
        """
        reasons = []
        
        # Check news proximity
        if features.news_proximity_min is not None:
            if features.news_proximity_min <= self.news_blackout_minutes:
                reasons.append(f"News event in {features.news_proximity_min} minutes")
        
        # Check spread
        if features.spread_ticks > self.spread_limit_ticks:
            reasons.append(f"Spread {features.spread_ticks:.1f} ticks > limit {self.spread_limit_ticks}")
        
        if reasons:
            return RegimeResult(
                regime='NOTRADE',
                confidence=1.0,
                reason="; ".join(reasons)
            )
        
        return None
    
    def _check_trend(self, features: MarketFeatures) -> RegimeResult | None:
        """
        Check if market is in TREND regime.
        
        Conditions:
        - ADX > 25 (strong trend)
        - AND (VWAP_slope > median OR OR_hold > 30min)
        
        Returns:
            RegimeResult if TREND, None otherwise
        """
        # ADX must be above trend threshold
        if features.adx_14 <= self.adx_trend_threshold:
            return None
        
        # Check secondary conditions
        vwap_slope_above_median = features.vwap_slope_abs > features.vwap_slope_median_20d
        or_hold_sufficient = features.or_hold_minutes >= self.or_hold_minutes_trend
        
        if vwap_slope_above_median or or_hold_sufficient:
            confidence = 0.8
            if vwap_slope_above_median and or_hold_sufficient:
                confidence = 0.95  # Both conditions met = very confident
            
            reason_parts = [f"ADX={features.adx_14:.1f} > {self.adx_trend_threshold}"]
            if vwap_slope_above_median:
                reason_parts.append("VWAP slope above median")
            if or_hold_sufficient:
                reason_parts.append(f"OR held {features.or_hold_minutes}min")
            
            return RegimeResult(
                regime='TREND',
                confidence=confidence,
                reason="; ".join(reason_parts)
            )
        
        return None
    
    def _check_range(self, features: MarketFeatures) -> RegimeResult | None:
        """
        Check if market is in RANGE regime.
        
        Conditions:
        - ADX < 20 (weak trend)
        - AND VWAP_slope <= median
        
        Returns:
            RegimeResult if RANGE, None otherwise
        """
        # ADX must be below range threshold
        if features.adx_14 >= self.adx_range_threshold:
            return None
        
        # VWAP slope must be at or below median
        if features.vwap_slope_abs > features.vwap_slope_median_20d:
            return None
        
        confidence = 0.75
        if features.adx_14 < 15:  # Very low ADX = very confident in range
            confidence = 0.9
        
        return RegimeResult(
            regime='RANGE',
            confidence=confidence,
            reason=f"ADX={features.adx_14:.1f} < {self.adx_range_threshold}, VWAP slope <= median"
        )
    
    def get_regime_multiplier(self, regime: str) -> float:
        """
        Get position sizing multiplier for regime.
        
        From Product_Concept.txt Section 0A:
        - TREND: 0.85 (tighter stops, more aggressive)
        - RANGE: 1.15 (wider stops, more conservative)
        - VOLATILE: 1.00 (neutral)
        - NOTRADE: 0.00 (no trading)
        
        Args:
            regime: Regime string ('TREND', 'RANGE', 'VOLATILE', 'NOTRADE')
            
        Returns:
            Multiplier for position sizing
        """
        multipliers = {
            'TREND': 0.85,
            'RANGE': 1.15,
            'VOLATILE': 1.00,
            'NOTRADE': 0.00
        }
        
        return multipliers.get(regime.upper(), 1.0)
    
    def is_tradeable(self, regime: str) -> bool:
        """
        Check if regime allows trading.
        
        Args:
            regime: Regime string
            
        Returns:
            True if trading is allowed, False otherwise
        """
        return regime.upper() != 'NOTRADE'

