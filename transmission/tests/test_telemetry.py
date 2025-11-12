"""
Tests for Telemetry module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from transmission.src.core.telemetry import Telemetry, MarketFeatures


@pytest.fixture
def sample_bars():
    """Create sample 15-minute bar data"""
    dates = pd.date_range(start='2025-01-01 08:30', periods=50, freq='15min')
    
    # Create trending data (upward)
    base_price = 16000.0
    prices = base_price + np.cumsum(np.random.randn(50) * 2)
    
    bars = pd.DataFrame({
        'open': prices + np.random.randn(50) * 0.5,
        'high': prices + abs(np.random.randn(50) * 1.0),
        'low': prices - abs(np.random.randn(50) * 1.0),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 50)
    }, index=dates)
    
    return bars


@pytest.fixture
def telemetry():
    """Create Telemetry instance"""
    return Telemetry(tick_size=0.25)


def test_calculate_adx(telemetry, sample_bars):
    """Test ADX calculation"""
    adx = telemetry.calculate_adx(
        sample_bars['high'],
        sample_bars['low'],
        sample_bars['close']
    )
    
    assert isinstance(adx, float)
    assert 0 <= adx <= 100
    assert not np.isnan(adx)


def test_calculate_vwap(telemetry, sample_bars):
    """Test VWAP calculation"""
    vwap = telemetry.calculate_vwap(
        sample_bars['close'],
        sample_bars['volume']
    )
    
    assert isinstance(vwap, float)
    assert vwap > 0
    assert not np.isnan(vwap)


def test_calculate_atr(telemetry, sample_bars):
    """Test ATR calculation"""
    atr = telemetry.calculate_atr(
        sample_bars['high'],
        sample_bars['low'],
        sample_bars['close']
    )
    
    assert isinstance(atr, float)
    assert atr > 0
    assert not np.isnan(atr)


def test_calculate_spread_ticks(telemetry):
    """Test spread calculation"""
    spread = telemetry.calculate_spread_ticks(16000.0, 16000.25)
    
    assert spread == 1.0  # 1 tick spread


def test_calculate_ob_imbalance(telemetry):
    """Test order book imbalance"""
    # All bids
    imbalance = telemetry.calculate_ob_imbalance(1000, 0)
    assert imbalance == 1.0
    
    # All asks
    imbalance = telemetry.calculate_ob_imbalance(0, 1000)
    assert imbalance == -1.0
    
    # Balanced
    imbalance = telemetry.calculate_ob_imbalance(500, 500)
    assert imbalance == 0.0


def test_calculate_all_features(telemetry, sample_bars):
    """Test complete feature calculation"""
    current_price = sample_bars['close'].iloc[-1]
    
    features = telemetry.calculate_all_features(
        bars_15m=sample_bars,
        current_price=current_price,
        bid=current_price - 0.25,
        ask=current_price + 0.25,
        bid_size=1000,
        ask_size=1000
    )
    
    assert isinstance(features, MarketFeatures)
    assert features.adx_14 >= 0
    assert features.vwap > 0
    assert features.atr_14 > 0
    assert features.spread_ticks >= 0

