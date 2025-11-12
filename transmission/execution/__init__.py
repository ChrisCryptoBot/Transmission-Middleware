"""
Execution Module - Order Management

Handles order placement and execution:
- Limit vs Market orders
- Slippage monitoring
- Fill tracking
- Multi-account staggering
"""

from transmission.execution.guard import ExecutionGuard, ExecutionCheck

__all__ = ['ExecutionGuard', 'ExecutionCheck']
