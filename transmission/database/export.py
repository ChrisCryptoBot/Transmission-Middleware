"""
Database Export Module

Exports trade data to CSV format as specified in Product_Concept.txt.
Enables backup, analysis, and broker reconciliation.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
from transmission.database.schema import Database


class CSVExporter:
    """
    Exports trade journal to CSV format.
    
    CSV format matches Product_Concept.txt Section 5 specifications.
    """
    
    def __init__(self, db: Database):
        """
        Initialize CSV Exporter.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def export_trades_to_csv(
        self,
        output_path: Optional[str] = None,
        include_all_fields: bool = True
    ) -> str:
        """
        Export all trades to CSV file.
        
        Args:
            output_path: Path to output CSV (default: data/journal.csv)
            include_all_fields: Include all fields from schema (default True)
            
        Returns:
            Path to exported CSV file
        """
        if output_path is None:
            output_path = Path(__file__).parent.parent / "data" / "journal.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get all trades
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM trades ORDER BY timestamp_entry DESC")
        trades = cursor.fetchall()
        
        if not trades:
            logger.warning("No trades to export")
            return str(output_path)
        
        # Define CSV columns (matching Product_Concept.txt)
        if include_all_fields:
            columns = [
                'trade_id', 'timestamp_entry', 'timestamp_exit',
                'symbol', 'trade_type', 'strategy_used', 'regime_at_entry', 'timeframe',
                'entry_price', 'exit_price', 'stop_loss_price', 'take_profit_price',
                'position_size', 'portfolio_equity_at_entry',
                'entry_execution_latency_ms', 'exit_execution_latency_ms',
                'entry_slippage_ticks', 'exit_slippage_ticks', 'execution_quality_score',
                'order_type_entry', 'order_type_exit',
                'holding_duration_minutes', 'exit_reason',
                'pl_amount_gross', 'pl_amount_net', 'pl_percentage', 'result_r', 'fees_paid', 'win_loss',
                'risk_reward_ratio', 'mae', 'mfe', 'stop_distance_points',
                'volatility_at_entry', 'volume_at_entry', 'vwap_at_entry', 'entry_vwap_distance_pct',
                'technical_signals_confluence', 'adx_at_entry', 'vwap_slope_at_entry',
                'strategy_confidence_score', 'trade_success_probability',
                'tf_alignment_score',
                'spread_ticks_at_entry', 'liquidity_quality_score',
                'account_id', 'dll_at_entry', 'dll_remaining_after',
                'mental_state_pre_trade', 'rule_breaks',
                'trade_trigger_signal', 'notes'
            ]
        else:
            # Minimal columns for basic export
            columns = [
                'trade_id', 'timestamp_entry', 'timestamp_exit',
                'symbol', 'trade_type', 'strategy_used', 'regime_at_entry',
                'entry_price', 'exit_price', 'stop_loss_price', 'take_profit_price',
                'position_size', 'result_r', 'win_loss', 'exit_reason', 'notes'
            ]
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for trade in trades:
                trade_dict = dict(trade)
                # Filter to only include columns we want
                row = {col: trade_dict.get(col, '') for col in columns}
                writer.writerow(row)
        
        logger.info(f"Exported {len(trades)} trades to {output_path}")
        return str(output_path)
    
    def export_performance_metrics_to_csv(
        self,
        output_path: Optional[str] = None,
        limit: int = 100
    ) -> str:
        """
        Export performance metrics to CSV.
        
        Args:
            output_path: Path to output CSV (default: data/performance_metrics.csv)
            limit: Number of recent metrics to export
            
        Returns:
            Path to exported CSV file
        """
        if output_path is None:
            output_path = Path(__file__).parent.parent / "data" / "performance_metrics.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM performance_metrics
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        metrics = cursor.fetchall()
        
        if not metrics:
            logger.warning("No performance metrics to export")
            return str(output_path)
        
        columns = [
            'metric_id', 'timestamp', 'window_trades', 'profit_factor', 'expected_r',
            'win_rate', 'win_rate_wilson_lb', 'max_drawdown_r', 'current_drawdown_r',
            'costs_pct', 'total_trades', 'total_wins', 'total_losses',
            'avg_win_r', 'avg_loss_r'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for metric in metrics:
                metric_dict = dict(metric)
                row = {col: metric_dict.get(col, '') for col in columns}
                writer.writerow(row)
        
        logger.info(f"Exported {len(metrics)} performance metrics to {output_path}")
        return str(output_path)

