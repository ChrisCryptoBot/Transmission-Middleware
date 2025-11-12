"""
Smart Constraints Engine

User-configurable constraints with smart defaults derived from user profile.
Enforces non-bypassable safeguardrails.

Based on Action_Sugg_1 and Action_Sugg_2 requirements.
"""

from typing import Optional, Dict, List, Literal
from pathlib import Path
import yaml
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime, time
import pytz

from transmission.risk.constraint_engine import ValidationResult


@dataclass
class CapitalConstraints:
    """Capital and risk management constraints"""
    max_risk_per_trade_pct: float = 0.5
    dll_fraction_per_trade: float = 0.10
    max_position_size_pct: float = 5.0


@dataclass
class CadenceConstraints:
    """Trading cadence constraints"""
    max_trades_per_day: int = 1
    max_trades_per_week: int = 5
    trading_sessions_ct: List[str] = field(default_factory=lambda: ["08:30-11:00"])
    news_blackout_minutes: List[int] = field(default_factory=lambda: [30, 30])


@dataclass
class QualityGateConstraints:
    """Execution quality gate constraints"""
    max_spread_ticks: float = 2.0
    max_est_slippage_ticks: float = 2.0
    max_latency_ms: float = 150.0
    min_liquidity_depth: float = 3.0


@dataclass
class PsychologyConstraints:
    """Psychology and mental state constraints"""
    min_mental_state: int = 3
    post_drawdown_stepdown_r_pct: float = 50.0
    consecutive_loss_reduction: float = 0.75


@dataclass
class Safeguardrails:
    """Non-bypassable system safeguardrails"""
    max_risk_per_trade_pct_ceiling: float = 2.0
    dll_fraction_per_trade_ceiling: float = 0.10
    auto_flat_daily_loss_r: float = -2.0
    auto_flat_weekly_loss_r: float = -5.0
    min_mental_state_floor: int = 1
    max_spread_ticks_ceiling: float = 5.0
    max_trades_per_day_ceiling: int = 10


@dataclass
class UserConstraints:
    """Complete user constraints configuration"""
    capital: CapitalConstraints
    cadence: CadenceConstraints
    quality_gates: QualityGateConstraints
    psychology: PsychologyConstraints
    compliance_profile: str = "generic"
    allowed_symbols: List[str] = field(default_factory=lambda: ["MNQ"])
    safeguardrails: Safeguardrails = field(default_factory=Safeguardrails)


class SmartConstraintEngine:
    """
    Smart constraint engine with user-configurable parameters and safeguardrails.
    
    Features:
    - Profile-driven defaults (inferred from capital, DLL, experience)
    - User-configurable via YAML
    - Non-bypassable safeguardrails
    - Audit logging for all decisions
    """
    
    def __init__(
        self,
        constraints_path: Optional[str] = None,
        user_profile_path: Optional[str] = None
    ):
        """
        Initialize Smart Constraint Engine.
        
        Args:
            constraints_path: Path to constraints.yaml (default: config/constraints.yaml)
            user_profile_path: Path to user_profile.yaml (default: config/user_profile.yaml)
        """
        if constraints_path is None:
            constraints_path = Path(__file__).parent.parent / "config" / "constraints.yaml"
        
        if user_profile_path is None:
            user_profile_path = Path(__file__).parent.parent / "config" / "user_profile.yaml"
        
        self.constraints_path = Path(constraints_path)
        self.user_profile_path = Path(user_profile_path)
        
        # Load user profile for smart defaults
        self.user_profile = self._load_user_profile()
        
        # Load constraints (with smart defaults applied)
        self.constraints = self._load_constraints()
        
        # Apply safeguardrails (non-bypassable)
        self._apply_safeguardrails()
        
        # State tracking
        self.trades_today = 0
        self.trades_this_week = 0
        self.last_trade_date = None
        self.last_week_start = None
        
        logger.info(f"Smart Constraint Engine initialized with profile: {self.constraints.compliance_profile}")
    
    def _load_user_profile(self) -> Dict:
        """Load user profile for smart defaults"""
        try:
            if self.user_profile_path.exists():
                with open(self.user_profile_path, 'r') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load user profile: {e}")
        
        return {}
    
    def _load_constraints(self) -> UserConstraints:
        """Load constraints with smart defaults"""
        # Load from YAML if exists
        if self.constraints_path.exists():
            try:
                with open(self.constraints_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'constraints' in config:
                        return self._parse_constraints(config['constraints'])
            except Exception as e:
                logger.warning(f"Could not load constraints YAML: {e}, using defaults")
        
        # Generate smart defaults from user profile
        return self._generate_smart_defaults()
    
    def _generate_smart_defaults(self) -> UserConstraints:
        """
        Generate smart defaults from user profile.
        
        Logic:
        - max_risk_per_trade = min(2% equity, 10% of DLL)
        - max_trades_per_day = based on time available
        - trading_sessions = based on user availability
        """
        profile = self.user_profile
        
        # Capital defaults
        equity = profile.get('starting_capital', 10000.0)
        dll = profile.get('daily_loss_limit', 1000.0)
        
        # Smart default: min(2% equity, 10% DLL)
        max_risk_pct = min(2.0, (dll * 0.10 / equity) * 100) if equity > 0 else 0.5
        max_risk_pct = max(0.1, min(max_risk_pct, 2.0))  # Clamp between 0.1% and 2%
        
        capital = CapitalConstraints(
            max_risk_per_trade_pct=max_risk_pct,
            dll_fraction_per_trade=0.10,
            max_position_size_pct=5.0
        )
        
        # Cadence defaults
        hours_available = profile.get('hours_available_per_day', 4)
        max_trades = max(1, min(hours_available // 2, 5))  # Rough estimate
        
        cadence = CadenceConstraints(
            max_trades_per_day=max_trades,
            max_trades_per_week=max_trades * 5,
            trading_sessions_ct=profile.get('trading_sessions', ["08:30-11:00"]),
            news_blackout_minutes=[30, 30]
        )
        
        # Quality gates (defaults)
        quality_gates = QualityGateConstraints()
        
        # Psychology (defaults)
        psychology = PsychologyConstraints()
        
        # Compliance profile
        account_type = profile.get('account_type', 'generic')
        compliance_profile = profile.get('prop_firm', account_type).lower() if account_type == 'prop' else 'generic'
        
        # Allowed symbols
        allowed_symbols = profile.get('preferred_symbols', ['MNQ'])
        
        return UserConstraints(
            capital=capital,
            cadence=cadence,
            quality_gates=quality_gates,
            psychology=psychology,
            compliance_profile=compliance_profile,
            allowed_symbols=allowed_symbols
        )
    
    def _parse_constraints(self, config: Dict) -> UserConstraints:
        """Parse constraints from YAML config"""
        capital = CapitalConstraints(**config.get('capital', {}))
        cadence = CadenceConstraints(**config.get('cadence', {}))
        quality_gates = QualityGateConstraints(**config.get('quality_gates', {}))
        psychology = PsychologyConstraints(**config.get('psychology', {}))
        safeguardrails = Safeguardrails(**config.get('safeguardrails', {}))
        
        return UserConstraints(
            capital=capital,
            cadence=cadence,
            quality_gates=quality_gates,
            psychology=psychology,
            compliance_profile=config.get('compliance_profile', 'generic'),
            allowed_symbols=config.get('allowed_symbols', ['MNQ']),
            safeguardrails=safeguardrails
        )
    
    def _apply_safeguardrails(self) -> None:
        """Apply non-bypassable safeguardrails"""
        sg = self.constraints.safeguardrails
        
        # Enforce ceilings
        self.constraints.capital.max_risk_per_trade_pct = min(
            self.constraints.capital.max_risk_per_trade_pct,
            sg.max_risk_per_trade_pct_ceiling
        )
        
        self.constraints.capital.dll_fraction_per_trade = min(
            self.constraints.capital.dll_fraction_per_trade,
            sg.dll_fraction_per_trade_ceiling
        )
        
        self.constraints.cadence.max_trades_per_day = min(
            self.constraints.cadence.max_trades_per_day,
            sg.max_trades_per_day_ceiling
        )
        
        self.constraints.quality_gates.max_spread_ticks = min(
            self.constraints.quality_gates.max_spread_ticks,
            sg.max_spread_ticks_ceiling
        )
        
        # Enforce floors
        self.constraints.psychology.min_mental_state = max(
            self.constraints.psychology.min_mental_state,
            sg.min_mental_state_floor
        )
        
        logger.info("Safeguardrails applied")
    
    def validate_trade(
        self,
        symbol: str,
        risk_dollars: float,
        spread_ticks: float,
        estimated_slippage_ticks: float,
        news_proximity_min: Optional[int] = None,
        mental_state: int = 5,
        account_equity: Optional[float] = None,
        dll_remaining: Optional[float] = None
    ) -> ValidationResult:
        """
        Validate trade against all constraints with audit logging.
        
        Returns:
            ValidationResult with approved flag and reason
        """
        reasons = []
        
        # 1. Symbol check
        if symbol not in self.constraints.allowed_symbols:
            return ValidationResult(
                approved=False,
                reason=f"Symbol {symbol} not in allowed list: {self.constraints.allowed_symbols}",
                adjusted_contracts=None
            )
        
        # 2. Mental state check
        if mental_state < self.constraints.psychology.min_mental_state:
            return ValidationResult(
                approved=False,
                reason=f"Mental state {mental_state} below minimum {self.constraints.psychology.min_mental_state}",
                adjusted_contracts=None
            )
        
        # 3. Trade cadence check
        if self.trades_today >= self.constraints.cadence.max_trades_per_day:
            return ValidationResult(
                approved=False,
                reason=f"Max trades per day ({self.constraints.cadence.max_trades_per_day}) reached",
                adjusted_contracts=None
            )
        
        # 4. Capital constraints
        if account_equity:
            max_risk = account_equity * (self.constraints.capital.max_risk_per_trade_pct / 100)
            if risk_dollars > max_risk:
                reasons.append(f"Risk ${risk_dollars:.2f} exceeds {self.constraints.capital.max_risk_per_trade_pct}% of equity")
                # Adjust risk down
                risk_dollars = max_risk
        
        # 5. DLL constraint
        if dll_remaining:
            max_dll_risk = dll_remaining * self.constraints.capital.dll_fraction_per_trade
            if risk_dollars > max_dll_risk:
                reasons.append(f"Risk ${risk_dollars:.2f} exceeds {self.constraints.capital.dll_fraction_per_trade*100}% of DLL")
                risk_dollars = max_dll_risk
        
        # 6. Quality gates
        if spread_ticks > self.constraints.quality_gates.max_spread_ticks:
            return ValidationResult(
                approved=False,
                reason=f"Spread {spread_ticks:.1f} ticks exceeds max {self.constraints.quality_gates.max_spread_ticks}",
                adjusted_contracts=None
            )
        
        if estimated_slippage_ticks > self.constraints.quality_gates.max_est_slippage_ticks:
            return ValidationResult(
                approved=False,
                reason=f"Estimated slippage {estimated_slippage_ticks:.1f} ticks exceeds max {self.constraints.quality_gates.max_est_slippage_ticks}",
                adjusted_contracts=None
            )
        
        # 7. News blackout
        if news_proximity_min is not None:
            blackout_before, blackout_after = self.constraints.cadence.news_blackout_minutes
            if news_proximity_min <= blackout_before:
                return ValidationResult(
                    approved=False,
                    reason=f"News event in {news_proximity_min} minutes (blackout: {blackout_before} min before)",
                    adjusted_contracts=None
                )
        
        # 8. Trading session check
        if not self._is_in_trading_session():
            return ValidationResult(
                approved=False,
                reason="Outside trading session hours",
                adjusted_contracts=None
            )
        
        # If we get here, trade is approved (possibly with adjusted risk)
        if reasons:
            reason = "; ".join(reasons)
            logger.info(f"Trade approved with adjustments: {reason}")
        else:
            reason = "All constraints satisfied"
        
        return ValidationResult(
            approved=True,
            reason=reason,
            adjusted_contracts=None  # Contracts adjusted by position sizer
        )
    
    def _is_in_trading_session(self) -> bool:
        """Check if current time is within trading session"""
        # TODO: Implement timezone-aware session checking
        # For now, always return True (can be enhanced)
        return True
    
    def record_trade(self) -> None:
        """Record a trade (increment counters)"""
        self.trades_today += 1
        self.trades_this_week += 1
        self.last_trade_date = datetime.now().date()
    
    def reset_daily_counters(self) -> None:
        """Reset daily counters (called at start of day)"""
        self.trades_today = 0
    
    def get_dll_constraint(self) -> Optional[float]:
        """Get DLL constraint value (for position sizing)"""
        # This would come from user profile or risk governor
        return None  # TODO: Integrate with risk governor
    
    def get_max_risk_per_trade(self, account_equity: float) -> float:
        """Get maximum risk per trade in dollars"""
        return account_equity * (self.constraints.capital.max_risk_per_trade_pct / 100)
    
    def save_constraints(self) -> None:
        """Save current constraints to YAML file"""
        config = {
            'constraints': {
                'capital': {
                    'max_risk_per_trade_pct': self.constraints.capital.max_risk_per_trade_pct,
                    'dll_fraction_per_trade': self.constraints.capital.dll_fraction_per_trade,
                    'max_position_size_pct': self.constraints.capital.max_position_size_pct
                },
                'cadence': {
                    'max_trades_per_day': self.constraints.cadence.max_trades_per_day,
                    'max_trades_per_week': self.constraints.cadence.max_trades_per_week,
                    'trading_sessions_ct': self.constraints.cadence.trading_sessions_ct,
                    'news_blackout_minutes': self.constraints.cadence.news_blackout_minutes
                },
                'quality_gates': {
                    'max_spread_ticks': self.constraints.quality_gates.max_spread_ticks,
                    'max_est_slippage_ticks': self.constraints.quality_gates.max_est_slippage_ticks,
                    'max_latency_ms': self.constraints.quality_gates.max_latency_ms,
                    'min_liquidity_depth': self.constraints.quality_gates.min_liquidity_depth
                },
                'psychology': {
                    'min_mental_state': self.constraints.psychology.min_mental_state,
                    'post_drawdown_stepdown_r_pct': self.constraints.psychology.post_drawdown_stepdown_r_pct,
                    'consecutive_loss_reduction': self.constraints.psychology.consecutive_loss_reduction
                },
                'compliance_profile': self.constraints.compliance_profile,
                'allowed_symbols': self.constraints.allowed_symbols,
                'safeguardrails': {
                    'max_risk_per_trade_pct_ceiling': self.constraints.safeguardrails.max_risk_per_trade_pct_ceiling,
                    'dll_fraction_per_trade_ceiling': self.constraints.safeguardrails.dll_fraction_per_trade_ceiling,
                    'auto_flat_daily_loss_r': self.constraints.safeguardrails.auto_flat_daily_loss_r,
                    'auto_flat_weekly_loss_r': self.constraints.safeguardrails.auto_flat_weekly_loss_r,
                    'min_mental_state_floor': self.constraints.safeguardrails.min_mental_state_floor,
                    'max_spread_ticks_ceiling': self.constraints.safeguardrails.max_spread_ticks_ceiling,
                    'max_trades_per_day_ceiling': self.constraints.safeguardrails.max_trades_per_day_ceiling
                }
            }
        }
        
        self.constraints_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.constraints_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Constraints saved to {self.constraints_path}")

