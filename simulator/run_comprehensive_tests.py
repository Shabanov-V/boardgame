#!/usr/bin/env python3
"""
Comprehensive testing script for Viva Bureaucracia!
Tests all possible player combinations and group sizes.
"""

import json
from pathlib import Path
import time
import math
from itertools import combinations
import random
from simulator.game import Game
from simulator.analytics import GameAnalytics, MultiGameAnalytics
from simulator.loader import load_game_data

def load_config():
    """Load the current config and the character profiles."""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    project_root = Path(__file__).parent.parent
    profiles_path = project_root / config['character_profiles']
    with open(profiles_path, 'r', encoding='utf-8') as f:
        character_config = json.load(f)

    config['character_profiles'] = character_config['character_profiles']
    return config

def run_single_game(config, game_data):
    """Runs a single game and returns its analytics."""
    # Ensure 'quiet_mode' is set to avoid excessive printing
    config['quiet_mode'] = True
    game = Game(config, game_data)
    game.run()
    return game.analytics

def test_group_sizes(base_config, game_data, max_players=6, runs_per_test=15):
    """Test different group sizes (2-6 players)."""
    results = {}
    all_games_analytics = []

    print("🎯 Testing different group sizes...")

    for group_size in range(2, max_players + 1):
        print(f"\n📊 Testing {group_size} players...")

        # Create a fresh config for this group size
        config = json.loads(json.dumps(base_config))
        config['game_parameters']['number_of_players'] = group_size
        config['character_profiles'] = random.sample(config['character_profiles'], group_size)

        multi_game_analytics = MultiGameAnalytics()
        start_time = time.time()

        for _ in range(runs_per_test):
            analytics = run_single_game(config, game_data)
            multi_game_analytics.add_game(analytics)
            all_games_analytics.append(analytics)

        duration = time.time() - start_time
        summary_report = multi_game_analytics.generate_summary_report()

        if summary_report:
            results[f"{group_size}_players"] = {
                'summary': summary_report,
                'test_duration_seconds': round(duration, 2),
                'group_size': group_size
            }

            # Print summary
            print(f"✅ {group_size} players completed in {duration:.1f}s")
            print(f"   Average game duration: {summary_report['summary']['average_turns']:.1f} turns")

            # Print win rates
            win_distribution = summary_report['summary']['win_distribution']
            total_wins = sum(win_distribution.values())
            print("   Win rates:")
            if total_wins > 0:
                for char, wins in win_distribution.items():
                    if char is not None:
                        print(f"     {char}: {wins/total_wins:.1%}")
        else:
            print(f"❌ Failed to test {group_size} players")

    return results, all_games_analytics

def test_all_combinations(base_config, game_data, target_group_size=6, runs_per_test=8):
    """Test ALL possible combinations of target_group_size from 8 characters."""
    results = {}
    all_games_analytics = []
    character_profiles = base_config['character_profiles']
    character_ids = [p['id'] for p in character_profiles]

    print(f"\n🎯 Testing ALL possible combinations of {target_group_size} players from {len(character_ids)} characters...")

    all_combos = list(combinations(character_ids, target_group_size))
    total_combos = len(all_combos)

    print(f"📊 Total combinations to test: {total_combos}")
    print(f"📊 Estimated time: ~{total_combos * runs_per_test * 0.1:.1f}s")

    for i, combo_ids in enumerate(all_combos, 1):
        print(f"\n📊 Testing combination {i}/{total_combos}: {', '.join(combo_ids)}")

        # Create a fresh config for this combination
        config = json.loads(json.dumps(base_config))
        selected_profiles = [p for p in character_profiles if p['id'] in combo_ids]
        config['character_profiles'] = selected_profiles
        config['game_parameters']['number_of_players'] = target_group_size

        multi_game_analytics = MultiGameAnalytics()
        start_time = time.time()

        for _ in range(runs_per_test):
            analytics = run_single_game(config, game_data)
            multi_game_analytics.add_game(analytics)
            all_games_analytics.append(analytics)

        duration = time.time() - start_time
        summary_report = multi_game_analytics.generate_summary_report()

        if summary_report:
            combo_key = f"combo_{i:02d}_{'_'.join(combo_ids[:3])}"
            results[combo_key] = {
                'summary': summary_report,
                'test_duration_seconds': round(duration, 2),
                'characters': list(combo_ids),
                'group_size': target_group_size,
                'combination_number': i,
                'total_combinations': total_combos
            }

            print(f"✅ Completed in {duration:.1f}s")
            print(f"   Average game duration: {summary_report['summary']['average_turns']:.1f} turns")

            win_distribution = summary_report['summary']['win_distribution']
            total_wins = sum(win_distribution.values())
            if total_wins > 0:
                win_rates = sorted([(char, wins/total_wins) for char, wins in win_distribution.items() if char is not None], key=lambda x: x[1], reverse=True)
                if win_rates:
                    best_char, best_rate = win_rates[0]
                    worst_char, worst_rate = win_rates[-1]
                    print(f"   Best: {best_char} ({best_rate:.1%}), Worst: {worst_char} ({worst_rate:.1%})")
        else:
            print(f"❌ Failed to test combination {i}")

    return results, all_games_analytics

def generate_and_save_cumulative_report(all_games_analytics, per_test_results):
    """Generates a cumulative report from all game analytics and saves it."""
    print("\n" + "="*80)
    print("🎯 CUMULATIVE ANALYSIS RESULTS")
    print("="*80)

    # Create a top-level MultiGameAnalytics object to aggregate everything
    cumulative_analytics = MultiGameAnalytics()
    for analytics in all_games_analytics:
        cumulative_analytics.add_game(analytics)

    # Generate the final cumulative report
    cumulative_report = cumulative_analytics.generate_summary_report()

    # Print a summary of the cumulative report to the console
    if cumulative_report:
        summary = cumulative_report['summary']
        print(f"Total Games Analyzed: {summary['total_games']}")
        print(f"Average Game Duration: {summary['average_turns']:.1f} turns")

        print("\nWin Distribution:")
        for winner, count in summary['win_distribution'].items():
            if winner:
                print(f"  {winner}: {count} wins")

        print("\nEnd Reason Distribution:")
        for reason, count in summary['end_reason_distribution'].items():
            print(f"  {reason}: {count} games")

    # Save the comprehensive report
    output_path = Path(__file__).parent / 'output' / 'comprehensive_analysis.json'
    output_path.parent.mkdir(exist_ok=True)

    final_report = {
        'test_metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_games_simulated': len(all_games_analytics),
        },
        'cumulative_summary': cumulative_report,
        'per_test_run_results': per_test_results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Comprehensive analysis saved to: {output_path}")

def main():
    """Main testing function."""
    print("🎮 VIVA BUREAUCRACIA! - COMPREHENSIVE TESTING SUITE")
    print("=" * 80)

    config = load_config()
    game_data = load_game_data()
    total_characters = len(config['character_profiles'])

    print(f"📋 Found {total_characters} character profiles")
    print(f"🎯 Testing groups from 2-6 players")
    print(f"🔬 Testing specific character combinations")

    start_time = time.time()
    per_test_results = {}
    all_games_analytics = []

    try:
        group_results, group_analytics = test_group_sizes(config, game_data, max_players=6, runs_per_test=8)
        per_test_results.update(group_results)
        all_games_analytics.extend(group_analytics)

        combo_results, combo_analytics = test_all_combinations(config, game_data, target_group_size=6, runs_per_test=5)
        per_test_results.update(combo_results)
        all_games_analytics.extend(combo_analytics)

        # Generate and save the final cumulative report
        generate_and_save_cumulative_report(all_games_analytics, per_test_results)

    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
    finally:
        total_time = time.time() - start_time
        print(f"\n⏱️ Total testing time: {total_time/60:.1f} minutes")
        print("🎯 Testing completed!")

if __name__ == "__main__":
    main()
