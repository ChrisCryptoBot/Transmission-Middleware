"""
Kraken Futures Broker Adapter

Integrates with Kraken Futures API for live/paper trading.
Uses ccxt library for order management and position tracking.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

import ccxt.async_support as ccxt

from .adapter import BrokerAdapter, Order, Position, Fill


logger = logging.getLogger(__name__)


class KrakenAdapter(BrokerAdapter):
    """
    Kraken Futures broker adapter using ccxt.

    Supports:
    - Order submission (MARKET, LIMIT)
    - Order cancellation
    - Position tracking
    - Fill notifications
    - Real-time bid/ask quotes
    - Market hours (crypto: 24/7)
    """

    def __init__(
        self,
        api_key: str,
        private_key: str,
        sandbox: bool = True,
        testnet: bool = True
    ):
        """
        Initialize Kraken adapter.

        Args:
            api_key: Kraken API key
            private_key: Kraken private key
            sandbox: Use paper trading environment
            testnet: Use testnet (demo) environment
        """
        self.api_key = api_key
        self.private_key = private_key
        self.sandbox = sandbox

        # Initialize ccxt exchange
        self.exchange = ccxt.krakenfutures({
            'apiKey': api_key,
            'secret': private_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True,
            }
        })

        # Set sandbox/testnet mode
        if sandbox or testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("Kraken adapter initialized in SANDBOX mode")
        else:
            logger.warning("Kraken adapter initialized in LIVE mode")

        # Internal state
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}
        self._fills: List[Fill] = []
        self._connected = False

        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # 100ms between requests

    async def connect(self) -> None:
        """Establish connection to Kraken."""
        try:
            await self.exchange.load_markets()
            balance = await self.exchange.fetch_balance()

            self._connected = True
            logger.info(f"Connected to Kraken Futures (Sandbox={self.sandbox})")
            logger.info(f"Account balance: {balance.get('total', {})}")

        except Exception as e:
            logger.error(f"Failed to connect to Kraken: {e}")
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Close connection to Kraken."""
        if self.exchange:
            await self.exchange.close()
        self._connected = False
        logger.info("Disconnected from Kraken")

    async def submit(self, order: Order) -> str:
        """
        Submit order to Kraken.

        Args:
            order: Order to submit

        Returns:
            broker_order_id: Kraken order ID
        """
        await self._rate_limit()

        try:
            # Map order type
            order_type = 'market' if order.order_type == 'MARKET' else 'limit'
            side = order.side.lower()  # 'buy' or 'sell'

            # Submit order via ccxt
            params = {}
            if order.order_type == 'LIMIT':
                result = await self.exchange.create_order(
                    symbol=order.symbol,
                    type=order_type,
                    side=side,
                    amount=order.quantity,
                    price=order.price,
                    params=params
                )
            else:
                result = await self.exchange.create_order(
                    symbol=order.symbol,
                    type=order_type,
                    side=side,
                    amount=order.quantity,
                    params=params
                )

            broker_order_id = result['id']

            # Update order tracking
            order.broker_order_id = broker_order_id
            order.status = 'SUBMITTED'
            order.submitted_at = datetime.now(timezone.utc)
            self._orders[broker_order_id] = order

            logger.info(f"Order submitted: {broker_order_id} | {order.symbol} {side} {order.quantity} @ {order.price or 'MKT'}")

            return broker_order_id

        except ccxt.NetworkError as e:
            logger.error(f"Network error submitting order: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error submitting order: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error submitting order: {e}")
            raise

    async def cancel(self, broker_order_id: str) -> bool:
        """
        Cancel order on Kraken.

        Args:
            broker_order_id: Kraken order ID

        Returns:
            success: True if canceled successfully
        """
        await self._rate_limit()

        try:
            order = self._orders.get(broker_order_id)
            if not order:
                logger.warning(f"Order {broker_order_id} not found in cache")
                return False

            result = await self.exchange.cancel_order(
                id=broker_order_id,
                symbol=order.symbol
            )

            order.status = 'CANCELED'
            logger.info(f"Order canceled: {broker_order_id}")

            return True

        except ccxt.OrderNotFound:
            logger.warning(f"Order {broker_order_id} not found on exchange")
            return False
        except Exception as e:
            logger.error(f"Error canceling order {broker_order_id}: {e}")
            return False

    async def modify(self, broker_order_id: str, new_price: Optional[float] = None, new_quantity: Optional[int] = None) -> bool:
        """
        Modify order on Kraken.

        Note: Kraken doesn't support order modification directly.
        This will cancel and re-submit as a new order.

        Args:
            broker_order_id: Kraken order ID
            new_price: New limit price
            new_quantity: New quantity

        Returns:
            success: True if modified successfully
        """
        await self._rate_limit()

        try:
            order = self._orders.get(broker_order_id)
            if not order:
                logger.warning(f"Order {broker_order_id} not found")
                return False

            # Cancel existing order
            await self.cancel(broker_order_id)

            # Create modified order
            modified_order = Order(
                symbol=order.symbol,
                side=order.side,
                quantity=new_quantity or order.quantity,
                order_type=order.order_type,
                price=new_price or order.price,
                stop_price=order.stop_price,
                time_in_force=order.time_in_force
            )

            # Submit new order
            new_id = await self.submit(modified_order)
            logger.info(f"Order modified: {broker_order_id} -> {new_id}")

            return True

        except Exception as e:
            logger.error(f"Error modifying order {broker_order_id}: {e}")
            return False

    async def get_orders(self) -> List[Order]:
        """Get all open orders from Kraken."""
        await self._rate_limit()

        try:
            open_orders = await self.exchange.fetch_open_orders()

            orders = []
            for order_data in open_orders:
                order = self._parse_order(order_data)
                orders.append(order)
                self._orders[order.broker_order_id] = order

            return orders

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []

    async def get_positions(self) -> List[Position]:
        """Get all open positions from Kraken."""
        await self._rate_limit()

        try:
            positions_data = await self.exchange.fetch_positions()

            positions = []
            for pos_data in positions_data:
                # Only include positions with non-zero size
                if abs(float(pos_data.get('contracts', 0))) > 0:
                    position = self._parse_position(pos_data)
                    positions.append(position)
                    self._positions[position.symbol] = position

            return positions

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    async def get_fills(self, since: Optional[datetime] = None) -> List[Fill]:
        """
        Get fills from Kraken.

        Args:
            since: Only return fills after this timestamp

        Returns:
            fills: List of fills
        """
        await self._rate_limit()

        try:
            # Fetch trades (fills)
            since_ms = int(since.timestamp() * 1000) if since else None
            trades = await self.exchange.fetch_my_trades(since=since_ms)

            fills = []
            for trade in trades:
                fill = self._parse_fill(trade)
                fills.append(fill)

                # Track in cache
                if fill not in self._fills:
                    self._fills.append(fill)

            return fills

        except Exception as e:
            logger.error(f"Error fetching fills: {e}")
            return []

    async def get_bid_ask(self, symbol: str) -> Tuple[float, float]:
        """
        Get current bid/ask prices for symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USD:USD')

        Returns:
            (bid, ask): Current bid and ask prices
        """
        await self._rate_limit()

        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            bid = float(ticker['bid'])
            ask = float(ticker['ask'])
            return (bid, ask)

        except Exception as e:
            logger.error(f"Error fetching bid/ask for {symbol}: {e}")
            # Return last known or raise
            raise

    def is_market_open(self, symbol: str) -> bool:
        """
        Check if market is open for symbol.

        Crypto markets are 24/7.
        """
        return True  # Kraken Futures trades 24/7

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time

        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    def _parse_order(self, order_data: dict) -> Order:
        """Parse ccxt order data into Order object."""
        return Order(
            symbol=order_data['symbol'],
            side='BUY' if order_data['side'] == 'buy' else 'SELL',
            quantity=int(order_data['amount']),
            order_type='LIMIT' if order_data['type'] == 'limit' else 'MARKET',
            price=order_data.get('price'),
            broker_order_id=order_data['id'],
            status=self._map_order_status(order_data['status']),
            submitted_at=datetime.fromtimestamp(order_data['timestamp'] / 1000, tz=timezone.utc) if order_data.get('timestamp') else None
        )

    def _parse_position(self, pos_data: dict) -> Position:
        """Parse ccxt position data into Position object."""
        contracts = float(pos_data.get('contracts', 0))
        side = 'LONG' if contracts > 0 else 'SHORT'

        return Position(
            symbol=pos_data['symbol'],
            side=side,
            quantity=abs(int(contracts)),
            entry_price=float(pos_data.get('entryPrice', 0)),
            current_price=float(pos_data.get('markPrice', 0)),
            unrealized_pnl=float(pos_data.get('unrealizedPnl', 0))
        )

    def _parse_fill(self, trade_data: dict) -> Fill:
        """Parse ccxt trade data into Fill object."""
        return Fill(
            broker_order_id=trade_data['order'],
            fill_id=trade_data['id'],
            symbol=trade_data['symbol'],
            side='BUY' if trade_data['side'] == 'buy' else 'SELL',
            quantity=int(trade_data['amount']),
            price=float(trade_data['price']),
            timestamp=datetime.fromtimestamp(trade_data['timestamp'] / 1000, tz=timezone.utc),
            fee=float(trade_data.get('fee', {}).get('cost', 0))
        )

    @staticmethod
    def _map_order_status(ccxt_status: str) -> str:
        """Map ccxt order status to internal status."""
        mapping = {
            'open': 'SUBMITTED',
            'closed': 'FILLED',
            'canceled': 'CANCELED',
            'expired': 'CANCELED',
            'rejected': 'REJECTED'
        }
        return mapping.get(ccxt_status, 'UNKNOWN')
