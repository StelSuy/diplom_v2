"""
Simple in-memory rate limiter for terminal endpoints.

Protects /terminal/scan, /terminal/secure-scan, /terminal/challenge, /register/first-scan
from brute-force and abuse.
"""
import time
import threading
import logging
from collections import defaultdict

from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# Config
WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 120  # per IP

_counts: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()


def _cleanup_window(timestamps: list[float], now: float) -> list[float]:
    """Remove timestamps older than the window."""
    cutoff = now - WINDOW_SECONDS
    return [t for t in timestamps if t > cutoff]


def check_rate_limit(request: Request):
    """
    FastAPI dependency that rate-limits by client IP.
    Raises 429 if limit exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    with _lock:
        _counts[client_ip] = _cleanup_window(_counts[client_ip], now)

        if len(_counts[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
            logger.warning(f"Rate limit exceeded for {client_ip}: {len(_counts[client_ip])} req/{WINDOW_SECONDS}s")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        _counts[client_ip].append(now)


def cleanup_all():
    """Periodic cleanup of stale entries."""
    now = time.time()
    with _lock:
        stale = [ip for ip, ts in _counts.items() if not _cleanup_window(ts, now)]
        for ip in stale:
            del _counts[ip]
