from fastapi import APIRouter
from stockfish import Stockfish

# Path to your Stockfish executable
# STOCKFISH_PATH = r"C:\Users\ionst\OneDrive\Desktop\Programming\hackaton\chess-api\stockfish\stockfish-windows-x86-64-avx2.exe"

router = APIRouter()


async def get_best_move(board: str):
    try:
        # Initialize Stockfish
        # stockfish = Stockfish(path=STOCKFISH_PATH)

        # # Set the board position
        # stockfish.set_fen_position(board)

        # # Get the best move in UCI format
        # best_move = stockfish.get_best_move()

        return {"best_move": "best_move"}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
