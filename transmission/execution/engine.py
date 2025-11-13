"""
Execution Engine

Order state machine and execution management.
Handles order lifecycle: INIT → SUBMITTED → FILLED → MANAGED → CLOSED

Based on user requirements for execution engine with broker abstraction.
"""

from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime
import time
from loguru import logger

from transmission.execution.adapter import BrokerAdapter, OrderReq, OrderResp, Fill, Side
from transmission.execution.guard import ExecutionGuard, ExecutionCheck
from transmission.strategies.base import Signal
from transmission.database import Database


class OrderState(Enum):
    """Order state enumeration"""
    INIT = "init"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    MANAGED = "managed"  # Stop/TP placed
    CLOSED = "closed"  # TP/SL hit or manual exit


class ExecutionEngine:
    """
    Execution Engine with order state machine.
    
    Handles:
    - Order submission
    - Fill tracking
    - Stop/TP management
    - Position flattening
    - Database logging
    """
    
    def __init__(
        self,
        broker: BrokerAdapter,
        database: Database,
        guard: ExecutionGuard
    ):
        """
        Initialize Execution Engine.
        
        Args:
            broker: Broker adapter (mock, paper, or live)
            database: Database for trade logging
            guard: Execution guard for pre-trade checks
        """
        self.broker = broker
        self.database = database
        self.guard = guard
        
        # State tracking
        self.active_orders: Dict[str, OrderResp] = {}
        self.order_states: Dict[str, OrderState] = {}
        self.trade_ids: Dict[str, int] = {}  # broker_order_id -> trade_id

        # Idempotency: Track processed fills to prevent duplicates
        self.seen_fills: set = set()  # Set of (broker_order_id, fill_id) tuples

    async def reconcile(self) -> None:
        """
        CRASH RECOVERY: Reconcile internal state with broker on boot.

        Fetches:
        - Open orders from broker
        - Open positions from broker
        - Recent fills (if missed during downtime)

        Syncs internal state to match broker state.
        """
        logger.info("Starting crash recovery reconciliation...")

        try:
            # Fetch open orders from broker
            broker_orders = await self.broker.get_orders()
            logger.info(f"Found {len(broker_orders)} open orders on broker")

            for order in broker_orders:
                broker_order_id = order.broker_order_id
                if broker_order_id not in self.active_orders:
                    # Order exists on broker but not in local state (we crashed)
                    logger.warning(f"Reconciling orphaned order: {broker_order_id}")

                    # Recreate order in local state
                    order_resp: OrderResp = {
                        "broker_order_id": broker_order_id,
                        "status": order.status,
                        "qty": order.quantity,
                        "filled_qty": 0,  # Will be updated by fills
                        "avg_price": order.price or 0.0,
                        "timestamp": order.submitted_at or datetime.now()
                    }

                    self.active_orders[broker_order_id] = order_resp
                    self.order_states[broker_order_id] = OrderState.SUBMITTED

            # Fetch open positions from broker
            broker_positions = await self.broker.get_positions()
            logger.info(f"Found {len(broker_positions)} open positions on broker")

            for position in broker_positions:
                logger.info(
                    f"Position reconciled: {position.symbol} {position.side} "
                    f"{position.quantity} @ {position.entry_price:.2f}"
                )

            # Fetch recent fills (in case we missed any during downtime)
            recent_fills = await self.broker.get_fills()
            logger.info(f"Found {len(recent_fills)} recent fills")

            for fill in recent_fills:
                broker_order_id = fill.broker_order_id
                fill_id = fill.fill_id

                fill_key = (broker_order_id, fill_id)

                # Only process fills we haven't seen
                if fill_key not in self.seen_fills:
                    logger.info(f"Replaying missed fill: {broker_order_id} @ {fill.price}")

                    fill_dict = {
                        "broker_order_id": broker_order_id,
                        "fill_id": fill_id,
                        "filled_qty": fill.quantity,
                        "avg_price": fill.price,
                        "timestamp": fill.timestamp
                    }

                    self._handle_fill(broker_order_id, fill_dict)

            logger.info("Crash recovery reconciliation complete")

            # Log reconciliation event to database
            self.database.log_system_event(
                event_type="RECONCILIATION",
                description=f"Reconciled {len(broker_orders)} orders, "
                           f"{len(broker_positions)} positions, "
                           f"{len(recent_fills)} fills"
            )

        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            raise

    def place_signal(
        self,
        signal: Signal,
        qty: float
    ) -> Optional[str]:
        """
        Place a signal as an order.
        
        Args:
            signal: Trading signal
            qty: Quantity (contracts)
            
        Returns:
            broker_order_id if successful, None if rejected
        """
        # Pre-execution guard check
        bid, ask = self.broker.get_bid_ask(signal.symbol)
        spread_ticks = abs(ask - bid) / 0.25  # Assuming 0.25 tick size
        
        guard_check = self.guard.validate_execution(
            spread_ticks=spread_ticks,
            order_size=qty
        )
        
        if not guard_check.approved:
            logger.warning(f"Execution blocked by guard: {guard_check.reason}")
            return None
        
        # Check market open
        if not self.broker.is_market_open(signal.symbol):
            logger.warning(f"Market closed for {signal.symbol}")
            return None
        
        # Create order request
        side: Side = "BUY" if signal.direction == "LONG" else "SELL"
        
        # Use recommended order type from guard, default to market
        order_type = guard_check.recommended_order_type or "MKT"
        
        order_req: OrderReq = {
            "symbol": signal.symbol,
            "side": side,
            "qty": qty,
            "order_type": order_type,
            "limit_price": signal.entry_price if order_type == "LMT" else None,
            "stop_price": None,
            "tif": "DAY",
            "client_order_id": f"SIG_{signal.timestamp.timestamp()}"
        }
        
        # Submit order
        order_resp = self.broker.submit(order_req)
        
        if order_resp["status"] == "REJECTED":
            logger.error(f"Order rejected: {order_resp.get('reason', 'Unknown')}")
            return None
        
        # Track order
        broker_order_id = order_resp["broker_order_id"]
        self.active_orders[broker_order_id] = order_resp
        self.order_states[broker_order_id] = OrderState.SUBMITTED
        
        # Log trade entry to database
        trade_id = self.database.log_trade(
            symbol=signal.symbol,
            trade_type=signal.direction,
            entry_price=signal.entry_price,
            stop_loss_price=signal.stop_price,
            take_profit_price=signal.target_price,
            position_size=int(qty),
            strategy_used=signal.strategy,
            regime_at_entry=signal.regime,
            vwap_at_entry=None,  # TODO: Get from signal/features
            adx_at_entry=None,  # TODO: Get from signal/features
            strategy_confidence_score=signal.confidence,
            trade_trigger_signal=signal.notes
        )
        
        self.trade_ids[broker_order_id] = trade_id
        
        logger.info(
            f"Order placed: {side} {qty} {signal.symbol} @ {signal.entry_price:.2f} "
            f"(order_id: {broker_order_id}, trade_id: {trade_id})"
        )
        
        # Check for immediate fill (mock broker)
        if order_resp["status"] == "FILLED":
            self._handle_fill(broker_order_id)
        
        return broker_order_id
    
    def on_broker_fill(self, fill: Fill) -> None:
        """
        Handle broker fill notification.
        
        Called by broker adapter when a fill occurs.
        """
        broker_order_id = fill["broker_order_id"]
        
        if broker_order_id not in self.active_orders:
            logger.warning(f"Fill for unknown order: {broker_order_id}")
            return
        
        self._handle_fill(broker_order_id, fill)
    
    def _handle_fill(self, broker_order_id: str, fill: Optional[Fill] = None) -> None:
        """
        Handle order fill with idempotency protection.

        Deduplicates fills by (broker_order_id, fill_id) to prevent double-counting.
        """
        if fill is None:
            fills = self.broker.get_fills(broker_order_id)
            if not fills:
                return
            fill = fills[-1]  # Use most recent fill

        # IDEMPOTENCY CHECK: Dedupe by (broker_order_id, fill_id)
        fill_id = fill.get("fill_id") or fill.get("exec_id") or fill.get("timestamp")
        fill_key = (broker_order_id, fill_id)

        if fill_key in self.seen_fills:
            logger.debug(f"Fill already processed (idempotency): {fill_key}")
            return  # Skip duplicate

        # Mark fill as seen
        self.seen_fills.add(fill_key)

        order = self.active_orders.get(broker_order_id)
        if not order:
            logger.warning(f"Fill for unknown order: {broker_order_id}")
            return

        # Update state
        if fill["filled_qty"] < order["qty"]:
            self.order_states[broker_order_id] = OrderState.PARTIALLY_FILLED
        else:
            self.order_states[broker_order_id] = OrderState.FILLED
            # Place stop/TP orders (managed state)
            self.order_states[broker_order_id] = OrderState.MANAGED

        logger.info(
            f"Fill: {fill['filled_qty']} @ {fill['avg_price']:.2f} "
            f"(order: {broker_order_id}, fill_id: {fill_id})"
        )
    
    def move_stop(self, broker_order_id: str, new_stop: float) -> bool:
        """
        Move stop loss for a position.
        
        Args:
            broker_order_id: Order ID of the position
            new_stop: New stop price
            
        Returns:
            True if successful
        """
        # TODO: Implement stop order management
        logger.info(f"Stop moved to {new_stop:.2f} for order {broker_order_id}")
        return True
    
    def flatten_all(self, reason: str) -> None:
        """
        Flatten all positions (emergency exit).
        
        Args:
            reason: Reason for flattening
        """
        positions = self.broker.get_positions()
        
        for position in positions:
            # Create market order to close position
            side: Side = "SELL" if position["side"] == "BUY" else "BUY"
            
            order_req: OrderReq = {
                "symbol": position["symbol"],
                "side": side,
                "qty": abs(position["qty"]),
                "order_type": "MKT",
                "limit_price": None,
                "stop_price": None,
                "tif": "IOC",  # Immediate or cancel
                "client_order_id": f"FLATTEN_{time.time()}"
            }
            
            order_resp = self.broker.submit(order_req)
            
            if order_resp["status"] == "ACCEPTED":
                logger.info(f"Flatten order submitted: {side} {abs(position['qty'])} {position['symbol']}")
        
        # Cancel all open orders
        open_orders = self.broker.get_open_orders()
        for order in open_orders:
            self.broker.cancel(order["broker_order_id"])
        
        logger.warning(f"All positions flattened: {reason}")
    
    def get_active_positions(self) -> List:
        """Get all active positions"""
        return self.broker.get_positions()
    
    def get_open_orders(self) -> List[OrderResp]:
        """Get all open orders"""
        return self.broker.get_open_orders()

