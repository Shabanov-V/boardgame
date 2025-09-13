"""Board game simulator package."""

from .entities.board import Board
from .entities.deck import Deck
from .entities.player import Player
from .entities.ai import AI

from .managers.event_manager import InteractiveEvent
from .managers.interaction_manager import InteractionManager
from .managers.trade_manager import TradeManager, TradeOffer
from .managers.elimination_manager import EliminationManager

from .mechanics.effects import EffectManager
from .mechanics.challenges import ChallengeManager

from .utils.constants import *
from .utils.helpers import *

__all__ = [
    'Board',
    'Deck',
    'Player',
    'AI',
    'InteractiveEvent',
    'InteractionManager',
    'TradeManager',
    'TradeOffer',
    'EliminationManager',
    'EffectManager',
    'ChallengeManager'
]