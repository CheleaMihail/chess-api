from datetime import datetime
from itertools import islice
import logging
import random
import chess
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List, Set, Optional, TypedDict
from requests import Session
from app.database import SessionLocal, get_db
from app import crud
import time
from contextlib import asynccontextmanager
from app.utils.chess import (
    get_default_battle_rules,
    get_opposite_color,
    get_random_color,
)
from app.models.game import Battle, ColorAttachMode, Game, create_battle, create_game

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class BroadcastData(TypedDict):
    fen: str
    message: Optional[str]


class ChessRoomManager:
    def __init__(self):
        self.rooms = {}
        self.user_connections = {}

    async def create_room(
        self,
        websocket: WebSocket,
        user_id: str,
        game_type: Optional[str] = None,
        is_rating: Optional[bool] = False,
        games_count: Optional[int] = 1,
        player_time: Optional[int] = 300,
        player_increment: Optional[int] = 0,
        opponent_time: Optional[int] = 300,
        opponent_increment: Optional[int] = 0,
        color_attach_mode: Optional[str] = "random",
        with_armaghedon: Optional[bool] = False,
        fen: Optional[str] = None,
    ):
        await websocket.accept()

        self.remove_created_room(user_id)

        board = chess.Board(fen)

        room = {
            "connect_status": "pending",
            "battle_id": None,
            "is_rating": is_rating,
            "game_type": game_type,
            "games_count": games_count,
            "opponent_time": opponent_time,
            "opponent_increment": opponent_increment,
            "color_attach_mode": color_attach_mode,
            "with_armaghedon": with_armaghedon,
            "active_board": {
                "game_id": None,
                "board": board,
                "fen": board.fen(),
                "white": None,
                "black": None,
                "moves": [],
                "start_time": datetime.now().timestamp(),
            },
            "players": {user_id: {"time": player_time, "increment": player_increment}},
            "messages": [],
        }

        self.rooms[user_id] = room

        game = self.get_game_preview(room, user_id, user_id)

        await websocket.send_json(
            {
                "message": f"Created new room {user_id}",
                "op": "created",
                "game": game,
            }
        )

    async def connect_with_room_id(
        self,
        db: Session,
        websocket: WebSocket,
        user_id: str,
        room_id: Optional[str],
    ):
        await websocket.accept()

        if room_id:
            # Check if room exists and is in 'pending player' status
            if room_id in self.rooms:
                await self.join_room(room_id, user_id, websocket, db)
            else:
                await websocket.send_json(
                    {"message": f"Room {room_id} is not available."}
                )

    async def connect_by_game_type(
        self,
        db: Session,
        websocket: WebSocket,
        user_id: str,
        game_type: Optional[str],
    ):
        await websocket.accept()

        if game_type:
            # Check if room exists and is in 'pending player' status
            room_id = self.find_pending_room(game_type)

            if room_id in self.rooms:
                await self.join_room(room_id, user_id, websocket, db)
            else:
                self.remove_created_room(user_id)

                board = chess.Board()

                default_room_values = get_default_battle_rules(game_type)

                room = {
                    "connect_status": "pending",
                    "battle_id": None,
                    "is_rating": False,
                    "game_type": game_type,
                    "games_count": 1,
                    "opponent_time": default_room_values["opponent_time"],
                    "opponent_increment": default_room_values["opponent_increment"],
                    "color_attach_mode": "random",
                    "with_armaghedon": False,
                    "active_board": {
                        "game_id": None,
                        "board": board,
                        "fen": board.fen(),
                        "white": None,
                        "black": None,
                        "moves": [],
                        "start_time": datetime.now().timestamp(),
                    },
                    "players": {
                        user_id: {
                            "time": default_room_values["player_time"],
                            "increment": default_room_values["player_increment"],
                        }
                    },
                    "messages": [],
                }

                self.rooms[user_id] = room

                game = self.get_game_preview(room, user_id, user_id)

                await websocket.send_json(
                    {
                        "message": f"Created new room {user_id}",
                        "op": "created",
                        "game": game,
                    }
                )

    async def make_move(
        self,
        move: str,
        websocket: WebSocket,
        room_id: Optional[str],
        user_id: Optional[str] = None,
    ):

        if not room_id or room_id not in self.rooms:
            await websocket.send_json({"message": "Game not found."})
            return

        # Retrieve the current room's game state
        room = self.rooms[room_id]
        if room["connect_status"] == "pending":
            await websocket.send_json(
                {"message": "Game not started. Waiting for player."}
            )
            return

        board = room["active_board"]["board"]

        # Determine current player's turn
        turn_color = "white" if board.turn == chess.WHITE else "black"

        player_id = room["active_board"][turn_color]

        if user_id and user_id != player_id:
            await websocket.send_json(
                {
                    "message": "Not your turn!",
                    "op": "move",
                    "fen": board.fen(),
                }
            )
            return

        try:
            # Try to create a chess move from UCI notation
            chess_move = chess.Move.from_uci(move)

            # Check if the move is legal
            if chess_move in board.legal_moves:
                board.push(chess_move)  # Make the move

                # Broadcast the move to other players in the room
                room["active_board"]["moves"].append(
                    {
                        "move": move,
                        "color": turn_color,
                        "time": datetime.now().timestamp(),
                    }
                )

                room["active_board"]["fen"] = board.fen()

                game_over_reason = None

                if board.is_checkmate():
                    game_over_reason = "Checkmate! Game Over."
                elif board.is_stalemate():
                    game_over_reason = "Stalemate! The game is a draw."
                elif board.is_insufficient_material():
                    game_over_reason = "Draw! Insufficient material."
                elif board.can_claim_fifty_moves():
                    game_over_reason = "Draw! 50-move rule."
                elif board.can_claim_threefold_repetition():
                    game_over_reason = "Draw! Threefold repetition."

                if game_over_reason:
                    room["connect_status"] = "finished"
                    await self.broadcast_move(
                        room,
                        board.fen(),
                        room["active_board"]["moves"],
                        game_over_reason,
                    )
                else:
                    # Transmite mutarea către ceilalți jucători
                    await self.broadcast_move(
                        room, board.fen(), room["active_board"]["moves"], ""
                    )
            else:
                await websocket.send_json(
                    {
                        "message": "Illegal move!",
                        "op": "move",
                        "fen": board.fen(),
                    }
                )

        except ValueError:
            await websocket.send_json(
                {
                    "message": "Invalid move format. Use UCI (e.g., e2e4).",
                    "op": "move",
                    "fen": board.fen(),
                }
            )

    async def broadcast_move(self, room, fen: str, moves, game_over_reason):
        for user_id in room["players"]:
            websocket = self.get_websocket_by_user_id(user_id)
            if websocket:
                await websocket.send_json(
                    {
                        "message": f"Moved {fen}",
                        "op": "move",
                        "fen": fen,
                        "moves": moves,
                        "gameOverReason": game_over_reason,
                    }
                )

    async def broadcast_remove(self, room_id):
        for user_id in self.rooms[room_id]["players"]:
            websocket = self.get_websocket_by_user_id(user_id)
            if websocket:
                await websocket.send_json(
                    {
                        "message": f"Game Canceled",
                        "op": "removed",
                        "connectedStatus": "removed",
                    }
                )

    def get_websocket_by_user_id(self, user_id: str) -> Optional[WebSocket]:
        return self.user_connections.get(user_id)

    async def join_room(
        self,
        room_id: Optional[str],
        user_id: str,
        ws: WebSocket,
        db: Session,
    ):
        # Check if the user is already in the room by user_id
        room = self.rooms[room_id]

        if user_id in room["players"]:
            opponent_id = self.get_opponent_id(room, user_id)

            await ws.send_json(
                {
                    "message": f"Reconnected to room {room_id}",
                    "op": "connected",
                    "game": self.get_game(room, room_id, user_id, opponent_id),
                }
            )
        else:
            opponent_id = self.get_opponent_id(room, user_id)

            # current user is connecting opponents room, opponent set it's time
            room["players"][user_id] = {
                "time": room["opponent_time"],
                "increment": room["opponent_increment"],
            }

            color_attach_mode = room["color_attach_mode"]

            if color_attach_mode == ColorAttachMode.random:
                color1, color2 = get_random_color()
                room["active_board"][color1] = user_id
                room["active_board"][color2] = opponent_id
            else:
                room["active_board"][color_attach_mode] = user_id
                room["active_board"][
                    get_opposite_color(color_attach_mode)
                ] = opponent_id

            room["connect_status"] = "connected"

            if "." not in user_id and "." not in room_id:
                battle_data = {
                    "type": room["game_type"],
                    "games_count": room["games_count"],
                    "player_time": room["players"][user_id]["time"],
                    "player_increment": room["players"][user_id]["increment"],
                    "opponent_time": room["players"][user_id]["time"],
                    "opponent_increment": room["players"][user_id]["increment"],
                    "color_attach_mode": room["color_attach_mode"],
                    "with_armaghedon": room["with_armaghedon"],
                }

                battle = create_battle(db, Battle(**battle_data))
                color = "white" if room["active_board"]["white"] == user_id else "black"

                game_data = {
                    "type": battle.type,
                    "is_rating": battle.is_rating,
                    "battle_id": battle.id,
                    "player_id": user_id,
                    "opponent_id": opponent_id,
                    "player_color": color == "white",
                    "moves": [],
                }

                create_game(db, Game(**game_data))

            await self.initiate_players(room, room_id)

    async def initiate_players(self, room, room_id):
        for user_id in room["players"]:
            logger.debug("initiate_players ${user_id}")
            websocket = self.get_websocket_by_user_id(user_id)
            opponent_id = self.get_opponent_id(room, user_id)
            if websocket:
                await websocket.send_json(
                    {
                        "message": f"Initialized room {room_id}",
                        "op": "connected",
                        "game": self.get_game(room, room_id, user_id, opponent_id),
                    }
                )

    def get_opponent_id(self, room, user_id):
        players = list(room["players"].keys())
        for player in players:
            if player != user_id:
                return player
        return None

    def get_game_preview(self, room, room_id, user_id):
        color = "white" if room["active_board"]["white"] == user_id else "black"

        return {
            "roomId": user_id,
            "connectStatus": room["connect_status"],
            "battleId": room["battle_id"],
            "gameId": room["active_board"]["game_id"],
            "type": room["game_type"],
            "isRating": room["is_rating"],
            "gamesCount": room["games_count"],
            "playerTime": room["players"][user_id]["time"],
            "playerIncrement": room["players"][user_id]["increment"],
            "opponentId": "",
            "opponentTime": room["opponent_time"],
            "opponentIncrement": room["opponent_increment"],
            "withArmaghedon": room["with_armaghedon"],
            "messages": room["messages"],
            "activeBoard": {
                "fen": room["active_board"]["fen"],
                "playerColor": color,
                "moves": room["active_board"]["moves"],
            },
        }

    def get_game(self, room, room_id, user_id, opponent_id):
        color = "white" if room["active_board"]["white"] == user_id else "black"

        return {
            "roomId": room_id,
            "connectStatus": room["connect_status"],
            "battleId": room["battle_id"],
            "gameId": room["active_board"]["game_id"],
            "type": room["game_type"],
            "isRating": room["is_rating"],
            "gamesCount": room["games_count"],
            "playerTime": room["players"][user_id]["time"],
            "playerIncrement": room["players"][user_id]["increment"],
            "opponentId": opponent_id,
            "opponentTime": room["players"][opponent_id]["time"],
            "opponentIncrement": room["players"][opponent_id]["increment"],
            "withArmaghedon": room["with_armaghedon"],
            "messages": room["messages"],
            "activeBoard": {
                "fen": room["active_board"]["fen"],
                "playerColor": color,
                "moves": room["active_board"]["moves"],
            },
        }

    def find_pending_room(self, game_type):
        for room_id, room in self.rooms.items():
            if room["connect_status"] == "pending" and room["game_type"] == game_type:
                return room_id  # Returnează primul room_id găsit
        return None

    def remove_created_room(self, user_id):
        if user_id in self.rooms:
            del self.rooms[user_id]
        return

    def remove_unconnected_room(self, user_id):
        if user_id in self.rooms:
            if self.rooms[user_id]["connect_status"] == "pending":
                del self.rooms[user_id]
        return

    def remove_room(
        self,
        room_id: Optional[str],
    ):
        self.broadcast_remove(room_id)

    async def connect(self, websocket: WebSocket, user_id: str):
        self.user_connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        if user_id in self.user_connections:
            self.remove_unconnected_room(user_id)
            del self.user_connections[user_id]


manager = ChessRoomManager()

router = APIRouter()


@router.websocket("/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    op: str,
    user_id: str,
    room_id: Optional[str] = None,
    game_type: Optional[str] = None,
    is_rating: Optional[bool] = False,
    games_count: Optional[int] = 1,
    player_time: Optional[int] = 300,
    player_increment: Optional[int] = 0,
    opponent_time: Optional[int] = 300,
    opponent_increment: Optional[int] = 0,
    color_attach_mode: Optional[str] = "random",
    with_armaghedon: Optional[bool] = False,
    fen: Optional[str] = None,
):
    await manager.connect(websocket, user_id)

    db: Session = SessionLocal()

    params = websocket.query_params

    if op == "connect":
        if room_id:
            await manager.connect_with_room_id(
                db,
                websocket,
                user_id,
                room_id,
            )
    if op == "remove":
        if room_id:
            await manager.remove_room(room_id)
    elif op == "search":
        if game_type:
            await manager.connect_by_game_type(
                db,
                websocket,
                user_id,
                game_type,
            )
    elif op == "create":
        is_rating = params.get("is_rating", is_rating) == "true"
        game_type = params.get("game_type", game_type)
        games_count = int(params.get("games_count", games_count))
        player_time = int(params.get("player_time", player_time))
        player_increment = int(params.get("player_increment", player_increment))
        opponent_time = int(params.get("opponent_time", opponent_time))
        opponent_increment = int(params.get("opponent_increment", opponent_increment))
        color_attach_mode = params.get("color_attach_mode", color_attach_mode)
        with_armaghedon = params.get("with_armaghedon", with_armaghedon) == "true"
        fen = params.get("fen", fen)

        await manager.create_room(
            websocket,
            user_id,
            game_type,
            is_rating,
            games_count,
            player_time,
            player_increment,
            opponent_time,
            opponent_increment,
            color_attach_mode,
            with_armaghedon,
            fen,
        )

    try:
        while True:
            data = await websocket.receive_json()
            if "move" not in data or "room_id" not in data:
                await websocket.send_json(
                    {
                        "message": "Invalid message format. 'move' and 'room_id' are required."
                    }
                )
                continue

            # manager.last_interaction[user_id] = time.time()
            await manager.make_move(data["move"], websocket, data["room_id"], user_id)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)

    # async def message_reponse(ws, message, room_id, fen, color):
    #     await ws.send_json(
    #         {
    #             message,
    #             room_id,
    #             fen,
    #             color,
    #         }
    #     )
    #     return


# async def inactivity_task():
#     while True:
#         await manager.handle_inactivity(timeout=30)  # Check inactivity every 30 seconds
#         await asyncio.sleep(30)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     task = asyncio.create_task(inactivity_task())
#     try:
#         yield
#     finally:
#         task.cancel()
#         await task


# async def handle_inactivity(self, timeout: int = 30):
#     """Check for inactive players and disconnect them after the timeout"""
#     current_time = time.time()
#     for user_id, last_interaction in list(self.last_interaction.items()):
#         if current_time - last_interaction > timeout:
#             # Find the room the user is in and remove them
#             for room_id, info in self.rooms.items():
#                 if any(ws == user_id for ws in info["players"]):
#                     info["players"] = {
#                         ws for ws in info["players"] if ws != user_id
#                     }
#                     # Remove the room if it's empty
#                     if not info["players"]:
#                         del self.rooms[room_id]
#                     break
#             # Remove user from last_interaction
#             del self.last_interaction[user_id]
