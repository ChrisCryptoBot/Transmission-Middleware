"""
Database Schema for Transmission™

SQLite schema for MVP (can migrate to PostgreSQL later).
Handles:
- Trade journal
- Performance metrics
- System state
- User configuration
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class Database:
    """
    Database manager for Transmission system.
    
    Uses SQLite for MVP, designed to migrate to PostgreSQL + TimescaleDB later.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database (default: data/transmission.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "transmission.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        
        self._create_schema()
    
    def _create_schema(self) -> None:
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # Trade Journal (Complete schema from Product_Concept.txt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Identifiers
                timestamp_entry DATETIME NOT NULL,
                timestamp_exit DATETIME,

                -- Asset & Strategy
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,  -- "Long" or "Short"
                strategy_used TEXT NOT NULL,
                regime_at_entry TEXT,
                timeframe TEXT DEFAULT '15m',

                -- Gear State (Transmission visualization)
                gear_at_entry TEXT,  -- P/R/N/D/L
                gear_at_exit TEXT,   -- P/R/N/D/L
                gear_shift_reason_entry TEXT,
                
                -- Prices
                entry_price REAL NOT NULL,
                exit_price REAL,
                stop_loss_price REAL NOT NULL,
                take_profit_price REAL,
                
                -- Position
                position_size INTEGER NOT NULL,  -- Contracts
                portfolio_equity_at_entry REAL,
                
                -- Execution
                entry_execution_latency_ms REAL,
                exit_execution_latency_ms REAL,
                entry_slippage_ticks REAL DEFAULT 0.0,
                exit_slippage_ticks REAL DEFAULT 0.0,
                execution_quality_score REAL,  -- 0-1
                order_type_entry TEXT,  -- "Limit" or "Market"
                order_type_exit TEXT,
                
                -- Results
                holding_duration_minutes REAL,
                exit_reason TEXT,  -- "Target", "Stop", "Time", "Regime_Shift", "Manual"
                pl_amount_gross REAL,
                pl_amount_net REAL,
                pl_percentage REAL,
                result_r REAL,  -- In R multiples
                fees_paid REAL DEFAULT 0.0,
                win_loss TEXT,  -- "Win", "Loss", "Breakeven"
                
                -- Risk metrics
                risk_reward_ratio REAL,
                mae REAL,  -- Maximum Adverse Excursion
                mfe REAL,  -- Maximum Favorable Excursion
                stop_distance_points REAL,
                
                -- Market conditions at entry
                volatility_at_entry REAL,  -- ATR
                volume_at_entry INTEGER,
                vwap_at_entry REAL,
                entry_vwap_distance_pct REAL,
                
                -- Technical
                technical_signals_confluence INTEGER,  -- Count of aligned signals
                adx_at_entry REAL,
                vwap_slope_at_entry REAL,
                
                -- Strategy specific
                strategy_confidence_score REAL,  -- 0-1
                trade_success_probability REAL,  -- Pre-trade estimate
                
                -- Multi-timeframe
                tf_alignment_score REAL,  -- 0-1
                
                -- Costs
                spread_ticks_at_entry REAL,
                liquidity_quality_score REAL,  -- 0-1
                
                -- Account (for multi-account)
                account_id TEXT,
                dll_at_entry REAL,
                dll_remaining_after REAL,
                
                -- Mental/psychological
                mental_state_pre_trade INTEGER,  -- 1-5
                rule_breaks INTEGER DEFAULT 0,
                
                -- Notes
                trade_trigger_signal TEXT,
                notes TEXT
            )
        """)
        
        # Performance Metrics (rolling windows)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                window_trades INTEGER NOT NULL,
                profit_factor REAL,
                expected_r REAL,
                win_rate REAL,
                win_rate_wilson_lb REAL,
                max_drawdown_r REAL,
                current_drawdown_r REAL,
                costs_pct REAL,
                total_trades INTEGER,
                total_wins INTEGER,
                total_losses INTEGER,
                avg_win_r REAL,
                avg_loss_r REAL
            )
        """)
        
        # System State
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                system_state TEXT NOT NULL,
                current_regime TEXT,
                active_strategy TEXT,
                daily_pnl_r REAL,
                weekly_pnl_r REAL,
                current_r REAL,
                consecutive_red_days INTEGER
            )
        """)
        
        # Market Data Cache (for backtesting/analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                bar_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                vwap REAL,
                adx REAL,
                atr REAL,
                regime TEXT,
                UNIQUE(timestamp, symbol, timeframe)
            )
        """)
        
        # Risk State (already in risk_governor, but centralized here)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_state (
                key TEXT PRIMARY KEY,
                value REAL,
                updated_at TIMESTAMP
            )
        """)
        
        # Daily P&L History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_pnl (
                date DATE PRIMARY KEY,
                pnl_r REAL,
                is_red_day INTEGER,
                trades_count INTEGER
            )
        """)

        # Gear Shifts (Transmission learning loop)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gear_shifts (
                shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                from_gear TEXT NOT NULL,
                to_gear TEXT NOT NULL,
                reason TEXT NOT NULL,

                -- Context snapshot at shift
                daily_r REAL,
                weekly_r REAL,
                consecutive_losses INTEGER,
                current_drawdown REAL,
                regime TEXT,
                volatility_percentile REAL,
                mental_state INTEGER,
                dll_remaining REAL,
                tripwire_active INTEGER,
                in_trading_session INTEGER,
                news_blackout_active INTEGER,
                kill_switch_active INTEGER,
                positions_open INTEGER
            )
        """)
        
        # Create indexes for performance (optimized queries)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp_entry 
            ON trades(timestamp_entry)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp_exit 
            ON trades(timestamp_exit)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_strategy 
            ON trades(strategy_used)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_regime 
            ON trades(regime_at_entry)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_symbol 
            ON trades(symbol)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_win_loss 
            ON trades(win_loss)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_exit_reason 
            ON trades(exit_reason)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_timestamp 
            ON market_data(timestamp, symbol, timeframe)
        """)
        
        # Composite index for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_strategy_regime
            ON trades(strategy_used, regime_at_entry)
        """)

        # Gear state indexes for learning dashboard
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_gear_at_entry
            ON trades(gear_at_entry)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_gear_at_exit
            ON trades(gear_at_exit)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gear_shifts_timestamp
            ON gear_shifts(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gear_shifts_to_gear
            ON gear_shifts(to_gear)
        """)

        # Composite indexes for performance-by-gear queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_gear_regime
            ON trades(gear_at_entry, regime_at_entry)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_gear_win_loss
            ON trades(gear_at_entry, win_loss)
        """)

        self.conn.commit()
        logger.info("Database schema created/verified")
    
    def log_trade(
        self,
        symbol: str,
        trade_type: str,  # "Long" or "Short"
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        position_size: int,  # Contracts
        strategy_used: str,
        regime_at_entry: str,
        portfolio_equity_at_entry: Optional[float] = None,
        vwap_at_entry: Optional[float] = None,
        adx_at_entry: Optional[float] = None,
        volatility_at_entry: Optional[float] = None,
        volume_at_entry: Optional[int] = None,
        spread_ticks_at_entry: Optional[float] = None,
        strategy_confidence_score: float = 0.0,
        trade_trigger_signal: Optional[str] = None,
        account_id: Optional[str] = None,
        notes: Optional[str] = None,
        gear_at_entry: Optional[str] = None,
        gear_shift_reason_entry: Optional[str] = None
    ) -> int:
        """
        Log a new trade entry.
        
        Returns:
            trade_id of created trade
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (
                timestamp_entry, symbol, trade_type, entry_price, stop_loss_price,
                take_profit_price, position_size, portfolio_equity_at_entry,
                strategy_used, regime_at_entry, vwap_at_entry, adx_at_entry,
                volatility_at_entry, volume_at_entry, spread_ticks_at_entry,
                strategy_confidence_score, trade_trigger_signal, account_id, notes,
                gear_at_entry, gear_shift_reason_entry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            symbol,
            trade_type,
            entry_price,
            stop_loss_price,
            take_profit_price,
            position_size,
            portfolio_equity_at_entry,
            strategy_used,
            regime_at_entry,
            vwap_at_entry,
            adx_at_entry,
            volatility_at_entry,
            volume_at_entry,
            spread_ticks_at_entry,
            strategy_confidence_score,
            trade_trigger_signal,
            account_id,
            notes,
            gear_at_entry,
            gear_shift_reason_entry
        ))
        
        trade_id = cursor.lastrowid
        self.conn.commit()
        
        logger.info(f"Trade logged: {trade_id} - {trade_type} {position_size} {symbol} @ {entry_price}")
        
        return trade_id
    
    def update_trade_exit(
        self,
        trade_id: int,
        exit_price: float,
        exit_reason: str,
        pl_amount_gross: float,
        result_r: float,
        fees_paid: float,
        holding_duration_minutes: float,
        entry_slippage_ticks: float = 0.0,
        exit_slippage_ticks: float = 0.0,
        exit_execution_latency_ms: Optional[float] = None,
        order_type_exit: Optional[str] = None,
        mae: Optional[float] = None,
        mfe: Optional[float] = None,
        win_loss: Optional[str] = None,
        dll_remaining_after: Optional[float] = None,
        gear_at_exit: Optional[str] = None
    ) -> None:
        """Update trade with exit information"""
        cursor = self.conn.cursor()
        
        pl_amount_net = pl_amount_gross - fees_paid
        
        # Calculate P&L percentage (need entry price from trade)
        cursor.execute("SELECT entry_price, portfolio_equity_at_entry FROM trades WHERE trade_id = ?", (trade_id,))
        trade_data = cursor.fetchone()
        if trade_data:
            entry_price, equity = trade_data
            if equity and equity > 0:
                pl_percentage = (pl_amount_net / equity) * 100
            else:
                pl_percentage = 0.0
        else:
            pl_percentage = 0.0
        
        cursor.execute("""
            UPDATE trades SET
                timestamp_exit = ?,
                exit_price = ?,
                exit_reason = ?,
                pl_amount_gross = ?,
                pl_amount_net = ?,
                pl_percentage = ?,
                result_r = ?,
                fees_paid = ?,
                holding_duration_minutes = ?,
                entry_slippage_ticks = ?,
                exit_slippage_ticks = ?,
                exit_execution_latency_ms = ?,
                order_type_exit = ?,
                mae = ?,
                mfe = ?,
                win_loss = ?,
                dll_remaining_after = ?,
                gear_at_exit = ?
            WHERE trade_id = ?
        """, (
            datetime.now(),
            exit_price,
            exit_reason,
            pl_amount_gross,
            pl_amount_net,
            pl_percentage,
            result_r,
            fees_paid,
            holding_duration_minutes,
            entry_slippage_ticks,
            exit_slippage_ticks,
            exit_execution_latency_ms,
            order_type_exit,
            mae,
            mfe,
            win_loss,
            dll_remaining_after,
            gear_at_exit,
            trade_id
        ))
        
        self.conn.commit()
        logger.info(f"Trade {trade_id} closed: {exit_reason}, P&L: {result_r:+.2f}R")
    
    def get_recent_trades(self, limit: int = 20) -> list:
        """Get recent trades"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            ORDER BY timestamp_entry DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_trades_for_metrics(self, window: int = 20) -> list:
        """Get trades for performance metrics calculation"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            WHERE timestamp_exit IS NOT NULL
            ORDER BY timestamp_exit DESC
            LIMIT ?
        """, (window,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_performance_metrics(
        self,
        window_trades: int,
        profit_factor: float,
        expected_r: float,
        win_rate: float,
        win_rate_wilson_lb: float,
        max_drawdown_r: float,
        current_drawdown_r: float,
        costs_pct: float,
        total_trades: int,
        total_wins: int,
        total_losses: int,
        avg_win_r: float,
        avg_loss_r: float
    ) -> None:
        """Save performance metrics snapshot"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics (
                timestamp, window_trades, profit_factor, expected_r, win_rate,
                win_rate_wilson_lb, max_drawdown_r, current_drawdown_r, costs_pct,
                total_trades, total_wins, total_losses, avg_win_r, avg_loss_r
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            window_trades,
            profit_factor,
            expected_r,
            win_rate,
            win_rate_wilson_lb,
            max_drawdown_r,
            current_drawdown_r,
            costs_pct,
            total_trades,
            total_wins,
            total_losses,
            avg_win_r,
            avg_loss_r
        ))
        
        self.conn.commit()
    
    def save_system_state(
        self,
        system_state: str,
        current_regime: Optional[str] = None,
        active_strategy: Optional[str] = None,
        daily_pnl_r: float = 0.0,
        weekly_pnl_r: float = 0.0,
        current_r: float = 5.0,
        consecutive_red_days: int = 0
    ) -> None:
        """Save system state snapshot"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO system_state (
                timestamp, system_state, current_regime, active_strategy,
                daily_pnl_r, weekly_pnl_r, current_r, consecutive_red_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            system_state,
            current_regime,
            active_strategy,
            daily_pnl_r,
            weekly_pnl_r,
            current_r,
            consecutive_red_days
        ))

        self.conn.commit()

    def log_gear_shift(
        self,
        from_gear: str,
        to_gear: str,
        reason: str,
        daily_r: float = 0.0,
        weekly_r: float = 0.0,
        consecutive_losses: int = 0,
        current_drawdown: float = 0.0,
        regime: Optional[str] = None,
        volatility_percentile: float = 0.0,
        mental_state: int = 3,
        dll_remaining: float = 2.0,
        tripwire_active: bool = False,
        in_trading_session: bool = True,
        news_blackout_active: bool = False,
        kill_switch_active: bool = False,
        positions_open: int = 0
    ) -> int:
        """
        Log a gear shift event with full context snapshot.

        Returns:
            shift_id of created gear shift
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO gear_shifts (
                timestamp, from_gear, to_gear, reason,
                daily_r, weekly_r, consecutive_losses, current_drawdown,
                regime, volatility_percentile, mental_state, dll_remaining,
                tripwire_active, in_trading_session, news_blackout_active,
                kill_switch_active, positions_open
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            from_gear,
            to_gear,
            reason,
            daily_r,
            weekly_r,
            consecutive_losses,
            current_drawdown,
            regime,
            volatility_percentile,
            mental_state,
            dll_remaining,
            1 if tripwire_active else 0,
            1 if in_trading_session else 0,
            1 if news_blackout_active else 0,
            1 if kill_switch_active else 0,
            positions_open
        ))

        shift_id = cursor.lastrowid
        self.conn.commit()

        logger.info(f"Gear shift logged: {from_gear} → {to_gear} (Reason: {reason})")

        return shift_id

    def get_recent_gear_shifts(self, limit: int = 20) -> list:
        """Get recent gear shifts for UI display"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM gear_shifts
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_performance_by_gear(self) -> dict:
        """
        Get performance metrics broken down by gear.

        Returns dict with structure:
        {
            "P": {"trades": 0, "win_rate": 0.0, "profit_factor": 0.0, ...},
            "R": {"trades": 5, "win_rate": 0.6, "profit_factor": 1.5, ...},
            ...
        }
        """
        cursor = self.conn.cursor()

        gears = ['P', 'R', 'N', 'D', 'L']
        results = {}

        for gear in gears:
            cursor.execute("""
                SELECT
                    COUNT(*) as trades,
                    SUM(CASE WHEN win_loss = 'Win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN win_loss = 'Loss' THEN 1 ELSE 0 END) as losses,
                    AVG(CASE WHEN win_loss = 'Win' THEN result_r ELSE NULL END) as avg_win_r,
                    AVG(CASE WHEN win_loss = 'Loss' THEN result_r ELSE NULL END) as avg_loss_r,
                    SUM(result_r) as total_r
                FROM trades
                WHERE gear_at_entry = ? AND timestamp_exit IS NOT NULL
            """, (gear,))

            row = cursor.fetchone()
            if row:
                trades = row[0] or 0
                wins = row[1] or 0
                losses = row[2] or 0
                avg_win_r = row[3] or 0.0
                avg_loss_r = row[4] or 0.0
                total_r = row[5] or 0.0

                win_rate = (wins / trades) if trades > 0 else 0.0

                # Profit factor = (wins * avg_win_r) / (losses * abs(avg_loss_r))
                gross_wins = wins * avg_win_r if wins > 0 else 0.0
                gross_losses = abs(losses * avg_loss_r) if losses > 0 else 0.0
                profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else 0.0

                results[gear] = {
                    "trades": trades,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "avg_win_r": avg_win_r,
                    "avg_loss_r": avg_loss_r,
                    "total_r": total_r,
                    "profit_factor": profit_factor
                }
            else:
                results[gear] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.0,
                    "avg_win_r": 0.0,
                    "avg_loss_r": 0.0,
                    "total_r": 0.0,
                    "profit_factor": 0.0
                }

        return results

    def get_performance_by_gear_and_regime(self) -> dict:
        """
        Get performance metrics broken down by gear AND regime.

        Returns dict with structure:
        {
            "D": {
                "TREND": {"trades": 10, "win_rate": 0.7, ...},
                "RANGE": {"trades": 8, "win_rate": 0.625, ...},
                ...
            },
            ...
        }
        """
        cursor = self.conn.cursor()

        gears = ['P', 'R', 'N', 'D', 'L']
        regimes = ['TREND', 'RANGE', 'VOLATILE']
        results = {}

        for gear in gears:
            results[gear] = {}
            for regime in regimes:
                cursor.execute("""
                    SELECT
                        COUNT(*) as trades,
                        SUM(CASE WHEN win_loss = 'Win' THEN 1 ELSE 0 END) as wins,
                        SUM(result_r) as total_r
                    FROM trades
                    WHERE gear_at_entry = ? AND regime_at_entry = ? AND timestamp_exit IS NOT NULL
                """, (gear, regime))

                row = cursor.fetchone()
                if row:
                    trades = row[0] or 0
                    wins = row[1] or 0
                    total_r = row[2] or 0.0

                    win_rate = (wins / trades) if trades > 0 else 0.0

                    results[gear][regime] = {
                        "trades": trades,
                        "wins": wins,
                        "win_rate": win_rate,
                        "total_r": total_r
                    }
                else:
                    results[gear][regime] = {
                        "trades": 0,
                        "wins": 0,
                        "win_rate": 0.0,
                        "total_r": 0.0
                    }

        return results

    def close(self) -> None:
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

