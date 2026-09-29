import json
import asyncio
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.routing import haversine_distance
from app.safety import check_route_deviation


class ConnectionManager:
    def __init__(self):
        # Map ride_id -> set of active WebSockets
        self.ride_rooms: Dict[int, Set[WebSocket]] = {}
        # Map tracking_token -> set of active WebSockets
        self.token_rooms: Dict[str, Set[WebSocket]] = {}

    async def connect_ride(self, ride_id: int, websocket: WebSocket):
        await websocket.accept()
        if ride_id not in self.ride_rooms:
            self.ride_rooms[ride_id] = set()
        self.ride_rooms[ride_id].add(websocket)

    def disconnect_ride(self, ride_id: int, websocket: WebSocket):
        if ride_id in self.ride_rooms:
            self.ride_rooms[ride_id].discard(websocket)
            if not self.ride_rooms[ride_id]:
                del self.ride_rooms[ride_id]

    async def connect_token(self, token: str, websocket: WebSocket):
        await websocket.accept()
        if token not in self.token_rooms:
            self.token_rooms[token] = set()
        self.token_rooms[token].add(websocket)

    def disconnect_token(self, token: str, websocket: WebSocket):
        if token in self.token_rooms:
            self.token_rooms[token].discard(websocket)
            if not self.token_rooms[token]:
                del self.token_rooms[token]

    async def broadcast_ride(self, ride_id: int, message: Dict[str, Any]):
        if ride_id in self.ride_rooms:
            dead_sockets = []
            for ws in list(self.ride_rooms[ride_id]):
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.ride_rooms[ride_id].discard(ws)

    async def broadcast_token(self, token: str, message: Dict[str, Any]):
        if token in self.token_rooms:
            dead_sockets = []
            for ws in list(self.token_rooms[token]):
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.token_rooms[token].discard(ws)


ws_manager = ConnectionManager()
