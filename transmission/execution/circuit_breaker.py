"""
Circuit Breaker Pattern for Broker API Calls

Prevents cascading failures when broker API is down/flapping.

States:
- CLOSED: Normal operation, calls pass through
- OPEN: Too many failures, block all calls
- HALF_OPEN: Testing if service recovered

Logic:
1. Track consecutive failures
2. Open circuit after threshold (default: 5 failures)
3. Block calls when open, throw CircuitBreakerOpen exception
4. After timeout (default: 60s), enter HALF_OPEN state
5. Allow 1 test call in HALF_OPEN
6. If test succeeds → CLOSED
7. If test fails → OPEN again
"""

import time
import asyncio
from typing import Callable, Any, TypeVar, ParamSpec
from enum import Enum
from functools import wraps
from loguru import logger


P = ParamSpec('P')
T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open (service unavailable)"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
            expected_exception=BrokerAPIError
        )

        @breaker.protect
        async def submit_order(order):
            return await broker.submit(order)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures to open circuit
            timeout_seconds: Seconds to wait before testing recovery
            expected_exception: Exception type that triggers circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0

        # Stats
        self.total_calls = 0
        self.total_failures = 0
        self.total_rejections = 0

    def protect(self, func: Callable[P, T]) -> Callable[P, T]:
        """
        Decorator to protect a function with circuit breaker.

        Usage:
            @breaker.protect
            async def risky_call():
                return await broker.submit_order()
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await self._call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return self._call_sync(func, *args, **kwargs)
            return sync_wrapper

    async def _call_async(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute async function with circuit breaker logic."""
        self.total_calls += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit breaker entering HALF_OPEN state (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                self.total_rejections += 1
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN (failed {self.failure_count}/{self.failure_threshold} times). "
                    f"Will retry in {self.timeout_seconds - self._time_since_last_failure():.1f}s"
                )

        # Attempt the call
        try:
            result = await func(*args, **kwargs)

            # Success - update circuit state
            self._record_success()
            return result

        except self.expected_exception as e:
            # Expected failure - update circuit state
            self._record_failure()

            # Re-raise the original exception
            raise

    def _call_sync(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute sync function with circuit breaker logic."""
        self.total_calls += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit breaker entering HALF_OPEN state (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                self.total_rejections += 1
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN (failed {self.failure_count}/{self.failure_threshold} times). "
                    f"Will retry in {self.timeout_seconds - self._time_since_last_failure():.1f}s"
                )

        # Attempt the call
        try:
            result = func(*args, **kwargs)

            # Success - update circuit state
            self._record_success()
            return result

        except self.expected_exception as e:
            # Expected failure - update circuit state
            self._record_failure()

            # Re-raise the original exception
            raise

    def _record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            # Test call succeeded - close the circuit
            logger.info("Circuit breaker test succeeded - closing circuit")
            self.state = CircuitState.CLOSED

        elif self.state == CircuitState.CLOSED:
            # Normal success
            pass

    def _record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
        )

        if self.failure_count >= self.failure_threshold:
            # Open the circuit
            logger.error(
                f"Circuit breaker OPEN - threshold reached ({self.failure_threshold} failures)"
            )
            self.state = CircuitState.OPEN

        elif self.state == CircuitState.HALF_OPEN:
            # Test call failed - back to OPEN
            logger.warning("Circuit breaker test failed - back to OPEN")
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True

        time_since_failure = self._time_since_last_failure()
        return time_since_failure >= self.timeout_seconds

    def _time_since_last_failure(self) -> float:
        """Get seconds since last failure."""
        if self.last_failure_time is None:
            return float('inf')

        return time.time() - self.last_failure_time

    def reset(self) -> None:
        """Manually reset circuit breaker (for testing or manual recovery)."""
        logger.info("Circuit breaker manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_rejections": self.total_rejections,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_rate": self.total_failures / self.total_calls if self.total_calls > 0 else 0.0,
            "time_since_last_failure": self._time_since_last_failure()
        }


# Global circuit breaker instance for broker calls
broker_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout_seconds=60.0,
    expected_exception=Exception  # Catch all broker exceptions
)
