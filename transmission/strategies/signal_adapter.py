"""
Signal Adapter Abstraction

Converts external signal formats (TradingView, MT5, custom webhooks) into
Transmission's internal Signal format.

This enables Transmission to accept signals from ANY platform via webhooks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from transmission.strategies.base import Signal


class SignalAdapter(ABC):
    """
    Base class for converting platform-specific signals to Transmission format.

    Each platform (TradingView, MT5, etc.) has its own adapter that:
    1. Validates the incoming signal format
    2. Parses and normalizes the data
    3. Converts to Transmission Signal format
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
            ValueError: If signal cannot be parsed
        """
        pass

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format across platforms.

        Examples:
            TradingView: "MNQM2023" → "MNQ"
            MT5: "MNQ-FUTURES" → "MNQ"
            Generic: "mnq" → "MNQ"

        Args:
            symbol: Platform-specific symbol

        Returns:
            Normalized symbol (uppercase, base symbol only)
        """
        symbol = symbol.upper().strip()

        # Remove common futures suffixes
        for suffix in ["-FUTURES", ".FUT", ".F"]:
            symbol = symbol.replace(suffix, "")

        # Remove month/year codes (e.g., M2023, H24)
        # Keep only letters at the start
        normalized = ""
        for char in symbol:
            if char.isalpha():
                normalized += char
            else:
                break

        return normalized or symbol


class TradingViewAdapter(SignalAdapter):
    """
    TradingView webhook format adapter.

    Expected format (from TradingView alert):
    {
        "ticker": "MNQ",  # or "MNQM2023"
        "action": "BUY" or "SELL",
        "close": 12345.50,  # Current price
        "time": 1703001600,  # Unix timestamp
        "strategy": "VWAP Pullback",  # Optional
        "message": "Entry signal"  # Optional
    }

    TradingView alert webhook setup:
    - Alert message should be JSON format
    - Webhook URL: https://your-api.com/api/webhooks/tradingview
    - Add X-API-Key header in TradingView webhook settings
    """

    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate TradingView signal format"""
        required_fields = ["ticker", "action", "close"]
        has_required = all(field in raw_signal for field in required_fields)

        if not has_required:
            logger.warning(f"TradingView signal missing required fields: {required_fields}")
            return False

        # Validate action
        action = raw_signal.get("action", "").upper()
        if action not in ["BUY", "SELL"]:
            logger.warning(f"Invalid TradingView action: {action}")
            return False

        return True

    def parse(self, raw_signal: Dict[str, Any]) -> Signal:
        """Parse TradingView signal"""
        if not self.validate(raw_signal):
            raise ValueError("Invalid TradingView signal format")

        # Parse direction
        action = raw_signal["action"].upper()
        direction = "LONG" if action == "BUY" else "SHORT"

        # Parse symbol
        symbol = self.normalize_symbol(raw_signal["ticker"])

        # Parse price
        entry_price = float(raw_signal["close"])

        # Parse timestamp (use provided or current)
        if "time" in raw_signal:
            timestamp = datetime.fromtimestamp(float(raw_signal["time"]))
        else:
            timestamp = datetime.now()

        # Strategy name
        strategy = raw_signal.get("strategy", "TradingView")

        # Notes/message
        notes = raw_signal.get("message", "TradingView alert")

        # Default stop/target (will be set by Position Sizer)
        # These are placeholders - Transmission will calculate actual values
        stop_price = entry_price * 0.98 if direction == "LONG" else entry_price * 1.02
        target_price = entry_price * 1.02 if direction == "LONG" else entry_price * 0.98

        # Default confidence (TradingView alerts are treated as high confidence)
        confidence = 0.8

        # Contracts (default 1, will be adjusted by Position Sizer)
        contracts = raw_signal.get("contracts", 1)

        return Signal(
            symbol=symbol,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            direction=direction,
            contracts=contracts,
            confidence=confidence,
            regime="UNKNOWN",  # Will be determined by Transmission
            strategy=strategy,
            timestamp=timestamp,
            notes=notes
        )


class MT5Adapter(SignalAdapter):
    """
    MetaTrader 5 Expert Advisor webhook format adapter.

    Expected format:
    {
        "symbol": "MNQ",
        "type": 0 or 1,  # 0=BUY, 1=SELL
        "price": 12345.50,
        "sl": 12300.0,  # Stop loss (optional)
        "tp": 12400.0,  # Take profit (optional)
        "volume": 1.0,  # Lot size
        "comment": "MA Crossover",  # Optional
        "magic": 123456  # EA magic number (optional)
    }
    """

    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate MT5 signal format"""
        required_fields = ["symbol", "type", "price"]
        has_required = all(field in raw_signal for field in required_fields)

        if not has_required:
            logger.warning(f"MT5 signal missing required fields: {required_fields}")
            return False

        # Validate type (0=BUY, 1=SELL)
        trade_type = raw_signal.get("type")
        if trade_type not in [0, 1]:
            logger.warning(f"Invalid MT5 trade type: {trade_type}")
            return False

        return True

    def parse(self, raw_signal: Dict[str, Any]) -> Signal:
        """Parse MT5 signal"""
        if not self.validate(raw_signal):
            raise ValueError("Invalid MT5 signal format")

        # Parse direction (MT5: 0=BUY, 1=SELL)
        direction = "LONG" if raw_signal["type"] == 0 else "SHORT"

        # Parse symbol
        symbol = self.normalize_symbol(raw_signal["symbol"])

        # Parse price
        entry_price = float(raw_signal["price"])

        # Parse stop loss and take profit
        if "sl" in raw_signal and raw_signal["sl"] > 0:
            stop_price = float(raw_signal["sl"])
        else:
            # Default stop (2% from entry)
            stop_price = entry_price * 0.98 if direction == "LONG" else entry_price * 1.02

        if "tp" in raw_signal and raw_signal["tp"] > 0:
            target_price = float(raw_signal["tp"])
        else:
            # Default target (2% from entry)
            target_price = entry_price * 1.02 if direction == "LONG" else entry_price * 0.98

        # Parse volume (MT5 lots → contracts)
        # For micro futures: 1 lot = 1 contract
        contracts = int(raw_signal.get("volume", 1.0))

        # Strategy name (from comment or magic number)
        comment = raw_signal.get("comment", "")
        magic = raw_signal.get("magic")
        strategy = f"MT5_{comment}" if comment else f"MT5_EA_{magic}" if magic else "MT5_EA"

        # Confidence (MT5 signals are medium confidence)
        confidence = 0.75

        return Signal(
            symbol=symbol,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            direction=direction,
            contracts=contracts,
            confidence=confidence,
            regime="UNKNOWN",
            strategy=strategy,
            timestamp=datetime.now(),
            notes=f"MT5 EA signal (magic={magic})" if magic else "MT5 EA signal"
        )


class GenericWebhookAdapter(SignalAdapter):
    """
    Generic webhook format adapter.

    Flexible format for custom integrations:
    {
        "symbol": "MNQ",
        "side": "LONG" or "SHORT",
        "entry": 12345.50,
        "stop": 12300.0,  # Optional
        "target": 12400.0,  # Optional
        "contracts": 1,  # Optional
        "strategy": "Custom Strategy",  # Optional
        "confidence": 0.8,  # Optional (0.0-1.0)
        "notes": "Custom signal"  # Optional
    }
    """

    def validate(self, raw_signal: Dict[str, Any]) -> bool:
        """Validate generic signal format"""
        required_fields = ["symbol", "side", "entry"]
        has_required = all(field in raw_signal for field in required_fields)

        if not has_required:
            logger.warning(f"Generic signal missing required fields: {required_fields}")
            return False

        # Validate side
        side = raw_signal.get("side", "").upper()
        if side not in ["LONG", "SHORT"]:
            logger.warning(f"Invalid generic signal side: {side}")
            return False

        return True

    def parse(self, raw_signal: Dict[str, Any]) -> Signal:
        """Parse generic signal"""
        if not self.validate(raw_signal):
            raise ValueError("Invalid generic signal format")

        # Parse direction
        direction = raw_signal["side"].upper()

        # Parse symbol
        symbol = self.normalize_symbol(raw_signal["symbol"])

        # Parse price
        entry_price = float(raw_signal["entry"])

        # Parse stop/target (with defaults)
        if "stop" in raw_signal:
            stop_price = float(raw_signal["stop"])
        else:
            stop_price = entry_price * 0.98 if direction == "LONG" else entry_price * 1.02

        if "target" in raw_signal:
            target_price = float(raw_signal["target"])
        else:
            target_price = entry_price * 1.02 if direction == "LONG" else entry_price * 0.98

        # Parse optional fields
        contracts = raw_signal.get("contracts", 1)
        confidence = raw_signal.get("confidence", 0.7)  # Default: medium confidence
        strategy = raw_signal.get("strategy", "Generic")
        notes = raw_signal.get("notes", "Generic webhook signal")

        return Signal(
            symbol=symbol,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            direction=direction,
            contracts=contracts,
            confidence=confidence,
            regime="UNKNOWN",
            strategy=strategy,
            timestamp=datetime.now(),
            notes=notes
        )


# Factory function for getting adapters
ADAPTERS = {
    "tradingview": TradingViewAdapter,
    "mt5": MT5Adapter,
    "generic": GenericWebhookAdapter,
}


def get_signal_adapter(adapter_type: str) -> SignalAdapter:
    """
    Get signal adapter by type.

    Args:
        adapter_type: "tradingview", "mt5", or "generic"

    Returns:
        SignalAdapter instance

    Raises:
        ValueError: If adapter type is unknown
    """
    if adapter_type not in ADAPTERS:
        raise ValueError(f"Unknown adapter type: {adapter_type}. Available: {list(ADAPTERS.keys())}")

    return ADAPTERS[adapter_type]()
