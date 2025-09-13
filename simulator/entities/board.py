import random

class Board:
    """Represents the game board."""
    def __init__(self, config):
        self.size = config['game_parameters']['board_size']
        cell_freq = config['game_parameters']['cell_frequencies']

        cells = []
        for color, count in cell_freq.items():
            cells.extend([color] * count)

        # Ensure the board is the correct size, filling with a default if necessary
        while len(cells) < self.size:
            cells.append('white')  # Default to white for any unspecified cells

        random.shuffle(cells)
        self.cells = cells[:self.size]

    def get_cell_type(self, position):
        return self.cells[position % self.size]

