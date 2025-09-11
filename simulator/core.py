import random


class InteractiveEvent:
    """Represents an event that can be interfered with by other players."""
    def __init__(self, action_type, acting_player, target_player=None, effects=None, description=""):
        self.action_type = action_type  # "document_exchange", "money_gain", etc.
        self.acting_player = acting_player
        self.target_player = target_player
        self.effects = effects or {}
        self.description = description
        self.is_blocked = False
        self.is_modified = False
        self.modifiers = []
        
    def can_be_interfered(self):
        """Check if this event can be interfered with."""
        interferable_actions = [
            "document_exchange", "money_gain", "document_level_up", 
            "any_positive_effect", "close_to_win"
        ]
        return self.action_type in interferable_actions
    
    def apply_interference(self, interference_card, interfering_player):
        """Apply interference from another player."""
        effects = interference_card.get('effects', {})
        
        if effects.get('block_action'):
            self.is_blocked = True
            print(f"🚫 {interfering_player.name} blocked {self.acting_player.name}'s action with '{interference_card['name']}'!")
            
        if 'reduce_effect' in effects:
            reduction = effects['reduce_effect']
            for key in self.effects:
                if isinstance(self.effects[key], (int, float)) and self.effects[key] > 0:
                    self.effects[key] = int(self.effects[key] * (1 - reduction))
            self.is_modified = True
            print(f"📉 {interfering_player.name} reduced {self.acting_player.name}'s effects by {int(reduction*100)}%!")
            
        # Apply effects to targets
        if 'target_nerves' in effects:
            self.acting_player.nerves = max(1, self.acting_player.nerves + effects['target_nerves'])
        if 'target_money' in effects:
            self.acting_player.money = max(0, self.acting_player.money + effects['target_money'])
        if 'target_document_cards' in effects:
            self.acting_player.document_cards = max(0, self.acting_player.document_cards + effects['target_document_cards'])
            
    def apply_defense(self, defense_card, defending_player):
        """Apply defense against interference."""
        effects = defense_card.get('effects', {})
        
        if effects.get('block_sabotage'):
            self.is_blocked = False
            self.is_modified = False
            print(f"🛡️ {defending_player.name} defended with '{defense_card['name']}'!")
            
            # Apply self-effects from defense
            if 'self_nerves' in effects:
                defending_player.nerves = min(25, defending_player.nerves + effects['self_nerves'])
            if 'self_money' in effects:
                defending_player.money += effects['self_money']
            if 'self_document_cards' in effects:
                defending_player.document_cards += effects['self_document_cards']
                
        if effects.get('reflect_sabotage'):
            # Reflect the sabotage back to interfering player
            print(f"🔄 {defending_player.name} reflected the sabotage!")
            # Find who interfered and apply effects to them
            self.is_blocked = False
            return True
            
        return False


class InteractionManager:
    """Manages instant responses and card interactions between players."""
    def __init__(self, players):
        self.players = players
        self.pending_event = None
        
    def announce_event(self, event):
        """Announce an event and allow other players to respond."""
        if not event.can_be_interfered():
            return event
            
        self.pending_event = event
        print(f"\n⚡ INTERACTIVE EVENT: {event.description}")
        print(f"   Other players can respond with interference cards...")
        
        # Ask other players for interference in turn order
        interference_applied = False
        interfering_player = None
        interference_card = None
        
        for player in self.players:
            if player == event.acting_player or player.is_eliminated:
                continue
                
            # Check if player wants to interfere
            interference = player.ai.decide_interference(event)
            if interference:
                card, cost_paid = interference
                if self._can_pay_cost(player, card) and cost_paid:
                    interference_applied = True
                    interfering_player = player
                    interference_card = card
                    event.apply_interference(card, player)
                    player.action_cards.remove(card)
                    break
                    
        # If interference was applied, check for defense
        if interference_applied and not event.is_blocked:
            defense = event.acting_player.ai.decide_defense(event, interference_card)
            if defense:
                defense_card, cost_paid = defense
                if self._can_pay_cost(event.acting_player, defense_card) and cost_paid:
                    reflected = event.apply_defense(defense_card, event.acting_player)
                    event.acting_player.action_cards.remove(defense_card)
                    
                    # If reflected, apply interference effects to interfering player
                    if reflected and interfering_player:
                        interference_effects = interference_card.get('effects', {})
                        if 'target_nerves' in interference_effects:
                            interfering_player.nerves = max(1, interfering_player.nerves + interference_effects['target_nerves'])
                        if 'target_money' in interference_effects:
                            interfering_player.money = max(0, interfering_player.money + interference_effects['target_money'])
                            
        self.pending_event = None
        return event
        
    def _can_pay_cost(self, player, card):
        """Check if player can pay the cost of playing a card."""
        cost = card.get('cost', {})
        
        if 'money' in cost and player.money < cost['money']:
            return False
        if 'nerves' in cost and player.nerves <= cost['nerves']:
            return False
            
        return True
    
    def _pay_cost(self, player, card):
        """Make player pay the cost of playing a card."""
        cost = card.get('cost', {})
        
        if 'money' in cost:
            player.money -= cost['money']
        if 'nerves' in cost:
            player.nerves -= cost['nerves']


class TradeOffer:
    """Represents a trade offer between players."""
    def __init__(self, offering_player, requested_effects, offered_items, description=""):
        self.offering_player = offering_player  
        self.requested_effects = requested_effects  # What the player wants (e.g., {"nerves": 2})
        self.offered_items = offered_items  # What the player offers (e.g., {"document_cards": 2})
        self.description = description  # Human-readable description
        self.can_lie = True  # Whether the offering player can lie about what they're offering
        self.actual_items = offered_items.copy()  # What they actually have (for potential lies)

    def __repr__(self):
        return f"TradeOffer({self.offering_player.name}: wants {self.requested_effects}, offers {self.offered_items})"


class TradeManager:
    """Handles trading interactions between players."""
    def __init__(self, players):
        self.players = players
        self.pending_offer = None
        
    def create_trade_offer(self, offering_player, requested_effects, offered_items, description=""):
        """Create a new trade offer."""
        offer = TradeOffer(offering_player, requested_effects, offered_items, description)
        
        # AI can decide to lie about what they're offering
        if hasattr(offering_player, 'ai'):
            should_lie = offering_player.ai.decide_to_lie_in_trade(offer)
            if should_lie:
                offer = offering_player.ai.create_deceptive_offer(offer)
                
        return offer
    
    def find_potential_trading_partners(self, offer):
        """Find players who could fulfill the trade request."""
        potential_partners = []
        
        for player in self.players:
            if player == offer.offering_player or player.is_eliminated:
                continue
                
            can_fulfill = True
            for effect_type, amount in offer.requested_effects.items():
                if not self._player_can_provide_effect(player, effect_type, amount):
                    can_fulfill = False
                    break
                    
            if can_fulfill:
                potential_partners.append(player)
                
        return potential_partners
    
    def _player_can_provide_effect(self, player, effect_type, amount):
        """Check if a player can provide a specific effect."""
        if effect_type == "nerves":
            # Player needs action cards that give nerves
            return any(card.get('effects', {}).get('nerves', 0) >= amount 
                      for card in player.action_cards)
        elif effect_type == "money":
            return player.money >= amount
        elif effect_type == "document_cards":
            return player.document_cards >= amount
        # Add more effect types as needed
        return False
    
    def execute_trade(self, offer, accepting_player):
        """Execute a completed trade between two players."""
        offering_player = offer.offering_player
        
        print(f"\nTRADE EXECUTION: {offering_player.name} ↔ {accepting_player.name}")
        print(f"Requested: {offer.requested_effects}")
        print(f"Offered: {offer.offered_items}")
        
        # Check if offering player can actually deliver what they promised
        can_deliver = self._validate_offered_items(offering_player, offer.actual_items)
        
        if not can_deliver:
            print(f"🎭 TRADE SCAM! {offering_player.name} couldn't deliver what they promised!")
            # Penalty for lying
            offering_player.nerves = max(1, offering_player.nerves - 2)
            accepting_player.nerves = max(1, accepting_player.nerves - 1)
            return False
            
        # Execute the actual exchange
        success = True
        
        # Accepting player provides the requested effects
        success &= self._apply_trade_effects(accepting_player, offer.requested_effects, give=True)
        success &= self._apply_trade_effects(offering_player, offer.requested_effects, give=False)
        
        # Offering player provides the offered items  
        success &= self._apply_trade_effects(offering_player, offer.actual_items, give=True)
        success &= self._apply_trade_effects(accepting_player, offer.actual_items, give=False)
        
        if success:
            print(f"✅ Trade completed successfully!")
        else:
            print(f"❌ Trade failed to execute properly!")
            
        return success
    
    def _validate_offered_items(self, player, items):
        """Check if player actually has what they're offering."""
        for item_type, amount in items.items():
            if item_type == "document_cards":
                if player.document_cards < amount:
                    return False
            elif item_type == "money":
                if player.money < amount:
                    return False
            # Add more validation as needed
        return True
    
    def _apply_trade_effects(self, player, effects, give=True):
        """Apply trade effects to a player (give=True means player loses resources)."""
        multiplier = -1 if give else 1
        
        for effect_type, amount in effects.items():
            if effect_type == "nerves":
                if give:
                    # Find and use action cards that provide nerves
                    cards_to_use = []
                    nerves_needed = amount
                    for card in player.action_cards[:]:
                        card_nerves = card.get('effects', {}).get('nerves', 0)
                        if card_nerves > 0 and nerves_needed > 0:
                            cards_to_use.append(card)
                            nerves_needed -= card_nerves
                            if nerves_needed <= 0:
                                break
                    
                    # Use the cards
                    for card in cards_to_use:
                        player.action_cards.remove(card)
                        print(f"  {player.name} used action card: {card['name']}")
                else:
                    player.nerves = min(10, player.nerves + amount)
                    
            elif effect_type == "money":
                player.money += multiplier * amount
                player.money = max(0, player.money)
                
            elif effect_type == "document_cards":
                player.document_cards += multiplier * amount
                player.document_cards = max(0, player.document_cards)
                
        return True


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
        self.lie_probability = 0.3  # 30% chance to lie in trades
        self.trust_levels = {}  # Track trust towards other players


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
            required_docs_for_upgrade = 2 + self.player.document_level  # Progressive requirements
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
    
    def should_initiate_trade(self):
        """Decide if the player should try to initiate a trade this turn."""
        # Check if player has urgent needs
        urgent_needs = self._identify_urgent_needs()
        if not urgent_needs:
            return False
            
        # Only trade if we have something valuable to offer
        valuable_items = self._identify_valuable_items()
        return len(valuable_items) > 0 and random.random() < 0.4  # 40% chance if conditions met
    
    def _identify_urgent_needs(self):
        """Identify what the player urgently needs."""
        needs = {}
        
        # Low nerves is always urgent
        if self.player.nerves <= self.nerve_threshold:
            needs["nerves"] = min(3, 8 - self.player.nerves)
            
        # Check goal-specific needs
        goal_key = self.player.win_condition['key']
        requires = self.player.win_condition.get('requires', {})
        
        if 'money' in requires:
            needed_money = requires['money'] - self.player.money
            if needed_money > 0 and needed_money <= 5:  # Only if close to goal
                needs["money"] = min(needed_money, 3)
                
        if 'document_cards' in requires:
            # Not directly in requirements, but if close to exchange
            if self.player.document_cards == 1:  # One away from exchange
                needs["document_cards"] = 1
                
        return needs
    
    def _identify_valuable_items(self):
        """Identify what valuable items the player can offer."""
        items = {}
        
        # Extra document cards
        if self.player.document_cards > 2:
            items["document_cards"] = min(2, self.player.document_cards - 1)
            
        # Extra money (if not needed for goal)
        goal_money = self.player.win_condition.get('requires', {}).get('money', 0)
        extra_money = self.player.money - goal_money - 3  # Keep some buffer
        if extra_money > 0:
            items["money"] = min(3, extra_money)
            
        return items
    
    def create_trade_proposal(self):
        """Create a trade proposal based on needs and available items."""
        needs = self._identify_urgent_needs()
        items = self._identify_valuable_items()
        
        if not needs or not items:
            return None
            
        # Pick the most urgent need and most available item
        primary_need = max(needs.items(), key=lambda x: x[1])
        primary_item = max(items.items(), key=lambda x: x[1])
        
        requested = {primary_need[0]: primary_need[1]}
        offered = {primary_item[0]: primary_item[1]}
        
        description = f"{self.player.name} wants {primary_need[1]} {primary_need[0]} for {primary_item[1]} {primary_item[0]}"
        
        return requested, offered, description
    
    def decide_to_lie_in_trade(self, offer):
        """Decide whether to lie about what we're offering."""
        # More likely to lie if desperate or if character is untrustworthy
        desperation_factor = (5 - self.player.nerves) / 5.0  # Higher if low nerves
        character_factor = 0.5 if self.player.id == "it_specialist" else 0.3  # IT guys lie more often
        
        lie_chance = (self.lie_probability + desperation_factor * 0.2 + character_factor * 0.2)
        return random.random() < lie_chance
    
    def create_deceptive_offer(self, original_offer):
        """Create a deceptive version of the trade offer."""
        # Lie by claiming to have more than we actually do
        deceptive_offer = TradeOffer(
            original_offer.offering_player,
            original_offer.requested_effects,
            original_offer.offered_items.copy(),
            original_offer.description + " (DECEPTIVE)"
        )
        
        # Keep track of what we actually have vs what we claim
        deceptive_offer.actual_items = {}
        for item_type, claimed_amount in original_offer.offered_items.items():
            if item_type == "document_cards":
                actual_amount = min(claimed_amount, self.player.document_cards)
            elif item_type == "money":
                actual_amount = min(claimed_amount, self.player.money)
            else:
                actual_amount = claimed_amount
                
            deceptive_offer.actual_items[item_type] = actual_amount
            
        print(f"🎭 {self.player.name} is being deceptive in trade offer!")
        return deceptive_offer
    
    def evaluate_trade_offer(self, offer):
        """Decide whether to accept an incoming trade offer."""
        if not offer:
            return False
            
        offering_player = offer.offering_player
        
        # Check trust level
        trust = self.trust_levels.get(offering_player.name, 0.5)  # Default neutral trust
        
        # Check if we can actually provide what's requested
        can_provide = True
        for effect_type, amount in offer.requested_effects.items():
            if effect_type == "nerves":
                nerve_cards = [card for card in self.player.action_cards 
                              if card.get('effects', {}).get('nerves', 0) >= amount]
                if not nerve_cards:
                    can_provide = False
            elif effect_type == "money":
                if self.player.money < amount:
                    can_provide = False
            elif effect_type == "document_cards":
                if self.player.document_cards < amount:
                    can_provide = False
                    
        if not can_provide:
            return False
            
        # Check if what they're offering is valuable to us
        value_to_us = 0
        for item_type, amount in offer.offered_items.items():
            if item_type == "document_cards" and self.player.document_cards < 2:
                value_to_us += amount * 2  # High value if we need docs
            elif item_type == "money":
                goal_money = self.player.win_condition.get('requires', {}).get('money', 0)
                if self.player.money < goal_money:
                    value_to_us += amount
                    
        # Accept if valuable and we trust the player (or desperate)
        desperation = (5 - self.player.nerves) / 5.0
        accept_threshold = 2 - trust - desperation
        
        should_accept = value_to_us >= accept_threshold
        
        if should_accept:
            print(f"🤝 {self.player.name} accepts trade offer (trust: {trust:.1f}, value: {value_to_us})")
        
        return should_accept
    
    def update_trust(self, other_player, was_honest):
        """Update trust level towards another player based on trade outcome."""
        current_trust = self.trust_levels.get(other_player.name, 0.5)
        
        if was_honest:
            self.trust_levels[other_player.name] = min(1.0, current_trust + 0.2)
        else:
            self.trust_levels[other_player.name] = max(0.0, current_trust - 0.4)
            
        print(f"🎯 {self.player.name} trust in {other_player.name}: {self.trust_levels[other_player.name]:.1f}")
    
    def decide_interference(self, event):
        """Decide whether to interfere with another player's action."""
        if event.acting_player == self.player:
            return None
            
        # Check if we have interference cards
        interference_cards = [card for card in self.player.action_cards 
                            if card.get('when_to_play') == 'instant_response' 
                            and card.get('type') == 'interference']
        
        if not interference_cards:
            return None
            
        # Decide if we should interfere
        should_interfere = self._should_interfere_with_event(event)
        
        if not should_interfere:
            return None
            
        # Pick the best interference card
        best_card = self._pick_best_interference_card(interference_cards, event)
        
        if best_card:
            # Check if we can and want to pay the cost
            cost = best_card.get('cost', {})
            if self._willing_to_pay_cost(cost, event):
                self._pay_interference_cost(cost)
                print(f"💥 {self.player.name} plays interference: '{best_card['name']}'!")
                return (best_card, True)
                
        return None
    
    def _should_interfere_with_event(self, event):
        """Decide if we should interfere with this specific event."""
        acting_player = event.acting_player
        
        # More likely to interfere if acting player is close to winning
        if self._is_player_close_to_win(acting_player):
            return random.random() < 0.7  # 70% chance to interfere with close-to-win players
            
        # More likely to interfere if we have low trust in the player
        trust = self.trust_levels.get(acting_player.name, 0.5)
        if trust < 0.3:
            return random.random() < 0.4  # 40% chance to interfere with distrusted players
            
        # Less likely to interfere if we're doing well
        if self._am_i_doing_well():
            return random.random() < 0.2  # 20% chance if we're doing well
            
        # Normal interference rate
        return random.random() < 0.3  # 30% base chance
    
    def _is_player_close_to_win(self, player):
        """Check if a player is close to winning."""
        goal = player.win_condition
        requires = goal.get('requires', {})
        
        # Check if player is close to any goal requirement
        close_factors = 0
        total_factors = 0
        
        if 'money' in requires:
            money_progress = player.money / requires['money']
            if money_progress >= 0.8:  # 80% of required money
                close_factors += 1
            total_factors += 1
            
        if 'document_level' in requires:
            doc_progress = player.document_level / requires['document_level']
            if doc_progress >= 0.8:  # 80% of required document level
                close_factors += 1
            total_factors += 1
            
        if 'language_level' in requires:
            lang_progress = player.language_level / requires['language_level']
            if lang_progress >= 0.8:  # 80% of required language level
                close_factors += 1
            total_factors += 1
            
        if 'housing_type' in requires:
            housing_levels = {'room': 1, 'apartment': 2, 'mortgage': 3}
            required_level = housing_levels.get(requires['housing_type'], 1)
            if player.housing_level >= required_level:
                close_factors += 1
            total_factors += 1
            
        return total_factors > 0 and (close_factors / total_factors) >= 0.5
    
    def _am_i_doing_well(self):
        """Check if I'm doing well myself."""
        goal = self.player.win_condition
        requires = goal.get('requires', {})
        
        progress_factors = 0
        total_factors = 0
        
        if 'money' in requires:
            progress_factors += min(1.0, self.player.money / requires['money'])
            total_factors += 1
            
        if 'document_level' in requires:
            progress_factors += min(1.0, self.player.document_level / requires['document_level'])
            total_factors += 1
            
        return total_factors > 0 and (progress_factors / total_factors) >= 0.6
    
    def _pick_best_interference_card(self, cards, event):
        """Pick the best interference card for this event."""
        # Filter cards that can target this event type
        applicable_cards = []
        
        for card in cards:
            target = card.get('target', '')
            if (target == event.action_type or 
                target == 'any_positive_effect' or
                (target == 'close_to_win' and self._is_player_close_to_win(event.acting_player))):
                applicable_cards.append(card)
                
        if not applicable_cards:
            return None
            
        # Pick the most effective card
        best_card = None
        best_impact = 0
        
        for card in applicable_cards:
            impact = self._calculate_interference_impact(card, event)
            if impact > best_impact:
                best_impact = impact
                best_card = card
                
        return best_card
    
    def _calculate_interference_impact(self, card, event):
        """Calculate the impact value of an interference card."""
        effects = card.get('effects', {})
        impact = 0
        
        if effects.get('block_action'):
            impact += 5  # Blocking is very impactful
            
        if 'reduce_effect' in effects:
            impact += effects['reduce_effect'] * 3  # Effect reduction
            
        if 'target_nerves' in effects:
            impact += abs(effects['target_nerves'])  # Nerve damage
            
        if 'target_money' in effects:
            impact += abs(effects['target_money']) * 0.5  # Money damage
            
        return impact
    
    def _willing_to_pay_cost(self, cost, event):
        """Check if we're willing to pay the cost for interference."""
        if not cost:
            return True
            
        # More willing to pay if target is close to winning
        if self._is_player_close_to_win(event.acting_player):
            return True
            
        # Check if cost is reasonable
        money_cost = cost.get('money', 0)
        nerve_cost = cost.get('nerves', 0)
        
        if money_cost > self.player.money * 0.3:  # Don't spend more than 30% of money
            return False
            
        if nerve_cost >= self.player.nerves - 2:  # Don't go below 2 nerves
            return False
            
        return True
    
    def _pay_interference_cost(self, cost):
        """Pay the cost for playing interference."""
        if 'money' in cost:
            self.player.money -= cost['money']
        if 'nerves' in cost:
            self.player.nerves -= cost['nerves']
    
    def decide_defense(self, event, interference_card):
        """Decide whether to play a defense card against interference."""
        # Check if we have defense cards
        defense_cards = [card for card in self.player.action_cards 
                        if card.get('when_to_play') == 'instant_response' 
                        and card.get('type') == 'counter']
        
        if not defense_cards:
            return None
            
        # Always try to defend if we can afford it
        for card in defense_cards:
            cost = card.get('cost', {})
            if self._willing_to_pay_cost(cost, event):
                self._pay_interference_cost(cost)
                print(f"🛡️ {self.player.name} plays defense: '{card['name']}'!")
                return (card, True)
                
        return None


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
        self.salary_base = profile.get('salary_base', 0)  # Base salary for dice-based income
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
        
        # Initialize trade manager and interaction manager after players are created
        self.trade_manager = TradeManager(self.players)
        self.interaction_manager = InteractionManager(self.players)

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

            # Dynamic turn limit based on number of players
            # Optimized for 45-80 minute games (assuming 2 min per turn)
            # Base: 22-40 turns for different player counts
            if len(self.players) <= 4:
                max_turns = 35  # ~70 minutes
            elif len(self.players) <= 6:
                max_turns = 40  # ~80 minutes
            else:
                max_turns = 45  # ~90 minutes for 8 players
            
            if self.turn >= max_turns:
                self.game_over = True
                if not self.winner:
                    self.end_reason = 'time_limit'

        return {"winner": self.winner.name if self.winner else "None", "turns": self.turn}

    def handle_lap_completion(self):
        """Handles events that occur when a player completes a lap, like salary."""
        for player in self.players:
            if not player.is_eliminated:
                # Handle different salary types
                if player.salary_type == 'dice':
                    # Dice-based salary: base + dice roll
                    dice_roll = random.randint(1, 6)
                    earned_salary = player.salary_base + dice_roll
                    print(f"System: {player.name} earned {earned_salary} money (base {player.salary_base} + dice {dice_roll})")
                    player.money += earned_salary
                else:
                    # Fixed salary
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

        # 3. Trade phase (before cell effect)
        self.handle_trade_phase(player)

        # 4. Handle cell effect
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

        # 5. Check for win/loss conditions
        self.check_win_condition(player)
        if not self.game_over:
            self.check_elimination(player)

        print(f"State after turn:  {player}")
    
    def handle_trade_phase(self, current_player):
        """Handle the trading phase for the current player."""
        if current_player.is_eliminated:
            return
            
        # Check if current player wants to initiate a trade
        if current_player.ai.should_initiate_trade():
            trade_proposal = current_player.ai.create_trade_proposal()
            
            if trade_proposal:
                requested, offered, description = trade_proposal
                print(f"\n💰 TRADE PROPOSAL: {description}")
                
                # Create the offer through trade manager
                offer = self.trade_manager.create_trade_offer(
                    current_player, requested, offered, description
                )
                
                # Find potential partners
                partners = self.trade_manager.find_potential_trading_partners(offer)
                
                if partners:
                    print(f"   Potential partners: {[p.name for p in partners]}")
                    
                    # Ask each potential partner in random order
                    random.shuffle(partners)
                    trade_completed = False
                    
                    for partner in partners:
                        if partner.ai.evaluate_trade_offer(offer):
                            print(f"   {partner.name} accepts the trade!")
                            
                            # Execute the trade
                            was_honest = self.trade_manager.execute_trade(offer, partner)
                            
                            # Update trust levels
                            partner.ai.update_trust(current_player, was_honest)
                            current_player.ai.update_trust(partner, True)  # Partner was honest by accepting
                            
                            trade_completed = True
                            break
                        else:
                            print(f"   {partner.name} declines the trade.")
                    
                    if not trade_completed:
                        print(f"   No one accepted the trade offer.")
                else:
                    print(f"   No potential trading partners found.")

    def apply_card_effect(self, player, card, decision, chosen_effect=None):
        """
        The main engine for applying card effects.
        It checks conditions, handles challenges, and applies effects based on a decision.
        """
        # 1. Handle document exchange decision
        if decision == 'exchange':
            # Create interactive event for document exchange
            event = InteractiveEvent(
                "document_exchange",
                player,
                effects={"document_level": 1},
                description=f"{player.name} attempts to exchange documents for level up"
            )
            
            # Allow other players to interfere
            event = self.interaction_manager.announce_event(event)
            
            if event.is_blocked:
                print(f"System: {player.name}'s document exchange was blocked!")
                return
            
            # Progressive requirements: more cards needed for higher levels
            required_docs = 2 + player.document_level  # Level 0→1: 2 cards, Level 1→2: 3 cards, etc.
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

        # Check if this is a significant positive effect that can be interfered with
        is_significant_positive = (
            effects.get('money', 0) > 2 or
            effects.get('documents_cards', 0) > 2 or
            effects.get('instant_document_upgrade', 0) > 0 or
            effects.get('language_level_up', False)
        )
        
        if is_significant_positive:
            # Create interactive event for significant positive effects
            event = InteractiveEvent(
                "any_positive_effect",
                player,
                effects=effects.copy(),
                description=f"{player.name} gets significant benefit from '{card['name']}'"
            )
            
            # Allow other players to interfere
            event = self.interaction_manager.announce_event(event)
            
            if event.is_blocked:
                print(f"System: {player.name}'s positive effect was blocked!")
                return
                
            # Use modified effects if interference applied reduction
            if event.is_modified:
                effects = event.effects

        for key, value in effects.items():
            if key == 'nerves':
                player.nerves += value
            elif key == 'money':
                # Create money gain event for values > 2
                if value > 2:
                    money_event = InteractiveEvent(
                        "money_gain",
                        player,
                        effects={"money": value},
                        description=f"{player.name} gains {value} money"
                    )
                    money_event = self.interaction_manager.announce_event(money_event)
                    
                    if not money_event.is_blocked:
                        final_value = money_event.effects.get("money", value)
                        player.money += final_value
                else:
                    player.money += value
            elif key == 'documents_cards':
                player.document_cards += value
            elif key == 'draw_action_card':
                for _ in range(value):
                    drawn_card = self.decks['action'].draw()
                    if drawn_card:
                        player.add_action_card(drawn_card)
            elif key == 'instant_document_upgrade':
                # Create interactive event for document level up
                doc_event = InteractiveEvent(
                    "document_level_up",
                    player,
                    effects={"document_level": 1},
                    description=f"{player.name} instantly upgrades document level"
                )
                doc_event = self.interaction_manager.announce_event(doc_event)
                
                if not doc_event.is_blocked:
                    player.document_level += 1
            elif key == 'language_level_up':
                if player.language_level < 3:
                    player.language_level += 1
                    print(f"System: {player.name} improved language to level {player.language_level}!")
            elif key == 'document_level':
                # Can be positive or negative
                old_level = player.document_level
                player.document_level = max(0, player.document_level + value)
                if value < 0:
                    print(f"System: {player.name} lost document level! {old_level} → {player.document_level}")
                else:
                    print(f"System: {player.name} gained document level! {old_level} → {player.document_level}")
            elif key == 'language_level':
                # Can be positive or negative  
                old_level = player.language_level
                player.language_level = max(1, min(3, player.language_level + value))
                if value < 0:
                    print(f"System: {player.name} lost language level! {old_level} → {player.language_level}")
                else:
                    print(f"System: {player.name} gained language level! {old_level} → {player.language_level}")

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


