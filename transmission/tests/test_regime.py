"""
Tests for Regime Classifier module
"""

import pytest
from datetime import datetime
from transmission.regime.classifier import RegimeClassifier, RegimeResult
from transmission.telemetry.market_data import MarketFeatures


@pytest.fixture
def classifier():
    """Create RegimeClassifier instance"""
    return RegimeClassifier()


@pytest.fixture
def trend_features():
    """Create features for trending market"""
    return MarketFeatures(
        timestamp=datetime.now(),
        adx_14=30.0,  # Above 25 threshold
        vwap=16000.0,
        vwap_slope_abs=2.5,
        vwap_slope_median_20d=1.5,  # Slope above median
        atr_14=50.0,
        baseline_atr=45.0,
        or_high=16050.0,
        or_low=15950.0,
        or_hold_minutes=35,  # Above 30min threshold
        spread_ticks=1.0,  # Within limit
        ob_imbalance=0.2,
        rel_volume_hour=1.2,
        news_proximity_min=None,
        entry_p90_slippage=0.5,
        exit_p90_slippage=0.5
    )


@pytest.fixture
def range_features():
    """Create features for ranging market"""
    return MarketFeatures(
        timestamp=datetime.now(),
        adx_14=15.0,  # Below 20 threshold
        vwap=16000.0,
        vwap_slope_abs=0.5,
        vwap_slope_median_20d=1.0,  # Slope below median
        atr_14=30.0,
        baseline_atr=35.0,
        or_high=16020.0,
        or_low=15980.0,
        or_hold_minutes=10,
        spread_ticks=1.0,
        ob_imbalance=0.0,
        rel_volume_hour=0.8,
        news_proximity_min=None,
        entry_p90_slippage=0.3,
        exit_p90_slippage=0.3
    )


@pytest.fixture
def volatile_features():
    """Create features for volatile market"""
    return MarketFeatures(
        timestamp=datetime.now(),
        adx_14=22.0,  # Between thresholds
        vwap=16000.0,
        vwap_slope_abs=1.0,
        vwap_slope_median_20d=1.0,
        atr_14=80.0,  # High volatility
        baseline_atr=45.0,
        or_high=16050.0,
        or_low=15950.0,
        or_hold_minutes=15,
        spread_ticks=1.5,
        ob_imbalance=0.1,
        rel_volume_hour=1.5,
        news_proximity_min=None,
        entry_p90_slippage=1.0,
        exit_p90_slippage=1.0
    )


@pytest.fixture
def notrade_features_news():
    """Create features with news proximity"""
    return MarketFeatures(
        timestamp=datetime.now(),
        adx_14=30.0,
        vwap=16000.0,
        vwap_slope_abs=2.0,
        vwap_slope_median_20d=1.5,
        atr_14=50.0,
        baseline_atr=45.0,
        or_high=16050.0,
        or_low=15950.0,
        or_hold_minutes=35,
        spread_ticks=1.0,
        ob_imbalance=0.2,
        rel_volume_hour=1.2,
        news_proximity_min=15,  # News in 15 minutes
        entry_p90_slippage=0.5,
        exit_p90_slippage=0.5
    )


@pytest.fixture
def notrade_features_spread():
    """Create features with wide spread"""
    return MarketFeatures(
        timestamp=datetime.now(),
        adx_14=30.0,
        vwap=16000.0,
        vwap_slope_abs=2.0,
        vwap_slope_median_20d=1.5,
        atr_14=50.0,
        baseline_atr=45.0,
        or_high=16050.0,
        or_low=15950.0,
        or_hold_minutes=35,
        spread_ticks=3.0,  # Above 2 tick limit
        ob_imbalance=0.2,
        rel_volume_hour=1.2,
        news_proximity_min=None,
        entry_p90_slippage=0.5,
        exit_p90_slippage=0.5
    )


def test_classify_trend(classifier, trend_features):
    """Should classify as TREND when ADX > 25 and conditions met"""
    result = classifier.classify(trend_features)
    
    assert result.regime == 'TREND'
    assert result.confidence >= 0.8
    assert 'ADX' in result.reason
    assert classifier.is_tradeable(result.regime) is True


def test_classify_range(classifier, range_features):
    """Should classify as RANGE when ADX < 20 and VWAP slope <= median"""
    result = classifier.classify(range_features)
    
    assert result.regime == 'RANGE'
    assert result.confidence >= 0.75
    assert 'ADX' in result.reason
    assert classifier.is_tradeable(result.regime) is True


def test_classify_volatile(classifier, volatile_features):
    """Should classify as VOLATILE when neither trend nor range"""
    result = classifier.classify(volatile_features)
    
    assert result.regime == 'VOLATILE'
    assert result.confidence >= 0.6
    assert classifier.is_tradeable(result.regime) is True


def test_classify_notrade_news(classifier, notrade_features_news):
    """Should classify as NOTRADE when news is near"""
    result = classifier.classify(notrade_features_news)
    
    assert result.regime == 'NOTRADE'
    assert 'News' in result.reason
    assert classifier.is_tradeable(result.regime) is False


def test_classify_notrade_spread(classifier, notrade_features_spread):
    """Should classify as NOTRADE when spread is too wide"""
    result = classifier.classify(notrade_features_spread)
    
    assert result.regime == 'NOTRADE'
    assert 'Spread' in result.reason
    assert classifier.is_tradeable(result.regime) is False


def test_get_regime_multiplier(classifier):
    """Should return correct multipliers for each regime"""
    assert classifier.get_regime_multiplier('TREND') == 0.85
    assert classifier.get_regime_multiplier('RANGE') == 1.15
    assert classifier.get_regime_multiplier('VOLATILE') == 1.00
    assert classifier.get_regime_multiplier('NOTRADE') == 0.00


def test_trend_high_confidence(classifier):
    """Should have high confidence when both trend conditions met"""
    features = MarketFeatures(
        timestamp=datetime.now(),
        adx_14=30.0,
        vwap=16000.0,
        vwap_slope_abs=2.5,
        vwap_slope_median_20d=1.5,  # Above median
        atr_14=50.0,
        baseline_atr=45.0,
        or_high=16050.0,
        or_low=15950.0,
        or_hold_minutes=35,  # Above 30min
        spread_ticks=1.0,
        ob_imbalance=0.2,
        rel_volume_hour=1.2,
        news_proximity_min=None,
        entry_p90_slippage=0.5,
        exit_p90_slippage=0.5
    )
    
    result = classifier.classify(features)
    assert result.regime == 'TREND'
    assert result.confidence >= 0.9  # High confidence


def test_range_low_adx_high_confidence(classifier):
    """Should have high confidence in range when ADX is very low"""
    features = MarketFeatures(
        timestamp=datetime.now(),
        adx_14=10.0,  # Very low
        vwap=16000.0,
        vwap_slope_abs=0.3,
        vwap_slope_median_20d=1.0,
        atr_14=30.0,
        baseline_atr=35.0,
        or_high=16020.0,
        or_low=15980.0,
        or_hold_minutes=10,
        spread_ticks=1.0,
        ob_imbalance=0.0,
        rel_volume_hour=0.8,
        news_proximity_min=None,
        entry_p90_slippage=0.3,
        exit_p90_slippage=0.3
    )
    
    result = classifier.classify(features)
    assert result.regime == 'RANGE'
    assert result.confidence >= 0.9  # High confidence for very low ADX

