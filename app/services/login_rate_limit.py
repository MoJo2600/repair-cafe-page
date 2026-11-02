"""
In-memory limit for failed password logins (break-glass /api/auth/login).
"""

import threading
import time
from collections import deque

from flask import current_app, request


class LoginRateLimiter:
    """Counts failed logins per client IP and per username in a sliding window."""

    def __init__(self):
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float, window: float) -> deque[float]:
        entries = self._failures.get(key, deque())
        while entries and entries[0] <= now - window:
            entries.popleft()
        return entries

    def retry_after(self, ip: str, username: str) -> int | None:
        """Seconds until the next attempt is allowed, or None if not blocked."""
        cfg = current_app.config
        window = cfg["LOGIN_RATE_WINDOW_MINUTES"] * 60
        now = time.monotonic()
        limits = (
            (f"ip:{ip}", cfg["LOGIN_MAX_FAILED_PER_IP"]),
            (f"user:{username.lower()}", cfg["LOGIN_MAX_FAILED_PER_USER"]),
        )
        waits = []
        with self._lock:
            for key, limit in limits:
                entries = self._recent(key, now, window)
                if len(entries) >= limit:
                    # Blocked until the oldest failure in the window expires.
                    waits.append(entries[0] + window - now)
        return int(max(waits)) + 1 if waits else None

    def record_failure(self, ip: str, username: str) -> None:
        now = time.monotonic()
        window = current_app.config["LOGIN_RATE_WINDOW_MINUTES"] * 60
        with self._lock:
            # Drop keys without recent failures so the dict cannot grow unbounded.
            for key in [k for k, v in self._failures.items() if not self._recent(k, now, window)]:
                del self._failures[key]
            for key in (f"ip:{ip}", f"user:{username.lower()}"):
                self._failures.setdefault(key, deque()).append(now)

    def reset_user(self, username: str) -> None:
        with self._lock:
            self._failures.pop(f"user:{username.lower()}", None)


def login_limiter() -> LoginRateLimiter:
    return current_app.extensions["login_rate_limiter"]


def client_ip() -> str:
    # ProxyFix sets remote_addr from the X-Forwarded-For value of the frontend nginx.
    return request.remote_addr or "unknown"
