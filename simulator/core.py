import random


class Deck:
    """Represents a deck of cards."""
    def __init__(self, cards_data):
        self.cards = list(cards_data)
        self.discard_pile = []
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            if not self.discard_pile:
                return None  # Deck is completely empty
            # Reshuffle discard pile into the deck
            self.cards.extend(self.discard_pile)
            self.discard_pile = []
            self.shuffle()
            print("Reshuffled discard pile into deck.")
        return self.cards.pop(0)

    def discard(self, card):
        self.discard_pile.append(card)


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


class AI:
    """Holds the decision-making logic for a player."""
    def __init__(self, player, config):
        self.player = player
        self.config = config
        self.nerve_threshold = config['simulation_parameters'].get('ai_nerve_threshold', 3)

    def decide_play_action_card(self, turn_context):
        """Decides which action card to play from hand, if any."""
        if self.player.nerves < self.nerve_threshold:
            for card in self.player.action_cards:
                # Simple logic: if a card gives nerves and can be played now, play it.
                if card.get('effects', {}).get('nerves', 0) > 0 and card.get('when_to_play') in ['anytime', 'start_of_turn']:
                    print(f"AI ({self.player.name}): Nerves are low ({self.player.nerves}), deciding to play '{card['name']}'.")
                    return card
        return None

    def decide_on_green_space(self):
        """
        Decides whether to draw a green card or an action card.
        Based on game rule: "Можно взять карту или вместо этого — карту действия"
        (You can take a card or instead - an action card)
        """
        if len(self.player.action_cards) < self.player.max_action_cards:
            print(f"AI ({self.player.name}): Decided to draw a green card to advance game state.")
            return 'draw_green'
        else:
            print(f"AI ({self.player.name}): Action card hand is full, must draw green card.")
            return 'draw_green'  # No choice if hand is full, must interact with the space.

    def decide_green_card_use(self, card):
        """Decides whether to exchange a document card or play its event effect."""
        is_doc_goal = 'document_level' in self.player.win_condition['requires']
        # A simple placeholder logic for required docs. This can be configured.
        required_docs_for_upgrade = self.player.document_level + 2

        if card.get('category') == 'documents' and is_doc_goal and self.player.document_cards >= required_docs_for_upgrade:
            print(f"AI ({self.player.name}): Has enough doc cards, attempting exchange.")
            return 'exchange'
        else:
            print(f"AI ({self.player.name}): Playing card for its event effect.")
            return 'event'


class Player:
    """Represents a player in the game."""
    def __init__(self, profile, win_condition, config, game_constants):
        self.id = profile['id']
        self.name = profile['name']
        self.money = profile['starting_money']
        self.nerves = profile['starting_nerves']
        self.language_level = profile['starting_language']
        self.housing = profile['starting_housing']
        self.salary = profile.get('salary', 0)
        self.salary_type = profile.get('salary_type', 'fixed')
        self.housing_cost = profile.get('housing_cost', 0)

        self.position = 0
        self.document_level = 0
        self.action_cards = []
        self.max_action_cards = game_constants['game_constants']['max_action_cards']
        self.document_cards = 0  # Number of collected document cards

        self.win_condition = win_condition
        self.is_eliminated = False
        self.eliminated_on_turn = None
        self.ai = AI(self, config)

    def __repr__(self):
        return f"Player(Name: {self.name}, Money: {self.money}, Nerves: {self.nerves}, Docs: {self.document_level})"

    def add_action_card(self, card):
        if len(self.action_cards) < self.max_action_cards:
            self.action_cards.append(card)
            print(f"{self.name} received action card: {card['name']}.")
        else:
            print(f"{self.name}'s action card hand is full, cannot draw more.")


class Game:
    """Orchestrates a single game simulation."""
    def __init__(self, config, game_data):
        self.config = config
        self.game_data = game_data
        self.board = Board(config)
        self.setup_decks()
        self.setup_players()
        self.turn = 0
        self.game_over = False
        self.winner = None
        self.end_reason = None

    def setup_decks(self):
        self.decks = {
            'action': Deck(self.game_data['action_cards']['action_cards']),
            'green': Deck(self.game_data['green_cards']['green_cards']),
            'red': Deck(self.game_data['health_cards']['health_cards'] + self.game_data['housing_cards']['housing_cards']),
            'white': Deck(self.game_data['random_events']['random_events']),
        }

    def setup_players(self):
        self.players = []
        num_players = self.config['game_parameters']['number_of_players']
        profiles = random.sample(self.config['character_profiles'], num_players)
        win_conditions = list(self.config['win_conditions'].items())

        for i in range(num_players):
            profile = profiles[i]
            win_key, win_data = random.choice(win_conditions)
            player_win_condition = {"key": win_key, **win_data}
            player = Player(profile, player_win_condition, self.config, self.game_data['game_constants'])

            # Give starting action cards
            starting_card_count = self.game_data['game_constants']['game_constants']['starting_action_cards']
            for _ in range(starting_card_count):
                drawn_card = self.decks['action'].draw()
                if drawn_card:
                    player.add_action_card(drawn_card)

            self.players.append(player)

    def run(self):
        """Main loop for a single game, handling turns until a winner is found or a limit is reached."""
        num_players = self.config['game_parameters']['number_of_players']
        while not self.game_over:
            self.turn += 1

            # A rough estimate for a 'lap'
            if self.turn > 1 and self.turn % (self.board.size // num_players if num_players > 0 else self.board.size) == 0:
                self.handle_lap_completion()

            active_players = [p for p in self.players if not p.is_eliminated]
            if not active_players or (len(active_players) <= 1 and len(self.players) > 1):
                self.game_over = True
                self.winner = active_players[0] if active_players else None
                self.end_reason = 'elimination'
                continue

            for player in active_players:
                self.take_turn(player)
                if self.game_over:
                    break

            if self.turn >= 200:
                self.game_over = True
                if not self.winner:
                    self.end_reason = 'time_limit'

        return {"winner": self.winner.name if self.winner else "None", "turns": self.turn}

    def handle_lap_completion(self):
        """Handles events that occur when a player completes a lap, like salary."""
        for player in self.players:
            if not player.is_eliminated:
                player.money += player.salary
                player.money -= player.housing_cost

    def take_turn(self, player):
        """Manages the sequence of actions for a single player's turn."""
        # 1. AI decides to play a pre-turn action card
        card_to_play = player.ai.decide_play_action_card('start_of_turn')
        if card_to_play:
            self.apply_card_effect(player, card_to_play)
            player.action_cards.remove(card_to_play)
            self.decks['action'].discard(card_to_play)

        # 2. Roll dice and move
        roll = random.randint(1, 6)
        player.position = (player.position + roll) % self.board.size

        # 3. Handle cell effect
        cell_type = self.board.get_cell_type(player.position)

        if cell_type == 'green':
            decision = player.ai.decide_on_green_space()
            if decision == 'draw_green':
                card = self.decks['green'].draw()
                if card:
                    if card.get('exchange_instruction'):
                        use_decision = player.ai.decide_green_card_use(card)
                        self.apply_card_effect(player, card)
                    else:
                        self.apply_card_effect(player, card)
            elif decision == 'draw_action':
                action_card = self.decks['action'].draw()
                if action_card:
                    player.add_action_card(action_card)

        elif cell_type in ['red', 'white']:
            card = self.decks[cell_type].draw()
            if card:
                self.apply_card_effect(player, card)

        # 4. Check for win/loss conditions
        self.check_win_condition(player)
        if not self.game_over:
            self.check_elimination(player)

    def apply_card_effect(self, player, card, chosen_effect=None):
        """
        The main engine for applying card effects.
        It checks conditions, handles challenges, and applies effects.
        """
        # 1. Check conditions
        if 'conditions' in card and not self.check_conditions(player, card['conditions']):
            return

        # 2. Handle dice challenges
        if 'challenge' in card:
            self.handle_dice_challenge(player, card['challenge'])
            return

        # 3. Apply direct effects
        effects = chosen_effect or card.get('effects', {})
        if not effects:
            return

        for key, value in effects.items():
            if key == 'nerves':
                player.nerves += value
            elif key == 'money':
                player.money += value
            elif key == 'documents_cards':
                player.document_cards += value
            elif key == 'draw_action_card':
                for _ in range(value):
                    drawn_card = self.decks['action'].draw()
                    if drawn_card:
                        player.add_action_card(drawn_card)
            elif key == 'instant_document_upgrade':
                player.document_level += 1

        # Also handle special_effect outside the main effects block
        if 'special_effect' in card:
            if card['special_effect'] == 'upgrade_housing':
                pass
            elif card['special_effect'] == 'draw_action_card':
                drawn_card = self.decks['action'].draw()
                if drawn_card:
                    player.add_action_card(drawn_card)

    def check_conditions(self, player, conditions):
        """Checks if a player meets all conditions specified on a card."""
        for key, value in conditions.items():
            if key == 'housing_type':
                if isinstance(value, list) and player.housing not in value:
                    return False
                if isinstance(value, str) and player.housing != value:
                    return False
            elif key == 'character_id':
                if isinstance(value, list) and player.id not in value:
                    return False
                if isinstance(value, str) and player.id != value:
                    return False
            elif key == 'documents_level':
                try:
                    if not eval(f"{player.document_level} {value}"):
                        return False
                except:
                    return False  # a bit unsafe, but for this context is ok
        return True

    def handle_dice_challenge(self, player, challenge):
        """Manages a dice roll challenge for a player."""
        roll = random.randint(1, 6)

        outcome_key = 'failure'  # Default to failure
        for outcome, details in challenge['outcomes'].items():
            condition = details['condition']
            if '-' in condition:  # Range like "2-4"
                low, high = map(int, condition.split('-'))
                if low <= roll <= high:
                    outcome_key = outcome
                    break
            elif '>' in condition:
                val = int(condition.replace('>', '').strip())
                if roll > val:
                    outcome_key = outcome
                    break
            elif str(roll) == condition:
                outcome_key = outcome
                break

        chosen_outcome = challenge['outcomes'][outcome_key]

        if 'effects' in chosen_outcome:
            self.apply_card_effect(player, card={'name': f"Challenge: {challenge['description']}"}, chosen_effect=chosen_outcome['effects'])

    def check_win_condition(self, player):
        """Checks if a player has met their victory condition."""
        if self.game_over:
            return

        goal = player.win_condition['requires']
        met_all_conditions = True
        for key, required_value in goal.items():
            player_value = getattr(player, key, None)
            if key == 'housing_type':
                if player.housing != required_value:
                    met_all_conditions = False
                    break
            elif player_value is None or player_value < required_value:
                met_all_conditions = False
                break

        if met_all_conditions:
            self.game_over = True
            self.winner = player
            self.end_reason = 'win'

    def check_elimination(self, player):
        elimination_threshold = self.game_data['game_constants']['game_constants'].get('elimination_threshold', -1)
        if player.nerves <= elimination_threshold:
            player.is_eliminated = True
            if player.eliminated_on_turn is None:
                player.eliminated_on_turn = self.turn

            active_players = [p for p in self.players if not p.is_eliminated]
            if len(active_players) <= 1 and len(self.players) > 1:
                self.game_over = True
                self.winner = active_players[0] if active_players else None


