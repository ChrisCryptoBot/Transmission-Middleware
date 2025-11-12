"""
Multi-Timeframe Fusion

Synthesizes data from multiple timeframes to improve regime detection and entry quality.
Uses HTF (Higher Timeframe) confirmation to gate LTF (Lower Timeframe) entries.
"""

from typing import Optional, Dict, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np

from transmission.telemetry.market_data import MarketFeatures, Telemetry


@dataclass
class HTFFeatures:
    """Higher timeframe market features"""
    timeframe: str  # e.g., "15m", "1h"
    adx: float
    atr: float
    vwap: float
    regime: Optional[str] = None
    trend_direction: Optional[Literal["UP", "DOWN", "NEUTRAL"]] = None


@dataclass
class FusionResult:
    """Result of multi-timeframe fusion"""
    ltf_features: MarketFeatures  # Lower timeframe (1m/5m)
    htf_features: Dict[str, HTFFeatures]  # Higher timeframes
    consensus_regime: Optional[str]  # Consensus across timeframes
    entry_gated: bool  # True if HTF disagrees with LTF
    gate_reason: Optional[str] = None


class MultiTimeframeFusion:
    """
    Fuses data from multiple timeframes.
    
    Computes HTF indicators from LTF stream using rolling resampling.
    Gates entries when LTF and HTF disagree.
    """
    
    def __init__(
        self,
        ltf_interval: str = "1m",
        htf_intervals: list[str] = None,
        gate_on_disagreement: bool = True
    ):
        """
        Initialize Multi-Timeframe Fusion.
        
        Args:
            ltf_interval: Lower timeframe interval (e.g., "1m", "5m")
            htf_intervals: Higher timeframe intervals (e.g., ["15m", "1h"])
            gate_on_disagreement: Gate entries when HTF disagrees with LTF
        """
        self.ltf_interval = ltf_interval
        self.htf_intervals = htf_intervals or ["15m", "1h"]
        self.gate_on_disagreement = gate_on_disagreement
        
        # Cache for HTF data
        self.htf_cache: Dict[str, pd.DataFrame] = {}
        self.telemetry = Telemetry(tick_size=0.25)
        
        # Regime thresholds
        self.adx_trend_threshold = 25.0
        self.adx_range_threshold = 20.0
    
    def add_bar(self, bar: pd.Series, timestamp: datetime) -> None:
        """
        Add a new bar to the fusion engine.
        
        Args:
            bar: OHLCV bar data
            timestamp: Bar timestamp
        """
        # Add to cache for each timeframe
        for htf_interval in self.htf_intervals:
            if htf_interval not in self.htf_cache:
                self.htf_cache[htf_interval] = pd.DataFrame()
            
            # Append bar
            bar_df = pd.DataFrame([{
                'timestamp': timestamp,
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar.get('volume', 0)
            }])
            
            self.htf_cache[htf_interval] = pd.concat([
                self.htf_cache[htf_interval],
                bar_df
            ], ignore_index=True)
            
            # Keep only recent data (last 100 bars per timeframe)
            if len(self.htf_cache[htf_interval]) > 100:
                self.htf_cache[htf_interval] = self.htf_cache[htf_interval].tail(100)
    
    def compute_htf_features(self, htf_interval: str) -> Optional[HTFFeatures]:
        """
        Compute features for a higher timeframe.
        
        Args:
            htf_interval: Timeframe (e.g., "15m", "1h")
        
        Returns:
            HTFFeatures or None if insufficient data
        """
        if htf_interval not in self.htf_cache:
            return None
        
        df = self.htf_cache[htf_interval]
        
        if len(df) < 20:  # Need minimum bars for indicators
            return None
        
        # Resample to HTF if needed (if we're getting 1m bars, resample to 15m)
        # For now, assume bars are already at the correct interval
        # In production, would resample: df.resample(htf_interval).agg(...)
        
        try:
            # Calculate indicators
            features = self.telemetry.calculate_all_features(df)
            
            if not features:
                return None
            
            # Determine regime
            regime = self._classify_regime(features.adx, features.atr)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(df, features.vwap)
            
            return HTFFeatures(
                timeframe=htf_interval,
                adx=features.adx,
                atr=features.atr,
                vwap=features.vwap,
                regime=regime,
                trend_direction=trend_direction
            )
        except Exception as e:
            logger.warning(f"Failed to compute HTF features for {htf_interval}: {e}")
            return None
    
    def fuse(
        self,
        ltf_features: MarketFeatures,
        ltf_regime: str,
        entry_direction: Optional[Literal["LONG", "SHORT"]] = None
    ) -> FusionResult:
        """
        Fuse LTF and HTF data to determine consensus and gate entries.
        
        Args:
            ltf_features: Lower timeframe features
            ltf_regime: Lower timeframe regime classification
            entry_direction: Proposed entry direction (for trend confirmation)
        
        Returns:
            FusionResult with consensus and gating decision
        """
        htf_features_dict = {}
        
        # Compute HTF features for each timeframe
        for htf_interval in self.htf_intervals:
            htf_feat = self.compute_htf_features(htf_interval)
            if htf_feat:
                htf_features_dict[htf_interval] = htf_feat
        
        # Determine consensus regime
        consensus_regime = self._determine_consensus(ltf_regime, htf_features_dict)
        
        # Gate entry if HTF disagrees
        entry_gated = False
        gate_reason = None
        
        if self.gate_on_disagreement:
            # Check if any HTF disagrees with LTF
            for htf_interval, htf_feat in htf_features_dict.items():
                if htf_feat.regime and htf_feat.regime != ltf_regime:
                    # Check if disagreement is significant
                    if self._is_significant_disagreement(ltf_regime, htf_feat.regime):
                        entry_gated = True
                        gate_reason = f"HTF ({htf_interval}) regime {htf_feat.regime} disagrees with LTF {ltf_regime}"
                        break
                
                # Check trend direction for directional entries
                if entry_direction and htf_feat.trend_direction:
                    if entry_direction == "LONG" and htf_feat.trend_direction == "DOWN":
                        entry_gated = True
                        gate_reason = f"HTF ({htf_interval}) trend DOWN conflicts with LONG entry"
                        break
                    elif entry_direction == "SHORT" and htf_feat.trend_direction == "UP":
                        entry_gated = True
                        gate_reason = f"HTF ({htf_interval}) trend UP conflicts with SHORT entry"
                        break
        
        return FusionResult(
            ltf_features=ltf_features,
            htf_features=htf_features_dict,
            consensus_regime=consensus_regime,
            entry_gated=entry_gated,
            gate_reason=gate_reason
        )
    
    def _classify_regime(self, adx: float, atr: float) -> Optional[str]:
        """Classify regime from ADX/ATR"""
        if adx > self.adx_trend_threshold:
            return "TREND"
        elif adx < self.adx_range_threshold:
            return "RANGE"
        else:
            return "VOLATILE"
    
    def _determine_trend_direction(
        self,
        df: pd.DataFrame,
        vwap: float
    ) -> Optional[Literal["UP", "DOWN", "NEUTRAL"]]:
        """Determine trend direction from price vs VWAP"""
        if len(df) < 2:
            return None
        
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        # Compare to VWAP
        if current_price > vwap and current_price > prev_price:
            return "UP"
        elif current_price < vwap and current_price < prev_price:
            return "DOWN"
        else:
            return "NEUTRAL"
    
    def _determine_consensus(
        self,
        ltf_regime: str,
        htf_features: Dict[str, HTFFeatures]
    ) -> str:
        """Determine consensus regime across timeframes"""
        regimes = [ltf_regime]
        
        for htf_feat in htf_features.values():
            if htf_feat.regime:
                regimes.append(htf_feat.regime)
        
        # Return most common regime
        from collections import Counter
        regime_counts = Counter(regimes)
        return regime_counts.most_common(1)[0][0]
    
    def _is_significant_disagreement(self, ltf_regime: str, htf_regime: str) -> bool:
        """Check if regime disagreement is significant enough to gate"""
        # Don't gate if both are volatile/uncertain
        if ltf_regime == "VOLATILE" or htf_regime == "VOLATILE":
            return False
        
        # Gate if one is TREND and other is RANGE (opposite)
        if (ltf_regime == "TREND" and htf_regime == "RANGE") or \
           (ltf_regime == "RANGE" and htf_regime == "TREND"):
            return True
        
        return False
    
    def clear_cache(self) -> None:
        """Clear HTF cache"""
        self.htf_cache.clear()

