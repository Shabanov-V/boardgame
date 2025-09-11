"""Simulator package for Viva Bureaucracia!.

Modules:
- utils: JSON loading and game data loading utilities
- core: Core game classes (Deck, Board, AI, Player, Game)
- stats: Statistics aggregation across runs
- runner: Single game run helper
- cli: Command-line interface entrypoint
"""

from .utils import load_json_file, load_game_data
from .core import Deck, Board, AI, Player, Game
from .stats import Statistics
from .runner import run_game_simulation

__all__ = [
    "load_json_file",
    "load_game_data",
    "Deck",
    "Board",
    "AI",
    "Player",
    "Game",
    "Statistics",
    "run_game_simulation",
]


