from fastapi import APIRouter

# from app.services.stockfish import get_best_move

router = APIRouter()


@router.get("/game")
async def game(board: str):
    try:
        # best_move = await get_best_move(board)
        return {"best_move": "best_move"}
    except Exception as e:
        print(e)
        return {"error": str(e)}
