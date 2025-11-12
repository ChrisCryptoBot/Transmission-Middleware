"""
Tests for Risk Governor module
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from transmission.risk.governor import RiskGovernor, PerformanceMetrics


@pytest.fixture
def temp_db():
    """Create temporary database file"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def risk_governor(temp_db):
    """Create RiskGovernor instance with temp database"""
    return RiskGovernor(initial_r=5.0, db_path=temp_db)


def test_initial_state(risk_governor):
    """Should initialize with correct default values"""
    assert risk_governor.current_r == 5.0
    assert risk_governor.daily_limit_r == -2.0
    assert risk_governor.weekly_limit_r == -5.0
    assert risk_governor.max_red_days == 3


def test_check_tripwires_all_clear(risk_governor):
    """Should allow trading when no limits hit"""
    result = risk_governor.check_tripwires()
    
    assert result.can_trade is True
    assert result.action == 'TRADE'
    assert result.reason == "All clear"


def test_daily_limit_enforcement(risk_governor):
    """Should block trading when daily limit hit"""
    risk_governor.daily_pnl_r = -2.1  # Below -2R limit
    
    result = risk_governor.check_tripwires()
    
    assert result.can_trade is False
    assert result.action == 'FLAT'
    assert 'Daily loss limit' in result.reason


def test_weekly_limit_enforcement(risk_governor):
    """Should block trading when weekly limit hit"""
    risk_governor.weekly_pnl_r = -5.1  # Below -5R limit
    
    result = risk_governor.check_tripwires()
    
    assert result.can_trade is False
    assert result.action == 'FLAT'
    assert 'Weekly loss limit' in result.reason


def test_record_trade(risk_governor):
    """Should update daily and weekly P&L when trade recorded"""
    risk_governor.record_trade(1.5)  # +1.5R
    
    assert risk_governor.daily_pnl_r == 1.5
    assert risk_governor.weekly_pnl_r == 1.5
    
    risk_governor.record_trade(-0.5)  # -0.5R
    
    assert risk_governor.daily_pnl_r == 1.0
    assert risk_governor.weekly_pnl_r == 1.0


def test_step_down_poor_performance(risk_governor):
    """Should reduce $R by 30% when PF < 1.10"""
    metrics = PerformanceMetrics(
        profit_factor=1.05,  # Below 1.10
        expected_r=0.10,
        win_rate=0.45,
        max_drawdown_r=2.0,
        current_drawdown_r=-1.0,
        rule_breaks=0,
        total_trades=12
    )
    
    new_r = risk_governor.evaluate_scaling(metrics)
    
    assert new_r == pytest.approx(5.0 * 0.70, rel=0.01)  # 30% reduction
    assert risk_governor.current_r == new_r


def test_step_down_drawdown(risk_governor):
    """Should reduce $R by 30% when drawdown <= -4R"""
    metrics = PerformanceMetrics(
        profit_factor=1.20,
        expected_r=0.15,
        win_rate=0.50,
        max_drawdown_r=4.5,
        current_drawdown_r=-4.1,  # Below -4R
        rule_breaks=0,
        total_trades=12
    )
    
    new_r = risk_governor.evaluate_scaling(metrics)
    
    assert new_r == pytest.approx(5.0 * 0.70, rel=0.01)  # 30% reduction


def test_scale_up_good_performance(risk_governor):
    """Should increase $R by 15% when all conditions met"""
    metrics = PerformanceMetrics(
        profit_factor=1.35,  # >= 1.30
        expected_r=0.22,  # >= 0.20
        win_rate=0.52,  # >= 0.50
        max_drawdown_r=2.5,  # <= 3.0
        current_drawdown_r=-0.5,
        rule_breaks=0,  # No breaks
        total_trades=20
    )
    
    new_r = risk_governor.evaluate_scaling(metrics)
    
    assert new_r == pytest.approx(5.0 * 1.15, rel=0.01)  # 15% increase
    assert risk_governor.current_r == new_r


def test_scale_up_blocked_by_rule_breaks(risk_governor):
    """Should not scale up if rule breaks > 0"""
    metrics = PerformanceMetrics(
        profit_factor=1.35,
        expected_r=0.22,
        win_rate=0.52,
        max_drawdown_r=2.5,
        current_drawdown_r=-0.5,
        rule_breaks=1,  # Has rule breaks
        total_trades=20
    )
    
    original_r = risk_governor.current_r
    new_r = risk_governor.evaluate_scaling(metrics)
    
    assert new_r == original_r  # No change


def test_scale_up_blocked_by_drawdown(risk_governor):
    """Should not scale up if max drawdown > 3R"""
    metrics = PerformanceMetrics(
        profit_factor=1.35,
        expected_r=0.22,
        win_rate=0.52,
        max_drawdown_r=3.5,  # Above 3R
        current_drawdown_r=-0.5,
        rule_breaks=0,
        total_trades=20
    )
    
    original_r = risk_governor.current_r
    new_r = risk_governor.evaluate_scaling(metrics)
    
    assert new_r == original_r  # No change


def test_persistence(risk_governor, temp_db):
    """Should persist state to database"""
    risk_governor.record_trade(1.0)
    risk_governor.current_r = 6.0
    
    # Create new instance with same DB
    new_governor = RiskGovernor(initial_r=5.0, db_path=temp_db)
    
    # Should load saved state
    assert new_governor.current_r == 6.0
    assert new_governor.daily_pnl_r == 1.0


def test_get_current_r(risk_governor):
    """Should return current $R value"""
    assert risk_governor.get_current_r() == 5.0
    
    risk_governor.current_r = 7.5
    assert risk_governor.get_current_r() == 7.5

