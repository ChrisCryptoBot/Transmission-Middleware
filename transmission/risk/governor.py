"""
Risk Governor Module

Enforces risk limits and manages position sizing:
- Daily loss limit (-2R)
- Weekly loss limit (-5R)
- Step-down logic (reduce $R on poor performance)
- Scale-up logic (increase $R on good performance)
- Performance-based adjustments

Based on Product_Concept.txt Section 1.4 and 1.5.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Literal
import sqlite3
from pathlib import Path
from loguru import logger


@dataclass
class TripwireResult:
    """Result of risk tripwire check"""
    can_trade: bool
    reason: str
    action: Literal['TRADE', 'FLAT', 'PAUSE']
    daily_pnl_r: float
    weekly_pnl_r: float
    consecutive_red_days: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for scaling decisions"""
    profit_factor: float  # Sum(wins) / abs(Sum(losses))
    expected_r: float  # Average R per trade
    win_rate: float  # Win rate (0.0 to 1.0)
    max_drawdown_r: float  # Maximum drawdown in R
    current_drawdown_r: float  # Current drawdown in R
    rule_breaks: int  # Number of rule violations
    total_trades: int  # Total number of trades


class RiskGovernor:
    """
    Manages risk limits and position sizing.
    
    Hard Limits:
    - Daily: -2R maximum loss
    - Weekly: -5R maximum loss
    - Red Days: 3 consecutive red days → pause
    
    Performance Governor:
    - Step-down: PF < 1.10 over 12 trades OR -4R drawdown → reduce $R by 30%
    - Scale-up: PF ≥ 1.30 AND E[R] ≥ 0.20 AND WR ≥ 50% AND MaxDD ≤ 3R → increase $R by 15%
    """
    
    def __init__(
        self,
        initial_r: float = 5.0,
        daily_limit_r: float = -2.0,
        weekly_limit_r: float = -5.0,
        max_red_days: int = 3,
        db_path: Optional[str] = None
    ):
        """
        Initialize Risk Governor.
        
        Args:
            initial_r: Starting risk per trade in dollars (default $5)
            daily_limit_r: Daily loss limit in R (default -2R)
            weekly_limit_r: Weekly loss limit in R (default -5R)
            max_red_days: Maximum consecutive red days before pause (default 3)
            db_path: Path to SQLite database for persistence (default: in-memory)
        """
        self.current_r = initial_r
        self.daily_limit_r = daily_limit_r
        self.weekly_limit_r = weekly_limit_r
        self.max_red_days = max_red_days
        
        # State tracking
        self.daily_pnl_r = 0.0
        self.weekly_pnl_r = 0.0
        self.consecutive_red_days = 0
        self.last_trade_date: Optional[datetime] = None
        self.week_start: Optional[datetime] = None
        
        # Database for persistence
        if db_path is None:
            db_path = ":memory:"
        self.db_path = db_path
        self._init_database()
        
        # Load state from database
        self._load_state()
    
    def _init_database(self) -> None:
        """Initialize SQLite database for state persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_state (
                key TEXT PRIMARY KEY,
                value REAL,
                updated_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_pnl (
                date DATE PRIMARY KEY,
                pnl_r REAL,
                is_red_day INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_state(self) -> None:
        """Load state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load current R
            cursor.execute("SELECT value FROM risk_state WHERE key = 'current_r'")
            result = cursor.fetchone()
            if result:
                self.current_r = result[0]
            
            # Load daily P&L
            today = datetime.now().date()
            cursor.execute(
                "SELECT pnl_r FROM daily_pnl WHERE date = ?",
                (today,)
            )
            result = cursor.fetchone()
            if result:
                self.daily_pnl_r = result[0]
            
            # Load weekly P&L
            if self.week_start is None:
                self.week_start = self._get_week_start()
            
            cursor.execute("""
                SELECT SUM(pnl_r) FROM daily_pnl 
                WHERE date >= ?
            """, (self.week_start.date(),))
            result = cursor.fetchone()
            if result and result[0] is not None:
                self.weekly_pnl_r = result[0]
            
            # Load consecutive red days
            cursor.execute("""
                SELECT COUNT(*) FROM daily_pnl
                WHERE is_red_day = 1
                ORDER BY date DESC
                LIMIT ?
            """, (self.max_red_days,))
            result = cursor.fetchone()
            if result:
                self.consecutive_red_days = result[0]
            
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to load risk state: {e}")
    
    def _save_state(self) -> None:
        """Save state to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save current R
            cursor.execute("""
                INSERT OR REPLACE INTO risk_state (key, value, updated_at)
                VALUES ('current_r', ?, ?)
            """, (self.current_r, datetime.now()))
            
            # Save daily P&L
            today = datetime.now().date()
            is_red = 1 if self.daily_pnl_r < 0 else 0
            cursor.execute("""
                INSERT OR REPLACE INTO daily_pnl (date, pnl_r, is_red_day)
                VALUES (?, ?, ?)
            """, (today, self.daily_pnl_r, is_red))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save risk state: {e}")
    
    def _get_week_start(self) -> datetime:
        """Get start of current week (Monday)"""
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def check_tripwires(self) -> TripwireResult:
        """
        Check if risk tripwires are triggered.
        
        Returns:
            TripwireResult with can_trade flag and reason
        """
        # Reset daily P&L if new day
        today = datetime.now().date()
        if self.last_trade_date is None or self.last_trade_date.date() != today:
            if self.last_trade_date is not None:
                # Check if previous day was red
                prev_date = self.last_trade_date.date()
                if self.daily_pnl_r < 0:
                    self.consecutive_red_days += 1
                else:
                    self.consecutive_red_days = 0
            
            # Reset for new day
            self.daily_pnl_r = 0.0
            self.last_trade_date = datetime.now()
            self._save_state()
        
        # Reset weekly P&L if new week
        week_start = self._get_week_start()
        if self.week_start is None or week_start > self.week_start:
            self.weekly_pnl_r = 0.0
            self.week_start = week_start
        
        # Check daily limit
        if self.daily_pnl_r <= self.daily_limit_r:
            return TripwireResult(
                can_trade=False,
                reason=f"Daily loss limit hit: {self.daily_pnl_r:.2f}R <= {self.daily_limit_r}R",
                action='FLAT',
                daily_pnl_r=self.daily_pnl_r,
                weekly_pnl_r=self.weekly_pnl_r,
                consecutive_red_days=self.consecutive_red_days
            )
        
        # Check weekly limit
        if self.weekly_pnl_r <= self.weekly_limit_r:
            return TripwireResult(
                can_trade=False,
                reason=f"Weekly loss limit hit: {self.weekly_pnl_r:.2f}R <= {self.weekly_limit_r}R",
                action='FLAT',
                daily_pnl_r=self.daily_pnl_r,
                weekly_pnl_r=self.weekly_pnl_r,
                consecutive_red_days=self.consecutive_red_days
            )
        
        # Check consecutive red days
        if self.consecutive_red_days >= self.max_red_days:
            return TripwireResult(
                can_trade=False,
                reason=f"{self.consecutive_red_days} consecutive red days (limit: {self.max_red_days})",
                action='PAUSE',
                daily_pnl_r=self.daily_pnl_r,
                weekly_pnl_r=self.weekly_pnl_r,
                consecutive_red_days=self.consecutive_red_days
            )
        
        return TripwireResult(
            can_trade=True,
            reason="All clear",
            action='TRADE',
            daily_pnl_r=self.daily_pnl_r,
            weekly_pnl_r=self.weekly_pnl_r,
            consecutive_red_days=self.consecutive_red_days
        )
    
    def record_trade(self, pnl_r: float) -> None:
        """
        Record a completed trade's P&L.
        
        Args:
            pnl_r: Profit/loss in R units
        """
        self.daily_pnl_r += pnl_r
        self.weekly_pnl_r += pnl_r
        self._save_state()
        
        logger.info(f"Trade recorded: {pnl_r:+.2f}R | Daily: {self.daily_pnl_r:+.2f}R | Weekly: {self.weekly_pnl_r:+.2f}R")
    
    def evaluate_scaling(self, metrics: PerformanceMetrics) -> float:
        """
        Evaluate if $R should be scaled up or down based on performance.
        
        Scale-up conditions (Section 1.4):
        - PF ≥ 1.30
        - E[R] ≥ 0.20
        - WR ≥ 50%
        - MaxDD ≤ 3R
        - Rule breaks = 0
        
        Step-down conditions (Section 1.5):
        - PF < 1.10 over 12 trades OR
        - Current drawdown <= -4R
        
        Args:
            metrics: PerformanceMetrics with recent performance data
            
        Returns:
            New $R value (adjusted or unchanged)
        """
        new_r = self.current_r
        
        # Step-down conditions
        if metrics.profit_factor < 1.10 or metrics.current_drawdown_r <= -4.0:
            new_r = self.current_r * 0.70  # Reduce by 30%
            logger.warning(
                f"Step-down triggered: PF={metrics.profit_factor:.2f}, "
                f"DD={metrics.current_drawdown_r:.2f}R → $R: ${self.current_r:.2f} → ${new_r:.2f}"
            )
        
        # Scale-up conditions (only if not stepping down)
        elif (metrics.profit_factor >= 1.30 and
              metrics.expected_r >= 0.20 and
              metrics.win_rate >= 0.50 and
              metrics.max_drawdown_r <= 3.0 and
              metrics.rule_breaks == 0):
            new_r = self.current_r * 1.15  # Increase by 15%
            logger.info(
                f"Scale-up triggered: PF={metrics.profit_factor:.2f}, "
                f"E[R]={metrics.expected_r:.2f}, WR={metrics.win_rate:.1%} → "
                f"$R: ${self.current_r:.2f} → ${new_r:.2f}"
            )
        
        if new_r != self.current_r:
            self.current_r = new_r
            self._save_state()
        
        return self.current_r
    
    def reset_daily(self) -> None:
        """Reset daily P&L (call at start of new trading day)"""
        self.daily_pnl_r = 0.0
        self._save_state()
    
    def reset_weekly(self) -> None:
        """Reset weekly P&L (call at start of new week)"""
        self.weekly_pnl_r = 0.0
        self.week_start = self._get_week_start()
        self._save_state()
    
    def get_current_r(self) -> float:
        """Get current $R value"""
        return self.current_r

