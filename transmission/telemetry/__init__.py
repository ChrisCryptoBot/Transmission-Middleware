"""
Telemetry Module - Market Data Processing

Calculates market features from OHLCV data:
- ADX (trend strength)
- VWAP (volume-weighted average price)
- ATR (volatility)
- Opening Range
- Microstructure features
"""

from transmission.telemetry.market_data import Telemetry, MarketFeatures

__all__ = ['Telemetry', 'MarketFeatures']

