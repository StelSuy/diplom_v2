"""
Server-side challenge store for replay attack protection.

The terminal requests a challenge from the server before each scan.
The server generates a random challenge, stores it with a TTL, and returns it.
When the terminal sends the signed challenge back, the server verifies
that the challenge was indeed issued by it AND hasn't been used yet.
"""
import secrets
import time
import threading
import logging

logger = logging.getLogger(__name__)

# challenge_token -> (terminal_id, created_at)
_challenges: dict[str, tuple[int, float]] = {}
_lock = threading.Lock()

# Challenge is valid for 30 seconds
CHALLENGE_TTL_SECONDS = 30

# Cleanup old challenges every 60 seconds
_CLEANUP_INTERVAL = 60


def generate_challenge(terminal_id: int) -> str:
    """Generate a new challenge for a terminal, store it, and return base64."""
    token = secrets.token_urlsafe(32)
    now = time.time()

    with _lock:
        _challenges[token] = (terminal_id, now)

    logger.debug(f"Challenge issued for terminal {terminal_id}: {token[:12]}…")
    return token


def consume_challenge(token: str, terminal_id: int) -> bool:
    """
    Validate and consume a challenge (one-time use).
    Returns True if valid, False otherwise.
    """
    now = time.time()

    with _lock:
        entry = _challenges.pop(token, None)

    if entry is None:
        logger.warning(f"Challenge not found or already used: {token[:12]}…")
        return False

    stored_terminal_id, created_at = entry

    if stored_terminal_id != terminal_id:
        logger.warning(
            f"Challenge terminal mismatch: expected {stored_terminal_id}, got {terminal_id}"
        )
        return False

    age = now - created_at
    if age > CHALLENGE_TTL_SECONDS:
        logger.warning(f"Challenge expired: age={age:.1f}s > TTL={CHALLENGE_TTL_SECONDS}s")
        return False

    logger.debug(f"Challenge consumed OK (age={age:.1f}s)")
    return True


def cleanup_expired():
    """Remove expired challenges from the store."""
    now = time.time()
    removed = 0

    with _lock:
        expired_keys = [
            k for k, (_, created_at) in _challenges.items()
            if now - created_at > CHALLENGE_TTL_SECONDS * 2
        ]
        for k in expired_keys:
            del _challenges[k]
            removed += 1

    if removed:
        logger.debug(f"Cleaned up {removed} expired challenges")
