"""
Unit tests for resilience module.

Tests the CircuitBreaker, retry, and rate limiting classes.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestCircuitState:
    """Test CircuitState enum."""

    def test_circuit_state_values(self):
        """Test all circuit state values."""
        from src.runtime.agents.resilience import CircuitState

        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_init_defaults(self):
        """Test CircuitBreaker initialization with defaults."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker()

        assert breaker.failure_threshold == 5
        assert breaker.timeout_seconds == 60
        assert breaker.success_threshold == 2
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_init_custom_params(self):
        """Test CircuitBreaker with custom parameters."""
        from src.runtime.agents.resilience import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=3,
            timeout_seconds=30,
            success_threshold=1
        )

        assert breaker.failure_threshold == 3
        assert breaker.timeout_seconds == 30
        assert breaker.success_threshold == 1

    def test_call_success(self):
        """Test successful call through circuit breaker."""
        from src.runtime.agents.resilience import CircuitBreaker

        breaker = CircuitBreaker()
        func = MagicMock(return_value="result")

        result = breaker.call(func, "arg1", key="value")

        assert result == "result"
        func.assert_called_once_with("arg1", key="value")
        assert breaker.failure_count == 0

    def test_call_failure_increment(self):
        """Test that failures increment failure count."""
        from src.runtime.agents.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=5)
        func = MagicMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError):
            breaker.call(func)

        assert breaker.failure_count == 1

    def test_call_opens_circuit_after_threshold(self):
        """Test circuit opens after failure threshold."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(failure_threshold=3)
        func = MagicMock(side_effect=ValueError("test error"))

        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.opened_at is not None

    def test_call_rejects_when_open(self):
        """Test circuit rejects calls when open."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState, CircuitBreakerOpenError

        breaker = CircuitBreaker(failure_threshold=1, timeout_seconds=60)
        failing_func = MagicMock(side_effect=ValueError("error"))
        good_func = MagicMock(return_value="result")

        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Now calls should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(good_func)

        # Good func should not have been called
        good_func.assert_not_called()

    def test_call_enters_half_open_after_timeout(self):
        """Test circuit enters half-open after timeout."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(failure_threshold=1, timeout_seconds=1)
        func = MagicMock(side_effect=ValueError("error"))

        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call(func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Change func to succeed
        func.side_effect = None
        func.return_value = "success"

        # Should enter half-open and succeed
        result = breaker.call(func)

        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_closes_after_success_threshold(self):
        """Test half-open closes after success threshold."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(failure_threshold=1, timeout_seconds=1, success_threshold=2)
        func = MagicMock(side_effect=ValueError("error"))

        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(func)

        time.sleep(1.1)

        # Change to succeed
        func.side_effect = None
        func.return_value = "success"

        # First success - should be half-open
        breaker.call(func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success - should close
        breaker.call(func)
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Test half-open reopens on failure."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(failure_threshold=1, timeout_seconds=1)

        # Open circuit
        func = MagicMock(side_effect=ValueError("error"))
        with pytest.raises(ValueError):
            breaker.call(func)

        time.sleep(1.1)

        # Enter half-open
        func.return_value = "success"
        func.side_effect = None
        breaker.call(func)

        assert breaker.state == CircuitState.HALF_OPEN

        # Fail again - should reopen
        func.side_effect = ValueError("error again")
        with pytest.raises(ValueError):
            breaker.call(func)

        assert breaker.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        """Test successful call resets failure count in closed state."""
        from src.runtime.agents.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=5)

        # Add some failures
        func = MagicMock(side_effect=ValueError("error"))
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(func)

        assert breaker.failure_count == 3

        # Succeed
        func.side_effect = None
        func.return_value = "success"
        breaker.call(func)

        assert breaker.failure_count == 0

    def test_reset(self):
        """Test manual reset."""
        from src.runtime.agents.resilience import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(failure_threshold=1)

        # Open circuit
        func = MagicMock(side_effect=ValueError("error"))
        with pytest.raises(ValueError):
            breaker.call(func)

        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.opened_at is None


class TestCircuitBreakerOpenError:
    """Test CircuitBreakerOpenError exception."""

    def test_exception_message(self):
        """Test exception has correct message."""
        from src.runtime.agents.resilience import CircuitBreakerOpenError

        error = CircuitBreakerOpenError("Circuit is open")

        assert str(error) == "Circuit is open"


class TestRetryWithExponentialBackoff:
    """Test retry_with_exponential_backoff function."""

    def test_success_first_try(self):
        """Test success on first try."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(return_value="success")

        result = retry_with_exponential_backoff(func, max_retries=3)

        assert result == "success"
        func.assert_called_once()

    def test_success_after_retries(self):
        """Test success after retries."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(side_effect=[ValueError("error"), ValueError("error"), "success"])

        result = retry_with_exponential_backoff(
            func, max_retries=3, base_delay=0.01, jitter=False
        )

        assert result == "success"
        assert func.call_count == 3

    def test_exhausted_retries(self):
        """Test all retries exhausted."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(side_effect=ValueError("persistent error"))

        with pytest.raises(ValueError) as exc_info:
            retry_with_exponential_backoff(
                func, max_retries=2, base_delay=0.01, jitter=False
            )

        assert "persistent error" in str(exc_info.value)
        assert func.call_count == 3  # Initial + 2 retries

    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(side_effect=[ValueError("error"), "success"])
        on_retry = MagicMock()

        result = retry_with_exponential_backoff(
            func, max_retries=3, base_delay=0.01, jitter=False, on_retry=on_retry
        )

        assert result == "success"
        on_retry.assert_called_once()

    def test_respects_max_delay(self):
        """Test delay respects max_delay."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(side_effect=[ValueError("error")] * 10 + ["success"])

        start_time = time.time()
        retry_with_exponential_backoff(
            func, max_retries=10, base_delay=0.01, max_delay=0.02, jitter=False
        )
        elapsed = time.time() - start_time

        # With max_delay=0.02 and 10 retries, max total delay should be ~0.2s
        assert elapsed < 1.0

    def test_non_retryable_exception(self):
        """Test non-retryable exception is raised immediately."""
        from src.runtime.agents.resilience import retry_with_exponential_backoff

        func = MagicMock(side_effect=KeyboardInterrupt())

        with pytest.raises(KeyboardInterrupt):
            retry_with_exponential_backoff(
                func, max_retries=3, retryable_exceptions=(ValueError,)
            )

        func.assert_called_once()


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_init(self):
        """Test RateLimiter initialization."""
        from src.runtime.agents.resilience import RateLimiter

        limiter = RateLimiter(max_calls_per_second=10)

        assert limiter.max_calls_per_second == 10
        assert limiter.min_interval == 0.1

    def test_wait_if_needed_first_call(self):
        """Test first call doesn't wait."""
        from src.runtime.agents.resilience import RateLimiter

        limiter = RateLimiter(max_calls_per_second=10)

        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time

        assert elapsed < 0.01  # Should be nearly instant

    def test_wait_if_needed_rate_limits(self):
        """Test subsequent calls wait if needed."""
        from src.runtime.agents.resilience import RateLimiter

        limiter = RateLimiter(max_calls_per_second=100)  # 10ms between calls

        limiter.wait_if_needed()

        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time

        # Should have waited approximately 10ms
        assert elapsed < 0.02


class TestMultiDimensionalRateLimiter:
    """Test MultiDimensionalRateLimiter class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()

        assert limiter.limits["requests"] == 2000
        assert limiter.limits["input_tokens"] == 800_000
        assert limiter.limits["output_tokens"] == 4_000_000
        assert limiter.window_seconds == 60

    def test_init_custom(self):
        """Test initialization with custom values."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=1000,
            max_output_tokens_per_minute=5000,
            window_seconds=30
        )

        assert limiter.limits["requests"] == 100
        assert limiter.limits["input_tokens"] == 1000
        assert limiter.window_seconds == 30

    def test_get_current_usage_empty(self):
        """Test getting usage when empty."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()

        assert limiter.get_current_usage("requests") == 0
        assert limiter.get_current_usage("input_tokens") == 0

    def test_record_usage(self):
        """Test recording usage."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()

        limiter.record_usage(input_tokens=100, output_tokens=50)

        assert limiter.get_current_usage("requests") == 1
        assert limiter.get_current_usage("input_tokens") == 100
        assert limiter.get_current_usage("output_tokens") == 50

    def test_get_all_usage(self):
        """Test getting all usage metrics."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()
        limiter.record_usage(input_tokens=100, output_tokens=50)

        usage = limiter.get_all_usage()

        assert usage["requests"] == 1
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    def test_get_remaining_capacity(self):
        """Test getting remaining capacity."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=1000
        )

        limiter.record_usage(input_tokens=100, output_tokens=50)

        remaining = limiter.get_remaining_capacity()

        assert remaining["requests"] == 99
        assert remaining["input_tokens"] == 900

    def test_would_exceed_limit_false(self):
        """Test would_exceed_limit returns False when under limit."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=1000
        )

        result = limiter.would_exceed_limit(estimated_input_tokens=100)

        assert result is False

    def test_would_exceed_limit_true_requests(self):
        """Test would_exceed_limit returns True when requests exceeded."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(max_requests_per_minute=2)

        limiter.record_usage(input_tokens=10, output_tokens=10)
        limiter.record_usage(input_tokens=10, output_tokens=10)

        result = limiter.would_exceed_limit()

        assert result is True

    def test_would_exceed_limit_true_tokens(self):
        """Test would_exceed_limit returns True when tokens exceeded."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(max_input_tokens_per_minute=100)

        limiter.record_usage(input_tokens=90, output_tokens=10)

        # Would put us at 90 + 20 = 110, over limit
        result = limiter.would_exceed_limit(estimated_input_tokens=20)

        assert result is True

    def test_wait_time_needed_zero(self):
        """Test wait_time_needed returns 0 when under limits."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()

        wait = limiter.wait_time_needed()

        assert wait == 0.0

    def test_wait_time_needed_positive(self):
        """Test wait_time_needed returns positive when at limit."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=1,
            window_seconds=1
        )

        limiter.record_usage(input_tokens=10, output_tokens=10)

        wait = limiter.wait_time_needed()

        # Should need to wait approximately 1 second
        assert 0 <= wait <= 1.0

    def test_reset(self):
        """Test reset clears all usage."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter()
        limiter.record_usage(input_tokens=100, output_tokens=50)

        limiter.reset()

        assert limiter.get_current_usage("requests") == 0
        assert limiter.get_current_usage("input_tokens") == 0
        assert limiter.get_current_usage("output_tokens") == 0

    def test_cleanup_old_entries(self):
        """Test old entries are cleaned up."""
        from src.runtime.agents.resilience import MultiDimensionalRateLimiter

        limiter = MultiDimensionalRateLimiter(window_seconds=1)

        limiter.record_usage(input_tokens=100, output_tokens=50)

        assert limiter.get_current_usage("requests") == 1

        # Wait for window to expire
        time.sleep(1.1)

        # Should be cleaned up
        assert limiter.get_current_usage("requests") == 0


class TestGetGlobalRateLimiter:
    """Test get_global_rate_limiter function."""

    def test_returns_instance(self):
        """Test get_global_rate_limiter returns instance."""
        import src.runtime.agents.resilience as module
        module._global_rate_limiter = None

        from src.runtime.agents.resilience import get_global_rate_limiter

        limiter = get_global_rate_limiter()

        assert limiter is not None

        # Cleanup
        module._global_rate_limiter = None

    def test_returns_same_instance(self):
        """Test get_global_rate_limiter returns same instance."""
        import src.runtime.agents.resilience as module
        module._global_rate_limiter = None

        from src.runtime.agents.resilience import get_global_rate_limiter

        limiter1 = get_global_rate_limiter()
        limiter2 = get_global_rate_limiter()

        assert limiter1 is limiter2

        # Cleanup
        module._global_rate_limiter = None


class TestTimeoutManager:
    """Test TimeoutManager class."""

    def test_init_default(self):
        """Test initialization with default timeout."""
        from src.runtime.agents.resilience import TimeoutManager

        manager = TimeoutManager()

        assert manager.default_timeout == 120.0

    def test_init_custom(self):
        """Test initialization with custom timeout."""
        from src.runtime.agents.resilience import TimeoutManager

        manager = TimeoutManager(default_timeout=60.0)

        assert manager.default_timeout == 60.0

    def test_get_timeout_default(self):
        """Test getting timeout falls back to default."""
        from src.runtime.agents.resilience import TimeoutManager

        manager = TimeoutManager(default_timeout=30.0)

        timeout = manager.get_timeout("unknown_operation")

        assert timeout == 30.0

    def test_set_and_get_timeout(self):
        """Test setting and getting specific timeout."""
        from src.runtime.agents.resilience import TimeoutManager

        manager = TimeoutManager(default_timeout=30.0)

        manager.set_timeout("api_call", 60.0)

        assert manager.get_timeout("api_call") == 60.0
        assert manager.get_timeout("other") == 30.0
