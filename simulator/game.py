"""Main game class that orchestrates all game components."""

import random
from simulator.entities.board import Board
from simulator.entities.deck import Deck
from simulator.entities.player import Player
from simulator.entities.ai import AI

from simulator.managers.event_manager import InteractiveEvent
from simulator.managers.interaction_manager import InteractionManager
from simulator.managers.trade_manager import TradeManager
from simulator.managers.elimination_manager import EliminationManager

from simulator.mechanics.effects import EffectManager
from simulator.mechanics.challenges import ChallengeManager

from simulator.utils.constants import CARD_TYPES
from simulator.utils.helpers import calculate_win_progress, is_global_event_card

from simulator.analytics import GameAnalytics

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

        # Initialize managers
        self.interaction_manager = InteractionManager(self.players)
        self.trade_manager = TradeManager(self.players, self.config['quiet_mode'])
        self.elimination_manager = EliminationManager(game_data, self.players, self.config['quiet_mode'])
        self.effect_manager = EffectManager()
        self.challenge_manager = ChallengeManager()
        
        # Initialize analytics
        self.analytics = GameAnalytics()
        self.analytics.start_game(self.players)

    def setup_decks(self):
        """Initialize all card decks."""
        self.decks = {
            'action': Deck(self.game_data['action_cards']['action_cards']),
            'green': Deck(self.game_data['green_cards']['green_cards']),
            'red': Deck(self.game_data['health_cards']['health_cards'] + self.game_data['housing_cards']['housing_cards']),
            'white': Deck(self.game_data['white_cards']['random_events']) if 'white_cards' in self.game_data else Deck([]),
        }
        
        # Add items deck if available
        if 'personal_items' in self.game_data:
            all_items = self.game_data['personal_items']['personal_items'].copy()
            if 'steal_effect_cards' in self.game_data['personal_items']:
                all_items.extend(self.game_data['personal_items']['steal_effect_cards'])
            self.decks['item'] = Deck(all_items)

    def log(self, message):
        if not self.config['quiet_mode']:
            print(message)


    def setup_players(self):
        """Initialize all players."""
        self.players = []
        num_players = self.config['game_parameters']['number_of_players']
        
        # Load character profiles from character_config.json
        with open(self.config['character_profiles']) as f:
            import json
            character_config = json.load(f)
            profiles = random.sample(character_config['character_profiles'], num_players)

        for profile in profiles:
            # Players start without a goal - will choose at document level 5
            player = Player(profile, None, self.config, self.game_data)

            # Give starting action cards (3 per player)
            if 'item' in self.decks:
                for _ in range(3):
                    item_card = self.decks['item'].draw()
                    if item_card:
                        player.add_action_card(item_card)

            self.players.append(player)

    def run(self):
        """Main game loop."""
        self.log(f"Starting game with {len(self.players)} players")
        while not self.game_over:
            self.turn += 1
            # Get active players
            active_players = [p for p in self.players if not p.is_eliminated]
            # Check for game over due to eliminations
            game_over, winner = self.elimination_manager.check_game_over(self.players)
            if game_over:
                self.game_over = True
                self.winner = winner
                self.end_reason = 'elimination'
                break
            # Each player takes their turn
            for player in active_players:
                self.take_turn(player)
                if self.game_over:
                    break
            # Check turn limit
            max_turns = len(self.players) * 15  # 15 turns per player
            if self.turn >= max_turns:
                self.game_over = True
                self.end_reason = 'time_limit'
                self.winner = None
        # End game analytics
        self.analytics.end_game(self.winner, self.end_reason)
        return self.winner

    def take_turn(self, player):
        """Handle a single player's turn."""
        self.log(f"\n--- Game turn {self.turn}, Player: {player.name}, Player's turn: {player.turn_count} ---")
        self.log(f"State before turn: {player}")
        
        player.turn_count += 1  # Increment player's turn count

        # Analytics: Track turn start
        self.analytics.track_turn_start(player, self.turn)

        # 1. Pre-turn actions
        self.handle_pre_turn_actions(player)
        
        # 2. Movement
        self.handle_movement(player)
        
        # 3. Trade phase
        self.handle_trade_phase(player)
        
        # 4. Cell effect
        self.handle_cell_effect(player)
        
        # 5. Check goal selection
        self.check_goal_selection(player)
        
        # 6. Check win/elimination conditions
        self.check_win_condition(player)
        if not self.game_over:
            self.elimination_manager.check_elimination(player, self.turn)
        
        # 7. Check personal items limit
        if player.force_discard_excess_personal_items():
            self.log(f"📦 {player.name} now has {len(player.personal_items_hand)}/{player.max_personal_items_hand} personal items")
        
        self.log(f"State after turn: {player}")
        
        # Analytics: Track goal progress
        if player.win_condition:
            goal_requirements = player.win_condition['requires']
            current_progress = {
                'money': player.money,
                'document_level': int(player.document_level),
                'language_level': player.language_level,
                'housing_level': player.housing_level,
                'housing_type': player.housing,
                'nerves': player.nerves
            }
            self.analytics.track_goal_progress(player, goal_requirements, current_progress)

    def handle_pre_turn_actions(self, player):
        """Handle actions at the start of a turn."""
        decision = player.ai.decide_play_action_card('start_of_turn')
        if decision:
            if isinstance(decision, tuple) and decision[0] == 'personal_item':
                # Use personal item
                _, item_to_use = decision
                if player.use_personal_item(item_to_use):
                    self.effect_manager.apply_effects(player, item_to_use.get('effects', {}))
            else:
                # Handle action cards
                cards_to_play = decision if isinstance(decision, list) else [decision]
                for card_to_play in cards_to_play:
                    # Create pre-turn action event
                    event = InteractiveEvent(
                        "pre_turn_action",
                        player,
                        card_to_play.get('effects', {}),
                        f"{player.name} plays '{card_to_play['name']}' before turn"
                    )
                    event = self.interaction_manager.announce_event(event)
                    
                    if not event.is_blocked:
                        self.effect_manager.apply_effects(player, event.effects)
                    player.action_cards.remove(card_to_play)
                    self.decks['action'].discard(card_to_play)

    def handle_movement(self, player):
        """Handle player movement."""
        roll = random.randint(1, 6)
        # Create movement event
        movement_event = InteractiveEvent(
            "movement",
            player,
            {"movement": roll},
            f"{player.name} rolled {roll} and will move to position {(player.position + roll) % self.board.size}"
        )
        movement_event = self.interaction_manager.announce_event(movement_event)
        if not movement_event.is_blocked:
            final_roll = movement_event.effects.get("movement", roll)
            old_position = player.position
            new_position = (player.position + final_roll) % self.board.size
            player.position = new_position
            if old_position > new_position:
                self.log(f"System: {player.name} completed a lap!")
                self.handle_lap_completion(player)
        else:
            self.log(f"🚫 {player.name}'s movement was blocked!")
        # Analytics: Track cell visit
        cell_type = self.board.get_cell_type(player.position)
        self.analytics.track_cell_visit(player, player.position, cell_type)

    def handle_trade_phase(self, player):
        """Handle trading between players."""
        if player.ai.should_initiate_trade():
            trade_proposal = player.ai.create_trade_proposal()
            
            if trade_proposal:
                requested, offered, description = trade_proposal
                self.log(f"\n💰 TRADE PROPOSAL: {description}")
                
                # Create offer through trade manager
                offer = self.trade_manager.create_trade_offer(
                    player, requested, offered, description
                )
                
                # Find potential partners
                partners = self.trade_manager.find_potential_trading_partners(offer)
                
                if partners:
                    self.log(f"   Potential partners: {[p.name for p in partners]}")
                    
                    # Ask each potential partner in random order
                    random.shuffle(partners)
                    trade_completed = False
                    
                    for partner in partners:
                        if partner.ai.evaluate_trade_offer(offer):
                            self.log(f"   {partner.name} accepts the trade!")
                            
                            # Execute the trade
                            was_honest = self.trade_manager.execute_trade(offer, partner)
                            
                            # Update trust levels
                            partner.ai.update_trust(player, was_honest)
                            player.ai.update_trust(partner, True)
                            
                            trade_completed = True
                            break
                        else:
                            self.log(f"   {partner.name} declines the trade.")
                    
                    if not trade_completed:
                        self.log(f"   No one accepted the trade offer.")
                else:
                    self.log(f"   No potential trading partners found.")

    def handle_cell_effect(self, player):
        """Handle effects of the cell player landed on."""
        cell_type = self.board.get_cell_type(player.position)
        
        if cell_type == 'green':
            decision = player.ai.decide_on_green_space()
            if decision == 'buy_document_level':
                # Try to buy document level
                if player.buy_document_level():
                    # Create document level up event
                    level_up_event = InteractiveEvent(
                        "document_level_up",
                        player,
                        {"document_level": 1},
                        f"{player.name} attempts to buy document level"
                    )
                    level_up_event = self.interaction_manager.announce_event(level_up_event)
                    
                    if level_up_event.is_blocked:
                        self.log(f"🚫 {player.name}'s document level up was blocked!")
                        # Refund the money
                        cost = (player.document_level + 1) * 3
                        player.money += cost
                        player.document_level -= 1
            elif decision == 'draw_green':
                card = self.decks['green'].draw()
                if card:
                    use_decision = 'event'  # Default for non-exchange cards
                    if card.get('exchange_instruction'):
                        use_decision = player.ai.decide_green_card_use(card)
                        
                        if use_decision == 'exchange':
                            # Create document exchange event
                            exchange_event = InteractiveEvent(
                                "document_exchange",
                                player,
                                {"document_level": 1},
                                f"{player.name} attempts document exchange with '{card['name']}'"
                            )
                            exchange_event = self.interaction_manager.announce_event(exchange_event)
                            
                            if not exchange_event.is_blocked:
                                self.effect_manager.apply_effects(player, exchange_event.effects)
                            else:
                                self.log(f"🚫 {player.name}'s document exchange was blocked!")
                        else:
                            self.effect_manager.apply_effects(player, card.get('effects', {}))
                    else:
                        self.effect_manager.apply_effects(player, card.get('effects', {}))
            elif decision == 'draw_personal_item':
                player.add_personal_items(1, self)
                self.log(f"{player.name} получил одноразовую шмотку вместо зелёной карты.")
        
        elif cell_type in ['red', 'white']:
            card = self.decks[cell_type].draw()
            if card:
                # Create challenge/event card event
                challenge_event = InteractiveEvent(
                    "challenge_event",
                    player,
                    card.get('effects', {}),
                    f"{player.name} faces '{card['name']}' ({cell_type} card)"
                )
                challenge_event = self.interaction_manager.announce_event(challenge_event)
                
                if not challenge_event.is_blocked:
                    # Apply potentially modified effects
                    modified_card = card.copy()
                    modified_card['effects'] = challenge_event.effects
                    if 'challenge' in modified_card:
                        self.challenge_manager.handle_challenge(self.log, player, modified_card['challenge'])
                    else:
                        self.effect_manager.apply_effects(player, modified_card['effects'])
                else:
                    self.log(f"🚫 {player.name}'s challenge was blocked!")

    def check_goal_selection(self, player):
        """Check if player needs to select a goal."""
        if not player.goal_chosen and player.document_level >= 5:
            # Choose random goal
            win_conditions = list(self.config['win_conditions'].items())
            win_key, win_data = random.choice(win_conditions)
            player.win_condition = {"key": win_key, **win_data}
            player.goal_chosen = True
            
            # Update AI with new goal
            player.ai.goal_requirements = player.win_condition.get('requires', {})
            
            self.log(f"🎯 {player.name} достиг 5-го уровня документов и выбрал цель: {win_key}!")

    def check_win_condition(self, player):
        """Check if player has met their victory condition."""
        if self.game_over or not player.win_condition:
            return
        
        goal = player.win_condition['requires']
        met_all_conditions = True
        
        for key, required_value in goal.items():
            player_value = getattr(player, key, None)
            
            # Special handling for document_level
            if key == 'document_level':
                player_value = int(player_value)
                
            if key == 'housing_type':
                if player.housing != required_value:
                    met_all_conditions = False
                    break
            elif player_value is None:
                met_all_conditions = False
                break
            else:
                try:
                    if player_value is None:
                        met_all_conditions = False
                        break
                    
                    # Convert to appropriate type
                    if isinstance(required_value, (int, float)):
                        player_value = float(player_value)
                        required_value = float(required_value)
                    elif isinstance(required_value, str):
                        player_value = str(player_value)
                    
                    if player_value < required_value:
                        met_all_conditions = False
                        break
                except (ValueError, TypeError) as e:
                    self.log(f"❌ ERROR in check_win_condition: {e}")
                    self.log(f"   key = {key}, player_value = {player_value} (type: {type(player_value)})")
                    self.log(f"   required_value = {required_value} (type: {type(required_value)})")
                    met_all_conditions = False
                    break
        
        if met_all_conditions:
            self.game_over = True
            self.winner = player
            self.end_reason = 'win'
            self.analytics.end_game(player, self.end_reason)

    def handle_lap_completion(self, player):
        """Handle events that occur when a player completes a lap."""
        if not player.is_eliminated:
            # Pay housing costs first
            housing_cost = player.housing_cost
            old_money = player.money
            player.money -= housing_cost
            # Analytics: Track housing cost
            self.analytics.track_resource_change(player, 'money', -housing_cost, 'housing_cost')
            # Then handle salary
            if player.salary_type == 'dice':
                salary = random.randint(1, 6) + player.salary_base
            else:
                salary = player.salary
            player.money += salary
            # Analytics: Track salary
            self.analytics.track_resource_change(player, 'money', salary, 'salary')
            # Give document card
            player.document_cards += 1
            self.analytics.track_resource_change(player, 'document_cards', 1, 'round_income')
            self.log(f"End of round: {player.name} +{salary} salary -{housing_cost} rent = {player.money - old_money} net")
            # Update lap counter
            player.lap_count += 1
            self.log(f"Lap count for {player.name}: {player.lap_count}")
            # Check elimination after income/expenses
            self.elimination_manager.check_elimination(player, self.turn)
                
    def calculate_win_progress(self, player) -> float:
        """Calculate how close a player is to winning (0.0 to 1.0)"""
        if not hasattr(player, 'win_condition') or not player.win_condition:
            return 0.0
        
        goal = player.win_condition['requires']
        progress = 0.0
        requirements = 0
        
        for key, required_value in goal.items():
            requirements += 1
            player_value = getattr(player, key, 0)
            # Ensure document_level is always int
            if key == 'document_level':
                player_value = int(player_value)
            
            if key == 'housing_type':
                # Special handling for housing type
                housing_levels = {'room': 1, 'apartment': 2, 'mortgage': 3}
                player_level = housing_levels.get(getattr(player, 'housing', 'room'), 1)
                required_level = housing_levels.get(required_value, 1)
                progress += min(1.0, player_level / required_level)
            else:
                # Ensure both values are numeric for comparison
                try:
                    required_value = float(required_value)
                    player_value = float(player_value)
                    if required_value > 0:
                        progress += min(1.0, player_value / required_value)
                    else:
                        progress += 1.0 if player_value >= required_value else 0.0
                except (ValueError, TypeError) as e:
                    # If conversion fails, assume no progress
                    self.log(f"❌ CONVERSION ERROR in calculate_win_progress: {e}")
                    self.log(f"   key={key}, player_value={player_value} (type: {type(player_value)})")
                    self.log(f"   required_value={required_value} (type: {type(required_value)})")
                    progress += 0.0
        
        return progress / requirements if requirements > 0 else 0.0
