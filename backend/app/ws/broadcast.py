"""
Helper to broadcast scan events from synchronous (non-async) route handlers.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)


def broadcast_scan_event(event_data: dict[str, Any]) -> None:
    """
    Fire-and-forget broadcast from a sync context.
    Safe to call from synchronous FastAPI route handlers running under uvicorn.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.broadcast(event_data))
        else:
            loop.run_until_complete(ws_manager.broadcast(event_data))
    except RuntimeError:
        # No event loop — skip silently (e.g. during tests)
        logger.debug("No event loop available for WS broadcast")
