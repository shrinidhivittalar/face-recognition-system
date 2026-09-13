"""In-memory sliding-window rate limiter for expensive recognition endpoints.

Single-process only (blueprint section 12: "where practical"). Sufficient for
this assignment's scale; a distributed deployment would need a shared store
(e.g. Redis) instead.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self._window_seconds:
            bucket.popleft()
        if len(bucket) >= self._max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")
        bucket.append(now)


def client_key(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
