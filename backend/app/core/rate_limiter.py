"""In-memory rate limiting dependency for sensitive and resource-intensive endpoints."""

import collections
import time
from typing import Callable, Deque, Dict
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter per client key."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # client_key -> deque of timestamps
        self._records: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier from Cloudflare or remote IP."""
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()
        client_host = request.client.host if request.client else "unknown"
        return client_host

    def check(self, request: Request) -> None:
        """Evaluate rate limit; raises HTTP 429 if exceeded."""
        key = self._get_client_key(request)
        now = time.time()
        window_start = now - self.window_seconds

        queue = self._records[key]

        # Purge timestamps outside the current sliding window
        while queue and queue[0] < window_start:
            queue.popleft()

        if len(queue) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - queue[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds}s.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        # Record this request
        queue.append(now)

    def reset(self) -> None:
        """Clear all rate limit records (used in tests)."""
        self._records.clear()


def rate_limit(max_requests: int = 60, window_seconds: int = 60) -> Callable:
    """FastAPI dependency factory for rate limiting an endpoint."""
    limiter = SlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    def dependency(request: Request) -> None:
        limiter.check(request)

    return dependency
