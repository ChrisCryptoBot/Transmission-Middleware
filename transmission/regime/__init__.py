"""
Regime Module - Market Regime Classification

Classifies market conditions:
- TREND: Strong directional movement
- RANGE: Sideways consolidation
- VOLATILE: High volatility, unclear direction
- NOTRADE: Unsuitable conditions (news, wide spreads)
"""

from transmission.regime.classifier import RegimeClassifier, RegimeResult

__all__ = ['RegimeClassifier', 'RegimeResult']
