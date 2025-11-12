"""
Tests for Position Sizer Module
"""

import pytest
from transmission.risk.position_sizer import PositionSizer


class TestPositionSizer:
    """Test Position Sizer calculations"""
    
    def test_basic_calculation(self):
        """Test basic position sizing"""
        sizer = PositionSizer()
        
        # $10 risk, 5 point stop, $2/point = $10 per contract risk
        # Should get 1 contract
        contracts = sizer.calculate_contracts(
            risk_dollars=10.0,
            stop_points=5.0,
            atr_current=10.0,
            atr_baseline=10.0
        )
        
        assert contracts == 1
    
    def test_atr_normalization_low_volatility(self):
        """Test ATR normalization when current ATR < baseline"""
        sizer = PositionSizer()
        
        # Low volatility (ATR = 5) vs baseline (ATR = 10)
        # Adjustment = 10/5 = 2.0, clipped to 1.5
        # Risk = $10 * 1.5 = $15
        # Contracts = $15 / ($5 * $2) = 1.5 → 1
        contracts = sizer.calculate_contracts(
            risk_dollars=10.0,
            stop_points=5.0,
            atr_current=5.0,  # Low volatility
            atr_baseline=10.0  # Baseline
        )
        
        assert contracts == 1
    
    def test_atr_normalization_high_volatility(self):
        """Test ATR normalization when current ATR > baseline"""
        sizer = PositionSizer()
        
        # High volatility (ATR = 20) vs baseline (ATR = 10)
        # Adjustment = 10/20 = 0.5, clipped to 0.67
        # Risk = $10 * 0.67 = $6.70
        # Contracts = $6.70 / ($5 * $2) = 0.67 → 0 (too small)
        contracts = sizer.calculate_contracts(
            risk_dollars=10.0,
            stop_points=5.0,
            atr_current=20.0,  # High volatility
            atr_baseline=10.0  # Baseline
        )
        
        assert contracts == 0  # Too small after adjustment
    
    def test_dll_constraint(self):
        """Test DLL constraint limits position size"""
        sizer = PositionSizer()
        
        # $10 risk, but DLL = $100, so max risk = $100 * 0.10 = $10
        contracts = sizer.calculate_contracts(
            risk_dollars=20.0,  # Would normally allow 2 contracts
            stop_points=5.0,
            atr_current=10.0,
            atr_baseline=10.0,
            dll_constraint=100.0  # DLL = $100
        )
        
        # Should be limited to $10 risk (1 contract)
        assert contracts == 1
    
    def test_mental_state_adjustment(self):
        """Test mental state reduces position size"""
        sizer = PositionSizer()
        
        # Mental state 2 (poor) should cut size in half
        contracts_low = sizer.calculate_contracts(
            risk_dollars=20.0,
            stop_points=5.0,
            atr_current=10.0,
            atr_baseline=10.0,
            mental_state=2  # Poor mental state
        )
        
        # Mental state 5 (good) should use full size
        contracts_high = sizer.calculate_contracts(
            risk_dollars=20.0,
            stop_points=5.0,
            atr_current=10.0,
            atr_baseline=10.0,
            mental_state=5  # Good mental state
        )
        
        assert contracts_low < contracts_high
        assert contracts_low == 1  # $20 * 0.5 = $10 → 1 contract
        assert contracts_high == 2  # $20 → 2 contracts
    
    def test_validate_position_size(self):
        """Test position size validation"""
        sizer = PositionSizer()
        
        # Valid position
        is_valid, reason = sizer.validate_position_size(
            contracts=2,
            stop_points=5.0,
            account_balance=1000.0
        )
        assert is_valid
        assert reason == "Position size valid"
        
        # Invalid: too small
        is_valid, reason = sizer.validate_position_size(
            contracts=0,
            stop_points=5.0,
            account_balance=1000.0
        )
        assert not is_valid
        assert "too small" in reason.lower()
        
        # Invalid: risk too high
        is_valid, reason = sizer.validate_position_size(
            contracts=100,  # Way too many
            stop_points=5.0,
            account_balance=1000.0  # $1000 * 2% = $20 max risk
        )
        assert not is_valid
        assert "too high" in reason.lower()
    
    def test_calculate_stop_distance(self):
        """Test stop distance calculation"""
        sizer = PositionSizer()
        
        # Long: entry 100, stop 95 = 5 points
        distance = sizer.calculate_stop_distance_points(
            entry_price=100.0,
            stop_price=95.0,
            direction="LONG"
        )
        assert distance == 5.0
        
        # Short: entry 100, stop 105 = 5 points
        distance = sizer.calculate_stop_distance_points(
            entry_price=100.0,
            stop_price=105.0,
            direction="SHORT"
        )
        assert distance == 5.0
    
    def test_calculate_risk_dollars(self):
        """Test risk dollars calculation"""
        sizer = PositionSizer()
        
        # 2 contracts, 5 point stop, $2/point = $20 risk
        risk = sizer.calculate_risk_dollars(
            contracts=2,
            stop_points=5.0
        )
        assert risk == 20.0

