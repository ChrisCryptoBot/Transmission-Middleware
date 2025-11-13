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

from .adapter import BrokerAdapter, OrderReq, OrderResp, Position, Fill


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
        self._orders: Dict[str, OrderResp] = {}
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

    async def submit(self, order: OrderReq) -> OrderResp:
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
            order_type = 'market' if order['order_type'] == 'MKT' else 'limit'
            side = order['side'].lower()  # 'buy' or 'sell'

            # Submit order via ccxt
            params = {}
            if order['order_type'] == 'LMT':
                result = await self.exchange.create_order(
                    symbol=order['symbol'],
                    type=order_type,
                    side=side,
                    amount=order['qty'],
                    price=order.get('limit_price'),
                    params=params
                )
            else:
                result = await self.exchange.create_order(
                    symbol=order['symbol'],
                    type=order_type,
                    side=side,
                    amount=order['qty'],
                    params=params
                )

            broker_order_id = result['id']
            client_order_id = order.get('client_order_id') or f"kraken_{broker_order_id}"

            # Create order response
            order_resp: OrderResp = {
                'client_order_id': client_order_id,
                'broker_order_id': broker_order_id,
                'status': 'ACCEPTED',
                'reason': None,
                'timestamp': datetime.now(timezone.utc).timestamp()
            }

            # Update order tracking
            self._orders[broker_order_id] = order_resp

            logger.info(f"Order submitted: {broker_order_id} | {order['symbol']} {side} {order['qty']} @ {order.get('limit_price') or 'MKT'}")

            return order_resp

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
                # Try to cancel anyway - might be on exchange but not in cache
                logger.warning(f"Order {broker_order_id} not found in cache, attempting cancel anyway")
                try:
                    await self.exchange.cancel_order(id=broker_order_id)
                    return True
                except:
                    return False

            # Get symbol from order if available, otherwise try to fetch from exchange
            symbol = None  # We'll need to get this from somewhere
            result = await self.exchange.cancel_order(id=broker_order_id)

            # Update order status in cache
            if order:
                order['status'] = 'CANCELED'
            logger.info(f"Order canceled: {broker_order_id}")

            return True

        except ccxt.OrderNotFound:
            logger.warning(f"Order {broker_order_id} not found on exchange")
            return False
        except Exception as e:
            logger.error(f"Error canceling order {broker_order_id}: {e}")
            return False

    # Note: modify() method removed - not part of BrokerAdapter protocol
    # If order modification is needed, cancel and resubmit using the protocol methods

    async def get_open_orders(self) -> List[OrderResp]:
        """Get all open orders from Kraken."""
        await self._rate_limit()

        try:
            open_orders = await self.exchange.fetch_open_orders()

            orders = []
            for order_data in open_orders:
                order = self._parse_order(order_data)
                orders.append(order)
                self._orders[order['broker_order_id']] = order

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

    def _parse_order(self, order_data: dict) -> OrderResp:
        """Parse ccxt order data into OrderResp object."""
        timestamp = order_data.get('timestamp')
        if timestamp:
            timestamp_float = timestamp / 1000 if timestamp > 1e10 else timestamp
        else:
            timestamp_float = datetime.now(timezone.utc).timestamp()
        
        status_str = order_data.get('status', 'open')
        # Map ccxt status to our OrderStatus
        status_map = {
            'open': 'ACCEPTED',
            'closed': 'FILLED',
            'canceled': 'CANCELED',
            'expired': 'CANCELED'
        }
        mapped_status = status_map.get(status_str.lower(), 'ACCEPTED')
        
        return {
            'client_order_id': order_data.get('clientOrderId') or f"kraken_{order_data['id']}",
            'broker_order_id': str(order_data['id']),
            'status': mapped_status,
            'reason': None,
            'timestamp': timestamp_float
        }

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
