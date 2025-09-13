"""Tests for game entities."""

import unittest
from ..simulator.entities.deck import Deck
from ..simulator.entities.board import Board
from ..simulator.entities.player import Player
from ..simulator.entities.ai import AI

class TestDeck(unittest.TestCase):
    """Test cases for Deck class."""
    
    def setUp(self):
        self.test_cards = [
            {"id": "card1", "name": "Test Card 1"},
            {"id": "card2", "name": "Test Card 2"},
            {"id": "card3", "name": "Test Card 3"}
        ]
        self.deck = Deck(self.test_cards)
    
    def test_draw(self):
        """Test drawing cards."""
        # Draw all cards
        cards = []
        for _ in range(3):
            card = self.deck.draw()
            self.assertIsNotNone(card)
            cards.append(card)
        
        # Deck should be empty
        self.assertEqual(len(self.deck.cards), 0)
        
        # Draw from empty deck
        card = self.deck.draw()
        self.assertIsNone(card)
    
    def test_discard(self):
        """Test discarding cards."""
        card = self.deck.draw()
        self.deck.discard(card)
        self.assertEqual(len(self.deck.discard_pile), 1)
        
        # Draw from empty deck should reshuffle discard pile
        self.deck.draw()  # Draw remaining 2 cards
        self.deck.draw()
        card = self.deck.draw()  # Should reshuffle discard pile
        self.assertIsNotNone(card)
        self.assertEqual(len(self.deck.discard_pile), 0)

class TestBoard(unittest.TestCase):
    """Test cases for Board class."""
    
    def setUp(self):
        self.config = {
            'game_parameters': {
                'board_size': 10,
                'cell_frequencies': {
                    'green': 4,
                    'red': 3,
                    'white': 3
                }
            }
        }
        self.board = Board(self.config)
    
    def test_board_size(self):
        """Test board initialization."""
        self.assertEqual(len(self.board.cells), 10)
    
    def test_get_cell_type(self):
        """Test getting cell types."""
        # Test position wrapping
        pos = 15  # > board size
        cell_type = self.board.get_cell_type(pos)
        self.assertIn(cell_type, ['green', 'red', 'white'])
        
        # Test cell frequencies
        frequencies = {'green': 0, 'red': 0, 'white': 0}
        for cell in self.board.cells:
            frequencies[cell] += 1
        
        self.assertEqual(frequencies['green'], 4)
        self.assertEqual(frequencies['red'], 3)
        self.assertEqual(frequencies['white'], 3)

class TestPlayer(unittest.TestCase):
    """Test cases for Player class."""
    
    def setUp(self):
        self.profile = {
            'id': 'test_player',
            'name': 'Test Player',
            'starting_money': 10,
            'starting_nerves': 5,
            'starting_language': 1,
            'starting_housing': 'room',
            'salary': 5,
            'housing_cost': 1
        }
        self.config = {'simulation_parameters': {'ai_nerve_threshold': 3}}
        self.game_constants = {
            'game_constants': {
                'max_action_cards': 5,
                'max_personal_items_hand': 3
            }
        }
        self.player = Player(self.profile, None, self.config, self.game_constants)
    
    def test_initialization(self):
        """Test player initialization."""
        self.assertEqual(self.player.money, 10)
        self.assertEqual(self.player.nerves, 5)
        self.assertEqual(self.player.language_level, 1)
        self.assertEqual(self.player.housing, 'room')
        self.assertEqual(self.player.housing_level, 1)
        self.assertEqual(self.player.document_level, 0)
    
    def test_document_level(self):
        """Test document level property."""
        self.player.document_level = 5
        self.assertEqual(self.player.document_level, 5)
        
        # Test max level
        self.player.document_level = 10
        self.assertEqual(self.player.document_level, 7)
    
    def test_personal_items(self):
        """Test personal items management."""
        # Add items
        self.player.add_personal_items(2)
        self.assertEqual(len(self.player.personal_items_hand), 2)
        
        # Try to exceed limit
        self.player.add_personal_items(2)
        self.assertEqual(len(self.player.personal_items_hand), 3)  # Max limit
        
        # Force discard excess
        self.player.force_discard_excess_personal_items()
        self.assertEqual(len(self.player.personal_items_hand), 3)

class TestAI(unittest.TestCase):
    """Test cases for AI class."""
    
    def setUp(self):
        self.profile = {
            'id': 'test_player',
            'name': 'Test Player',
            'starting_money': 10,
            'starting_nerves': 5,
            'starting_language': 1,
            'starting_housing': 'room',
            'salary': 5,
            'housing_cost': 1
        }
        self.config = {'simulation_parameters': {'ai_nerve_threshold': 3}}
        self.game_constants = {
            'game_constants': {
                'max_action_cards': 5,
                'max_personal_items_hand': 3
            }
        }
        self.player = Player(self.profile, None, self.config, self.game_constants)
        self.ai = AI(self.player, self.config)
    
    def test_grudges(self):
        """Test grudge system."""
        self.ai.add_grudge('enemy1', 2)
        self.assertEqual(self.ai.grudges['enemy1'], 2)
        
        self.ai.reduce_grudge('enemy1')
        self.assertEqual(self.ai.grudges['enemy1'], 1)
        
        self.ai.reduce_grudge('enemy1', 2)
        self.assertNotIn('enemy1', self.ai.grudges)
    
    def test_item_evaluation(self):
        """Test item evaluation logic."""
        test_item = {
            'type': 'attack',
            'effects': {'nerves': 2, 'money': 3},
            'when_to_play': 'anytime'
        }
        
        self.assertTrue(self.ai._is_aggressive_item(test_item))
        self.assertTrue(self.ai._is_defensive_item(test_item))
        self.assertTrue(self.ai._can_use_item_now(test_item, 'anytime'))

if __name__ == '__main__':
    unittest.main()

