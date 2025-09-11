import argparse
import json
from pathlib import Path

from .utils import load_json_file, load_game_data
from .stats import Statistics
from .runner import run_game_simulation


def main():
    """Main entry point for the simulator."""
    # Establish default output directory inside the simulator package
    package_dir = Path(__file__).resolve().parent
    output_dir = package_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    default_output_file = output_dir / 'simulation_results.json'
    log_file_path = output_dir / 'simulation.log'

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
        default=str(default_output_file),
        help='Path to the output JSON file for statistics.'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Print progress and turn-by-turn output to console (also logs to file)."
    )
    args = parser.parse_args()

    # Setup logging: tee to file by default, or file-only when verbose is not set
    import sys

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams
        def write(self, data):
            for s in self._streams:
                s.write(data)
            return len(data)
        def flush(self):
            for s in self._streams:
                s.flush()

    # Ensure parent directory for output file exists if user overrides path
    Path(args.output).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    log_fp = open(log_file_path, 'w', encoding='utf-8')
    original_stdout = sys.stdout
    if args.verbose:
        sys.stdout = _Tee(original_stdout, log_fp)
    else:
        sys.stdout = log_fp

    print(f"Viva Bureaucracia! Simulator starting...")
    print(f"Running {args.runs} game simulations.")

    config_path = package_dir / 'config.json'
    config = load_json_file(str(config_path))
    game_data = load_game_data()
    stats = Statistics()

    for i in range(args.runs):
        if args.verbose and (i + 1) % (args.runs // 10 or 1) == 0:
            pass

        game_instance = run_game_simulation(config, game_data)
        stats.record_game(game_instance)

    # Restore stdout and close log file
    sys.stdout.flush()
    sys.stdout = original_stdout
    log_fp.close()

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


