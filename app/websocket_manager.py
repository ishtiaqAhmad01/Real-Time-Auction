"""WebSocket Connection Manager — room-based registry for live auction feeds."""

import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

# Message type constants
MSG_PLACE_BID = "PLACE_BID"
MSG_PING = "PING"
MSG_BID_ACCEPTED = "BID_ACCEPTED"
MSG_BID_REJECTED = "BID_REJECTED"
MSG_NEW_BID = "NEW_BID"
MSG_AUCTION_LOCKED = "AUCTION_LOCKED"
MSG_AUCTION_ACTIVATED = "AUCTION_ACTIVATED"
MSG_WINNER_ANNOUNCED = "WINNER_ANNOUNCED"
MSG_INIT = "INIT"
MSG_VIEWER_UPDATE = "VIEWER_UPDATE"
MSG_ERROR = "ERROR"
MSG_PONG = "PONG"


class ConnectionManager:
    def __init__(self):
        # Room-based: auction_id → set of active WebSocket connections
        self.active_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, auction_id: str) -> None:
        """Accept connection and register in auction room."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[auction_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, auction_id: str) -> None:
        """Remove connection from auction room."""
        async with self._lock:
            self.active_connections[auction_id].discard(websocket)
            if not self.active_connections[auction_id]:
                del self.active_connections[auction_id]

    async def broadcast_to_auction(self, auction_id: str, message: dict) -> None:
        """Send JSON message to ALL clients watching an auction."""
        connections = self.active_connections.get(auction_id, set()).copy()
        dead = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.add(websocket)
        # Clean up dead connections
        if dead:
            async with self._lock:
                self.active_connections[auction_id] -= dead

    def get_viewer_count(self, auction_id: str) -> int:
        return len(self.active_connections.get(auction_id, set()))


# Singleton instance — import this in routers
manager = ConnectionManager()
