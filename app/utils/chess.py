from typing import Tuple
from app.models.game import BattleType, ColorAttachMode
import random


def get_default_battle_rules(game_type):
    default_rules = {
        BattleType.ultra: {
            "player_time": 15,
            "player_increment": 0,
            "opponent_time": 15,
            "opponent_increment": 0,
        },
        BattleType.bullet: {
            "player_time": 60,
            "player_increment": 0,
            "opponent_time": 60,
            "opponent_increment": 0,
        },
        BattleType.rapid: {
            "player_time": 600,
            "player_increment": 10,
            "opponent_time": 600,
            "opponent_increment": 10,
        },
        BattleType.blitz: {
            "player_time": 300,
            "player_increment": 3,
            "opponent_time": 300,
            "opponent_increment": 3,
        },
        BattleType.classic: {
            "player_time": 1800,
            "player_increment": 30,
            "opponent_time": 1800,
            "opponent_increment": 30,
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
