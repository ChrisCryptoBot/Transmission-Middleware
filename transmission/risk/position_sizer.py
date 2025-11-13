"""
Position Sizer Module

ATR-normalized position sizing with prop firm constraints.
Calculates contract quantity based on risk dollars, stop distance, and volatility.

Based on Product_Concept.txt Section 4 specifications.
"""

import math
from typing import Optional
from loguru import logger
import numpy as np
from transmission.config.instrument_specs import InstrumentSpecService


class PositionSizer:
    """
    Position Sizer with ATR normalization and prop firm constraints.

    Features:
    - ATR-normalized sizing (risk same % across volatility regimes)
    - Prop firm DLL constraints (max 10% of DLL per trade)
    - Mental state adjustments
    - Minimum position validation
    - Multi-asset support via InstrumentSpecService
    """

    def __init__(
        self,
        instrument_spec_service: Optional[InstrumentSpecService] = None,
        min_contracts: int = 1,
        max_risk_pct: float = 0.02,  # 2% max risk per trade
        dll_risk_pct: float = 0.10  # 10% of DLL max per trade
    ):
        """
        Initialize Position Sizer.

        Args:
            instrument_spec_service: Service for looking up instrument specs (default: creates new instance)
            min_contracts: Minimum contracts to trade (default 1)
            max_risk_pct: Maximum risk as % of account (default 2%)
            dll_risk_pct: Max risk as % of DLL (default 10%)
        """
        self.instrument_spec = instrument_spec_service or InstrumentSpecService()
        self.min_contracts = min_contracts
        self.max_risk_pct = max_risk_pct
        self.dll_risk_pct = dll_risk_pct
    
    def calculate_contracts(
        self,
        symbol: str,
        risk_dollars: float,
        stop_points: float,
        atr_current: float,
        atr_baseline: float,
        dll_constraint: Optional[float] = None,
        mental_state: int = 5,  # 1-5 scale
        account_balance: Optional[float] = None
    ) -> int:
        """
        Calculate contract quantity with ATR normalization.

        Formula:
        Base: contracts = floor(Risk$ / (StopPts × PointValue))
        ATR-normalized: Risk$ × clip(BaselineATR/CurrentATR, 0.67, 1.5)
        DLL constraint: MIN(Base_R$, DLL × 0.10)
        Mental adjustment: Reduce size if mental_state < 3

        Args:
            symbol: Trading symbol (e.g., "MNQ", "ES") - for looking up point value
            risk_dollars: Risk amount in dollars (e.g., $5, $10)
            stop_points: Stop distance in points
            atr_current: Current ATR value
            atr_baseline: Baseline/median ATR for normalization
            dll_constraint: Daily Loss Limit constraint (optional)
            mental_state: Mental state 1-5 (5 = best, <3 = reduce size)
            account_balance: Account balance for validation (optional)

        Returns:
            Number of contracts (0 if position too small or invalid)
        """
        if risk_dollars <= 0:
            logger.warning("Risk dollars must be positive")
            return 0
        
        if stop_points <= 0:
            logger.warning("Stop distance must be positive")
            return 0
        
        if atr_current <= 0 or atr_baseline <= 0:
            logger.warning("ATR values must be positive")
            return 0
        
        # Step 1: Mental state adjustment
        adjusted_risk = risk_dollars
        if mental_state < 3:
            adjusted_risk *= 0.50  # Cut size in half if not mentally sharp
            logger.info(f"Mental state {mental_state}/5: Reducing position size by 50%")
        
        # Step 2: ATR normalization
        # Clip ratio between 0.67 and 1.5 to prevent extreme adjustments
        vol_adjust = np.clip(atr_baseline / atr_current, 0.67, 1.5)
        adjusted_risk = adjusted_risk * vol_adjust
        
        logger.debug(
            f"ATR normalization: baseline={atr_baseline:.2f}, "
            f"current={atr_current:.2f}, adjustment={vol_adjust:.2f}"
        )
        
        # Step 3: DLL constraint (if prop firm)
        if dll_constraint and dll_constraint > 0:
            max_dll_risk = dll_constraint * self.dll_risk_pct
            adjusted_risk = min(adjusted_risk, max_dll_risk)
            logger.debug(f"DLL constraint: max risk ${max_dll_risk:.2f}")
        
        # Step 4: Account balance validation (if provided)
        if account_balance and account_balance > 0:
            max_account_risk = account_balance * self.max_risk_pct
            adjusted_risk = min(adjusted_risk, max_account_risk)
            logger.debug(f"Account balance constraint: max risk ${max_account_risk:.2f}")
        
        # Step 5: Calculate contracts
        # Get instrument-specific point value
        point_value = self.instrument_spec.get_point_value(symbol)

        # contracts = floor(adjusted_risk / (stop_points × point_value))
        risk_per_contract = stop_points * point_value
        if risk_per_contract <= 0:
            logger.warning("Risk per contract must be positive")
            return 0

        contracts = math.floor(adjusted_risk / risk_per_contract)
        
        # Step 6: Validate minimum
        if contracts < self.min_contracts:
            logger.info(
                f"Position too small: {contracts} contracts < {self.min_contracts} minimum"
            )
            return 0
        
        logger.info(
            f"Position sizing: ${risk_dollars:.2f} risk → {contracts} contracts "
            f"(stop={stop_points:.2f} pts, ATR adj={vol_adjust:.2f})"
        )
        
        return contracts
    
    def validate_position_size(
        self,
        symbol: str,
        contracts: int,
        stop_points: float,
        account_balance: float,
        max_risk_pct: Optional[float] = None
    ) -> tuple[bool, str]:
        """
        Validate position size doesn't exceed risk limits.

        Args:
            symbol: Trading symbol (for looking up point value)
            contracts: Number of contracts
            stop_points: Stop distance in points
            account_balance: Account balance
            max_risk_pct: Maximum risk percentage (defaults to self.max_risk_pct)

        Returns:
            (is_valid, reason_if_invalid)
        """
        if max_risk_pct is None:
            max_risk_pct = self.max_risk_pct

        if contracts < self.min_contracts:
            return False, f"Position too small: {contracts} < {self.min_contracts} minimum"

        # Calculate risk per contract
        point_value = self.instrument_spec.get_point_value(symbol)
        risk_per_contract = stop_points * point_value
        total_risk = contracts * risk_per_contract

        # Check against account balance
        max_allowed_risk = account_balance * max_risk_pct
        if total_risk > max_allowed_risk:
            return False, (
                f"Risk too high: ${total_risk:.2f} > ${max_allowed_risk:.2f} "
                f"({max_risk_pct*100}% of account)"
            )

        return True, "Position size valid"
    
    def calculate_stop_distance_points(
        self,
        entry_price: float,
        stop_price: float,
        direction: str
    ) -> float:
        """
        Calculate stop distance in points.
        
        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            direction: "LONG" or "SHORT"
            
        Returns:
            Stop distance in points
        """
        if direction.upper() == "LONG":
            return entry_price - stop_price
        elif direction.upper() == "SHORT":
            return stop_price - entry_price
        else:
            raise ValueError(f"Invalid direction: {direction}")
    
    def calculate_risk_dollars(
        self,
        contracts: int,
        stop_points: float
    ) -> float:
        """
        Calculate risk in dollars for given position.
        
        Args:
            contracts: Number of contracts
            stop_points: Stop distance in points
            
        Returns:
            Risk in dollars
        """
        return contracts * stop_points * self.point_value

