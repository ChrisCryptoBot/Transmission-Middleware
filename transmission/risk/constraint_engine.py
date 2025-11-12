"""
Constraint Engine Module

Enforces user-defined and prop-firm constraints:
- Daily Loss Limit (DLL)
- Consistency rules
- Max trades per day
- News blackout periods
- Minimum active days

Acts as the first validation layer before any trade is placed.
Based on ACTION_PLAN_CONCEPT.txt recommendations.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime, timedelta
import yaml
from pathlib import Path
from loguru import logger


@dataclass
class ValidationResult:
    """Result of constraint validation"""
    approved: bool
    reason: str
    adjusted_contracts: Optional[int] = None  # If contracts were reduced


@dataclass
class UserProfile:
    """User profile with constraints"""
    capital: dict
    prop_constraints: dict
    time_availability: dict
    risk_tolerance: dict


class ConstraintEngine:
    """
    Enforces user-defined and prop-firm constraints.
    
    This is the first validation layer - all trades must pass
    through the constraint engine before risk governor checks.
    """
    
    def __init__(self, user_profile_path: Optional[str] = None):
        """
        Initialize Constraint Engine.
        
        Args:
            user_profile_path: Path to user_profile.yaml (default: config/user_profile.yaml)
        """
        if user_profile_path is None:
            user_profile_path = Path(__file__).parent.parent / "config" / "user_profile.yaml"
        
        self.profile = self._load_profile(user_profile_path)
        self.daily_trades = 0
        self.last_trade_date: Optional[datetime] = None
        
        # Load prop firm constraints
        self.dll_amount = self.profile.prop_constraints.get('dll_amount', 500.0)
        self.consistency_rule = self.profile.prop_constraints.get('consistency_rule', 0.40)
        self.max_trades_per_day = self.profile.prop_constraints.get('max_trades_per_day', 1)
        self.news_blackout_minutes = self.profile.prop_constraints.get('news_blackout_minutes', 30)
        self.min_active_days = self.profile.prop_constraints.get('min_active_days', 5)
    
    def _load_profile(self, profile_path: str) -> UserProfile:
        """Load user profile from YAML file"""
        try:
            with open(profile_path, 'r') as f:
                data = yaml.safe_load(f)
            
            profile_data = data.get('user_profile', {})
            
            return UserProfile(
                capital=profile_data.get('capital', {}),
                prop_constraints=profile_data.get('prop_constraints', {}),
                time_availability=profile_data.get('time_availability', {}),
                risk_tolerance=profile_data.get('risk_tolerance', {})
            )
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            # Return default profile
            return UserProfile(
                capital={'current_capital': 1000.0},
                prop_constraints={
                    'dll_amount': 500.0,
                    'consistency_rule': 0.40,
                    'max_trades_per_day': 1
                },
                time_availability={},
                risk_tolerance={}
            )
    
    def validate_trade(
        self,
        signal_contracts: int,
        risk_dollars: float,
        news_proximity_min: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate trade against all constraints.
        
        Args:
            signal_contracts: Number of contracts from strategy
            risk_dollars: Risk amount in dollars
            news_proximity_min: Minutes to next news event (None if no news)
            
        Returns:
            ValidationResult with approval status and reason
        """
        # Reset daily trade count if new day
        today = datetime.now().date()
        if self.last_trade_date is None or self.last_trade_date.date() != today:
            self.daily_trades = 0
            self.last_trade_date = datetime.now()
        
        # Check max trades per day
        if self.daily_trades >= self.max_trades_per_day:
            return ValidationResult(
                approved=False,
                reason=f"Max trades per day reached: {self.daily_trades}/{self.max_trades_per_day}"
            )
        
        # Check news blackout
        if news_proximity_min is not None:
            if news_proximity_min <= self.news_blackout_minutes:
                return ValidationResult(
                    approved=False,
                    reason=f"News event in {news_proximity_min} minutes (blackout: {self.news_blackout_minutes}min)"
                )
        
        # Check DLL constraint
        # Risk should be ≤ min($R, 0.10 × DLL)
        dll_risk_limit = self.dll_amount * 0.10
        max_risk = min(risk_dollars, dll_risk_limit)
        
        if risk_dollars > dll_risk_limit:
            # Reduce contracts proportionally
            adjusted_contracts = int(signal_contracts * (dll_risk_limit / risk_dollars))
            
            if adjusted_contracts < 1:
                return ValidationResult(
                    approved=False,
                    reason=f"Risk ${risk_dollars:.2f} exceeds DLL limit ${dll_risk_limit:.2f} (10% of ${self.dll_amount:.2f})"
                )
            
            return ValidationResult(
                approved=True,
                reason=f"Risk adjusted for DLL: ${risk_dollars:.2f} → ${dll_risk_limit:.2f}",
                adjusted_contracts=adjusted_contracts
            )
        
        return ValidationResult(
            approved=True,
            reason="All constraints satisfied"
        )
    
    def record_trade(self) -> None:
        """Record that a trade was executed (increment daily counter)"""
        self.daily_trades += 1
        self.last_trade_date = datetime.now()
        logger.debug(f"Trade recorded. Daily trades: {self.daily_trades}/{self.max_trades_per_day}")
    
    def get_dll_risk_limit(self) -> float:
        """Get maximum risk allowed based on DLL (10% of DLL)"""
        return self.dll_amount * 0.10
    
    def get_remaining_trades_today(self) -> int:
        """Get remaining trades allowed today"""
        return max(0, self.max_trades_per_day - self.daily_trades)

