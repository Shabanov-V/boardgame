import random
from ..managers.trade_manager import TradeOffer

class AI:
    """Holds the decision-making logic for a player."""
    def __init__(self, player, config):
        self.player = player
        self.config = config
        self.nerve_threshold = config['simulation_parameters'].get('ai_nerve_threshold', 3)
        self.goal_requirements = self.player.win_condition.get('requires', {}) if self.player.win_condition else {}
        self.lie_probability = 0.3  # 30% chance to lie in trades
        self.trust_levels = {}  # Track trust towards other players
        self.grudges = {}  # Track grudges against players who hurt us

    def decide_use_personal_item(self, turn_context):
        """Decide which personal item to use."""
        if not self.player.personal_items_hand:
            return None
            
        # Priority 1: Critically low nerves
        if self.player.nerves <= 2:
            for item in self.player.personal_items_hand:
                if (self._item_helps_nerves(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Критически низкие нервы, использую '{item['name']}'")
                    return item
        
        # Priority 2: Goal advancement
        if self.player.win_condition:
            for item in self.player.personal_items_hand:
                if (self._item_helps_goal(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Предмет поможет цели, использую '{item['name']}'")
                    return item
        
        # Priority 3: Defensive items when low on resources
        if self.player.money <= 3 or self.player.nerves <= 4:
            for item in self.player.personal_items_hand:
                if (self._is_defensive_item(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Низкие ресурсы, использую защитный предмет '{item['name']}'")
                    return item
        
        return None

    def decide_use_aggressive_item(self, turn_context, other_players):
        """Decide whether to use an aggressive item against an opponent."""
        if not self.player.personal_items_hand or not other_players:
            return None
            
        # Priority 1: Revenge against enemies
        if hasattr(self, 'grudges') and self.grudges:
            for enemy_id, grudge_level in self.grudges.items():
                if grudge_level >= 2:  # Serious grudge
                    target = next((p for p in other_players if p.id == enemy_id), None)
                    if target:
                        for item in self.player.personal_items_hand:
                            if (self._is_aggressive_item(item) and 
                                self.player.can_use_personal_item(item) and
                                self._should_target_enemy(item, target)):
                                print(f"AI ({self.player.name}): МЕСТЬ! Использую '{item['name']}' против {target.name} (обида: {grudge_level})")
                                return ('aggressive_item', item, target)
        
        # Priority 2: Attack leader if falling behind
        leader = max(other_players, key=lambda p: self._estimate_player_progress(p))
        if (self._estimate_player_progress(leader) > self._estimate_player_progress(self.player) + 3):
            for item in self.player.personal_items_hand:
                if (self._is_aggressive_item(item) and 
                    self.player.can_use_personal_item(item) and
                    self._should_target_leader(item, leader)):
                    print(f"AI ({self.player.name}): Атакую лидера {leader.name} предметом '{item['name']}'")
                    return ('aggressive_item', item, leader)
        
        # Priority 3: Preventive attack on close-to-win player
        for player in other_players:
            if self._is_close_to_winning_estimate(player):
                for item in self.player.personal_items_hand:
                    if (self._is_aggressive_item(item) and 
                        self.player.can_use_personal_item(item)):
                        print(f"AI ({self.player.name}): Превентивная атака! {player.name} близок к победе, использую '{item['name']}'")
                        return ('aggressive_item', item, player)
        
        return None

    def decide_play_action_card(self, turn_context):
        """Decide which action card(s) to play from hand."""
        cards_to_play = []
        
        # First check personal items
        personal_item = self.decide_use_personal_item(turn_context)
        if personal_item:
            return ('personal_item', personal_item)
        
        # Priority 1: Manage low nerves
        if self.player.nerves < self.nerve_threshold:
            for card in self.player.action_cards:
                if card.get('effects', {}).get('nerves', 0) > 0 and self._can_play_now(card, turn_context):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Nerves are low ({self.player.nerves}), playing '{card['name']}'.")
                    if self.player.nerves < 2 and len(cards_to_play) < 2:
                        continue
                    else:
                        break

        # Priority 2: Advance win condition
        if self.player.win_condition and not cards_to_play:
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and self._card_helps_goal(card):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Playing '{card['name']}' to advance win condition.")
                    break
        elif not self.player.win_condition and not cards_to_play:
            # Focus on documents without goal
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and card.get('effects', {}).get('documents_cards', 0) > 0:
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): No goal - accumulating documents with '{card['name']}'.")
                    break

        # Priority 3: Utility cards
        if not cards_to_play:
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and self._is_utility_card(card):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Playing utility card '{card['name']}'.")
                    break

        return cards_to_play if cards_to_play else None

    def _item_helps_nerves(self, item):
        """Check if item helps with nerves."""
        effects = item.get('effects', {})
        profile_effects = item.get('profile_modifiers', {}).get(self.player.id, {})
        return (effects.get('nerves', 0) > 0 or 
                profile_effects.get('nerves', 0) > 0)
    
    def _item_helps_goal(self, item):
        """Check if item helps achieve goal."""
        if not self.player.win_condition:
            return False
            
        effects = item.get('effects', {})
        profile_effects = item.get('profile_modifiers', {}).get(self.player.id, {})
        requirements = self.goal_requirements
        
        for req, target_value in requirements.items():
            current_value = getattr(self.player, req, 0)
            
            if isinstance(current_value, str) or isinstance(target_value, str):
                continue
                
            try:
                current_value = float(current_value)
                target_value = float(target_value)
            except (ValueError, TypeError):
                continue
                
            if current_value < target_value:
                item_bonus = effects.get(req, 0) + profile_effects.get(req, 0)
                if item_bonus > 0:
                    return True
        
        return False
    
    def _is_defensive_item(self, item):
        """Check if item is defensive."""
        effects = item.get('effects', {})
        special_effects = item.get('special_effects', [])
        
        defensive_keywords = ['immunity', 'protection', 'shield', 'block', 'prevent']
        for keyword in defensive_keywords:
            if keyword in str(special_effects).lower():
                return True
        
        return (effects.get('nerves', 0) >= 2 or 
                effects.get('money', 0) >= 3)
    
    def _can_use_item_now(self, item, turn_context):
        """Check if item can be used now."""
        when_to_play = item.get('when_to_play', 'anytime')
        return when_to_play == 'anytime' or when_to_play == turn_context
    
    def _is_aggressive_item(self, item):
        """Check if item is aggressive."""
        item_type = item.get('type', '')
        target_type = item.get('target', '')
        special_effects = item.get('special_effects', [])
        
        if item_type in ['attack', 'sabotage', 'interference']:
            return True
            
        if target_type in ['other_player', 'enemy', 'target_player']:
            return True
            
        aggressive_effects = ['challenge_target', 'reduce_resources', 'block_action', 'steal_effect']
        return any(effect in special_effects for effect in aggressive_effects)
    
    def _should_target_enemy(self, item, target):
        """Determine if should use item against specific enemy."""
        target_conditions = item.get('target_conditions', {})
        
        if 'min_money' in target_conditions and target.money < target_conditions['min_money']:
            return False
        if 'max_nerves' in target_conditions and target.nerves > target_conditions['max_nerves']:
            return False
        if 'required_resources' in target_conditions:
            for resource, min_value in target_conditions['required_resources'].items():
                if getattr(target, resource, 0) < min_value:
                    return False
        
        return True
    
    def _should_target_leader(self, item, leader):
        """Determine if should attack leader with this item."""
        effects = item.get('target_effects', {})
        special_effects = item.get('special_effects', [])
        
        anti_leader_effects = ['reduce_money', 'reduce_documents', 'force_challenge', 'block_progress']
        return (any(effect in effects for effect in ['money', 'documents_cards', 'nerves']) or
                any(effect in special_effects for effect in anti_leader_effects))
    
    def _estimate_player_progress(self, player):
        """Estimate player's progress towards victory."""
        if not player.win_condition:
            return player.money + player.nerves + player.document_level * 3
        
        requirements = player.win_condition.get('requires', {})
        progress = 0
        
        for req, target_value in requirements.items():
            current_value = getattr(player, req, 0)
            if isinstance(current_value, (int, float)):
                progress += min(current_value / target_value, 1.0) * 10
        
        return progress
    
    def _is_close_to_winning_estimate(self, player):
        """Estimate if player is close to winning."""
        if not player.win_condition:
            return False
            
        requirements = player.win_condition.get('requires', {})
        progress_ratio = 0
        total_requirements = len(requirements)
        
        for req, target_value in requirements.items():
            current_value = getattr(player, req, 0)
            if isinstance(current_value, (int, float)):
                progress_ratio += min(current_value / target_value, 1.0)
        
        return (progress_ratio / total_requirements) >= 0.75
    
    def add_grudge(self, enemy_player_id, severity=1):
        """Add a grudge against a player."""
        if enemy_player_id not in self.grudges:
            self.grudges[enemy_player_id] = 0
        self.grudges[enemy_player_id] += severity
        
        enemy_name = enemy_player_id
        print(f"💢 {self.player.name} запомнил обиду на {enemy_name} (уровень: {self.grudges[enemy_player_id]})")
    
    def reduce_grudge(self, player_id, amount=1):
        """Reduce grudge against a player."""
        if player_id in self.grudges:
            self.grudges[player_id] = max(0, self.grudges[player_id] - amount)
            if self.grudges[player_id] == 0:
                del self.grudges[player_id]

    def _can_play_now(self, card, turn_context):
        """Check if card can be played in current context."""
        when_to_play = card.get('when_to_play', 'anytime')
        return when_to_play == 'anytime' or when_to_play == turn_context
    
    def _is_utility_card(self, card):
        """Check if card provides general utility benefits."""
        effects = card.get('effects', {})
        return (effects.get('money', 0) > 0 or 
                effects.get('documents_cards', 0) > 0 or
                effects.get('steal_permanent_effect', False) or
                any(key.endswith('_bonus') for key in effects.keys()) or
                any(key.startswith('block_') for key in effects.keys()))

    def _card_helps_goal(self, card):
        """Check if card's effects align with win condition."""
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
        if self._is_close_to_winning_estimate(acting_player):
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
    
    def _pick_best_interference_card(self, cards, event):
        """Pick the best interference card for this event."""
        # Filter cards that can target this event type
        applicable_cards = []
        
        for card in cards:
            target = card.get('target', '')
            if (target == event.action_type or 
                target == 'any_positive_effect' or
                (target == 'close_to_win' and self._is_close_to_winning_estimate(event.acting_player))):
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
        if self._is_close_to_winning_estimate(event.acting_player):
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
        
    def should_initiate_trade(self):
        """Decide if the player should try to initiate a trade this turn."""
        # Check if player has urgent needs OR excess resources to trade
        urgent_needs = self._identify_urgent_needs()
        excess_resources = self._identify_excess_resources()
        
        # Trade if we have urgent needs OR if we have excess resources to sell
        should_trade = (len(urgent_needs) > 0 or len(excess_resources) > 0)
        
        if not should_trade:
            return False
            
        # Only trade if we have something valuable to offer
        valuable_items = self._identify_valuable_items()
        return len(valuable_items) > 0 and random.random() < 0.6  # 60% chance if conditions met
    
    def _identify_urgent_needs(self):
        """Identify what the player urgently needs."""
        needs = {}
        
        # Low nerves is always urgent
        if self.player.nerves <= self.nerve_threshold:
            needs["nerves"] = min(3, 8 - self.player.nerves)
            
        # Check goal-specific needs (only if goal is chosen)
        if self.player.win_condition:
            goal_key = self.player.win_condition['key']
            requires = self.player.win_condition.get('requires', {})
        else:
            # Without goal - focus on documents
            if self.player.document_cards == 1:  # Close to exchange
                needs["documents_cards"] = 1
            return needs
        
        if 'money' in requires:
            needed_money = requires['money'] - self.player.money
            if needed_money > 0 and needed_money <= 5:  # Only if close to goal
                needs["money"] = min(needed_money, 3)
                
        # Strategic trading: use excess money to buy needed resources
        if self.player.money > 50:  # Rich players should trade money for progress
            if 'nerves' in requires:
                needed_nerves = requires['nerves'] - self.player.nerves
                if needed_nerves > 0:
                    needs["nerves"] = min(needed_nerves, 3)
                    
            # Always need documents to progress
            if self.player.document_cards < 3:
                needs["document_cards"] = 2
                
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
        if self.player.win_condition:
            goal_money = self.player.win_condition.get('requires', {}).get('money', 0)
            extra_money = self.player.money - goal_money - 3  # Keep some buffer
        else:
            # Without goal keep only base amount for survival
            extra_money = self.player.money - 10  # Minimum for survival
            
        # Rich players should be more generous with money
        if self.player.money > 100:
            extra_money = self.player.money - goal_money if self.player.win_condition else self.player.money - 20
            if extra_money > 0:
                items["money"] = min(8, extra_money)  # Can offer more money
        elif extra_money > 0:
            items["money"] = min(3, extra_money)
            
        return items
    
    def _identify_excess_resources(self):
        """Identify resources the player has in excess and could trade away."""
        excess = {}
        
        # Excess document cards (if player has high document level and many cards)
        if (self.player.document_level >= 5 and 
            self.player.document_cards >= 4):
            excess["document_cards"] = min(3, self.player.document_cards - 2)
        
        # Excess money (if player has a lot of money)
        if self.player.money >= 15:
            excess["money"] = min(5, self.player.money - 10)
        
        # Excess nerves (if player has very high nerves)
        if self.player.nerves >= 12:
            excess["nerves"] = min(3, self.player.nerves - 10)
        
        # Excess personal items (if player has many items)
        if len(self.player.personal_items_hand) >= 4:
            excess["personal_items"] = 1
        
        return excess
    
    def create_trade_proposal(self):
        """Create a trade proposal based on needs and available items."""
        needs = self._identify_urgent_needs()
        items = self._identify_valuable_items()
        excess = self._identify_excess_resources()
        
        # If we have excess resources, try to sell them for money
        if excess and not needs:
            # Sell excess resources for money
            primary_excess = max(excess.items(), key=lambda x: x[1])
            requested = {"money": min(6, primary_excess[1] * 4)}  # Price: 4 money per resource
            offered = {primary_excess[0]: primary_excess[1]}
            description = f"{self.player.name} sells {primary_excess[1]} {primary_excess[0]} for {requested['money']} money"
            return requested, offered, description
        
        # If we have needs and items, trade normally
        if needs and items:
            primary_need = max(needs.items(), key=lambda x: x[1])
            primary_item = max(items.items(), key=lambda x: x[1])
            
            requested = {primary_need[0]: primary_need[1]}
            offered = {primary_item[0]: primary_item[1]}
            
            description = f"{self.player.name} wants {primary_need[1]} {primary_need[0]} for {primary_item[1]} {primary_item[0]}"
            return requested, offered, description
        
        return None
    
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
                if self.player.win_condition:
                    goal_money = self.player.win_condition.get('requires', {}).get('money', 0)
                    if self.player.money < goal_money:
                        value_to_us += amount
                else:
                    # Without goal money is always valuable for survival
                    value_to_us += amount * 0.5
                    
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
        
    def decide_on_green_space(self):
        """Decide whether to draw a green card, buy document level, or get a personal item."""
        # If we can buy a document level and need it, do it
        if self.player.can_buy_document_level():
            if not self.player.win_condition:
                # No goal yet, always good to get document levels
                print(f"AI ({self.player.name}): Buying document level to reach goal selection.")
                return 'buy_document_level'
            elif 'document_level' in self.goal_requirements:
                required_level = int(self.goal_requirements['document_level'])
                if self.player.document_level < required_level:
                    print(f"AI ({self.player.name}): Buying document level for goal.")
                    return 'buy_document_level'

        # If personal items hand is full, must draw green
        if len(self.player.personal_items_hand) >= self.player.max_personal_items_hand:
            print(f"AI ({self.player.name}): Personal items hand is full, must draw green card.")
            return 'draw_green'

        # If personal items hand is empty, prefer to get one
        if len(self.player.personal_items_hand) == 0:
            print(f"AI ({self.player.name}): No personal items, getting one.")
            return 'draw_personal_item'

        # If goal is money-based and low on money, personal items might help
        if self.player.win_condition and 'money' in self.goal_requirements:
            if int(self.goal_requirements['money']) > self.player.money:
                if len(self.player.personal_items_hand) < 3:
                    print(f"AI ({self.player.name}): Goal is financial, getting personal item for help.")
                    return 'draw_personal_item'

        # Default to drawing a green card to advance game state
        print(f"AI ({self.player.name}): Decided to draw a green card to advance game state.")
        return 'draw_green'
        
    def decide_green_card_use(self, card):
        """Decide whether to exchange a document card or play its event effect."""
        # If no goal - always aim for documents to quickly reach goal selection level
        if not self.player.win_condition:
            if card.get('category') == 'documents':
                # Check if we can exchange documents (need 2 cards + 1 money)
                if (self.player.document_cards >= 2 and 
                    self.player.money >= 1 and 
                    self.player.document_level < 5):
                    # Calculate how many levels we can get
                    potential_levels = self._calculate_potential_levels()
                    print(f"AI ({self.player.name}): No goal - exchanging documents for {potential_levels} levels.")
                    return 'exchange'
                else:
                    print(f"AI ({self.player.name}): No goal - playing event for documents.")
                    return 'event'
            else:
                print(f"AI ({self.player.name}): No goal - playing event '{card['name']}'.")
                return 'event'
        
        # If goal exists - standard logic
        is_doc_goal = 'document_level' in self.goal_requirements

        # If goal is document-related, prioritize exchanging cards to level up
        if is_doc_goal and card.get('category') == 'documents':
            # Check if we can exchange documents (need 2 cards + 1 money)
            if self.player.document_cards >= 2 and self.player.money >= 1:
                potential_levels = self._calculate_potential_levels()
                print(f"AI ({self.player.name}): Goal requires documents. Exchanging for {potential_levels} levels.")
                return 'exchange'
            else:
                print(f"AI ({self.player.name}): Goal requires documents, but not enough cards to exchange. Playing for event to get more.")
                return 'event'

        # Check if the card helps with any goal requirement via events/special effects
        if self._card_helps_goal(card):
            print(f"AI ({self.player.name}): Card '{card['name']}' helps with goal. Playing as event.")
            return 'event'

        # If the goal is financial, check if the event gives money
        if 'money' in self.goal_requirements:
            event_effects = card.get('effects', {})
            if event_effects.get('money', 0) > 0:
                print(f"AI ({self.player.name}): Goal is financial. Playing card for its event to get money.")
                return 'event'

        # Default behavior: if not a document goal and no clear financial benefit, prefer exchange if possible, else event
        if card.get('category') == 'documents':
             print(f"AI ({self.player.name}): No specific goal alignment. Defaulting to event for card '{card['name']}'.")
             return 'event'

        return 'event'
        
    def _calculate_potential_levels(self):
        """Calculate how many document levels we can get with current cards."""
        cards_available = self.player.document_cards
        current_level = int(self.player.document_level)
        levels_possible = 0
        
        while cards_available > 0:
            # Linear progression: level N requires N cards (max 6)
            required_docs = min(current_level + 1, 6)
            if cards_available >= required_docs:
                cards_available -= required_docs
                current_level += 1
                levels_possible += 1
            else:
                break
        
        return levels_possible
