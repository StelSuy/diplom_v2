"""
WebSocket endpoint for live scan updates on the admin dashboard.

Connect: ws://<host>/ws/scans
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/scans")
async def ws_scans(ws: WebSocket):
    """
    Admin dashboard connects here to receive live scan events.
    Messages sent TO the server are ignored (one-way push).
    """
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep connection alive; ignore any incoming messages
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)
