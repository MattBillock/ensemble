"""Resilience patterns for agent runtime: retry logic, circuit breaker, rate limiting."""

import time
import logging
from typing import Callable, Any, Optional, Type
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    After threshold failures, opens circuit and rejects calls for timeout period.
    After timeout, allows one test call (half-open). If successful, closes circuit.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: How long to keep circuit open
            success_threshold: Number of successes to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if datetime.now() - self.opened_at >= timedelta(seconds=self.timeout_seconds):
                logger.info("Circuit breaker timeout expired, entering half-open state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open. Opened at {self.opened_at}, "
                    f"will retry after {self.timeout_seconds}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"Circuit breaker success in half-open state: {self.success_count}/{self.success_threshold}")

            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing after successful test calls")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, error: Exception):
        """Handle failed call."""
        self.last_failure_time = datetime.now()
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker test call failed, reopening circuit")
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker opening after {self.failure_count} failures. "
                    f"Last error: {error}"
                )
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        logger.info("Circuit breaker manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Any:
    """
    Retry function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to delay
        retryable_exceptions: Tuple of exception types that should trigger retry
        on_retry: Optional callback(exception, attempt, delay) called before each retry

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    import random

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as e:
            last_exception = e

            if attempt >= max_retries:
                logger.error(f"All {max_retries} retries exhausted. Last error: {e}")
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (0.5 + random.random())  # Random factor between 0.5 and 1.5

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            # Call retry callback if provided
            if on_retry:
                on_retry(e, attempt + 1, delay)

            time.sleep(delay)

    # Should never reach here, but for type safety
    if last_exception:
        raise last_exception


class RateLimiter:
    """
    Token bucket rate limiter.

    Ensures a maximum rate of operations per second.
    """

    def __init__(self, max_calls_per_second: float):
        """
        Initialize rate limiter.

        Args:
            max_calls_per_second: Maximum calls allowed per second
        """
        self.max_calls_per_second = max_calls_per_second
        self.min_interval = 1.0 / max_calls_per_second if max_calls_per_second > 0 else 0
        self.last_call_time = None

    def wait_if_needed(self):
        """Wait if necessary to comply with rate limit."""
        if self.last_call_time is None:
            self.last_call_time = time.time()
            return

        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_call_time = time.time()


class TimeoutManager:
    """
    Manages timeouts for operations with configurable limits.
    """

    def __init__(self, default_timeout: float = 120.0):
        """
        Initialize timeout manager.

        Args:
            default_timeout: Default timeout in seconds
        """
        self.default_timeout = default_timeout
        self.timeouts = {}

    def set_timeout(self, operation: str, timeout: float):
        """Set timeout for specific operation."""
        self.timeouts[operation] = timeout

    def get_timeout(self, operation: str) -> float:
        """Get timeout for operation, falling back to default."""
        return self.timeouts.get(operation, self.default_timeout)
