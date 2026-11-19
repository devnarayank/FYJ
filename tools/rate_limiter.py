"""
Rate limiting utilities for enforcing API and email rate limits.
"""
import logging
import time
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter using sliding window approach."""

    def __init__(self, max_per_hour: int, delay_between_calls: float = 0):
        """
        Initialize rate limiter.
        
        Args:
            max_per_hour: Maximum operations per hour
            delay_between_calls: Minimum delay in seconds between calls
        """
        self.max_per_hour = max_per_hour
        self.delay_between_calls = delay_between_calls
        self.call_times = []
        self.last_call = None
        self.lock = Lock()

    def is_rate_limited(self) -> bool:
        """Check if we've exceeded rate limit."""
        with self.lock:
            now = datetime.now()
            # Remove calls older than 1 hour
            self.call_times = [t for t in self.call_times if (now - t).total_seconds() < 3600]
            return len(self.call_times) >= self.max_per_hour

    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits.
        
        Returns:
            Time waited in seconds
        """
        with self.lock:
            # Check delay between calls
            if self.last_call:
                elapsed = time.time() - self.last_call
                if elapsed < self.delay_between_calls:
                    wait_time = self.delay_between_calls - elapsed
                    logger.debug(f"Rate limiter: waiting {wait_time:.1f}s before next call")
                    time.sleep(wait_time)
                    self.last_call = time.time()
                    return wait_time

            # Record the call
            self.call_times.append(datetime.now())
            self.last_call = time.time()
            return 0

    def get_remaining_quota(self) -> int:
        """Get remaining operations available this hour."""
        with self.lock:
            now = datetime.now()
            self.call_times = [t for t in self.call_times if (now - t).total_seconds() < 3600]
            return max(0, self.max_per_hour - len(self.call_times))

    def reset(self) -> None:
        """Reset the rate limiter."""
        with self.lock:
            self.call_times = []
            self.last_call = None


class EmailRateLimiter(RateLimiter):
    """Specialized rate limiter for email operations."""

    def __init__(self, max_per_hour: int = 10):
        """Initialize email rate limiter."""
        # Default: 10 emails per hour = 360 seconds between emails
        delay_between_calls = 3600 / max_per_hour
        super().__init__(max_per_hour=max_per_hour, delay_between_calls=delay_between_calls)

    def can_send_email(self) -> bool:
        """Check if we can send email without exceeding rate limit."""
        return not self.is_rate_limited()

    def wait_before_send(self) -> float:
        """Wait before sending next email."""
        if self.is_rate_limited():
            logger.warning("Email rate limit exceeded!")
            raise RuntimeError("Email rate limit exceeded")
        return self.wait_if_needed()


class APIRateLimiter(RateLimiter):
    """Specialized rate limiter for API calls."""

    def __init__(self, max_per_minute: int = 30, max_per_hour: int = 500):
        """Initialize API rate limiter."""
        self.max_per_minute = max_per_minute
        self.call_times_minute = []
        super().__init__(max_per_hour=max_per_hour, delay_between_calls=0)

    def is_rate_limited(self) -> bool:
        """Check if we've exceeded rate limits (minute or hour)."""
        with self.lock:
            now = datetime.now()

            # Remove calls older than 1 hour
            self.call_times = [t for t in self.call_times if (now - t).total_seconds() < 3600]

            # Remove calls older than 1 minute
            self.call_times_minute = [t for t in self.call_times_minute if (now - t).total_seconds() < 60]

            # Check both limits
            minute_exceeded = len(self.call_times_minute) >= self.max_per_minute
            hour_exceeded = len(self.call_times) >= self.max_per_hour

            return minute_exceeded or hour_exceeded

    def wait_if_needed(self) -> float:
        """Wait if necessary to respect rate limits."""
        with self.lock:
            now = datetime.now()

            # Clean up old records
            self.call_times = [t for t in self.call_times if (now - t).total_seconds() < 3600]
            self.call_times_minute = [t for t in self.call_times_minute if (now - t).total_seconds() < 60]

            # Check minute limit
            if len(self.call_times_minute) >= self.max_per_minute:
                oldest = self.call_times_minute[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.debug(f"Minute rate limit: waiting {wait_time:.1f}s")
                    time.sleep(wait_time)

            # Record call
            now = datetime.now()
            self.call_times.append(now)
            self.call_times_minute.append(now)

            return 0
