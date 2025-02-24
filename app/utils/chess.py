from typing import Tuple
from app.models.game import BattleType, ColorAttachMode
import random


def get_default_battle_rules(game_type):
    default_rules = {
        BattleType.ultra: {
            "player_time": 0.25,
            "player_increment": 5,
            "opponent_time": 0.25,
            "opponent_increment": 5,
        },
        BattleType.bullet: {
            "player_time": 1,
            "player_increment": 5,
            "opponent_time": 1,
            "opponent_increment": 5,
        },
        BattleType.rapid: {
            "player_time": 10,
            "player_increment": 10,
            "opponent_time": 10,
            "opponent_increment": 10,
        },
        BattleType.blitz: {
            "player_time": 3,
            "player_increment": 2,
            "opponent_time": 3,
            "opponent_increment": 2,
        },
        BattleType.classic: {
            "player_time": 30,
            "player_increment": 15,
            "opponent_time": 30,
            "opponent_increment": 15,
        },
    }

    return default_rules.get(game_type, {})


def get_random_color() -> Tuple[str, str]:
    color1, color2 = random.choice([("white", "black"), ("black", "white")])
    return color1, color2


def get_opposite_color(color: str) -> str:
    if color == "white":
        return "black"
    return "white"
