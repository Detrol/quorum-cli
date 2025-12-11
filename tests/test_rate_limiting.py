"""Tests for rate limiting functionality."""

from __future__ import annotations

import asyncio
import time

import pytest


class TokenBucketRateLimiter:
    """Simple token bucket rate limiter for testing.

    This is a standalone implementation for testing purposes.
    The actual rate limiter is in ipc.py.
    """

    def __init__(self, tokens_per_second: float, burst_size: int):
        self.tokens_per_second = tokens_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.tokens_per_second
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_refill = now

    def try_acquire(self) -> bool:
        """Try to acquire a token. Returns True if successful."""
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        while not self.try_acquire():
            await asyncio.sleep(0.01)


class TestTokenBucketRefill:
    """Tests for token bucket refill logic."""

    def test_initial_tokens(self):
        """Rate limiter starts with burst_size tokens."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10, burst_size=5)
        assert limiter.tokens == 5.0

    def test_tokens_refill_over_time(self):
        """Tokens refill based on elapsed time."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10, burst_size=10)
        # Consume all tokens
        for _ in range(10):
            assert limiter.try_acquire() is True
        assert limiter.tokens < 1.0

        # Wait for refill
        time.sleep(0.2)  # Should add ~2 tokens
        limiter._refill()
        assert limiter.tokens >= 1.0

    def test_tokens_cap_at_burst_size(self):
        """Tokens cannot exceed burst_size."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100, burst_size=5)
        time.sleep(0.1)  # Would add 10 tokens if uncapped
        limiter._refill()
        assert limiter.tokens == 5.0


class TestBurstEnforcement:
    """Tests for burst limit enforcement."""

    def test_burst_allows_rapid_requests(self):
        """Burst size allows rapid initial requests."""
        limiter = TokenBucketRateLimiter(tokens_per_second=1, burst_size=5)
        # Should allow 5 rapid requests
        for i in range(5):
            assert limiter.try_acquire() is True, f"Request {i+1} should succeed"

    def test_burst_blocks_excess_requests(self):
        """Requests beyond burst are blocked without refill time."""
        limiter = TokenBucketRateLimiter(tokens_per_second=1, burst_size=3)
        # Consume burst
        for _ in range(3):
            limiter.try_acquire()
        # Next should fail immediately
        assert limiter.try_acquire() is False


class TestRateLimitExceeded:
    """Tests for rate limit exceeded behavior."""

    def test_try_acquire_returns_false_when_empty(self):
        """try_acquire returns False when no tokens available."""
        limiter = TokenBucketRateLimiter(tokens_per_second=1, burst_size=1)
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False

    @pytest.mark.asyncio
    async def test_acquire_waits_for_token(self):
        """acquire() waits until token is available."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100, burst_size=1)
        limiter.try_acquire()  # Empty the bucket

        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should wait ~10ms for refill at 100 tokens/sec
        assert elapsed >= 0.005  # Allow some timing variance
        assert elapsed < 0.5  # But not too long


class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_limit(self):
        """Concurrent requests don't exceed rate limit."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10, burst_size=5)

        success_count = 0
        fail_count = 0

        async def try_request():
            nonlocal success_count, fail_count
            if limiter.try_acquire():
                success_count += 1
            else:
                fail_count += 1

        # Fire 10 concurrent requests with only 5 burst
        await asyncio.gather(*[try_request() for _ in range(10)])

        assert success_count == 5
        assert fail_count == 5

    @pytest.mark.asyncio
    async def test_blocking_acquire_handles_concurrency(self):
        """Multiple blocking acquire() calls eventually succeed."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100, burst_size=2)

        completed = []

        async def acquire_and_record(task_id: int):
            await limiter.acquire()
            completed.append(task_id)

        # 4 tasks competing for 2 burst tokens + refill
        await asyncio.wait_for(
            asyncio.gather(*[acquire_and_record(i) for i in range(4)]),
            timeout=1.0
        )

        assert len(completed) == 4
