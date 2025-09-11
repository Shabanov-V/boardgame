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
        self.goal_requirements = self.player.win_condition.get('requires', {})


    def decide_play_action_card(self, turn_context):
        """Decides which action card to play from hand, if any, based on goal and current status."""
        # Priority 1: Manage low nerves
        if self.player.nerves < self.nerve_threshold:
            for card in self.player.action_cards:
                if card.get('effects', {}).get('nerves', 0) > 0 and self._can_play_now(card, turn_context):
                    print(f"AI ({self.player.name}): Nerves are low ({self.player.nerves}), playing '{card['name']}' to restore them.")
                    return card

        # Priority 2: Play cards that directly advance the win condition
        for card in self.player.action_cards:
            if self._can_play_now(card, turn_context) and self._card_helps_goal(card):
                print(f"AI ({self.player.name}): Playing '{card['name']}' to advance win condition '{self.player.win_condition['key']}'.")
                return card

        return None

    def _can_play_now(self, card, turn_context):
        """Checks if a card can be played in the current context."""
        when_to_play = card.get('when_to_play', 'anytime')
        return when_to_play == 'anytime' or when_to_play == turn_context

    def _card_helps_goal(self, card):
        """Checks if a card's effects align with the player's win condition."""
        effects = card.get('effects', {})
        special_effect = card.get('special_effect')
        
        for req, value in self.goal_requirements.items():
            if req == 'money' and effects.get('money', 0) > 0:
                return True
            if req == 'document_level' and effects.get('instant_document_upgrade', 0) > 0:
                return True
            if req == 'document_level' and effects.get('documents_cards', 0) > 0:
                return True
            if req == 'language_level' and effects.get('language_level_up'):
                return True
            if req == 'housing_type' and special_effect == 'upgrade_housing':
                return True
        return False

    def decide_on_green_space(self):
        """Decides whether to draw a green card or an action card."""
        # If hand is full, must draw green
        if len(self.player.action_cards) >= self.player.max_action_cards:
            print(f"AI ({self.player.name}): Action card hand is full, must draw green card.")
            return 'draw_green'

        # If goal is money-based, prefer action cards which might give money or other advantages
        if 'money' in self.goal_requirements and self.goal_requirements['money'] > self.player.money:
            print(f"AI ({self.player.name}): Goal is financial, preferring to draw an action card.")
            return 'draw_action'

        # Default to drawing a green card to advance game state
        print(f"AI ({self.player.name}): Decided to draw a green card to advance game state.")
        return 'draw_green'


    def decide_green_card_use(self, card):
        """Decides whether to exchange a document card or play its event effect based on the goal."""
        is_doc_goal = 'document_level' in self.goal_requirements

        # If the goal is document-related, prioritize exchanging cards to level up.
        if is_doc_goal and card.get('category') == 'documents':
            required_docs_for_upgrade = 2  # Now always 2 cards needed
            if self.player.document_cards >= required_docs_for_upgrade:
                print(f"AI ({self.player.name}): Goal requires documents. Have enough cards, attempting exchange.")
                return 'exchange'
            else:
                print(f"AI ({self.player.name}): Goal requires documents, but not enough cards to exchange. Playing for event to get more.")
                return 'event'

        # Check if the card helps with any goal requirement via events/special effects
        if self._card_helps_goal(card):
            print(f"AI ({self.player.name}): Card '{card['name']}' helps with goal. Playing as event.")
            return 'event'

        # If the goal is financial, check if the event gives money.
        if 'money' in self.goal_requirements:
            event_effects = card.get('effects', {})
            if event_effects.get('money', 0) > 0:
                print(f"AI ({self.player.name}): Goal is financial. Playing card for its event to get money.")
                return 'event'

        # Default behavior: if not a document goal and no clear financial benefit, prefer exchange if possible, else event.
        if card.get('category') == 'documents':
             print(f"AI ({self.player.name}): No specific goal alignment. Defaulting to event for card '{card['name']}'.")
             return 'event'

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
        # Track housing level as an integer alongside the type string for progress visibility
        housing_level_map = {
            'room': 1,
            'apartment': 2,
            'mortgage': 3,
        }
        self.housing_level = housing_level_map.get(self.housing, 0)
        self.salary = profile.get('salary', 0)
        self.salary_type = profile.get('salary_type', 'fixed')
        self.housing_cost = profile.get('housing_cost', 0)

        self.position = 0
        self.document_level = 0
        self.action_cards = []
        self.max_action_cards = game_constants['game_constants']['max_action_cards']
        self.document_cards = 0  # Number of collected document cards
        self.housing_search = False  # Whether player is actively searching for housing

        self.win_condition = win_condition
        self.is_eliminated = False
        self.eliminated_on_turn = None
        self.ai = AI(self, config)

    def __repr__(self):
        return (f"Player(Name: {self.name}, Money: {self.money}, Nerves: {self.nerves}, "
                f"Lang Lvl: {self.language_level}, Housing: {self.housing} (Lvl {self.housing_level}), "
                f"Docs Lvl: {self.document_level}, Doc Cards: {self.document_cards}, "
                f"Goal: {self.win_condition['key']})")

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
        print(f"\n--- Turn {self.turn}, Player: {player.name} ---")
        print(f"State before turn: {player}")

        # 1. AI decides to play a pre-turn action card
        card_to_play = player.ai.decide_play_action_card('start_of_turn')
        if card_to_play:
            self.apply_card_effect(player, card_to_play, 'event') # Action cards are always events
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
                    use_decision = 'event' # Default for non-exchange cards
                    if card.get('exchange_instruction'):
                        use_decision = player.ai.decide_green_card_use(card)
                    self.apply_card_effect(player, card, use_decision)
            elif decision == 'draw_action':
                action_card = self.decks['action'].draw()
                if action_card:
                    player.add_action_card(action_card)

        elif cell_type in ['red', 'white']:
            card = self.decks[cell_type].draw()
            if card:
                self.apply_card_effect(player, card, 'event') # Red/White cards are always events

        # 4. Check for win/loss conditions
        self.check_win_condition(player)
        if not self.game_over:
            self.check_elimination(player)

        print(f"State after turn:  {player}")

    def apply_card_effect(self, player, card, decision, chosen_effect=None):
        """
        The main engine for applying card effects.
        It checks conditions, handles challenges, and applies effects based on a decision.
        """
        # 1. Handle document exchange decision
        if decision == 'exchange':
            # Simplified requirements: always need just 2 cards for any level
            required_docs = 2
            if player.document_cards >= required_docs:
                # Roll dice for exchange success (3+ = success)
                roll = random.randint(1, 6)
                if roll >= 3:
                    player.document_cards -= required_docs
                    player.document_level += 1
                    print(f"System: {player.name} exchanged {required_docs} doc cards for Level {player.document_level} (rolled {roll}).")
                else:
                    # Failed exchange - lose 1 card and discard the drawn card
                    player.document_cards = max(0, player.document_cards - 1)
                    print(f"System: {player.name} failed exchange (rolled {roll}), lost 1 doc card.")
            else:
                # This case should ideally not be reached if AI is smart
                print(f"System: {player.name} failed to exchange, not enough doc cards.")
            return # Exchange action is complete

        # 2. Check conditions for event/challenge
        if 'conditions' in card and not self.check_conditions(player, card['conditions']):
            return

        # 3. Handle dice challenges for event
        if 'challenge' in card:
            self.handle_dice_challenge(player, card['challenge'])
            return

        # 4. Apply direct effects for event
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
            elif key == 'language_level_up':
                if player.language_level < 3:
                    player.language_level += 1
                    print(f"System: {player.name} improved language to level {player.language_level}!")

        # Also handle special_effect outside the main effects block
        if 'special_effect' in card:
            if card['special_effect'] == 'upgrade_housing':
                old_housing = player.housing
                if player.housing == 'room':
                    player.housing = 'apartment'
                    player.housing_level = 2
                    player.housing_cost = 3  # Update cost
                    print(f"System: {player.name} upgraded housing from {old_housing} to {player.housing}!")
                elif player.housing == 'apartment':
                    player.housing = 'mortgage'
                    player.housing_level = 3
                    player.housing_cost = 5  # Update cost
                    print(f"System: {player.name} upgraded housing from {old_housing} to {player.housing}!")
            elif card['special_effect'] == 'downgrade_housing':
                old_housing = player.housing
                if player.housing == 'mortgage':
                    player.housing = 'apartment'
                    player.housing_level = 2
                    player.housing_cost = 3
                    print(f"System: {player.name} downgraded housing from {old_housing} to {player.housing}.")
                elif player.housing == 'apartment':
                    player.housing = 'room'
                    player.housing_level = 1
                    player.housing_cost = 1
                    print(f"System: {player.name} downgraded housing from {old_housing} to {player.housing}.")
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
            elif key == 'housing_search':
                if value != player.housing_search:
                    return False
            elif key == 'money_range':
                # Support for money range checks like ">15" or "<5"
                try:
                    if not eval(f"{player.money} {value}"):
                        return False
                except:
                    return False
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
            self.apply_card_effect(player, card={'name': f"Challenge: {challenge['description']}"}, decision='event', chosen_effect=chosen_outcome['effects'])

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


