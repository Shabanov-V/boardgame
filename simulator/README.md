## Viva Bureaucracia! Simulator

This directory contains the automated simulator for the Viva Bureaucracia! board game prototype. It runs many games in succession, collects aggregate statistics, and saves both results and logs to an output directory.

### What it is
- **Purpose**: Quickly evaluate balance and outcomes across many simulated games.
- **Outputs**:
  - `output/simulation_results.json`: aggregate stats across all runs
  - `output/simulation.log`: detailed per-turn log (very large for many runs)

### How it works (modules)
- `simulator.py`: entry point that calls `simulator/cli.py`.
- `simulator/cli.py`: argument parsing, config + data loading, log/output setup, main loop over runs.
- `simulator/runner.py`: creates and runs a single `Game` instance.
- `simulator/core.py`: core game engine (`Game`, `Player`, `AI`, `Deck`, `Board`). Handles turns, card effects, win checks.
- `simulator/stats.py`: collects statistics over completed games and produces a summary.
- `simulator/utils.py`: helpers to load JSON config and the various card/data files.
- `simulator/config.json`: game configuration (board size, character profiles, win conditions, etc.).

The simulator also reads data from top-level folders:
- `actionCards/`, `greenCards/`, `redCards/`, `whiteCards/`, and `Common/`.

### Requirements
- Python 3.10+ (tested with 3.12)

### Running the simulator
From the repository root:

```bash
python /root/boardgame/simulator.py --runs 100
```

By default, the simulator is non-verbose (prints nothing to the console) and writes logs to `simulator/output/simulation.log`. Results are written to `simulator/output/simulation_results.json`.

#### Examples
- Run 200 simulations (silent to console, logs to file):
```bash
python /root/boardgame/simulator.py --runs 200
```

- Run 50 simulations and show progress on the console as well as logging to file:
```bash
python /root/boardgame/simulator.py --runs 50 --verbose
```

- Write results to a custom file (parent directories will be created):
```bash
python /root/boardgame/simulator.py --runs 500 --output /root/boardgame/simulator/output/results_500.json
```

### Output files
- `simulator/output/simulation_results.json` — A JSON summary with fields like:
  - `total_simulations`, `average_game_duration_turns`
  - `win_rate_by_character`, `win_rate_by_goal`
  - `goal_assignments_by_character`, `elimination_rate_by_character`
  - `no_winner_due_to_time_limit`

- `simulator/output/simulation.log` — Detailed per-turn logs of every simulated game. This file can grow large for high `--runs` values.

### Tips
- Start with a smaller `--runs` (e.g., 50–100) to validate changes quickly.
- Use non-verbose mode (default) for performance when running thousands of simulations.
- If you customize `simulator/config.json` or the card data files, re-run the simulator to see how outcomes change.


