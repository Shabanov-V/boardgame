"""Combinatorial testing script for the board game."""

import json
import random
from collections import defaultdict
from simulator.game import Game

def load_config():
    """Load game configuration."""
    with open('boardgame/simulator/config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_game_data():
    """Load all game data."""
    game_data = {
        'game_constants': {
            'game_constants': {
                'max_action_cards': 5,
                'max_personal_items_hand': 3,
                'elimination_threshold': -1
            }
        }
    }
    
    # Load action cards
    with open('boardgame/actionCartds/action_cards.json', 'r', encoding='utf-8') as f:
        action_cards = json.load(f)
        game_data['action_cards'] = {'additional_action_cards': action_cards['action_cards']}
    
    # Load green cards
    with open('boardgame/greenCards/documents_work_cards.json', 'r', encoding='utf-8') as f:
        game_data['green_cards'] = json.load(f)
    
    # Load red cards
    with open('boardgame/redCards/health_cards.json', 'r', encoding='utf-8') as f:
        game_data['health_cards'] = json.load(f)
    with open('boardgame/redCards/housing_cards.json', 'r', encoding='utf-8') as f:
        game_data['housing_cards'] = json.load(f)
    
    # Load white cards
    with open('boardgame/whiteCards/random_events.json', 'r', encoding='utf-8') as f:
        game_data['white_cards'] = json.load(f)
    
    # Load personal items
    with open('boardgame/itemCards/utility_items.json', 'r', encoding='utf-8') as f:
        utility_items = json.load(f)
    with open('boardgame/itemCards/steal_effect_items.json', 'r', encoding='utf-8') as f:
        steal_items = json.load(f)
    game_data['personal_items'] = {
        'personal_items': utility_items['utility_items'],
        'steal_effect_cards': steal_items['steal_effect_items']
    }
    
    return game_data

class GameStats:
    def __init__(self):
        self.total_games = 0
        self.completed_games = 0
        self.wins_by_character = defaultdict(int)
        self.wins_by_goal = defaultdict(int)
        self.eliminations = defaultdict(int)
        self.elimination_reasons = defaultdict(int)
        self.resource_stats = defaultdict(lambda: {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0})
        self.goal_progress = defaultdict(lambda: {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0})
        self.incomplete_reasons = defaultdict(int)
        self.turn_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # char -> turn -> resource -> values
        
    def track_turn(self, turn_number, players):
        """Track resources for all players at given turn"""
        for player in players:
            if player.is_eliminated:
                continue
                
            # Track basic resources
            self.turn_stats[player.profile][turn_number]['money'].append(player.money)
            self.turn_stats[player.profile][turn_number]['nerves'].append(player.nerves)
            self.turn_stats[player.profile][turn_number]['items'].append(len(player.items) if hasattr(player, 'items') else 0)
            self.turn_stats[player.profile][turn_number]['documents'].append(player.document_level)
            self.turn_stats[player.profile][turn_number]['language'].append(player.language_level)
            
            # Track goal progress if exists
            if player.win_condition:
                self.turn_stats[player.profile][turn_number]['has_goal'] = True
                if hasattr(player, 'goal_progress'):
                    self.turn_stats[player.profile][turn_number]['goal_progress'].append(player.goal_progress)

def run_combinatorial_test(num_games=1000):
    """Run combinatorial testing of the game."""
    config = load_config()
    game_data = load_game_data()
    stats = GameStats()
    
    print(f"Starting combinatorial testing with {num_games} games...")
    
    for i in range(num_games):
        if i % 100 == 0:
            print(f"Running game {i+1}/{num_games}...")
        
        game = Game(config, game_data)
        winner = game.run()
        
        # Track state each turn
        current_turn = game.current_turn if hasattr(game, 'current_turn') else 0
        for player in game.players:
            if player.is_eliminated:
                continue
            
            # Track resources for all active players
            stats.turn_stats[player.profile][current_turn]['money'].append(player.money)
            stats.turn_stats[player.profile][current_turn]['nerves'].append(player.nerves)
            stats.turn_stats[player.profile][current_turn]['items'].append(len(player.items) if hasattr(player, 'items') else 0)
            stats.turn_stats[player.profile][current_turn]['documents'].append(player.document_level)
            stats.turn_stats[player.profile][current_turn]['language'].append(player.language_level)
            
            if player.win_condition:
                stats.turn_stats[player.profile][current_turn]['goal'].append(player.win_condition['key'])
                stats.turn_stats[player.profile][current_turn]['goal_progress'].append(game.calculate_win_progress(player))
        stats.total_games += 1
        
        if winner:
            stats.completed_games += 1
            stats.wins_by_character[winner.profile] += 1
            if winner.win_condition:
                stats.wins_by_goal[winner.win_condition['key']] += 1
        
        # Track eliminations
        for player in game.players:
            if player.is_eliminated:
                stats.eliminations[player.profile] += 1
                if player.nerves <= game_data['game_constants']['game_constants']['elimination_threshold']:
                    stats.elimination_reasons['nerves'] += 1
                elif player.money < 0:
                    stats.elimination_reasons['money'] += 1
            
            # Track resource stats
            for resource in ['money', 'nerves', 'document_level', 'language_level']:
                value = float(getattr(player, resource))
                resource_stats = stats.resource_stats[resource]
                resource_stats['min'] = min(resource_stats['min'], value)
                resource_stats['max'] = max(resource_stats['max'], value)
                resource_stats['sum'] += value
                resource_stats['count'] += 1
            
            # Track goal progress
            if player.win_condition:
                progress = game.calculate_win_progress(player)
                goal_stats = stats.goal_progress[player.profile]
                goal_stats['min'] = min(goal_stats['min'], progress)
                goal_stats['max'] = max(goal_stats['max'], progress)
                goal_stats['sum'] += progress
                goal_stats['count'] += 1
        
        # Track incomplete reasons
        if not winner:
            if game.end_reason == 'time_limit':
                stats.incomplete_reasons['time_limit'] += 1
            elif game.end_reason == 'elimination':
                stats.incomplete_reasons['all_eliminated'] += 1
    
    # Print results
    print("\n=== TEST RESULTS ===")
    print(f"\nTotal games: {stats.total_games}")
    print(f"Completed games: {stats.completed_games} ({stats.completed_games/stats.total_games*100:.1f}%)")
    
    print("\nWins by character:")
    total_wins = sum(stats.wins_by_character.values())
    for char, wins in stats.wins_by_character.items():
        print(f"  {char}: {wins} ({wins/stats.total_games*100:.1f}%)")
    
    print("\nWins by goal:")
    for goal, wins in stats.wins_by_goal.items():
        print(f"  {goal}: {wins} ({wins/stats.total_games*100:.1f}%)")
    
    print("\nEliminations:")
    for char, count in stats.eliminations.items():
        print(f"  {char}: {count} ({count/stats.total_games*100:.1f}%)")
    
    print("\nElimination reasons:")
    total_elims = sum(stats.elimination_reasons.values())
    if total_elims > 0:
        for reason, count in stats.elimination_reasons.items():
            print(f"  {reason}: {count} ({count/total_elims*100:.1f}%)")
    
    print("\nResource statistics:")
    for resource, resource_stats in stats.resource_stats.items():
        if resource_stats['count'] > 0:
            avg = resource_stats['sum'] / resource_stats['count']
            print(f"  {resource}:")
            print(f"    Min: {resource_stats['min']:.1f}")
            print(f"    Max: {resource_stats['max']:.1f}")
            print(f"    Avg: {avg:.1f}")
    
    print("\nGoal progress:")
    for char, goal_stats in stats.goal_progress.items():
        if goal_stats['count'] > 0:
            avg = goal_stats['sum'] / goal_stats['count']
            print(f"  {char}:")
            print(f"    Min: {goal_stats['min']*100:.1f}%")
            print(f"    Max: {goal_stats['max']*100:.1f}%")
            print(f"    Avg: {avg*100:.1f}%")
    
    print("\nIncomplete game reasons:")
    incomplete = stats.total_games - stats.completed_games
    if incomplete > 0:
        for reason, count in stats.incomplete_reasons.items():
            print(f"  {reason}: {count} ({count/incomplete*100:.1f}%)")
    
    # Calculate and save turn-by-turn statistics
    print("\nСохраняем статистику по ходам...")
    
    # Prepare data for JSON
    stats_by_turn = {
        'turns': {},
        'characters': list(stats.turn_stats.keys())
    }
    
    # Calculate averages for each turn
    for turn in range(0, 120):  # All turns
        turn_data = {
            'turn_number': turn,
            'characters': {}
        }
        
        for char in stats.turn_stats:
            if not stats.turn_stats[char][turn]['money']:  # Skip if no data
                continue
                
            char_data = {
                'money': sum(stats.turn_stats[char][turn]['money']) / len(stats.turn_stats[char][turn]['money']),
                'nerves': sum(stats.turn_stats[char][turn]['nerves']) / len(stats.turn_stats[char][turn]['nerves']),
                'items': sum(stats.turn_stats[char][turn]['items']) / len(stats.turn_stats[char][turn]['items']),
                'documents': sum(stats.turn_stats[char][turn]['documents']) / len(stats.turn_stats[char][turn]['documents']),
                'language': sum(stats.turn_stats[char][turn]['language']) / len(stats.turn_stats[char][turn]['language'])
            }
            
            # Add goal progress if available
            if stats.turn_stats[char][turn].get('goal_progress'):
                char_data['goal_progress'] = sum(stats.turn_stats[char][turn]['goal_progress']) / len(stats.turn_stats[char][turn]['goal_progress'])
            
            turn_data['characters'][char] = char_data
        
        if turn_data['characters']:  # Only save turns with data
            stats_by_turn['turns'][str(turn)] = turn_data
    
    # Save to JSON file
    with open('boardgame/stats/turn_by_turn_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats_by_turn, f, indent=2, ensure_ascii=False)
    
    print("Статистика сохранена в boardgame/stats/turn_by_turn_stats.json")
    
    # Print balance metrics
    print("\n=== BALANCE METRICS ===")
    
    # Character win rate spread
    if stats.wins_by_character:
        win_rates = [wins/stats.total_games*100 for wins in stats.wins_by_character.values()]
        win_rate_spread = max(win_rates) - min(win_rates)
        print(f"\nCharacter win rate spread: {win_rate_spread:.1f}% (target: 5%)")
    
    # Goal win rate spread
    if stats.wins_by_goal:
        goal_rates = [wins/stats.total_games*100 for wins in stats.wins_by_goal.values()]
        goal_rate_spread = max(goal_rates) - min(goal_rates)
        print(f"Goal win rate spread: {goal_rate_spread:.1f}% (target: 10%)")
    
    # Elimination rate
    total_players = stats.total_games * len(config['character_profiles'])
    total_eliminations = sum(stats.eliminations.values())
    elimination_rate = total_eliminations / total_players * 100
    print(f"Elimination rate: {elimination_rate:.1f}% (target: 10-15%)")
    
    # Game completion rate
    completion_rate = stats.completed_games / stats.total_games * 100
    print(f"Game completion rate: {completion_rate:.1f}% (target: 95%)")
    
    return stats

if __name__ == '__main__':
    run_combinatorial_test(100)  # Уменьшаем количество игр для ускорения тестирования