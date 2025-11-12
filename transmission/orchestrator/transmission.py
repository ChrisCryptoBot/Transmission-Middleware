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
from transmission.risk.constraint_engine import ConstraintEngine, ValidationResult
from transmission.strategies.base import BaseStrategy, Signal, Position
from transmission.strategies.vwap_pullback import VWAPPullbackStrategy
from transmission.execution.guard import ExecutionGuard, ExecutionCheck


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
        constraint_engine: Optional[ConstraintEngine] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize Transmission Orchestrator.
        
        Args:
            risk_governor: RiskGovernor instance (creates default if None)
            constraint_engine: ConstraintEngine instance (creates default if None)
            db_path: Path to SQLite database for state
        """
        # Core modules
        self.telemetry = Telemetry(tick_size=0.25)
        self.regime_classifier = RegimeClassifier()
        
        # Risk management
        if risk_governor is None:
            risk_governor = RiskGovernor(db_path=db_path)
        self.risk_governor = risk_governor
        
        if constraint_engine is None:
            constraint_engine = ConstraintEngine()
        self.constraint_engine = constraint_engine
        
        # Execution
        self.execution_guard = ExecutionGuard()
        
        # Strategies
        self.strategies: Dict[str, BaseStrategy] = {
            'TREND': VWAPPullbackStrategy(),
            # 'RANGE': ORBRetestStrategy(),  # Will add in Week 2
            # 'VOLATILE': MeanReversionStrategy(),  # Will add later
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
            
            # Step 5: Select strategy based on regime
            strategy = self._select_strategy(regime_result.regime)
            if strategy is None:
                logger.info(f"No strategy available for regime {regime_result.regime}")
                return None
            
            self.current_strategy = strategy
            
            # Step 6: Generate signal
            signal = strategy.generate_signal(
                features=features,
                regime=regime_result.regime,
                current_positions=self.current_positions
            )
            
            if signal is None:
                return None
            
            self.state = SystemState.SIGNAL_GENERATED
            
            # Step 7: Validate constraints
            risk_dollars = self.risk_governor.get_current_r()
            constraint_result = self.constraint_engine.validate_trade(
                signal_contracts=signal.contracts,
                risk_dollars=risk_dollars,
                news_proximity_min=features.news_proximity_min
            )
            
            if not constraint_result.approved:
                logger.warning(f"Trade blocked by constraints: {constraint_result.reason}")
                return None
            
            # Adjust contracts if needed
            if constraint_result.adjusted_contracts is not None:
                signal.contracts = constraint_result.adjusted_contracts
                logger.info(f"Contracts adjusted: {constraint_result.reason}")
            
            # Step 8: Check execution quality
            if bid is not None and ask is not None:
                spread_ticks = self.telemetry.calculate_spread_ticks(bid, ask)
                execution_check = self.execution_guard.validate_execution(
                    spread_ticks=spread_ticks,
                    order_size=signal.contracts
                )
                
                if not execution_check.approved:
                    logger.warning(f"Execution blocked: {execution_check.reason}")
                    return None
                
                signal.notes = f"{signal.notes or ''} | Order type: {execution_check.recommended_order_type}"
            
            # Step 9: Final risk check (calculate position size)
            # Position sizing will be handled by execution engine
            # For now, signal.contracts is set by strategy (will be adjusted)
            
            logger.info(
                f"Signal generated: {signal.strategy} {signal.direction} "
                f"{signal.contracts} contracts @ {signal.entry_price:.2f}, "
                f"stop: {signal.stop_price:.2f}, target: {signal.target_price:.2f}"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in process_bar: {e}", exc_info=True)
            self.state = SystemState.ERROR
            return None
    
    def _select_strategy(self, regime: str) -> Optional[BaseStrategy]:
        """
        Select strategy based on regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            Strategy instance or None if no strategy for regime
        """
        return self.strategies.get(regime)
    
    def record_trade_result(self, pnl_r: float) -> None:
        """
        Record completed trade result.
        
        Args:
            pnl_r: Profit/loss in R units
        """
        self.risk_governor.record_trade(pnl_r)
        self.constraint_engine.record_trade()
        self.state = SystemState.READY
        
        logger.info(f"Trade result recorded: {pnl_r:+.2f}R")
    
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

