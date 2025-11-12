"""
Strategies Module - Trading Strategy Engines

Strategy implementations:
- VWAP Pullback (trend-following)
- ORB Retest (range breakout)
- Mean Reversion (range-bound)
- Base interface for custom strategies
"""

from transmission.strategies.base import BaseStrategy, Signal, Position

__all__ = ['BaseStrategy', 'Signal', 'Position']
