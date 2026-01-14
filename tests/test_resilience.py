"""Tests for resilience patterns."""

import pytest
import time
from src.runtime.agents.resilience import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    retry_with_exponential_backoff,
    RateLimiter
)


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_successful_calls_pass_through(self):
        """Test successful calls pass through circuit breaker."""
        cb = CircuitBreaker()

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise ValueError("Test error")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(failing_func)

    def test_circuit_enters_half_open_after_timeout(self):
        """Test circuit enters half-open state after timeout."""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should enter half-open state
        def success_func():
            return "success"

        # This should work and move to half-open then closed
        result = cb.call(success_func)
        assert result == "success"

    def test_circuit_closes_after_successes_in_half_open(self):
        """Test circuit closes after successful test calls."""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1, success_threshold=2)

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Succeed twice to close circuit
        def success_func():
            return "success"

        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN

        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED

    def test_reset_circuit(self):
        """Test manually resetting circuit breaker."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRetryWithExponentialBackoff:
    """Test retry with exponential backoff."""

    def test_successful_function_returns_immediately(self):
        """Test that successful function returns without retry."""
        call_count = [0]

        def success_func():
            call_count[0] += 1
            return "success"

        result = retry_with_exponential_backoff(success_func, max_retries=3)
        assert result == "success"
        assert call_count[0] == 1  # Called only once

    def test_retries_on_failure(self):
        """Test that function is retried on failure."""
        call_count = [0]

        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary error")
            return "success"

        result = retry_with_exponential_backoff(
            failing_func,
            max_retries=3,
            base_delay=0.01  # Fast for testing
        )
        assert result == "success"
        assert call_count[0] == 3  # Called 3 times

    def test_raises_after_max_retries(self):
        """Test that exception is raised after max retries."""
        call_count = [0]

        def always_failing():
            call_count[0] += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            retry_with_exponential_backoff(
                always_failing,
                max_retries=2,
                base_delay=0.01
            )

        assert call_count[0] == 3  # Initial + 2 retries

    def test_exponential_backoff_delays(self):
        """Test that delays increase exponentially."""
        delays = []

        def on_retry(error, attempt, delay):
            delays.append(delay)

        def failing_func():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            retry_with_exponential_backoff(
                failing_func,
                max_retries=3,
                base_delay=0.1,
                exponential_base=2,
                jitter=False,  # Disable jitter for predictable testing
                on_retry=on_retry
            )

        # Check delays are roughly exponential (allowing for small variations)
        assert len(delays) == 3
        assert delays[0] < delays[1] < delays[2]


class TestRateLimiter:
    """Test rate limiter."""

    def test_rate_limiter_enforces_delay(self):
        """Test that rate limiter enforces minimum delay between calls."""
        limiter = RateLimiter(max_calls_per_second=10)  # Max 10 calls/sec = 0.1s between calls

        start = time.time()

        # Make 3 calls
        for i in range(3):
            limiter.wait_if_needed()

        elapsed = time.time() - start

        # Should take at least 0.2 seconds (2 * 0.1s delay)
        assert elapsed >= 0.2

    def test_first_call_has_no_delay(self):
        """Test that first call has no delay."""
        limiter = RateLimiter(max_calls_per_second=1)

        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        # First call should be immediate
        assert elapsed < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
