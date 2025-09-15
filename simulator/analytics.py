#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Game Analytics System
Tracks all game mechanics, card usage, and game flow
"""

import json
import time
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional


class GameAnalytics:
    """Comprehensive analytics system for tracking all game mechanics"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all analytics for a new game"""
        # Game metadata
        self.game_start_time = time.time()
        self.game_end_time = None
        self.total_turns = 0
        self.winner = None
        self.end_reason = None
        
        # Player tracking
        self.players_data = {}
        self.eliminations = []
        
        # Card usage tracking
        self.card_usage = {
            'action_cards': defaultdict(int),
            'personal_items': defaultdict(int),
            'health_cards': defaultdict(int),
            'housing_cards': defaultdict(int),
            'green_cards': defaultdict(int),
            'white_cards': defaultdict(int),
            'red_cards': defaultdict(int)
        }
        
        # Mechanics tracking
        self.mechanics_stats = {
            'document_exchanges': {'attempts': 0, 'successes': 0, 'failures': 0},
            'language_challenges': {'attempts': 0, 'successes': 0, 'failures': 0},
            'dice_challenges': {'total': 0, 'health': 0, 'housing': 0, 'successes': 0},
            'housing_upgrades': {'room_to_apartment': 0, 'apartment_to_mortgage': 0},
            'language_upgrades': {'basic_to_b1': 0, 'b1_to_c1': 0},
            'money_transactions': {'gains': [], 'losses': []},
            'nerve_changes': {'gains': [], 'losses': []},
            'interactions': {'interferences': 0, 'defenses': 0, 'blocks': 0},
            'effect_thefts': {
                'total_thefts': 0,
                'thefts_by_effect': defaultdict(int),
                'thefts_by_stealer': defaultdict(int),
                'thefts_by_target': defaultdict(int),
                'steal_cards_used': defaultdict(int)
            }
        }
        
        # Game flow tracking
        self.turn_events = []
        self.cell_visits = defaultdict(int)
        self.goal_progress = {}
        
        # Performance metrics
        self.performance_metrics = {
            'cards_per_turn': [],
            'resources_per_turn': [],
            'progress_per_turn': []
        }
    
    def start_game(self, players: List[Any]):
        """Initialize analytics for a new game"""
        self.game_start_time = time.time()
        for player in players:
            self.players_data[player.name] = {
                'profile': player.profile,
                'starting_resources': {
                    'money': player.money,
                    'nerves': player.nerves,
                    'document_level': player.document_level,
                    'language_level': player.language_level,
                    'housing_level': getattr(player, 'housing_level', 1)
                },
                'final_resources': {},
                'cards_played': defaultdict(int),
                'turns_taken': 0,
                'cells_visited': defaultdict(int),
                'challenges_faced': defaultdict(int),
                'goal': getattr(player, 'goal', None),
                'goal_progress': []
            }
    
    def end_game(self, winner: Optional[Any], end_reason: str):
        """Finalize game analytics"""
        self.game_end_time = time.time()
        self.winner = winner.name if winner else None
        self.end_reason = end_reason
        
        # Record final resources for all players
        for player_name, data in self.players_data.items():
            # This will be filled by the game engine
            pass
    
    def track_turn_start(self, player: Any, turn_number: int):
        """Track the start of a player's turn"""
        self.total_turns = turn_number
        self.players_data[player.name]['turns_taken'] += 1
        
        # Record current state
        turn_data = {
            'turn': turn_number,
            'player': player.name,
            'position': player.position,
            'resources': {
                'money': player.money,
                'nerves': player.nerves,
                'document_level': player.document_level,
                'language_level': player.language_level,
                'action_cards': len(player.action_cards)
            },
            'events': []
        }
        self.turn_events.append(turn_data)
    
    def track_cell_visit(self, player: Any, cell_position: int, cell_type: str):
        """Track when a player visits a cell"""
        self.cell_visits[f"{cell_type}_{cell_position}"] += 1
        self.players_data[player.name]['cells_visited'][cell_type] += 1
    
    def track_card_played(self, card: Dict, card_type: str, player: Any):
        """Track when a card is played"""
        card_id = card.get('id', card.get('name', 'unknown'))
        self.card_usage[card_type][card_id] += 1
        self.players_data[player.name]['cards_played'][card_id] += 1
    
    def track_document_exchange(self, player: Any, success: bool, card_used: Dict):
        """Track document exchange attempts"""
        self.mechanics_stats['document_exchanges']['attempts'] += 1
        if success:
            self.mechanics_stats['document_exchanges']['successes'] += 1
        else:
            self.mechanics_stats['document_exchanges']['failures'] += 1
    
    def track_language_upgrade(self, current_lvl: int):
        """Track language challenge attempts"""
        self.mechanics_stats['language_challenges']['attempts'] += 1
        self.mechanics_stats['language_challenges']['successes'] += 1
        if current_lvl == 1:
            self.mechanics_stats['language_upgrades']['basic_to_b1'] += 1
        else:
            self.mechanics_stats['language_upgrades']['b1_to_c1'] += 1

    def track_dice_challenge(self, player: Any, challenge_type: str, card: Dict, 
                           roll_result: int, outcome: str):
        """Track dice challenge results"""
        self.mechanics_stats['dice_challenges']['total'] += 1
        self.mechanics_stats['dice_challenges'][challenge_type] += 1
        
        if outcome == 'success':
            self.mechanics_stats['dice_challenges']['successes'] += 1
        
        self.players_data[player.name]['challenges_faced'][challenge_type] += 1
        
        # Add to current turn events
        if self.turn_events:
            self.turn_events[-1]['events'].append({
                'type': 'dice_challenge',
                'challenge_type': challenge_type,
                'card': card.get('name', 'unknown'),
                'roll': roll_result,
                'outcome': outcome
            })
    
    def track_interaction(self, interaction_type: str, acting_player: Any, 
                         target_player: Any, card_used: Dict, success: bool):
        """Track player interactions (interference, defense)"""
        self.mechanics_stats['interactions'][interaction_type] += 1
        
        if success:
            self.mechanics_stats['interactions']['blocks'] += 1
        
        # Track card usage
        if card_used:
            self.track_card_played(card_used, 'action_cards', acting_player)
        
        # Add to turn events
        if self.turn_events:
            self.turn_events[-1]['events'].append({
                'type': 'interaction',
                'interaction_type': interaction_type,
                'acting_player': acting_player.name,
                'target_player': target_player.name if target_player else None,
                'card': card_used.get('name', 'unknown') if card_used else None,
                'success': success
            })
    
    def track_resource_change(self, player: Any, resource_type: str, 
                            amount: int, reason: str):
        """Track resource changes (money, nerves)"""
        if resource_type == 'money':
            if amount > 0:
                self.mechanics_stats['money_transactions']['gains'].append(amount)
            else:
                self.mechanics_stats['money_transactions']['losses'].append(abs(amount))
        elif resource_type == 'nerves':
            if amount > 0:
                self.mechanics_stats['nerve_changes']['gains'].append(amount)
            else:
                self.mechanics_stats['nerve_changes']['losses'].append(abs(amount))
        
        # Add to turn events
        if self.turn_events:
            self.turn_events[-1]['events'].append({
                'type': 'resource_change',
                'player': player.name,
                'resource': resource_type,
                'amount': amount,
                'reason': reason
            })
    
    def track_upgrade(self, player: Any, upgrade_type: str, from_level: Any, to_level: Any):
        """Track upgrades (housing, language)"""
        if upgrade_type == 'housing':
            if from_level == 1 and to_level == 2:
                self.mechanics_stats['housing_upgrades']['room_to_apartment'] += 1
            elif from_level == 2 and to_level == 3:
                self.mechanics_stats['housing_upgrades']['apartment_to_mortgage'] += 1
        elif upgrade_type == 'language':
            if from_level == 1 and to_level == 2:
                self.mechanics_stats['language_upgrades']['basic_to_b1'] += 1
            elif from_level == 2 and to_level == 3:
                self.mechanics_stats['language_upgrades']['b1_to_c1'] += 1
    
    def track_goal_progress(self, player: Any, goal_requirements: Dict, current_progress: Dict):
        """Track player's progress toward their goal"""
        progress_percentage = 0
        met_requirements = 0
        total_requirements = len(goal_requirements)
        
        for req_type, req_value in goal_requirements.items():
            current_value = current_progress.get(req_type, 0)
            # Handle string types like housing_type
            if req_type == 'housing_type':
                # For housing_type, compare as strings or convert to levels
                if str(current_value) == str(req_value):
                    met_requirements += 1
            else:
                # For numeric values, ensure both are numbers
                try:
                    req_value = float(req_value)
                    current_value = float(current_value)
                    if current_value >= req_value:
                        met_requirements += 1
                except (ValueError, TypeError):
                    # If conversion fails, assume requirement not met
                    pass
        
        progress_percentage = (met_requirements / total_requirements) * 100 if total_requirements > 0 else 0
        
        self.players_data[player.name]['goal_progress'].append({
            'turn': self.total_turns,
            'progress_percentage': progress_percentage,
            'met_requirements': met_requirements,
            'total_requirements': total_requirements
        })
    
    def get_unused_cards(self, all_cards_data: Dict) -> Dict:
        """Identify cards that were never used"""
        unused_cards = {}
        
        for card_type, cards_dict in all_cards_data.items():
            if card_type in self.card_usage:
                used_card_ids = set(self.card_usage[card_type].keys())
                
                # Get all card IDs from the data
                if isinstance(cards_dict, dict):
                    # Handle different data structures
                    if 'action_cards' in cards_dict:
                        all_card_ids = {card['id'] for card in cards_dict['action_cards']}
                    elif 'personal_items' in cards_dict:
                        all_card_ids = {card['id'] for card in cards_dict['personal_items']}
                    elif 'health_cards' in cards_dict:
                        all_card_ids = {card['id'] for card in cards_dict['health_cards']}
                    elif 'housing_cards' in cards_dict:
                        all_card_ids = {card['id'] for card in cards_dict['housing_cards']}
                    else:
                        all_card_ids = {card['id'] for card in cards_dict if isinstance(card, dict)}
                else:
                    all_card_ids = {card['id'] for card in cards_dict if isinstance(card, dict)}
                
                unused_card_ids = all_card_ids - used_card_ids
                if unused_card_ids:
                    unused_cards[card_type] = list(unused_card_ids)
        
        return unused_cards
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analytics report"""
        duration = (self.game_end_time - self.game_start_time) if self.game_end_time else 0
        
        return {
            'game_metadata': {
                'duration_seconds': duration,
                'total_turns': self.total_turns,
                'winner': self.winner,
                'end_reason': self.end_reason,
                'players_count': len(self.players_data)
            },
            'card_usage_stats': {
                'total_cards_played': sum(sum(cards.values()) for cards in self.card_usage.values()),
                'cards_by_type': {k: sum(v.values()) for k, v in self.card_usage.items()},
                'most_used_cards': self._get_most_used_cards(),
                'card_usage_distribution': dict(self.card_usage)
            },
            'mechanics_performance': self.mechanics_stats,
            'player_performance': self.players_data,
            'game_flow': {
                'average_turns_per_player': self.total_turns / len(self.players_data) if self.players_data else 0,
                'cell_visit_frequency': dict(self.cell_visits),
                'turn_events_sample': self.turn_events[-10:] if len(self.turn_events) > 10 else self.turn_events
            },
            'balance_insights': self._analyze_balance()
        }
    
    def _get_most_used_cards(self, top_n: int = 10) -> Dict:
        """Get most frequently used cards across all types"""
        all_cards = []
        for card_type, cards in self.card_usage.items():
            for card_id, count in cards.items():
                all_cards.append((f"{card_type}:{card_id}", count))
        
        all_cards.sort(key=lambda x: x[1], reverse=True)
        return dict(all_cards[:top_n])
    
    def _analyze_balance(self) -> Dict:
        """Analyze game balance based on collected data"""
        insights = {}
        
        # Challenge success rates
        doc_exchanges = self.mechanics_stats['document_exchanges']
        if doc_exchanges['attempts'] > 0:
            insights['document_exchange_success_rate'] = doc_exchanges['successes'] / doc_exchanges['attempts']
        
        dice_challenges = self.mechanics_stats['dice_challenges']
        if dice_challenges['total'] > 0:
            insights['dice_challenge_success_rate'] = dice_challenges['successes'] / dice_challenges['total']
        
        # Resource flow analysis
        money_gains = self.mechanics_stats['money_transactions']['gains']
        money_losses = self.mechanics_stats['money_transactions']['losses']
        if money_gains and money_losses:
            insights['money_flow_balance'] = sum(money_gains) / sum(money_losses)
        
        # Interaction frequency
        total_interactions = sum(self.mechanics_stats['interactions'].values())
        if self.total_turns > 0:
            insights['interactions_per_turn'] = total_interactions / self.total_turns
        
        return insights
    
    def track_effect_theft(self, stealing_player: Any, target_player: Any, effect_stolen: str, steal_card: Dict):
        """Track when a player steals a permanent effect from another player."""
        theft_stats = self.mechanics_stats['effect_thefts']
        theft_stats['total_thefts'] += 1
        theft_stats['thefts_by_effect'][effect_stolen] += 1
        theft_stats['thefts_by_stealer'][stealing_player.profile] += 1
        theft_stats['thefts_by_target'][target_player.profile] += 1
        theft_stats['steal_cards_used'][steal_card['name']] += 1


class MultiGameAnalytics:
    """Analytics aggregator for multiple games"""
    
    def __init__(self):
        self.games = []
        self.aggregated_stats = defaultdict(list)
    
    def add_game(self, game_analytics: GameAnalytics):
        """Add a completed game's analytics"""
        report = game_analytics.generate_report()
        self.games.append(report)
        
        # Aggregate key metrics
        self.aggregated_stats['durations'].append(report['game_metadata']['duration_seconds'])
        self.aggregated_stats['turns'].append(report['game_metadata']['total_turns'])
        self.aggregated_stats['winners'].append(report['game_metadata']['winner'])
        self.aggregated_stats['end_reasons'].append(report['game_metadata']['end_reason'])
    
    def generate_summary_report(self) -> Dict:
        """Generate summary report across all games"""
        if not self.games:
            return {}
        
        total_games = len(self.games)
        
        # Aggregate card usage across all games
        all_card_usage = defaultdict(lambda: defaultdict(int))
        all_mechanics = defaultdict(lambda: defaultdict(int))
        
        for game in self.games:
            # Aggregate card usage
            for card_type, cards in game['card_usage_stats']['card_usage_distribution'].items():
                for card_id, count in cards.items():
                    all_card_usage[card_type][card_id] += count
            
            # Aggregate mechanics
            mechanics = game['mechanics_performance']
            for mechanic_type, stats in mechanics.items():
                if isinstance(stats, dict):
                    for stat_name, value in stats.items():
                        if isinstance(value, (int, float)):
                            all_mechanics[mechanic_type][stat_name] += value
                        elif isinstance(value, list):
                            if stat_name not in all_mechanics[mechanic_type]:
                                all_mechanics[mechanic_type][stat_name] = []
                            all_mechanics[mechanic_type][stat_name].extend(value)
        
        return {
            'summary': {
                'total_games': total_games,
                'average_duration': sum(self.aggregated_stats['durations']) / total_games,
                'average_turns': sum(self.aggregated_stats['turns']) / total_games,
                'win_distribution': Counter(self.aggregated_stats['winners']),
                'end_reason_distribution': Counter(self.aggregated_stats['end_reasons'])
            },
            'card_usage_summary': {
                'total_cards_played': sum(sum(cards.values()) for cards in all_card_usage.values()),
                'cards_by_type': {k: sum(v.values()) for k, v in all_card_usage.items()},
                'most_used_cards_overall': self._get_top_cards(all_card_usage, 20),
                'unused_cards': self._find_unused_cards(all_card_usage)
            },
            'mechanics_summary': dict(all_mechanics),
            'balance_analysis': self._analyze_overall_balance()
        }
    
    def _get_top_cards(self, card_usage: Dict, top_n: int) -> List:
        """Get top N most used cards across all games"""
        all_cards = []
        for card_type, cards in card_usage.items():
            for card_id, count in cards.items():
                all_cards.append({
                    'card_type': card_type,
                    'card_id': card_id,
                    'usage_count': count,
                    'games_appeared': len([g for g in self.games if card_id in g['card_usage_stats']['card_usage_distribution'].get(card_type, {})])
                })
        
        all_cards.sort(key=lambda x: x['usage_count'], reverse=True)
        return all_cards[:top_n]
    
    def _find_unused_cards(self, card_usage: Dict) -> Dict:
        """Find cards that were never used across all games"""
        # This would need access to the full card database
        # For now, return cards with very low usage
        rarely_used = {}
        for card_type, cards in card_usage.items():
            rarely_used[card_type] = [
                card_id for card_id, count in cards.items() 
                if count < len(self.games) * 0.1  # Used in less than 10% of games
            ]
        return rarely_used
    
    def _analyze_overall_balance(self) -> Dict:
        """Analyze overall game balance across all simulations"""
        if not self.games:
            return {}
        
        # Win rate analysis
        winners = [g['game_metadata']['winner'] for g in self.games if g['game_metadata']['winner']]
        win_distribution = Counter(winners)
        
        # Game length analysis
        turns = self.aggregated_stats['turns']
        
        # Success rates
        doc_success_rates = []
        challenge_success_rates = []
        
        for game in self.games:
            balance = game.get('balance_insights', {})
            if 'document_exchange_success_rate' in balance:
                doc_success_rates.append(balance['document_exchange_success_rate'])
            if 'dice_challenge_success_rate' in balance:
                challenge_success_rates.append(balance['dice_challenge_success_rate'])
        
        return {
            'game_length_stats': {
                'min_turns': min(turns) if turns else 0,
                'max_turns': max(turns) if turns else 0,
                'avg_turns': sum(turns) / len(turns) if turns else 0,
                'median_turns': sorted(turns)[len(turns)//2] if turns else 0
            },
            'win_balance': {
                'total_winners': len(winners),
                'unique_winners': len(win_distribution),
                'win_distribution': dict(win_distribution),
                'most_successful_profile': win_distribution.most_common(1)[0] if win_distribution else None
            },
            'success_rates': {
                'avg_document_success_rate': sum(doc_success_rates) / len(doc_success_rates) if doc_success_rates else 0,
                'avg_challenge_success_rate': sum(challenge_success_rates) / len(challenge_success_rates) if challenge_success_rates else 0
            }
        }
