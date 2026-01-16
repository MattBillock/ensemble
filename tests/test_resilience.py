"""Tests for resilience patterns."""

import pytest
import time
import threading
from src.runtime.agents.resilience import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    retry_with_exponential_backoff,
    RateLimiter,
    MultiDimensionalRateLimiter,
    get_global_rate_limiter,
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


class TestMultiDimensionalRateLimiter:
    """Test multi-dimensional rate limiter for Anthropic API limits."""

    def test_initialization_with_defaults(self):
        """Test rate limiter initializes with default Anthropic limits."""
        limiter = MultiDimensionalRateLimiter()

        assert limiter.limits["requests"] == 2000
        assert limiter.limits["input_tokens"] == 800_000
        assert limiter.limits["output_tokens"] == 4_000_000
        assert limiter.window_seconds == 60

    def test_initialization_with_custom_limits(self):
        """Test rate limiter accepts custom limits."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=50000,
            max_output_tokens_per_minute=100000,
            window_seconds=30,
        )

        assert limiter.limits["requests"] == 100
        assert limiter.limits["input_tokens"] == 50000
        assert limiter.limits["output_tokens"] == 100000
        assert limiter.window_seconds == 30

    def test_record_usage(self):
        """Test recording API usage updates counters."""
        limiter = MultiDimensionalRateLimiter()

        # Record some usage
        limiter.record_usage(input_tokens=1000, output_tokens=500)

        usage = limiter.get_all_usage()
        assert usage["requests"] == 1
        assert usage["input_tokens"] == 1000
        assert usage["output_tokens"] == 500

    def test_multiple_usage_records_accumulate(self):
        """Test multiple usage records accumulate correctly."""
        limiter = MultiDimensionalRateLimiter()

        limiter.record_usage(input_tokens=1000, output_tokens=500)
        limiter.record_usage(input_tokens=2000, output_tokens=1000)
        limiter.record_usage(input_tokens=500, output_tokens=250)

        usage = limiter.get_all_usage()
        assert usage["requests"] == 3
        assert usage["input_tokens"] == 3500
        assert usage["output_tokens"] == 1750

    def test_no_wait_needed_under_limits(self):
        """Test no wait time when under all limits."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=100000,
        )

        # Record some usage
        limiter.record_usage(input_tokens=1000, output_tokens=500)

        wait_time = limiter.wait_time_needed(estimated_input_tokens=1000)
        assert wait_time == 0.0

    def test_wait_needed_at_request_limit(self):
        """Test wait time calculated when at request limit."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=3,  # Very low limit for testing
            max_input_tokens_per_minute=100000,
            max_output_tokens_per_minute=100000,
        )

        # Fill up request quota
        for _ in range(3):
            limiter.record_usage(input_tokens=100, output_tokens=50)

        # Should need to wait
        wait_time = limiter.wait_time_needed()
        assert wait_time > 0
        assert wait_time <= 60  # At most window size

    def test_wait_needed_at_token_limit(self):
        """Test wait time calculated when at token limit."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=1000,
            max_input_tokens_per_minute=5000,  # Low limit for testing
            max_output_tokens_per_minute=100000,
        )

        # Use up most of token budget
        limiter.record_usage(input_tokens=4500, output_tokens=500)

        # Request with estimated tokens that would exceed limit
        wait_time = limiter.wait_time_needed(estimated_input_tokens=600)
        assert wait_time > 0

    def test_would_exceed_limit(self):
        """Test would_exceed_limit check."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=2,
            max_input_tokens_per_minute=5000,
        )

        # Should not exceed initially
        assert not limiter.would_exceed_limit()

        # Fill up request limit
        limiter.record_usage(input_tokens=100, output_tokens=50)
        limiter.record_usage(input_tokens=100, output_tokens=50)

        # Now should exceed
        assert limiter.would_exceed_limit()

    def test_would_exceed_with_estimated_tokens(self):
        """Test would_exceed_limit considers estimated tokens."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=5000,
        )

        limiter.record_usage(input_tokens=4500, output_tokens=500)

        # Without estimated tokens - still under
        assert not limiter.would_exceed_limit(estimated_input_tokens=400)

        # With estimated tokens - would exceed
        assert limiter.would_exceed_limit(estimated_input_tokens=600)

    def test_get_remaining_capacity(self):
        """Test get_remaining_capacity returns correct values."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            max_input_tokens_per_minute=10000,
            max_output_tokens_per_minute=50000,
        )

        limiter.record_usage(input_tokens=3000, output_tokens=10000)

        remaining = limiter.get_remaining_capacity()
        assert remaining["requests"] == 99
        assert remaining["input_tokens"] == 7000
        assert remaining["output_tokens"] == 40000

    def test_sliding_window_cleanup(self):
        """Test old entries are cleaned up after window expires."""
        limiter = MultiDimensionalRateLimiter(
            max_requests_per_minute=100,
            window_seconds=1,  # Very short window for testing
        )

        limiter.record_usage(input_tokens=1000, output_tokens=500)

        # Verify usage recorded
        assert limiter.get_current_usage("requests") == 1

        # Wait for window to expire
        time.sleep(1.1)

        # Usage should be cleaned up
        assert limiter.get_current_usage("requests") == 0

    def test_reset_clears_all_counters(self):
        """Test reset clears all usage counters."""
        limiter = MultiDimensionalRateLimiter()

        limiter.record_usage(input_tokens=1000, output_tokens=500)
        limiter.record_usage(input_tokens=2000, output_tokens=1000)

        limiter.reset()

        usage = limiter.get_all_usage()
        assert usage["requests"] == 0
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0

    def test_thread_safety(self):
        """Test rate limiter is thread-safe for concurrent access."""
        limiter = MultiDimensionalRateLimiter(max_requests_per_minute=10000)

        num_threads = 10
        records_per_thread = 100

        def record_many():
            for _ in range(records_per_thread):
                limiter.record_usage(input_tokens=100, output_tokens=50)

        threads = [threading.Thread(target=record_many) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        usage = limiter.get_all_usage()
        expected_requests = num_threads * records_per_thread
        assert usage["requests"] == expected_requests
        assert usage["input_tokens"] == expected_requests * 100
        assert usage["output_tokens"] == expected_requests * 50

    def test_global_rate_limiter_singleton(self):
        """Test get_global_rate_limiter returns same instance."""
        limiter1 = get_global_rate_limiter()
        limiter2 = get_global_rate_limiter()

        assert limiter1 is limiter2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
