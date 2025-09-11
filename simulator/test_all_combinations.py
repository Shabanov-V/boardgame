#!/usr/bin/env python3
"""
Comprehensive testing script for Viva Bureaucracia!
Tests all possible player combinations and group sizes.
"""

import json
import subprocess
import sys
from pathlib import Path
import time
import math
from itertools import combinations

def load_config():
    """Load the current config to get character profiles."""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """Save the modified config."""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def run_simulation(runs=20):
    """Run the simulation and return results."""
    # Change to the boardgame directory to ensure correct relative paths
    boardgame_dir = Path(__file__).parent.parent
    result = subprocess.run([
        sys.executable, 
        str(boardgame_dir / 'simulator.py'), 
        '--runs', str(runs)
    ], capture_output=True, text=True, cwd=boardgame_dir.parent)  # Run from BOARDGAME root
    
    if result.returncode != 0:
        print(f"Error running simulation: {result.stderr}")
        return None
    
    # Load results
    output_path = Path(__file__).parent / 'output' / 'simulation_results.json'
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def test_group_sizes(config, max_players=6, runs_per_test=15):
    """Test different group sizes (2-6 players)."""
    results = {}
    original_players = config['game_parameters']['number_of_players']
    
    print("🎯 Testing different group sizes...")
    
    for group_size in range(2, max_players + 1):
        print(f"\n📊 Testing {group_size} players...")
        
        # Update config
        config['game_parameters']['number_of_players'] = group_size
        save_config(config)
        
        # Run simulation
        start_time = time.time()
        result = run_simulation(runs_per_test)
        duration = time.time() - start_time
        
        if result:
            results[f"{group_size}_players"] = {
                'result': result,
                'test_duration_seconds': round(duration, 2),
                'group_size': group_size
            }
            
            # Print summary
            print(f"✅ {group_size} players completed in {duration:.1f}s")
            print(f"   Average game duration: {result['game_duration_statistics']['mean']:.1f} turns")
            print(f"   Timeouts: {result['no_winner_due_to_time_limit']}/{runs_per_test}")
            
            # Print win rates
            win_stats = result['win_rate_statistics']
            print("   Win rates:")
            for char, stats in win_stats.items():
                print(f"     {char}: {stats['win_rate']:.1%}")
        else:
            print(f"❌ Failed to test {group_size} players")
    
    # Restore original config
    config['game_parameters']['number_of_players'] = original_players
    save_config(config)
    
    return results

def test_all_combinations(config, target_group_size=6, runs_per_test=8):
    """Test ALL possible combinations of target_group_size from 8 characters."""
    results = {}
    character_profiles = config['character_profiles']
    character_ids = [p['id'] for p in character_profiles]
    
    print(f"\n🎯 Testing ALL possible combinations of {target_group_size} players from {len(character_ids)} characters...")
    
    # Generate all possible combinations
    all_combos = list(combinations(character_ids, target_group_size))
    total_combos = len(all_combos)
    
    print(f"📊 Total combinations to test: {total_combos}")
    print(f"📊 Estimated time: ~{total_combos * runs_per_test * 0.1:.1f}s")
    
    original_profiles = config['character_profiles'].copy()
    
    for i, combo_ids in enumerate(all_combos, 1):
        print(f"\n📊 Testing combination {i}/{total_combos}: {', '.join(combo_ids)}")
        
        # Filter to only selected characters
        selected_profiles = [p for p in character_profiles if p['id'] in combo_ids]
        config['character_profiles'] = selected_profiles
        config['game_parameters']['number_of_players'] = target_group_size
        save_config(config)
        
        # Run simulation
        start_time = time.time()
        result = run_simulation(runs_per_test)
        duration = time.time() - start_time
        
        if result:
            combo_key = f"combo_{i:02d}_{'_'.join(combo_ids[:3])}"  # Shortened key
            results[combo_key] = {
                'result': result,
                'test_duration_seconds': round(duration, 2),
                'characters': list(combo_ids),
                'group_size': target_group_size,
                'combination_number': i,
                'total_combinations': total_combos
            }
            
            print(f"✅ Completed in {duration:.1f}s")
            print(f"   Average game duration: {result['game_duration_statistics']['mean']:.1f} turns")
            print(f"   Timeouts: {result['no_winner_due_to_time_limit']}/{runs_per_test}")
            
            # Print most/least successful characters
            win_stats = result['win_rate_statistics']
            if win_stats:
                win_rates = [(char, stats['win_rate']) for char, stats in win_stats.items()]
                win_rates.sort(key=lambda x: x[1], reverse=True)
                best_char, best_rate = win_rates[0]
                worst_char, worst_rate = win_rates[-1]
                print(f"   Best: {best_char} ({best_rate:.1%}), Worst: {worst_char} ({worst_rate:.1%})")
        else:
            print(f"❌ Failed to test combination {i}")
    
    # Restore original config
    config['character_profiles'] = original_profiles
    config['game_parameters']['number_of_players'] = len(original_profiles)
    save_config(config)
    
    return results

def analyze_results(all_results):
    """Analyze and summarize all test results."""
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE ANALYSIS RESULTS")
    print("="*80)
    
    # Group size analysis
    group_results = {k: v for k, v in all_results.items() if k.endswith('_players')}
    if group_results:
        print("\n📊 GROUP SIZE ANALYSIS:")
        print("-" * 50)
        
        for size in sorted(group_results.keys(), key=lambda x: int(x.split('_')[0])):
            data = group_results[size]['result']
            group_size = group_results[size]['group_size']
            
            print(f"\n{group_size} Players:")
            print(f"  Average Duration: {data['game_duration_statistics']['mean']:.1f} ± {data['game_duration_statistics']['std_dev']:.1f} turns")
            print(f"  Timeout Rate: {data['no_winner_due_to_time_limit']}/{data['total_simulations']} ({data['no_winner_due_to_time_limit']/data['total_simulations']*100:.1f}%)")
            
            # Find most/least successful characters
            win_rates = [(char, stats['win_rate']) for char, stats in data['win_rate_statistics'].items()]
            win_rates.sort(key=lambda x: x[1], reverse=True)
            
            if win_rates:
                best_char, best_rate = win_rates[0]
                worst_char, worst_rate = win_rates[-1]
                print(f"  Best Character: {best_char} ({best_rate:.1%})")
                print(f"  Worst Character: {worst_char} ({worst_rate:.1%})")
                print(f"  Balance Range: {(best_rate - worst_rate)*100:.1f}% spread")
    
    # Combination analysis
    combo_results = {k: v for k, v in all_results.items() if k.startswith('combo_')}
    if combo_results:
        print("\n🎮 COMBINATION ANALYSIS:")
        print("-" * 50)
        
        for combo_name, combo_data in combo_results.items():
            data = combo_data['result']
            print(f"\n{combo_data['description']}:")
            print(f"  Characters: {', '.join(combo_data['characters'])}")
            print(f"  Average Duration: {data['game_duration_statistics']['mean']:.1f} turns")
            print(f"  Timeout Rate: {data['no_winner_due_to_time_limit']}/{data['total_simulations']}")
            
            # Character performance in this combo
            win_rates = [(char, stats['win_rate']) for char, stats in data['win_rate_statistics'].items()]
            win_rates.sort(key=lambda x: x[1], reverse=True)
            print("  Win Rates:")
            for char, rate in win_rates:
                print(f"    {char}: {rate:.1%}")
    
    # Overall recommendations
    print("\n🏆 RECOMMENDATIONS:")
    print("-" * 50)
    
    if group_results:
        # Find optimal group size (shortest games, fewest timeouts)
        optimal_size = None
        best_score = float('inf')
        
        for size_key, size_data in group_results.items():
            data = size_data['result']
            # Score = avg_duration + timeout_penalty
            timeout_penalty = (data['no_winner_due_to_time_limit'] / data['total_simulations']) * 100
            score = data['game_duration_statistics']['mean'] + timeout_penalty
            
            if score < best_score:
                best_score = score
                optimal_size = size_data['group_size']
        
        if optimal_size:
            print(f"🎯 Optimal Group Size: {optimal_size} players")
            print(f"   (Best balance of speed and completion rate)")
    
    print("\n📈 Character Balance Status:")
    # Analyze character performance across all tests
    char_performances = {}
    
    for test_name, test_data in all_results.items():
        if 'result' in test_data and 'win_rate_statistics' in test_data['result']:
            for char, stats in test_data['result']['win_rate_statistics'].items():
                if char not in char_performances:
                    char_performances[char] = []
                char_performances[char].append(stats['win_rate'])
    
    for char, rates in char_performances.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        min_rate = min(rates) if rates else 0
        max_rate = max(rates) if rates else 0
        
        status = "🟢 Balanced" if 0.15 <= avg_rate <= 0.35 else "🔴 Needs balancing"
        print(f"   {char}: {avg_rate:.1%} avg (range {min_rate:.1%}-{max_rate:.1%}) {status}")

def save_comprehensive_results(all_results):
    """Save all results to a comprehensive file."""
    output_path = Path(__file__).parent / 'output' / 'comprehensive_test_results.json'
    output_path.parent.mkdir(exist_ok=True)
    
    # Add metadata
    comprehensive_data = {
        'test_metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(all_results),
            'test_types': list(set('group' if k.endswith('_players') else 'combination' for k in all_results.keys()))
        },
        'results': all_results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Comprehensive results saved to: {output_path}")

def main():
    """Main testing function."""
    print("🎮 VIVA BUREAUCRACIA! - COMPREHENSIVE TESTING SUITE")
    print("=" * 80)
    
    # Load config
    config = load_config()
    total_characters = len(config['character_profiles'])
    
    print(f"📋 Found {total_characters} character profiles")
    print(f"🎯 Testing groups from 2-6 players")
    print(f"🔬 Testing specific character combinations")
    
    start_time = time.time()
    all_results = {}
    
    try:
        # Test different group sizes (reduced for speed)
        group_results = test_group_sizes(config, max_players=6, runs_per_test=8)
        all_results.update(group_results)
        
        # Test ALL combinations of 6 players from 8 characters
        combo_results = test_all_combinations(config, target_group_size=6, runs_per_test=5)
        all_results.update(combo_results)
        
        # Analyze everything
        analyze_results(all_results)
        
        # Save comprehensive results
        save_comprehensive_results(all_results)
        
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
