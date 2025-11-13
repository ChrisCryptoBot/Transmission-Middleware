"""
Transmission Orchestrator - Main Trading Loop

Coordinates all modules:
- Telemetry (market features)
- Regime Classifier
- Strategy Selection
- Risk Governor
- Constraint Engine
- Execution Guard

This is the "transmission" that shifts gears (strategies) based on market conditions.
"""

from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
import pandas as pd
from loguru import logger

from transmission.telemetry.market_data import Telemetry, MarketFeatures
from transmission.regime.classifier import RegimeClassifier, RegimeResult
from transmission.risk.governor import RiskGovernor, TripwireResult
from transmission.risk.smart_constraints import SmartConstraintEngine
from transmission.risk.position_sizer import PositionSizer
from transmission.strategies.base import BaseStrategy, Signal, Position
from transmission.strategies.vwap_pullback import VWAPPullbackStrategy
from transmission.strategies.orb_retest import ORBRetestStrategy
from transmission.strategies.mean_reversion import MeanReversionStrategy
from transmission.execution.guard import ExecutionGuard, ExecutionCheck
from transmission.execution.engine import ExecutionEngine
from transmission.execution.adapter import BrokerAdapter
from transmission.execution.mock_broker import MockBrokerAdapter
from transmission.execution.kraken_adapter import KrakenAdapter
from transmission.execution.in_trade_manager import InTradeManager, TrailingStopConfig, TrailingStopMode, ScaleOutRule
from transmission.telemetry.multi_tf_fusion import MultiTimeframeFusion
from transmission.risk.mental_governor import MentalGovernor, MentalState
from transmission.risk.news_flat import NewsFlat
from transmission.analytics.journal_analytics import JournalAnalytics
from transmission.orchestrator.gear_state import GearStateMachine, GearContext, GearState
from transmission.database import Database
from transmission.config.config_loader import ConfigLoader
from transmission.config.instrument_specs import InstrumentSpecService
from datetime import datetime


class SystemState(Enum):
    """System state enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    ANALYZING = "analyzing"
    SIGNAL_GENERATED = "signal_generated"
    TRADING = "trading"
    PAUSED = "paused"
    ERROR = "error"


class TransmissionOrchestrator:
    """
    Main orchestrator for the Transmission system.
    
    Coordinates all modules in the trading decision loop:
    1. Calculate market features (Telemetry)
    2. Classify regime (Regime Classifier)
    3. Check risk tripwires (Risk Governor)
    4. Select strategy (based on regime)
    5. Generate signal (Strategy)
    6. Validate constraints (Constraint Engine)
    7. Check execution quality (Execution Guard)
    8. Execute trade (Execution Engine - stub for now)
    """
    
    def __init__(
        self,
        risk_governor: Optional[RiskGovernor] = None,
        constraint_engine: Optional[SmartConstraintEngine] = None,
        db_path: Optional[str] = None,
        database: Optional[Database] = None,
        broker: Optional[BrokerAdapter] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize Transmission Orchestrator.
        
        Args:
            risk_governor: RiskGovernor instance (creates default if None)
            constraint_engine: SmartConstraintEngine instance (creates default if None)
            db_path: Path to SQLite database for state
            database: Database instance (creates default if None)
            broker: Broker adapter (creates mock if None)
            config: Configuration dict (loads from files if None)
        """
        # Load configuration
        if config is None:
            config = {}
            broker_config = ConfigLoader.load_broker_config()
            constraints_config = ConfigLoader.load_constraints_config()
            config['broker'] = broker_config.get('broker', {})
            config['execution'] = broker_config.get('execution', {})
            config['constraints'] = constraints_config.get('constraints', {})
        
        # Validate constraints at boot
        constraints_config = {'constraints': config.get('constraints', {})}
        is_valid, violations = ConfigLoader.validate_constraints(constraints_config)
        if not is_valid:
            error_msg = "Constraint validation failed:\n" + "\n".join(f"  - {v}" for v in violations)
            logger.error(error_msg)
            raise ValueError(f"Invalid constraints: {error_msg}")
        
        # Log effective values
        ConfigLoader.log_effective_values(constraints_config)

        # Instrument specifications (for multi-asset support)
        self.instrument_spec = InstrumentSpecService()

        # Core modules (default to MNQ specs for telemetry/trade manager)
        default_tick_size = self.instrument_spec.get_tick_size("MNQ")
        self.telemetry = Telemetry(tick_size=default_tick_size)
        self.regime_classifier = RegimeClassifier()

        # Risk management
        if risk_governor is None:
            risk_governor = RiskGovernor(db_path=db_path)
        self.risk_governor = risk_governor

        if constraint_engine is None:
            constraint_engine = SmartConstraintEngine()
        self.constraint_engine = constraint_engine

        # Execution
        guard_mode = config.get('execution', {}).get('guard_mode', 'strict')
        self.execution_guard = ExecutionGuard()

        # Position Sizing (with multi-asset support)
        self.position_sizer = PositionSizer(instrument_spec_service=self.instrument_spec)

        # New modules
        self.in_trade_manager = InTradeManager(tick_size=default_tick_size)
        self.multi_tf_fusion = MultiTimeframeFusion(
            ltf_interval="1m",
            htf_intervals=["15m", "1h"],
            gate_on_disagreement=config.get('execution', {}).get('htf_gating', True)
        )
        self.mental_governor = MentalGovernor()
        self.news_flat = NewsFlat()
        self.journal_analytics = JournalAnalytics(database=database if database else Database(db_path=db_path))

        # Gear State Machine (Transmission visualization)
        self.gear_state_machine = GearStateMachine(database=database if database else Database(db_path=db_path))

        # Database
        if database is None:
            database = Database(db_path=db_path)
        self.database = database
        
        # Broker & Execution Engine
        if broker is None:
            # Create broker adapter based on config
            broker_type = config.get('broker', {}).get('type', 'mock')

            if broker_type == 'mock':
                mock_config = config.get('broker', {}).get('mock', {})
                broker = MockBrokerAdapter(
                    slippage_ticks=mock_config.get('slippage_ticks', 0.5),
                    latency_ms=mock_config.get('latency_ms', 50.0),
                    fill_probability=mock_config.get('fill_probability', 1.0)
                )
                logger.info("Using MockBrokerAdapter")

            elif broker_type == 'kraken':
                kraken_config = config.get('broker', {})
                broker = KrakenAdapter(
                    api_key=kraken_config.get('api_key', ''),
                    private_key=kraken_config.get('private_key', ''),
                    sandbox=kraken_config.get('sandbox', True),
                    testnet=kraken_config.get('testnet', True)
                )
                logger.info(f"Using KrakenAdapter (sandbox={kraken_config.get('sandbox', True)})")

            else:
                # Default to mock if unknown type
                logger.warning(f"Unknown broker type '{broker_type}', defaulting to mock")
                broker = MockBrokerAdapter()
        
        self.broker = broker
        self.execution_engine = ExecutionEngine(
            broker=self.broker,
            database=self.database,
            guard=self.execution_guard
        )
        
        # Strategies (regime-based strategy selection)
        self.strategies: Dict[str, BaseStrategy] = {
            'TREND': VWAPPullbackStrategy(instrument_spec_service=self.instrument_spec),
            'RANGE': ORBRetestStrategy(instrument_spec_service=self.instrument_spec),
            'VOLATILE': MeanReversionStrategy(instrument_spec_service=self.instrument_spec),
        }
        
        self.current_strategy: Optional[BaseStrategy] = None
        self.current_regime: Optional[str] = None
        
        # State
        self.state = SystemState.INITIALIZING
        self.current_positions: List[Position] = []
        
        # Initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize system and transition to READY state"""
        try:
            logger.info("Initializing Transmission Orchestrator...")
            self.state = SystemState.READY
            logger.info("Transmission system ready")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state = SystemState.ERROR
            raise
    
    def process_bar(
        self,
        bars_15m: pd.DataFrame,
        current_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None
    ) -> Optional[Signal]:
        """
        Main decision loop - called every 15-minute bar.
        
        Args:
            bars_15m: DataFrame with OHLCV data (15-minute bars)
            current_price: Current market price
            bid: Current bid price (optional)
            ask: Current ask price (optional)
            
        Returns:
            Signal if generated and approved, None otherwise
        """
        try:
            self.state = SystemState.ANALYZING
            
            # Step 1: Calculate market features
            features = self.telemetry.calculate_all_features(
                bars_15m=bars_15m,
                current_price=current_price,
                bid=bid,
                ask=ask
            )
            
            # Step 2: Check risk tripwires
            tripwire = self.risk_governor.check_tripwires()
            if not tripwire.can_trade:
                logger.warning(f"Trading blocked: {tripwire.reason}")
                self.state = SystemState.PAUSED
                return None
            
            # Step 3: Classify regime
            regime_result = self.regime_classifier.classify(features)
            self.current_regime = regime_result.regime
            
            # Step 4: Check if regime is tradeable
            if not self.regime_classifier.is_tradeable(regime_result.regime):
                logger.info(f"Regime {regime_result.regime} - no trading allowed")
                return None
            
            # Step 8: Select strategy based on regime
            strategy = self._select_strategy(regime_result.regime)
            if strategy is None:
                logger.info(f"No strategy available for regime {regime_result.regime}")
                return None
            
            self.current_strategy = strategy
            
            # Step 9: Generate signal
            signal = strategy.generate_signal(
                features=features,
                regime=regime_result.regime,
                current_positions=self.current_positions
            )
            
            if signal is None:
                return None
            
            self.state = SystemState.SIGNAL_GENERATED
            
            # Step 10: Calculate position size (ATR-normalized)
            risk_dollars = self.risk_governor.get_current_r()
            stop_distance_points = abs(signal.entry_price - signal.stop_price)
            
            # Get DLL constraint if available
            dll_constraint = self.constraint_engine.get_dll_constraint()
            
            # Apply mental state multiplier
            mental_result = self.mental_governor.evaluate()
            risk_dollars *= mental_result.size_multiplier
            
            # Calculate contracts with ATR normalization
            contracts = self.position_sizer.calculate_contracts(
                risk_dollars=risk_dollars,
                stop_points=stop_distance_points,
                atr_current=features.atr_14,
                atr_baseline=features.baseline_atr,
                dll_constraint=dll_constraint,
                mental_state=mental_result.current_state.value
            )
            
            if contracts < 1:
                logger.info("Position too small after sizing - skipping trade")
                self._broadcast_rejection("position_too_small", "Position size < 1 contract")
                return None
            
            signal.contracts = contracts
            
            # Step 8: Validate constraints (Smart Constraints)
            if bid is not None and ask is not None:
                spread_ticks = self.telemetry.calculate_spread_ticks(bid, ask)
            else:
                spread_ticks = features.spread_ticks if hasattr(features, 'spread_ticks') else 1.0
            
            constraint_result = self.constraint_engine.validate_trade(
                symbol=signal.symbol,
                risk_dollars=risk_dollars,
                spread_ticks=spread_ticks,
                estimated_slippage_ticks=features.entry_p90_slippage if hasattr(features, 'entry_p90_slippage') else 1.0,
                news_proximity_min=features.news_proximity_min,
                mental_state=mental_result.current_state.value,
                account_equity=None,  # TODO: Get from account
                dll_remaining=dll_constraint
            )
            
            if not constraint_result.approved:
                logger.warning(f"Trade blocked by constraints: {constraint_result.reason}")
                self.database.save_system_state(
                    system_state="constraint_violation",
                    current_regime=self.current_regime,
                    active_strategy=signal.strategy
                )
                self._broadcast_rejection("constraint_violation", constraint_result.reason)
                return None
            
            # Step 9: Check execution quality (Guard)
            if bid is not None and ask is not None:
                execution_check = self.execution_guard.validate_execution(
                    spread_ticks=spread_ticks,
                    order_size=signal.contracts
                )
                
                if not execution_check.approved:
                    logger.warning(f"Execution blocked by guard: {execution_check.reason}")
                    self.database.save_system_state(
                        system_state="guard_reject",
                        current_regime=self.current_regime,
                        active_strategy=signal.strategy
                    )
                    self._broadcast_rejection("guard_reject", execution_check.reason)
                    return None
                
                signal.notes = f"{signal.notes or ''} | Order type: {execution_check.recommended_order_type}"
            
            # Step 10: Execute trade
            order_id = self.execution_engine.place_signal(
                signal=signal,
                qty=float(signal.contracts)
            )
            
            if order_id is None:
                logger.error("Order submission failed")
                return None
            
            # Step 11: Journal + Broadcast
            self.database.save_system_state(
                system_state="order_submitted",
                current_regime=self.current_regime,
                active_strategy=signal.strategy
            )
            self._broadcast_order_submitted(order_id, signal)
            
            logger.info(
                f"Signal executed: {signal.strategy} {signal.direction} "
                f"{signal.contracts} contracts @ {signal.entry_price:.2f} "
                f"(order_id: {order_id})"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in process_bar: {e}", exc_info=True)
            self.state = SystemState.ERROR
            return None

    async def process_signal(self, signal: Signal) -> Dict:
        """
        Process external signal (from webhooks or API).

        Simplified version for MVP - skips full market data fetching.
        Trusts signal source for entry/stop/target prices.

        Args:
            signal: Signal object with symbol, direction, entry, stop, target

        Returns:
            Dict with status, action, reason, and execution details
        """
        try:
            logger.info(f"Processing external signal: {signal.strategy} {signal.direction} on {signal.symbol}")

            # Step 1: Mental State Check
            mental_result = self.mental_governor.evaluate()
            if mental_result.current_state == MentalState.BLOCKED:
                logger.warning(f"Signal blocked by Mental Governor: {mental_result.reason}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": f"Mental state: {mental_result.current_state.value} - {mental_result.reason}",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 2: News Blackout Check
            if self.news_flat.is_blackout(signal.symbol):
                logger.warning(f"Signal blocked by News Blackout: {signal.symbol}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": "News blackout active",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 3: Risk Tripwire Check
            tripwire = self.risk_governor.check_tripwires()
            if not tripwire.can_trade:
                logger.warning(f"Signal blocked by Risk Governor: {tripwire.reason}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": tripwire.reason,
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 3.5: Gear State Calculation (NEW - Transmission Visualization)
            gear_context = self._build_gear_context(regime=signal.regime if hasattr(signal, 'regime') else None)
            current_gear, gear_reason = self.gear_state_machine.shift(gear_context)

            logger.info(f"Current gear: {current_gear.value} ({gear_reason})")

            # If gear is PARK, block trading immediately
            if current_gear == GearState.PARK:
                logger.warning(f"Trading blocked by Gear State: {current_gear.value} - {gear_reason}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": f"Gear: {current_gear.value} - {gear_reason}",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "gear": current_gear.value,
                    "gear_reason": gear_reason
                }

            # Step 4: Position Sizing (Simplified)
            # Use signal's entry and stop to calculate risk
            risk_dollars = self.risk_governor.get_current_r()
            stop_distance_points = abs(signal.entry_price - signal.stop_price)

            # Apply mental state multiplier
            risk_dollars *= mental_result.size_multiplier

            # Apply GEAR multiplier (NEW - Transmission adaptive sizing)
            gear_multiplier = self.gear_state_machine.get_risk_multiplier()
            risk_dollars *= gear_multiplier
            logger.info(f"Gear {current_gear.value} risk multiplier: {gear_multiplier:.2f}x (effective risk: ${risk_dollars:.2f})")

            # Calculate contracts (simplified - no ATR normalization for webhook signals)
            if stop_distance_points > 0:
                contracts = int(risk_dollars / stop_distance_points)
            else:
                logger.warning("Signal has zero stop distance - rejecting")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": "Invalid stop distance (zero)",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            if contracts < 1:
                logger.info(f"Position too small after sizing: {contracts}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": "Position size < 1 contract after sizing",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Update signal with calculated position size
            signal.contracts = contracts

            # Step 5: Constraint Validation (Simplified)
            # Get current bid/ask from broker
            bid, ask = self.broker.get_bid_ask(signal.symbol)
            tick_size = self.instrument_spec.get_tick_size(signal.symbol)
            spread_ticks = (ask - bid) / tick_size

            # DLL constraint
            dll_constraint = self.constraint_engine.get_dll_constraint()

            constraint_result = self.constraint_engine.validate_trade(
                symbol=signal.symbol,
                risk_dollars=risk_dollars,
                spread_ticks=spread_ticks,
                estimated_slippage_ticks=1.0,  # Default estimate for webhooks
                news_proximity_min=999,  # News already checked above
                mental_state=mental_result.current_state.value,
                account_equity=None,
                dll_remaining=dll_constraint
            )

            if not constraint_result.approved:
                logger.warning(f"Signal blocked by constraints: {constraint_result.reason}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": constraint_result.reason,
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 6: Execution Guard
            execution_check = self.execution_guard.validate_execution(
                spread_ticks=spread_ticks,
                order_size=signal.contracts
            )

            if not execution_check.approved:
                logger.warning(f"Signal blocked by Execution Guard: {execution_check.reason}")
                return {
                    "status": "rejected",
                    "action": "REJECT",
                    "reason": execution_check.reason,
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 7: Execute Trade (with gear state)
            order_id = self.execution_engine.place_signal(
                signal=signal,
                qty=float(signal.contracts),
                gear_at_entry=current_gear.value,
                gear_shift_reason=gear_reason
            )

            if order_id is None:
                logger.error("Order submission failed")
                return {
                    "status": "error",
                    "action": "ERROR",
                    "reason": "Order execution failed",
                    "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                    "symbol": signal.symbol,
                    "direction": signal.direction
                }

            # Step 8: Log and Broadcast
            self.database.save_system_state(
                system_state="order_submitted",
                current_regime=signal.regime,
                active_strategy=signal.strategy
            )
            self._broadcast_order_submitted(order_id, signal)

            logger.info(
                f"Signal executed: {signal.strategy} {signal.direction} "
                f"{signal.contracts} contracts @ {signal.entry_price:.2f} "
                f"(order_id: {order_id})"
            )

            # Return success response with gear state
            return {
                "status": "processed",
                "action": "TRADE",
                "reason": "Signal approved and executed",
                "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                "order_id": order_id,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "contracts": signal.contracts,
                "entry_price": signal.entry_price,
                "stop_price": signal.stop_price,
                "target_price": signal.target_price,
                "gear": current_gear.value,
                "gear_reason": gear_reason,
                "gear_multiplier": gear_multiplier
            }

        except Exception as e:
            logger.error(f"Error in process_signal: {e}", exc_info=True)
            return {
                "status": "error",
                "action": "ERROR",
                "reason": f"Internal error: {str(e)}",
                "signal_id": f"sig_{int(signal.timestamp.timestamp())}",
                "symbol": signal.symbol if hasattr(signal, 'symbol') else "UNKNOWN",
                "direction": signal.direction if hasattr(signal, 'direction') else "UNKNOWN"
            }

    def _select_strategy(self, regime: str) -> Optional[BaseStrategy]:
        """
        Select strategy based on regime.

        Args:
            regime: Current market regime

        Returns:
            Strategy instance or None if no strategy for regime
        """
        return self.strategies.get(regime)

    def _build_gear_context(self, regime: Optional[str] = None, features: Optional[MarketFeatures] = None) -> GearContext:
        """
        Build GearContext from current system state.

        Args:
            regime: Current market regime (optional)
            features: Market features (optional, for volatility)

        Returns:
            GearContext with current state snapshot
        """
        # Get risk metrics from RiskGovernor
        daily_r = self.risk_governor.get_daily_r()
        weekly_r = self.risk_governor.get_weekly_r()

        # Get consecutive losses from journal analytics
        recent_trades = self.database.get_recent_trades(limit=10)
        consecutive_losses = 0
        for trade in recent_trades:
            if trade.get('win_loss') == 'Loss':
                consecutive_losses += 1
            else:
                break  # Stop at first non-loss

        # Get drawdown from journal analytics
        performance = self.journal_analytics.calculate_rolling_metrics(window=20)
        current_drawdown = performance.get('current_drawdown_r', 0.0)

        # Get volatility percentile (if features available)
        volatility_percentile = 0.5  # Default to median
        if features is not None and hasattr(features, 'atr_14') and hasattr(features, 'baseline_atr'):
            if features.baseline_atr > 0:
                volatility_percentile = min(features.atr_14 / features.baseline_atr, 2.0) / 2.0

        # Get mental state
        mental_result = self.mental_governor.evaluate()
        mental_state = mental_result.current_state.value

        # Get DLL remaining
        dll_remaining = self.constraint_engine.get_dll_constraint()

        # Check tripwires
        tripwire = self.risk_governor.check_tripwires()
        tripwire_active = not tripwire.can_trade

        # Check trading session (simplified - assume always in session for now)
        in_trading_session = True  # TODO: Add session time logic

        # Check news blackout
        news_blackout_active = False  # TODO: Check if any symbols are in blackout

        # Kill switch (manual emergency stop)
        kill_switch_active = self.risk_governor.is_kill_switch_active() if hasattr(self.risk_governor, 'is_kill_switch_active') else False

        # Get open positions count
        positions_open = len(self.current_positions)

        return GearContext(
            daily_r=daily_r,
            weekly_r=weekly_r,
            consecutive_losses=consecutive_losses,
            current_drawdown=current_drawdown,
            regime=regime or "UNKNOWN",
            volatility_percentile=volatility_percentile,
            mental_state=mental_state,
            dll_remaining=dll_remaining,
            tripwire_active=tripwire_active,
            in_trading_session=in_trading_session,
            news_blackout_active=news_blackout_active,
            kill_switch_active=kill_switch_active,
            positions_open=positions_open
        )
    
    def record_trade_result(
        self,
        trade_id: int,
        exit_price: float,
        exit_reason: str,
        pl_amount_gross: float,
        pnl_r: float,
        fees_paid: float,
        holding_duration_minutes: float,
        entry_slippage_ticks: float = 0.0,
        exit_slippage_ticks: float = 0.0
    ) -> None:
        """
        Record completed trade result.
        
        Args:
            trade_id: Database trade ID
            exit_price: Exit price
            exit_reason: Reason for exit
            pl_amount_gross: Gross P&L in dollars
            pnl_r: Profit/loss in R units
            fees_paid: Fees paid
            holding_duration_minutes: Holding duration
            entry_slippage_ticks: Entry slippage
            exit_slippage_ticks: Exit slippage
        """
        # Update database
        self.database.update_trade_exit(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_reason=exit_reason,
            pl_amount_gross=pl_amount_gross,
            result_r=pnl_r,
            fees_paid=fees_paid,
            holding_duration_minutes=holding_duration_minutes,
            entry_slippage_ticks=entry_slippage_ticks,
            exit_slippage_ticks=exit_slippage_ticks
        )
        
        # Update risk governor
        self.risk_governor.record_trade(pnl_r)
        self.constraint_engine.record_trade()
        self.state = SystemState.READY
        
        logger.info(f"Trade {trade_id} result recorded: {pnl_r:+.2f}R")
    
    def get_current_state(self) -> SystemState:
        """Get current system state"""
        return self.state
    
    def get_current_regime(self) -> Optional[str]:
        """Get current market regime"""
        return self.current_regime
    
    def get_current_strategy(self) -> Optional[str]:
        """Get current active strategy name"""
        if self.current_strategy:
            return self.current_strategy.strategy_name
        return None
    
    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        tripwire = self.risk_governor.check_tripwires()
        return {
            'can_trade': tripwire.can_trade,
            'daily_pnl_r': tripwire.daily_pnl_r,
            'weekly_pnl_r': tripwire.weekly_pnl_r,
            'current_r': self.risk_governor.get_current_r(),
            'consecutive_red_days': tripwire.consecutive_red_days
        }

