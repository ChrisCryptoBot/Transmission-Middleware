"""
Signal Adapter Abstraction

Converts platform-specific signals to Transmission format.
Enables webhook integration with TradingView, MT5, and other platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from transmission.strategies.base import Signal


class SignalAdapter(ABC):
    """
    Abstract base class for signal adapters.
    
    Converts platform-specific signal formats to Transmission Signal format.
    """
    
    @abstractmethod
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """
        Validate that raw signal has required fields.
        
        Args:
            raw_signal: Platform-specific signal data
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, raw_signal: Dict[str, Any]) -> Signal:
        """
        Parse platform signal → Transmission Signal.
        
        Args:
            raw_signal: Platform-specific signal data
        
        Returns:
            Transmission Signal object
        
        Raises:
            ValueError if signal is invalid
        """
        pass
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format (e.g., "MNQ" vs "MNQ1!").
        
        Args:
            symbol: Raw symbol from platform
        
        Returns:
            Normalized symbol
        """
        # Remove exchange suffixes (e.g., "MNQ1!" -> "MNQ")
        if "!" in symbol:
            symbol = symbol.split("!")[0]
        if "1" in symbol and len(symbol) > 3:
            # Remove contract month (e.g., "MNQ1" -> "MNQ")
            symbol = symbol.rstrip("0123456789")
        return symbol.upper()


class TradingViewAdapter(SignalAdapter):
    """
    TradingView webhook adapter.
    
    Format:
    {
        "ticker": "MNQ",
        "action": "BUY" | "SELL",
        "close": 12345.50,
        "time": 1234567890,
        "message": "Optional message"
    }
    """
    
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate TradingView alert format"""
        required = ["ticker", "action", "close"]
        return all(k in raw_signal for k in required)
    
    def parse(self, alert: Dict[str, Any]) -> Signal:
        """Parse TradingView alert to Signal"""
        if not self.validate(alert):
            raise ValueError("Invalid TradingView alert format")
        
        # Normalize direction
        action = alert["action"].upper()
        if action in ["BUY", "LONG"]:
            direction = "LONG"
        elif action in ["SELL", "SHORT"]:
            direction = "SHORT"
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Parse timestamp
        if "time" in alert:
            timestamp = datetime.fromtimestamp(alert["time"])
        else:
            timestamp = datetime.now()
        
        # Normalize symbol
        symbol = self.normalize_symbol(alert["ticker"])
        
        return Signal(
            symbol=symbol,
            direction=direction,
            entry_price=float(alert["close"]),
            timestamp=timestamp,
            strategy="TradingView",
            confidence=0.8,  # Default confidence for external signals
            notes=f"TradingView alert: {alert.get('message', '')}"
        )


class MT5Adapter(SignalAdapter):
    """
    MetaTrader 5 EA adapter.
    
    Format:
    {
        "symbol": "MNQ",
        "type": 0 (BUY) | 1 (SELL),
        "price": 12345.50,
        "comment": "Optional comment",
        "magic": 12345
    }
    """
    
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate MT5 signal format"""
        required = ["symbol", "type", "price"]
        return all(k in raw_signal for k in required)
    
    def parse(self, signal: Dict[str, Any]) -> Signal:
        """Parse MT5 signal to Signal"""
        if not self.validate(signal):
            raise ValueError("Invalid MT5 signal format")
        
        # MT5 type: 0 = BUY, 1 = SELL
        direction = "LONG" if signal["type"] == 0 else "SHORT"
        
        # Normalize symbol
        symbol = self.normalize_symbol(signal["symbol"])
        
        return Signal(
            symbol=symbol,
            direction=direction,
            entry_price=float(signal["price"]),
            timestamp=datetime.now(),
            strategy="MT5_EA",
            confidence=0.75,  # Slightly lower confidence for EA signals
            notes=f"MT5 EA: {signal.get('comment', '')} (Magic: {signal.get('magic', 'N/A')})"
        )


class GenericWebhookAdapter(SignalAdapter):
    """
    Generic webhook adapter for custom integrations.
    
    Format:
    {
        "symbol": "MNQ",
        "direction": "LONG" | "SHORT",
        "entry_price": 12345.50,
        "timestamp": "2024-12-19T10:00:00Z" (optional),
        "strategy": "Custom",
        "confidence": 0.8 (optional),
        "notes": "Optional notes"
    }
    """
    
    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate generic webhook format"""
        required = ["symbol", "direction", "entry_price"]
        return all(k in raw_signal for k in required)
    
    def parse(self, signal: Dict[str, Any]) -> Signal:
        """Parse generic webhook to Signal"""
        if not self.validate(signal):
            raise ValueError("Invalid webhook signal format")
        
        # Normalize direction
        direction = signal["direction"].upper()
        if direction not in ["LONG", "SHORT"]:
            raise ValueError(f"Invalid direction: {direction}")
        
        # Parse timestamp
        if "timestamp" in signal:
            try:
                timestamp = datetime.fromisoformat(signal["timestamp"].replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Normalize symbol
        symbol = self.normalize_symbol(signal["symbol"])
        
        return Signal(
            symbol=symbol,
            direction=direction,
            entry_price=float(signal["entry_price"]),
            timestamp=timestamp,
            strategy=signal.get("strategy", "Webhook"),
            confidence=float(signal.get("confidence", 0.7)),
            notes=signal.get("notes", "")
        )


def get_adapter(platform: str) -> SignalAdapter:
    """
    Get signal adapter for platform.
    
    Args:
        platform: Platform name ("tradingview", "mt5", "generic")
    
    Returns:
        SignalAdapter instance
    
    Raises:
        ValueError if platform not supported
    """
    adapters = {
        "tradingview": TradingViewAdapter,
        "mt5": MT5Adapter,
        "generic": GenericWebhookAdapter
    }
    
    platform_lower = platform.lower()
    if platform_lower not in adapters:
        raise ValueError(f"Unsupported platform: {platform}. Supported: {list(adapters.keys())}")
    
    return adapters[platform_lower]()

