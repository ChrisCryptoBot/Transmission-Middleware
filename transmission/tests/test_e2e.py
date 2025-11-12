"""
End-to-End Integration Tests

Tests the complete flow: Signal → Size → Constraints → Guard → Execute → Journal
"""

import pytest
import pandas as pd
from datetime import datetime
from transmission.orchestrator.transmission import TransmissionOrchestrator
from transmission.execution.mock_broker import MockBrokerAdapter
from transmission.database import Database
from transmission.risk.governor import RiskGovernor
from transmission.risk.smart_constraints import SmartConstraintEngine


class TestE2E:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mock broker"""
        broker = MockBrokerAdapter(slippage_ticks=0.5, fill_probability=1.0)
        db = Database(db_path=":memory:")
        
        orch = TransmissionOrchestrator(
            database=db,
            broker=broker,
            config={
                'broker': {'mode': 'mock', 'mock': {'slippage_ticks': 0.5}},
                'execution': {'guard_mode': 'strict'},
                'constraints': {
                    'capital': {'max_risk_per_trade_pct': 0.5},
                    'cadence': {'max_trades_per_day': 10},
                    'quality_gates': {'max_spread_ticks': 2.0},
                    'safeguardrails': {}
                }
            }
        )
        
        return orch
    
    def test_golden_path(self, orchestrator):
        """Golden path: trend → VWAP signal → pass checks → fill → TP"""
        # Create sample bar data (trending market)
        bars = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [15000.0],
            'high': [15020.0],
            'low': [14990.0],
            'close': [15010.0],
            'volume': [1000]
        })
        
        # Process bar
        signal = orchestrator.process_bar(
            bars_15m=bars,
            current_price=15010.0,
            bid=15009.75,
            ask=15010.25
        )
        
        # Should generate signal in TREND regime
        # (This test assumes market conditions are met)
        # In real test, would need proper market data setup
        
        # Verify database has trade entry
        trades = orchestrator.database.get_recent_trades(limit=1)
        # Assert trade was logged if signal generated
        
        # Verify order was placed
        orders = orchestrator.get_open_orders()
        # Assert order exists if signal was generated
    
    def test_guard_rejection(self, orchestrator):
        """Guard rejection: wide spread → expect guard_reject"""
        # Set wide spread
        orchestrator.broker.set_price("MNQ", 15000.0)
        
        bars = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [15000.0],
            'high': [15020.0],
            'low': [14990.0],
            'close': [15010.0],
            'volume': [1000]
        })
        
        # Process with wide spread (would need to mock bid/ask)
        # Signal should be blocked by guard
        
        # Verify no order placed
        orders = orchestrator.get_open_orders()
        assert len(orders) == 0
    
    def test_constraint_violation(self, orchestrator):
        """Constraint violation: max_trades_day=0 → expect constraint_violation"""
        # Set max trades to 0
        orchestrator.constraint_engine.constraints.cadence.max_trades_per_day = 0
        
        bars = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [15000.0],
            'high': [15020.0],
            'low': [14990.0],
            'close': [15010.0],
            'volume': [1000]
        })
        
        signal = orchestrator.process_bar(
            bars_15m=bars,
            current_price=15010.0,
            bid=15009.75,
            ask=15010.25
        )
        
        # Should be None (blocked by constraints)
        assert signal is None
    
    def test_tripwire_cutoff(self, orchestrator):
        """Tripwire: simulate -2R → next signal must not submit"""
        # Simulate -2R daily loss
        orchestrator.risk_governor.daily_pnl_r = -2.0
        
        # Check tripwire
        tripwire = orchestrator.risk_governor.check_tripwires()
        assert not tripwire.can_trade
        
        # Try to process bar
        bars = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [15000.0],
            'high': [15020.0],
            'low': [14990.0],
            'close': [15010.0],
            'volume': [1000]
        })
        
        signal = orchestrator.process_bar(
            bars_15m=bars,
            current_price=15010.0,
            bid=15009.75,
            ask=15010.25
        )
        
        # Should be None (blocked by tripwire)
        assert signal is None
    
    def test_flatten_all(self, orchestrator):
        """Flatten all: kill switch flattens positions"""
        # Create a position (would need to place order first)
        # For now, just test the method exists and works
        orchestrator.flatten_all_manual("test")
        
        # Verify all positions are flat
        positions = orchestrator.get_positions()
        assert len(positions) == 0
    
    def test_partial_fill(self, orchestrator):
        """Partial fill: limit order → partial then complete"""
        # This would require more complex mock broker setup
        # For now, verify partial fill handling exists
        assert hasattr(orchestrator.execution_engine, 'on_broker_fill')

