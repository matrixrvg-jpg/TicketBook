from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Maps event_id to a list of active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, event_id: int):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, websocket: WebSocket, event_id: int):
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)
            if not self.active_connections[event_id]:
                del self.active_connections[event_id]

    async def broadcast_to_event(self, event_id: int, message: dict):
        """
        Broadcast a JSON message to all clients watching a specific event.
        """
        if event_id in self.active_connections:
            # We copy the list to safely iterate in case connections drop
            connections = self.active_connections[event_id].copy()
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    # Client disconnected unexpectedly
                    pass

# A global singleton instance that we can import anywhere
manager = ConnectionManager()
