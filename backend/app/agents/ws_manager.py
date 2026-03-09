"""WebSocket connection manager for real-time agent streaming."""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per case_id."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, case_id: str, websocket: WebSocket):
        await websocket.accept()
        if case_id not in self.active_connections:
            self.active_connections[case_id] = set()
        self.active_connections[case_id].add(websocket)
        logger.info(f"WebSocket connected for case {case_id}")

    def disconnect(self, case_id: str, websocket: WebSocket):
        if case_id in self.active_connections:
            self.active_connections[case_id].discard(websocket)
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]
        logger.info(f"WebSocket disconnected for case {case_id}")

    async def broadcast(self, case_id: str, data: dict):
        if case_id not in self.active_connections:
            return
        message = json.dumps(data)
        dead = set()
        for ws in self.active_connections[case_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections[case_id].discard(ws)


ws_manager = ConnectionManager()
