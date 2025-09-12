#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Game Runner with Comprehensive Analytics
Runs multiple games with detailed tracking and analysis
"""

import json
import time
import os
from typing import Dict, List
from .core import Game
from .analytics import MultiGameAnalytics
import random


class AdvancedGameRunner:
    """Advanced game runner with comprehensive analytics"""
    
    def __init__(self, config_path: str = None):
        """Initialize the runner with configuration"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Load all game data
        self.game_data = self._load_all_game_data()
        
        # Initialize analytics
        self.multi_analytics = MultiGameAnalytics()
        
        # Results storage
        self.results = {
            'games': [],
            'summary': {},
            'detailed_analytics': {}
        }
    
    def _load_all_game_data(self) -> Dict:
        """Load all game data files"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        
        game_data = {}
        
        # Load action cards
        action_cards_path = os.path.join(base_path, 'actionCartds', 'action_cards.json')
        with open(action_cards_path, 'r', encoding='utf-8') as f:
            game_data['action_cards'] = json.load(f)
        
        # Load personal items
        items_path = os.path.join(base_path, 'itemCards', 'personal_items.json')
        with open(items_path, 'r', encoding='utf-8') as f:
            game_data['personal_items'] = json.load(f)
        
        # Load health cards
        health_path = os.path.join(base_path, 'redCards', 'health_cards.json')
        with open(health_path, 'r', encoding='utf-8') as f:
            game_data['health_cards'] = json.load(f)
        
        # Load housing cards
        housing_path = os.path.join(base_path, 'redCards', 'housing_cards.json')
        with open(housing_path, 'r', encoding='utf-8') as f:
            game_data['housing_cards'] = json.load(f)
        
        # Load white cards (random events)
        white_path = os.path.join(base_path, 'whiteCards', 'random_events.json')
        with open(white_path, 'r', encoding='utf-8') as f:
            game_data['white_cards'] = json.load(f)
        
        # Load green cards (documents/work)
        green_path = os.path.join(base_path, 'greenCards', 'documents_work_cards.json')
        with open(green_path, 'r', encoding='utf-8') as f:
            game_data['green_cards'] = json.load(f)
        
        # Load game constants
        constants_path = os.path.join(base_path, 'Common', 'game_constants.json')
        with open(constants_path, 'r', encoding='utf-8') as f:
            game_data['game_constants'] = json.load(f)
        
        # Load goals from config
        game_data['goals'] = self.config['win_conditions']
        
        return game_data
    
    def run_simulation_batch(self, num_games: int, batch_size: int = 100, 
                           save_interval: int = 250) -> Dict:
        """Run a batch of games with periodic saving"""
        print(f"🚀 Starting simulation of {num_games} games...")
        print(f"📊 Batch size: {batch_size}, Save interval: {save_interval}")
        
        start_time = time.time()
        completed_games = 0
        
        for batch_start in range(0, num_games, batch_size):
            batch_end = min(batch_start + batch_size, num_games)
            batch_games = batch_end - batch_start
            
            print(f"\n🎮 Running batch {batch_start//batch_size + 1}: "
                  f"games {batch_start + 1}-{batch_end}")
            
            batch_start_time = time.time()
            
            for game_num in range(batch_start, batch_end):
                try:
                    # Run single game
                    game = Game(self.config, self.game_data)
                    game.run_simulation(max_turns=200)  # Reasonable limit
                    
                    # Collect analytics
                    self.multi_analytics.add_game(game.analytics)
                    
                    # Store basic result
                    self.results['games'].append({
                        'game_id': game_num + 1,
                        'winner': game.winner.name if game.winner else None,
                        'end_reason': game.end_reason,
                        'turns': game.turn,
                        'duration': time.time() - batch_start_time
                    })
                    
                    completed_games += 1
                    
                    # Progress indicator
                    if (game_num + 1) % 50 == 0:
                        progress = ((game_num + 1) / num_games) * 100
                        elapsed = time.time() - start_time
                        eta = (elapsed / (game_num + 1)) * (num_games - game_num - 1)
                        print(f"  Progress: {progress:.1f}% ({game_num + 1}/{num_games}) "
                              f"ETA: {eta/60:.1f}min")
                
                except Exception as e:
                    print(f"❌ Error in game {game_num + 1}: {e}")
                    continue
            
            batch_time = time.time() - batch_start_time
            print(f"  ✅ Batch completed in {batch_time:.1f}s "
                  f"({batch_games/batch_time:.1f} games/sec)")
            
            # Save intermediate results
            if completed_games % save_interval == 0 or batch_end >= num_games:
                self._save_intermediate_results(completed_games)
        
        # Generate final report
        total_time = time.time() - start_time
        print(f"\n🏁 Simulation completed!")
        print(f"⏱️ Total time: {total_time/60:.1f} minutes")
        print(f"📈 Average: {completed_games/total_time:.1f} games/second")
        print(f"✅ Successful games: {completed_games}/{num_games}")
        
        # Generate comprehensive analytics
        self.results['summary'] = self.multi_analytics.generate_summary_report()
        self.results['detailed_analytics'] = self._generate_detailed_analysis()
        
        return self.results
    
    def _save_intermediate_results(self, completed_games: int):
        """Save intermediate results to prevent data loss"""
        timestamp = int(time.time())
        filename = f"simulation_progress_{completed_games}games_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), 'output', filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Generate current summary
        current_summary = self.multi_analytics.generate_summary_report()
        
        progress_data = {
            'completed_games': completed_games,
            'timestamp': timestamp,
            'summary': current_summary,
            'recent_games': self.results['games'][-100:]  # Last 100 games
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Progress saved: {filename}")
    
    def _generate_detailed_analysis(self) -> Dict:
        """Generate detailed analysis of all games"""
        if not self.results['games']:
            return {}
        
        games = self.results['games']
        summary = self.results['summary']
        
        analysis = {
            'performance_metrics': {
                'completion_rate': len([g for g in games if g['winner']]) / len(games),
                'average_game_length': sum(g['turns'] for g in games) / len(games),
                'timeout_rate': len([g for g in games if g['end_reason'] == 'timeout']) / len(games),
                'elimination_rate': len([g for g in games if 'elimination' in g['end_reason']]) / len(games)
            },
            'balance_analysis': self._analyze_balance(),
            'card_effectiveness': self._analyze_card_effectiveness(),
            'mechanic_usage': self._analyze_mechanic_usage(),
            'player_profile_performance': self._analyze_profile_performance(),
            'recommendations': self._generate_recommendations()
        }
        
        return analysis
    
    def _analyze_balance(self) -> Dict:
        """Analyze game balance"""
        summary = self.results['summary']
        
        if 'balance_analysis' not in summary:
            return {}
        
        balance = summary['balance_analysis']
        
        return {
            'game_length_balance': {
                'status': 'good' if 50 <= balance.get('game_length_stats', {}).get('avg_turns', 0) <= 120 else 'needs_adjustment',
                'avg_turns': balance.get('game_length_stats', {}).get('avg_turns', 0),
                'recommendation': 'Optimal length' if 50 <= balance.get('game_length_stats', {}).get('avg_turns', 0) <= 120 else 'Consider adjusting game pace'
            },
            'win_distribution': {
                'status': 'good' if len(balance.get('win_balance', {}).get('win_distribution', {})) >= 3 else 'unbalanced',
                'unique_winners': balance.get('win_balance', {}).get('unique_winners', 0),
                'recommendation': 'Good variety' if len(balance.get('win_balance', {}).get('win_distribution', {})) >= 3 else 'Some profiles dominate'
            },
            'success_rates': balance.get('success_rates', {}),
            'challenge_difficulty': {
                'document_success_rate': balance.get('success_rates', {}).get('avg_document_success_rate', 0),
                'challenge_success_rate': balance.get('success_rates', {}).get('avg_challenge_success_rate', 0),
                'status': 'balanced' if 0.4 <= balance.get('success_rates', {}).get('avg_challenge_success_rate', 0) <= 0.7 else 'needs_adjustment'
            }
        }
    
    def _analyze_card_effectiveness(self) -> Dict:
        """Analyze which cards are most/least effective"""
        summary = self.results['summary']
        
        if 'card_usage_summary' not in summary:
            return {}
        
        card_usage = summary['card_usage_summary']
        
        return {
            'most_used_cards': card_usage.get('most_used_cards_overall', [])[:10],
            'underused_cards': card_usage.get('unused_cards', {}),
            'card_type_balance': card_usage.get('cards_by_type', {}),
            'total_cards_played': card_usage.get('total_cards_played', 0),
            'cards_per_game': card_usage.get('total_cards_played', 0) / len(self.results['games']) if self.results['games'] else 0
        }
    
    def _analyze_mechanic_usage(self) -> Dict:
        """Analyze usage of different game mechanics"""
        summary = self.results['summary']
        
        if 'mechanics_summary' not in summary:
            return {}
        
        mechanics = summary['mechanics_summary']
        
        return {
            'document_exchanges': mechanics.get('document_exchanges', {}),
            'dice_challenges': mechanics.get('dice_challenges', {}),
            'interactions': mechanics.get('interactions', {}),
            'upgrades': {
                'housing_upgrades': mechanics.get('housing_upgrades', {}),
                'language_upgrades': mechanics.get('language_upgrades', {})
            }
        }
    
    def _analyze_profile_performance(self) -> Dict:
        """Analyze performance of different character profiles"""
        games = self.results['games']
        summary = self.results['summary']
        
        if 'win_balance' not in summary.get('balance_analysis', {}):
            return {}
        
        win_dist = summary['balance_analysis']['win_balance']['win_distribution']
        
        # Calculate win rates
        total_games = len(games)
        profile_performance = {}
        
        for profile, wins in win_dist.items():
            win_rate = wins / total_games
            profile_performance[profile] = {
                'wins': wins,
                'win_rate': win_rate,
                'performance': 'excellent' if win_rate > 0.2 else 'good' if win_rate > 0.1 else 'needs_boost'
            }
        
        return profile_performance
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        balance = self._analyze_balance()
        card_effectiveness = self._analyze_card_effectiveness()
        profile_performance = self._analyze_profile_performance()
        
        # Game length recommendations
        if balance.get('game_length_balance', {}).get('status') == 'needs_adjustment':
            avg_turns = balance['game_length_balance']['avg_turns']
            if avg_turns > 120:
                recommendations.append("Games are too long - consider increasing resource generation or reducing requirements")
            elif avg_turns < 50:
                recommendations.append("Games are too short - consider increasing difficulty or requirements")
        
        # Balance recommendations
        if balance.get('win_distribution', {}).get('status') == 'unbalanced':
            recommendations.append("Some character profiles dominate - consider rebalancing starting conditions")
        
        # Challenge difficulty
        challenge_status = balance.get('challenge_difficulty', {}).get('status')
        if challenge_status == 'needs_adjustment':
            success_rate = balance['challenge_difficulty']['challenge_success_rate']
            if success_rate > 0.7:
                recommendations.append("Challenges are too easy - consider increasing difficulty requirements")
            elif success_rate < 0.4:
                recommendations.append("Challenges are too hard - consider reducing difficulty or providing more tools")
        
        # Card usage recommendations
        underused_cards = card_effectiveness.get('underused_cards', {})
        for card_type, cards in underused_cards.items():
            if len(cards) > 5:
                recommendations.append(f"Many {card_type} are underused - consider rebalancing or removing some")
        
        # Profile performance recommendations
        for profile, data in profile_performance.items():
            if data['performance'] == 'needs_boost':
                recommendations.append(f"Profile '{profile}' underperforms - consider buffing starting conditions")
        
        return recommendations
    
    def save_full_report(self, filename: str = None):
        """Save comprehensive report to file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"comprehensive_analysis_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), 'output', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Full report saved: {filename}")
        return filepath


def main():
    """Main function for running simulations"""
    runner = AdvancedGameRunner()
    
    # Run 1000 games
    results = runner.run_simulation_batch(1000, batch_size=50, save_interval=200)
    
    # Save comprehensive report
    report_path = runner.save_full_report()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SIMULATION SUMMARY")
    print("="*80)
    
    summary = results['summary']
    if 'summary' in summary:
        basic_summary = summary['summary']
        print(f"🎮 Total games: {basic_summary.get('total_games', 0)}")
        print(f"⏱️ Average duration: {basic_summary.get('average_duration', 0):.1f}s")
        print(f"🎯 Average turns: {basic_summary.get('average_turns', 0):.1f}")
        
        win_dist = basic_summary.get('win_distribution', {})
        print(f"\n🏆 WIN DISTRIBUTION:")
        for profile, wins in sorted(win_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (wins / basic_summary['total_games']) * 100
            print(f"  {profile}: {wins} wins ({percentage:.1f}%)")
    
    # Print recommendations
    detailed = results['detailed_analytics']
    if 'recommendations' in detailed:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(detailed['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print(f"\n📄 Full report saved to: {report_path}")


if __name__ == '__main__':
    main()
