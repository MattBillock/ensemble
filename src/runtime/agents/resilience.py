"""Resilience patterns for agent runtime: retry logic, circuit breaker, rate limiting."""

import time
import logging
import threading
from collections import deque
from typing import Callable, Any, Optional, Type, Dict
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


class MultiDimensionalRateLimiter:
    """
    Multi-dimensional rate limiter for Anthropic API limits.

    Tracks requests, input tokens, and output tokens per minute using
    sliding window counters. Thread-safe for concurrent agent usage.

    Default limits based on Anthropic API:
    - 2,000 requests/minute
    - 800,000 input tokens/minute (Sonnet/Opus)
    - 4,000,000 output tokens/minute
    """

    def __init__(
        self,
        max_requests_per_minute: int = 2000,
        max_input_tokens_per_minute: int = 800_000,
        max_output_tokens_per_minute: int = 4_000_000,
        window_seconds: int = 60,
    ):
        """
        Initialize multi-dimensional rate limiter.

        Args:
            max_requests_per_minute: Maximum API requests per minute
            max_input_tokens_per_minute: Maximum input tokens per minute
            max_output_tokens_per_minute: Maximum output tokens per minute
            window_seconds: Sliding window size in seconds (default 60)
        """
        self.limits = {
            "requests": max_requests_per_minute,
            "input_tokens": max_input_tokens_per_minute,
            "output_tokens": max_output_tokens_per_minute,
        }
        self.window_seconds = window_seconds
        # Each deque stores tuples of (timestamp, count)
        self.usage_windows: Dict[str, deque] = {
            "requests": deque(),
            "input_tokens": deque(),
            "output_tokens": deque(),
        }
        self._lock = threading.Lock()

    def _cleanup_old_entries(self, metric: str) -> None:
        """Remove entries older than the window period."""
        cutoff = time.time() - self.window_seconds
        while self.usage_windows[metric] and self.usage_windows[metric][0][0] < cutoff:
            self.usage_windows[metric].popleft()

    def get_current_usage(self, metric: str) -> int:
        """
        Get current usage for a metric in the sliding window.

        Args:
            metric: One of 'requests', 'input_tokens', 'output_tokens'

        Returns:
            Current usage count within the window
        """
        self._cleanup_old_entries(metric)
        return sum(entry[1] for entry in self.usage_windows[metric])

    def get_all_usage(self) -> Dict[str, int]:
        """
        Get current usage for all metrics.

        Returns:
            Dictionary with current usage for each metric
        """
        with self._lock:
            return {
                metric: self.get_current_usage(metric) for metric in self.limits.keys()
            }

    def get_remaining_capacity(self) -> Dict[str, int]:
        """
        Get remaining capacity for all metrics.

        Returns:
            Dictionary with remaining capacity for each metric
        """
        with self._lock:
            return {
                metric: max(0, self.limits[metric] - self.get_current_usage(metric))
                for metric in self.limits.keys()
            }

    def wait_time_needed(self, estimated_input_tokens: int = 0) -> float:
        """
        Calculate wait time needed before making a request.

        Args:
            estimated_input_tokens: Estimated input tokens for the upcoming request

        Returns:
            Seconds to wait before proceeding (0 if no wait needed)
        """
        with self._lock:
            wait_times = []
            now = time.time()

            # Check requests limit
            self._cleanup_old_entries("requests")
            req_usage = sum(entry[1] for entry in self.usage_windows["requests"])
            if req_usage >= self.limits["requests"]:
                if self.usage_windows["requests"]:
                    oldest = self.usage_windows["requests"][0][0]
                    wait_times.append(self.window_seconds - (now - oldest))

            # Check input token limit
            self._cleanup_old_entries("input_tokens")
            input_usage = sum(entry[1] for entry in self.usage_windows["input_tokens"])
            if input_usage + estimated_input_tokens >= self.limits["input_tokens"]:
                if self.usage_windows["input_tokens"]:
                    oldest = self.usage_windows["input_tokens"][0][0]
                    wait_times.append(self.window_seconds - (now - oldest))

            # Check output token limit (preemptive check based on recent output rate)
            self._cleanup_old_entries("output_tokens")
            output_usage = sum(entry[1] for entry in self.usage_windows["output_tokens"])
            if output_usage >= self.limits["output_tokens"] * 0.95:  # 95% threshold
                if self.usage_windows["output_tokens"]:
                    oldest = self.usage_windows["output_tokens"][0][0]
                    wait_times.append(self.window_seconds - (now - oldest))

            return max(0.0, max(wait_times)) if wait_times else 0.0

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        """
        Record API call usage after completion.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
        """
        with self._lock:
            now = time.time()
            self.usage_windows["requests"].append((now, 1))
            self.usage_windows["input_tokens"].append((now, input_tokens))
            self.usage_windows["output_tokens"].append((now, output_tokens))

            logger.debug(
                f"Rate limiter recorded: input={input_tokens}, output={output_tokens}, "
                f"totals: requests={self.get_current_usage('requests')}, "
                f"input={self.get_current_usage('input_tokens')}, "
                f"output={self.get_current_usage('output_tokens')}"
            )

    def would_exceed_limit(self, estimated_input_tokens: int = 0) -> bool:
        """
        Check if making a request would exceed rate limits.

        Args:
            estimated_input_tokens: Estimated input tokens for the request

        Returns:
            True if request would exceed limits
        """
        with self._lock:
            # Check requests
            self._cleanup_old_entries("requests")
            if sum(e[1] for e in self.usage_windows["requests"]) >= self.limits["requests"]:
                return True

            # Check input tokens
            self._cleanup_old_entries("input_tokens")
            input_total = sum(e[1] for e in self.usage_windows["input_tokens"])
            if input_total + estimated_input_tokens >= self.limits["input_tokens"]:
                return True

            return False

    def reset(self) -> None:
        """Reset all rate limit counters."""
        with self._lock:
            for metric in self.usage_windows:
                self.usage_windows[metric].clear()
            logger.info("Rate limiter counters reset")


# Global rate limiter instance for shared use across agents
_global_rate_limiter: Optional["MultiDimensionalRateLimiter"] = None


def get_global_rate_limiter() -> MultiDimensionalRateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        Shared MultiDimensionalRateLimiter instance
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = MultiDimensionalRateLimiter()
        logger.info(
            f"Global rate limiter initialized: "
            f"{_global_rate_limiter.limits['requests']} req/min, "
            f"{_global_rate_limiter.limits['input_tokens']} input tokens/min, "
            f"{_global_rate_limiter.limits['output_tokens']} output tokens/min"
        )
    return _global_rate_limiter


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
