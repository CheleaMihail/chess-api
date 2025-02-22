from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ChessRoomManager:
    def __init__(self):
        self.rooms: Dict[str, set] = {}  # room_id -> set of WebSocket connections

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    async def disconnect(self, room_id: str, websocket: WebSocket):
        self.rooms[room_id].remove(websocket)
        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: str):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                await connection.send_text(message)

manager = ChessRoomManager()

# WebSocket endpoint
from fastapi import APIRouter
router = APIRouter()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(room_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(room_id, websocket)
