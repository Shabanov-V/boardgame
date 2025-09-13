"""Tests for main Game class."""

import unittest
from ..simulator.game import Game

class TestGame(unittest.TestCase):
    """Test cases for Game class."""
    
    def setUp(self):
        self.config = {
            'game_parameters': {
                'number_of_players': 2,
                'board_size': 10,
                'cell_frequencies': {
                    'green': 4,
                    'red': 3,
                    'white': 3
                }
            },
            'character_profiles': [
                {
                    'id': 'player1',
                    'name': 'Player 1',
                    'starting_money': 10,
                    'starting_nerves': 5,
                    'starting_language': 1,
                    'starting_housing': 'room',
                    'salary': 5,
                    'housing_cost': 1
                },
                {
                    'id': 'player2',
                    'name': 'Player 2',
                    'starting_money': 10,
                    'starting_nerves': 5,
                    'starting_language': 1,
                    'starting_housing': 'room',
                    'salary': 5,
                    'housing_cost': 1
                }
            ],
            'simulation_parameters': {
                'ai_nerve_threshold': 3
            },
            'win_conditions': {
                'test_goal': {
                    'description': 'Test Goal',
                    'requires': {
                        'money': 20,
                        'document_level': 3
                    }
                }
            }
        }
        self.game_data = {
            'game_constants': {
                'game_constants': {
                    'max_action_cards': 5,
                    'max_personal_items_hand': 3,
                    'elimination_threshold': -1
                }
            },
            'action_cards': {
                'additional_action_cards': []
            },
            'green_cards': {
                'green_cards': []
            },
            'health_cards': {
                'health_cards': []
            },
            'housing_cards': {
                'housing_cards': []
            },
            'white_cards': {
                'random_events': []
            }
        }
        self.game = Game(self.config, self.game_data)
    
    def test_initialization(self):
        """Test game initialization."""
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.turn, 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)
        self.assertIsNone(self.game.end_reason)
    
    def test_setup_decks(self):
        """Test deck setup."""
        self.assertIn('action', self.game.decks)
        self.assertIn('green', self.game.decks)
        self.assertIn('red', self.game.decks)
        self.assertIn('white', self.game.decks)
    
    def test_setup_players(self):
        """Test player setup."""
        for player in self.game.players:
            self.assertEqual(player.money, 10)
            self.assertEqual(player.nerves, 5)
            self.assertEqual(player.language_level, 1)
            self.assertEqual(player.housing, 'room')
            self.assertEqual(player.housing_level, 1)
            self.assertEqual(player.document_level, 0)
            self.assertIsNone(player.win_condition)
            self.assertFalse(player.goal_chosen)
    
    def test_check_goal_selection(self):
        """Test goal selection."""
        player = self.game.players[0]
        
        # Test before document level 5
        self.game.check_goal_selection(player)
        self.assertIsNone(player.win_condition)
        self.assertFalse(player.goal_chosen)
        
        # Test at document level 5
        player.document_level = 5
        self.game.check_goal_selection(player)
        self.assertIsNotNone(player.win_condition)
        self.assertTrue(player.goal_chosen)
    
    def test_check_win_condition(self):
        """Test win condition check."""
        player = self.game.players[0]
        player.document_level = 5
        self.game.check_goal_selection(player)
        
        # Test before meeting requirements
        self.game.check_win_condition(player)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)
        
        # Test after meeting requirements
        player.money = 20
        player.document_level = 3
        self.game.check_win_condition(player)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, player)
        self.assertEqual(self.game.end_reason, 'win')
    
    def test_handle_lap_completion(self):
        """Test lap completion."""
        player = self.game.players[0]
        old_money = player.money
        old_docs = player.document_cards
        
        self.game.handle_lap_completion()
        
        # Check salary and housing cost
        expected_money = old_money + player.salary - player.housing_cost
        self.assertEqual(player.money, expected_money)
        
        # Check document cards
        self.assertEqual(player.document_cards, old_docs + 2)
    
    def test_run_game(self):
        """Test running a complete game."""
        # Run game until completion
        winner = self.game.run()
        
        # Game should be over
        self.assertTrue(self.game.game_over)
        
        # Should have a winner or time limit
        if winner:
            self.assertEqual(self.game.end_reason, 'win')
            self.assertEqual(self.game.winner, winner)
        else:
            self.assertEqual(self.game.end_reason, 'time_limit')

if __name__ == '__main__':
    unittest.main()

