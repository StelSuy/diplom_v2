"""
WebSocket connection manager for live scan updates.

Usage:
    from app.ws.manager import ws_manager

    # broadcast new scan event to all connected admin clients
    await ws_manager.broadcast({"type": "new_scan", ...})
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for the admin dashboard."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info(f"WS connected. Total clients: {len(self._connections)}")

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info(f"WS disconnected. Total clients: {len(self._connections)}")

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Send JSON message to all connected clients."""
        if not self._connections:
            return

        payload = json.dumps(data, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []

        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


ws_manager = ConnectionManager()
