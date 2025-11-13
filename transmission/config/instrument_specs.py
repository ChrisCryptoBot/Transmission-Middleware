"""
Instrument Specifications Service

Loads and provides instrument metadata from instruments.yaml.
Supports futures, equities, crypto, forex with symbol-specific specs.
"""

from typing import Dict, Optional
from pathlib import Path
import yaml
from loguru import logger
from dataclasses import dataclass


@dataclass
class InstrumentSpec:
    """Specification for a trading instrument"""
    symbol: str
    name: str
    exchange: str
    asset_class: str  # "futures", "equity", "crypto", "forex"
    point_value: float  # Dollar value per full point
    tick_size: float  # Minimum price increment
    tick_value: float  # Dollar value per tick
    margin_day: Optional[float] = None
    margin_overnight: Optional[float] = None
    trading_hours: Optional[str] = None
    session_start: Optional[str] = None
    session_end: Optional[str] = None
    timezone: Optional[str] = None


class InstrumentSpecService:
    """
    Service for loading and accessing instrument specifications.
    
    Usage:
        spec_service = InstrumentSpecService()
        mnq_spec = spec_service.get_spec("MNQ")
        point_value = mnq_spec.point_value  # 2.0
        tick_size = mnq_spec.tick_size  # 0.25
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Instrument Spec Service.
        
        Args:
            config_path: Path to instruments.yaml (default: config/instruments.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "instruments.yaml"
        
        self.config_path = Path(config_path)
        self.instruments: Dict[str, InstrumentSpec] = {}
        self._load_instruments()
    
    def _load_instruments(self) -> None:
        """Load instrument specifications from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'instruments' not in config:
                logger.warning("No instruments found in config")
                return
            
            for symbol, spec_dict in config['instruments'].items():
                # Infer asset_class if not specified
                asset_class = spec_dict.get('asset_class', self._infer_asset_class(symbol))
                
                self.instruments[symbol] = InstrumentSpec(
                    symbol=symbol,
                    name=spec_dict.get('name', symbol),
                    exchange=spec_dict.get('exchange', 'UNKNOWN'),
                    asset_class=asset_class,
                    point_value=spec_dict['point_value'],
                    tick_size=spec_dict['tick_size'],
                    tick_value=spec_dict['tick_value'],
                    margin_day=spec_dict.get('margin_day'),
                    margin_overnight=spec_dict.get('margin_overnight'),
                    trading_hours=spec_dict.get('trading_hours'),
                    session_start=spec_dict.get('session_start'),
                    session_end=spec_dict.get('session_end'),
                    timezone=spec_dict.get('timezone')
                )
            
            logger.info(f"Loaded {len(self.instruments)} instrument specifications")
        
        except Exception as e:
            logger.error(f"Failed to load instruments config: {e}")
            raise
    
    def _infer_asset_class(self, symbol: str) -> str:
        """Infer asset class from symbol if not specified"""
        # Futures patterns
        if symbol in ['MNQ', 'MES', 'ES', 'NQ', 'YM', 'RTY', 'CL', 'GC', 'SI']:
            return 'futures'
        # Crypto patterns
        if 'BTC' in symbol or 'ETH' in symbol or 'USD' in symbol:
            return 'crypto'
        # Forex patterns
        if len(symbol) == 6 and any(curr in symbol for curr in ['USD', 'EUR', 'GBP', 'JPY']):
            return 'forex'
        # Default to equity
        return 'equity'
    
    def get_spec(self, symbol: str) -> InstrumentSpec:
        """
        Get instrument specification.
        
        Args:
            symbol: Instrument symbol (e.g., "MNQ")
        
        Returns:
            InstrumentSpec for the symbol
        
        Raises:
            ValueError: If symbol not found
        """
        if symbol not in self.instruments:
            raise ValueError(f"Instrument '{symbol}' not found in configuration")
        return self.instruments[symbol]
    
    def get_tick_size(self, symbol: str) -> float:
        """Get tick size for symbol"""
        return self.get_spec(symbol).tick_size
    
    def get_point_value(self, symbol: str) -> float:
        """Get point value for symbol"""
        return self.get_spec(symbol).point_value
    
    def get_tick_value(self, symbol: str) -> float:
        """Get tick value for symbol"""
        return self.get_spec(symbol).tick_value
    
    def get_asset_class(self, symbol: str) -> str:
        """Get asset class for symbol"""
        return self.get_spec(symbol).asset_class
    
    def list_symbols(self) -> list[str]:
        """List all available symbols"""
        return list(self.instruments.keys())

