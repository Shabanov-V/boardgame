import argparse
import json
from pathlib import Path

from .utils import load_json_file, load_game_data
from .stats import Statistics
from .runner import run_game_simulation


def main():
    """Main entry point for the simulator."""
    parser = argparse.ArgumentParser(description="Viva Bureaucracia! Game Simulator")
    parser.add_argument(
        '--runs',
        type=int,
        default=100,
        help='Number of simulations to run.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='simulation_results.json',
        help='Path to the output JSON file for statistics.'
    )
    parser.add_argument(
        '--no-verbose',
        action='store_true',
        help="Run in silent mode, suppressing turn-by-turn output."
    )
    args = parser.parse_args()

    # Redirect print to a file if in non-verbose mode to speed up simulation
    if args.no_verbose:
        import sys
        sys.stdout = open('simulation_log.txt', 'w')

    print(f"Viva Bureaucracia! Simulator starting...")
    print(f"Running {args.runs} game simulations.")

    package_dir = Path(__file__).resolve().parent
    config_path = package_dir / 'config.json'
    config = load_json_file(str(config_path))
    game_data = load_game_data()
    stats = Statistics()

    for i in range(args.runs):
        if not args.no_verbose and (i + 1) % (args.runs // 10 or 1) == 0:
            pass

        game_instance = run_game_simulation(config, game_data)
        stats.record_game(game_instance)

    # Restore stdout if it was redirected
    if args.no_verbose:
        sys.stdout.close()
        sys.stdout = sys.__stdout__

    print("\nSimulation finished.")

    summary = stats.get_summary()
    output_file = args.output

    print(f"\n--- SIMULATION SUMMARY (writing to {output_file}) ---")
    # Print to console for immediate feedback
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"\nWriting simulation results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    print("Done.")


if __name__ == "__main__":
    main()


