# Board Game Simulator

A Python-based simulator for a board game about immigration and bureaucracy.

## Project Structure

```
boardgame/
├── simulator/           # Core simulator code
│   ├── entities/       # Game entities
│   │   ├── ai.py      # AI decision making
│   │   ├── board.py   # Game board
│   │   ├── deck.py    # Card decks
│   │   └── player.py  # Player class
│   ├── managers/       # Game managers
│   │   ├── elimination_manager.py  # Player elimination
│   │   ├── event_manager.py        # Event handling
│   │   ├── interaction_manager.py  # Player interactions
│   │   └── trade_manager.py        # Trading system
│   ├── mechanics/      # Game mechanics
│   │   ├── challenges.py  # Dice challenges
│   │   └── effects.py     # Card effects
│   ├── utils/         # Utilities
│   │   ├── constants.py  # Game constants
│   │   └── helpers.py    # Helper functions
│   ├── analytics.py   # Game analytics
│   ├── game.py        # Main game class
│   └── __init__.py    # Package initialization
├── tests/             # Test suite
│   ├── test_entities.py
│   ├── test_game.py
│   ├── test_managers.py
│   └── test_mechanics.py
├── requirements.txt   # Project dependencies
└── README.md         # This file
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=simulator tests/
```

## Code Style

This project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking
- isort for import sorting

Run formatters:
```bash
black .
isort .
```

Run linters:
```bash
flake8 .
mypy .
```

## Game Components

### Entities

- **Board**: Represents the game board with different cell types (green, red, white)
- **Deck**: Manages card decks with draw and discard functionality
- **Player**: Represents a player with resources and state
- **AI**: Handles AI decision making for non-human players

### Managers

- **EliminationManager**: Handles player elimination conditions
- **EventManager**: Manages game events and their effects
- **InteractionManager**: Handles player interactions and interference
- **TradeManager**: Manages trading between players

### Mechanics

- **ChallengeManager**: Handles dice-based challenges
- **EffectManager**: Applies card effects to players

### Game Flow

1. Players take turns moving around the board
2. Each cell type triggers different events:
   - Green: Document-related events
   - Red: Health and housing events
   - White: Random events
3. Players can trade resources
4. Players can interfere with others' actions
5. Game ends when a player achieves their goal or is eliminated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

This project is proprietary and confidential.



