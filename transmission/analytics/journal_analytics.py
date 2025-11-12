"""
Journal Analytics

Comprehensive trade analysis and attribution.
Computes metrics, heatmaps, and strategy/regime performance.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from loguru import logger

from transmission.database import Database


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    total_trades: int
    total_wins: int
    total_losses: int
    win_rate: float
    profit_factor: Optional[float]
    expected_r: Optional[float]
    avg_win_r: Optional[float]
    avg_loss_r: Optional[float]
    max_drawdown_r: Optional[float]
    current_drawdown_r: Optional[float]
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    largest_win_r: Optional[float]
    largest_loss_r: Optional[float]
    avg_holding_period_minutes: Optional[float]
    costs_pct: Optional[float]
    win_rate_wilson_lb: Optional[float]


@dataclass
class AttributionMetrics:
    """Performance attribution by dimension"""
    by_regime: Dict[str, Dict[str, float]]
    by_strategy: Dict[str, Dict[str, float]]
    by_symbol: Dict[str, Dict[str, float]]
    by_weekday: Dict[str, Dict[str, float]]
    by_hour: Dict[int, Dict[str, float]]


class JournalAnalytics:
    """
    Journal analytics engine.
    
    Computes:
    - Performance metrics (PF, E[R], Win%, MaxDD, etc.)
    - Attribution (regime × strategy × symbol)
    - Heatmaps (weekday/hour)
    - Time-in-market analysis
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize Journal Analytics.
        
        Args:
            database: Database instance (creates default if None)
        """
        self.database = database if database else Database()
    
    def compute_metrics(
        self,
        window_trades: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceMetrics:
        """
        Compute performance metrics.
        
        Args:
            window_trades: Number of recent trades to analyze
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            PerformanceMetrics
        """
        # Get trades
        if start_date or end_date:
            # Filter by date range
            trades = self.database.get_trades_for_metrics(window=1000)  # Get all, filter in memory
            if start_date:
                trades = [t for t in trades if datetime.fromisoformat(t['timestamp_entry']) >= start_date]
            if end_date:
                trades = [t for t in trades if datetime.fromisoformat(t['timestamp_entry']) <= end_date]
            trades = trades[-window_trades:]  # Take last N
        else:
            trades = self.database.get_trades_for_metrics(window=window_trades)
        
        if not trades:
            return PerformanceMetrics(
                total_trades=0,
                total_wins=0,
                total_losses=0,
                win_rate=0.0,
                profit_factor=None,
                expected_r=None,
                avg_win_r=None,
                avg_loss_r=None,
                max_drawdown_r=None,
                current_drawdown_r=None,
                sharpe_ratio=None,
                sortino_ratio=None,
                largest_win_r=None,
                largest_loss_r=None,
                avg_holding_period_minutes=None,
                costs_pct=None,
                win_rate_wilson_lb=None
            )
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades)
        
        # Basic counts
        total_trades = len(df)
        wins = df[df['win_loss'] == 'Win']
        losses = df[df['win_loss'] == 'Loss']
        total_wins = len(wins)
        total_losses = len(losses)
        
        # Win rate
        win_rate = total_wins / total_trades if total_trades > 0 else 0.0
        
        # Profit Factor
        profit_factor = None
        if total_losses > 0 and len(wins) > 0:
            total_win_r = wins['result_r'].sum() if 'result_r' in wins.columns else 0
            total_loss_r = abs(losses['result_r'].sum()) if 'result_r' in losses.columns else 0
            if total_loss_r > 0:
                profit_factor = total_win_r / total_loss_r
        
        # Expected R
        expected_r = None
        if 'result_r' in df.columns and total_trades > 0:
            expected_r = df['result_r'].sum() / total_trades
        
        # Average Win/Loss
        avg_win_r = None
        if len(wins) > 0 and 'result_r' in wins.columns:
            avg_win_r = wins['result_r'].mean()
        
        avg_loss_r = None
        if len(losses) > 0 and 'result_r' in losses.columns:
            avg_loss_r = losses['result_r'].mean()
        
        # Largest Win/Loss
        largest_win_r = None
        largest_loss_r = None
        if 'result_r' in df.columns:
            if len(wins) > 0:
                largest_win_r = wins['result_r'].max()
            if len(losses) > 0:
                largest_loss_r = losses['result_r'].min()
        
        # Drawdown
        max_drawdown_r, current_drawdown_r = self._calculate_drawdown(df)
        
        # Sharpe/Sortino
        sharpe_ratio, sortino_ratio = self._calculate_risk_adjusted_returns(df)
        
        # Average holding period
        avg_holding_period_minutes = None
        if 'timestamp_entry' in df.columns and 'timestamp_exit' in df.columns:
            holding_periods = []
            for _, trade in df.iterrows():
                if trade['timestamp_exit']:
                    entry = datetime.fromisoformat(trade['timestamp_entry'])
                    exit_time = datetime.fromisoformat(trade['timestamp_exit'])
                    holding_periods.append((exit_time - entry).total_seconds() / 60)
            if holding_periods:
                avg_holding_period_minutes = np.mean(holding_periods)
        
        # Costs percentage
        costs_pct = None
        if 'pl_amount_gross' in df.columns and 'fees_paid' in df.columns:
            total_gross = df['pl_amount_gross'].sum()
            total_fees = df['fees_paid'].sum()
            if total_gross > 0:
                costs_pct = (total_fees / total_gross) * 100
        
        # Wilson Lower Bound
        win_rate_wilson_lb = self._wilson_lower_bound(total_wins, total_trades)
        
        return PerformanceMetrics(
            total_trades=total_trades,
            total_wins=total_wins,
            total_losses=total_losses,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expected_r=expected_r,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r,
            max_drawdown_r=max_drawdown_r,
            current_drawdown_r=current_drawdown_r,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            largest_win_r=largest_win_r,
            largest_loss_r=largest_loss_r,
            avg_holding_period_minutes=avg_holding_period_minutes,
            costs_pct=costs_pct,
            win_rate_wilson_lb=win_rate_wilson_lb
        )
    
    def compute_attribution(
        self,
        window_trades: int = 100
    ) -> AttributionMetrics:
        """
        Compute performance attribution by dimension.
        
        Args:
            window_trades: Number of trades to analyze
        
        Returns:
            AttributionMetrics
        """
        trades = self.database.get_trades_for_metrics(window=window_trades)
        
        if not trades:
            return AttributionMetrics(
                by_regime={},
                by_strategy={},
                by_symbol={},
                by_weekday={},
                by_hour={}
            )
        
        df = pd.DataFrame(trades)
        
        # Attribution by regime
        by_regime = self._attribution_by_column(df, 'regime_at_entry')
        
        # Attribution by strategy
        by_strategy = self._attribution_by_column(df, 'strategy_used')
        
        # Attribution by symbol
        by_symbol = self._attribution_by_column(df, 'symbol')
        
        # Attribution by weekday
        by_weekday = {}
        if 'timestamp_entry' in df.columns:
            df['weekday'] = pd.to_datetime(df['timestamp_entry']).dt.day_name()
            by_weekday = self._attribution_by_column(df, 'weekday')
        
        # Attribution by hour
        by_hour = {}
        if 'timestamp_entry' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp_entry']).dt.hour
            by_hour = self._attribution_by_column(df, 'hour')
        
        return AttributionMetrics(
            by_regime=by_regime,
            by_strategy=by_strategy,
            by_symbol=by_symbol,
            by_weekday=by_weekday,
            by_hour=by_hour
        )
    
    def _attribution_by_column(
        self,
        df: pd.DataFrame,
        column: str
    ) -> Dict[str, Dict[str, float]]:
        """Compute attribution metrics for a column"""
        if column not in df.columns:
            return {}
        
        attribution = {}
        
        for value in df[column].unique():
            if pd.isna(value):
                continue
            
            subset = df[df[column] == value]
            
            wins = subset[subset['win_loss'] == 'Win']
            losses = subset[subset['win_loss'] == 'Loss']
            
            total_trades = len(subset)
            total_wins = len(wins)
            total_losses = len(losses)
            
            win_rate = total_wins / total_trades if total_trades > 0 else 0.0
            
            # Expected R
            expected_r = None
            if 'result_r' in subset.columns:
                expected_r = subset['result_r'].mean()
            
            # Profit Factor
            profit_factor = None
            if total_losses > 0 and len(wins) > 0 and 'result_r' in subset.columns:
                total_win_r = wins['result_r'].sum()
                total_loss_r = abs(losses['result_r'].sum())
                if total_loss_r > 0:
                    profit_factor = total_win_r / total_loss_r
            
            attribution[str(value)] = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'expected_r': expected_r,
                'profit_factor': profit_factor
            }
        
        return attribution
    
    def _calculate_drawdown(
        self,
        df: pd.DataFrame
    ) -> tuple[Optional[float], Optional[float]]:
        """Calculate max and current drawdown"""
        if 'result_r' not in df.columns:
            return None, None
        
        # Calculate cumulative R
        df_sorted = df.sort_values('timestamp_entry')
        df_sorted['cumulative_r'] = df_sorted['result_r'].cumsum()
        
        # Calculate running max
        df_sorted['running_max'] = df_sorted['cumulative_r'].expanding().max()
        
        # Calculate drawdown
        df_sorted['drawdown'] = df_sorted['cumulative_r'] - df_sorted['running_max']
        
        max_drawdown_r = df_sorted['drawdown'].min()
        current_drawdown_r = df_sorted['drawdown'].iloc[-1] if len(df_sorted) > 0 else None
        
        return max_drawdown_r, current_drawdown_r
    
    def _calculate_risk_adjusted_returns(
        self,
        df: pd.DataFrame
    ) -> tuple[Optional[float], Optional[float]]:
        """Calculate Sharpe and Sortino ratios"""
        if 'result_r' not in df.columns or len(df) < 2:
            return None, None
        
        returns = df['result_r'].values
        
        # Sharpe Ratio (assuming daily returns, annualized)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else None
        
        # Sortino Ratio (downside deviation only)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = (mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else None
        
        return sharpe, sortino
    
    def _wilson_lower_bound(
        self,
        successes: int,
        total: int,
        confidence: float = 0.95
    ) -> Optional[float]:
        """Calculate Wilson score lower bound"""
        if total == 0:
            return None
        
        z = 1.96  # 95% confidence
        p = successes / total
        n = total
        
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
        
        return max(0.0, centre - margin)

