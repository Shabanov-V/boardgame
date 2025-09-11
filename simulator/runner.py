from .core import Game


def run_game_simulation(config, game_data):
    """Initializes and runs a single game simulation."""
    game = Game(config, game_data)
    game.run()
    return game  # Return the final game state


