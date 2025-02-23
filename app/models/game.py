from requests import Session
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BattleType(str, enum.Enum):
    ultra = "ultra"
    bullet = "bullet"
    rapid = "rapid"
    blitz = "blitz"
    classic = "classic"


class ColorAttachMode(str, enum.Enum):
    white = "white"
    black = "black"
    random = "random"


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(BattleType), nullable=False)
    is_rating = Column(Boolean, default=False)
    games_count = Column(Integer, nullable=False)
    player_time = Column(Integer, nullable=False)  # Time in seconds
    player_increment = Column(Integer, nullable=False)
    opponent_time = Column(Integer, nullable=False)
    opponent_increment = Column(Integer, nullable=False)
    color_attach_mode = Column(Enum(ColorAttachMode), nullable=False)
    with_armaghedon = Column(Boolean, default=False)

    games = relationship("Game", back_populates="battle")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(BattleType), nullable=False)
    is_rating = Column(Boolean, default=False)
    moves = Column(JSON, default=[])  # Stores moves as JSON

    player_id = Column(Integer, ForeignKey("users.id"))
    opponent_id = Column(Integer, ForeignKey("users.id"))
    player_color = Column(
        Boolean, nullable=False
    )  # True = player is white, False = opponent is white
    battle_id = Column(Integer, ForeignKey("battles.id"))

    player = relationship("User", foreign_keys=[player_id])
    opponent = relationship("User", foreign_keys=[opponent_id])
    battle = relationship("Battle", back_populates="games")


def create_battle(db: Session, battle_data):
    db_battle = Battle(
        type=battle_data.type,
        is_rating=battle_data.is_rating,
        games_count=battle_data.games_count,
        player_time=battle_data.player_time,
        player_increment=battle_data.player_increment,
        opponent_time=battle_data.opponent_time,
        opponent_increment=battle_data.opponent_increment,
        color_attach_mode=battle_data.color_attach_mode,
        with_armaghedon=battle_data.with_armaghedon,
    )
    db.add(db_battle)
    db.commit()
    db.refresh(db_battle)
    return db_battle


def create_game(db: Session, game_data):
    db_game = Game(
        type=game_data.type,
        is_rating=game_data.is_rating,
        player_id=game_data.player_id,
        opponent_id=game_data.opponent_id,
        player_color=game_data.player_color,
        battle_id=game_data.battle_id,
        moves=game_data.moves,
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game
