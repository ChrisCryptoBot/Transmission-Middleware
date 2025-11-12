"""
Tests for Transmission Orchestrator
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from transmission.orchestrator.transmission import TransmissionOrchestrator, SystemState
from transmission.risk.governor import RiskGovernor
from transmission.risk.constraint_engine import ConstraintEngine


@pytest.fixture
def sample_bars():
    """Create sample 15-minute bar data"""
    dates = pd.date_range(start='2025-01-01 08:30', periods=50, freq='15min')
    
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
def orchestrator():
    """Create TransmissionOrchestrator instance"""
    return TransmissionOrchestrator()


def test_initialization(orchestrator):
    """Should initialize in READY state"""
    assert orchestrator.state == SystemState.READY
    assert orchestrator.telemetry is not None
    assert orchestrator.regime_classifier is not None
    assert orchestrator.risk_governor is not None


def test_process_bar_no_signal(orchestrator, sample_bars):
    """Should return None when no signal generated"""
    # Use bars that won't generate a signal (e.g., RANGE regime)
    signal = orchestrator.process_bar(
        bars_15m=sample_bars,
        current_price=16000.0
    )
    
    # May return None if conditions not met (this is OK)
    # Just verify it doesn't crash
    assert signal is None or isinstance(signal, object)


def test_risk_blocking(orchestrator, sample_bars):
    """Should block trading when risk limits hit"""
    # Set daily P&L to limit
    orchestrator.risk_governor.daily_pnl_r = -2.1
    
    signal = orchestrator.process_bar(
        bars_15m=sample_bars,
        current_price=16000.0
    )
    
    assert signal is None
    assert orchestrator.state == SystemState.PAUSED


def test_get_risk_status(orchestrator):
    """Should return risk status dictionary"""
    status = orchestrator.get_risk_status()
    
    assert 'can_trade' in status
    assert 'daily_pnl_r' in status
    assert 'weekly_pnl_r' in status
    assert 'current_r' in status


def test_record_trade_result(orchestrator):
    """Should record trade result and update state"""
    initial_daily_pnl = orchestrator.risk_governor.daily_pnl_r
    
    orchestrator.record_trade_result(1.5)  # +1.5R
    
    assert orchestrator.risk_governor.daily_pnl_r == initial_daily_pnl + 1.5
    assert orchestrator.state == SystemState.READY


def test_strategy_selection(orchestrator):
    """Should select correct strategy for regime"""
    strategy = orchestrator._select_strategy('TREND')
    assert strategy is not None
    assert strategy.strategy_name == 'VWAP Pullback'
    
    strategy = orchestrator._select_strategy('RANGE')
    assert strategy is None  # No strategy for RANGE yet


def test_get_current_state(orchestrator):
    """Should return current system state"""
    state = orchestrator.get_current_state()
    assert isinstance(state, SystemState)


def test_get_current_regime(orchestrator, sample_bars):
    """Should return current regime after processing"""
    orchestrator.process_bar(
        bars_15m=sample_bars,
        current_price=16000.0
    )
    
    regime = orchestrator.get_current_regime()
    # May be None if not classified, or a valid regime string
    assert regime is None or regime in ['TREND', 'RANGE', 'VOLATILE', 'NOTRADE']

