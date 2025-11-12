"""
Configuration Loader

Loads and validates configuration files with safeguardrail enforcement.
Refuses to start if any safeguardrail exceeds ceiling.
"""

from pathlib import Path
from typing import Dict, Optional
import yaml
from loguru import logger


class ConfigLoader:
    """Load and validate configuration files"""
    
    @staticmethod
    def load_broker_config(config_path: Optional[str] = None) -> Dict:
        """Load broker configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / "broker.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def load_constraints_config(config_path: Optional[str] = None) -> Dict:
        """Load constraints configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / "constraints.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def validate_constraints(constraints: Dict) -> tuple[bool, list[str]]:
        """
        Validate constraints against safeguardrail ceilings.
        
        Returns:
            (is_valid, list of violations)
        """
        violations = []
        
        if 'constraints' not in constraints:
            return True, []  # No constraints to validate
        
        c = constraints['constraints']
        sg = c.get('safeguardrails', {})
        
        # Check capital constraints
        capital = c.get('capital', {})
        max_risk_pct = capital.get('max_risk_per_trade_pct', 0.5)
        if max_risk_pct > sg.get('max_risk_per_trade_pct_ceiling', 2.0):
            violations.append(
                f"max_risk_per_trade_pct ({max_risk_pct}%) exceeds ceiling "
                f"({sg.get('max_risk_per_trade_pct_ceiling', 2.0)}%)"
            )
        
        dll_fraction = capital.get('dll_fraction_per_trade', 0.10)
        if dll_fraction > sg.get('dll_fraction_per_trade_ceiling', 0.10):
            violations.append(
                f"dll_fraction_per_trade ({dll_fraction}) exceeds ceiling "
                f"({sg.get('dll_fraction_per_trade_ceiling', 0.10)})"
            )
        
        # Check cadence constraints
        cadence = c.get('cadence', {})
        max_trades = cadence.get('max_trades_per_day', 1)
        if max_trades > sg.get('max_trades_per_day_ceiling', 10):
            violations.append(
                f"max_trades_per_day ({max_trades}) exceeds ceiling "
                f"({sg.get('max_trades_per_day_ceiling', 10)})"
            )
        
        # Check quality gates
        quality = c.get('quality_gates', {})
        max_spread = quality.get('max_spread_ticks', 2.0)
        if max_spread > sg.get('max_spread_ticks_ceiling', 5.0):
            violations.append(
                f"max_spread_ticks ({max_spread}) exceeds ceiling "
                f"({sg.get('max_spread_ticks_ceiling', 5.0)})"
            )
        
        return len(violations) == 0, violations
    
    @staticmethod
    def log_effective_values(constraints: Dict) -> None:
        """Log effective constraint values after merging defaults + overrides"""
        if 'constraints' not in constraints:
            return
        
        c = constraints['constraints']
        
        logger.info("=== Effective Constraint Values ===")
        
        capital = c.get('capital', {})
        logger.info(f"Capital: max_risk_pct={capital.get('max_risk_per_trade_pct')}%, "
                   f"dll_fraction={capital.get('dll_fraction_per_trade')}")
        
        cadence = c.get('cadence', {})
        logger.info(f"Cadence: max_trades/day={cadence.get('max_trades_per_day')}, "
                   f"sessions={cadence.get('trading_sessions_ct')}")
        
        quality = c.get('quality_gates', {})
        logger.info(f"Quality: max_spread={quality.get('max_spread_ticks')} ticks, "
                   f"max_slippage={quality.get('max_est_slippage_ticks')} ticks")
        
        logger.info("===================================")

