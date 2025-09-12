import random
from .analytics import GameAnalytics


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
            "any_positive_effect", "close_to_win", "pre_turn_action",
            "movement", "challenge_event", "resource_gain"
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
        # Only show interactive events if there's actual interference
        
        # Ask other players for interference in turn order
        interference_applied = False
        interfering_player = None
        interference_card = None
        
        for player in self.players:
            if player == event.acting_player or player.is_eliminated:
                continue
                
            # Check if player wants to interfere
            interference = None
            if hasattr(player, 'human_controller'):
                # Human player
                interference = player.human_controller.decide_interference(event)
            else:
                # AI player
                interference = player.ai.decide_interference(event)
                
            if interference:
                card, cost_paid = interference
                if self._can_pay_cost(player, card) and cost_paid:
                    # Show interference only when it actually happens
                    print(f"\n⚡ INTERFERENCE: {player.name} plays '{card['name']}' against {event.acting_player.name}")
                    
                    self._pay_cost(player, card)
                    interference_applied = True
                    interfering_player = player
                    interference_card = card
                    event.apply_interference(card, player)
                    player.action_cards.remove(card)
                    break
                    
        # If interference was applied, check for defense
        if interference_applied and not event.is_blocked:
            defense = None
            if hasattr(event.acting_player, 'human_controller'):
                # Human player
                defense = event.acting_player.human_controller.decide_defense(event, interference_card)
            else:
                # AI player
                defense = event.acting_player.ai.decide_defense(event, interference_card)
                
            if defense:
                defense_card, cost_paid = defense
                if self._can_pay_cost(event.acting_player, defense_card) and cost_paid:
                    self._pay_cost(event.acting_player, defense_card)
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
        self.goal_requirements = self.player.win_condition.get('requires', {}) if self.player.win_condition else {}
        self.lie_probability = 0.3  # 30% chance to lie in trades
        self.trust_levels = {}  # Track trust towards other players
        self.grudges = {}  # Track grudges against players who hurt us


    def decide_use_personal_item(self, turn_context):
        """Решает, какой одноразовый предмет использовать."""
        if not self.player.personal_items_hand:
            return None
            
        # Приоритет 1: Критически низкие нервы
        if self.player.nerves <= 2:
            for item in self.player.personal_items_hand:
                if (self._item_helps_nerves(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Критически низкие нервы, использую '{item['name']}'")
                    return item
        
        # Приоритет 2: Продвижение к цели
        if self.player.win_condition:
            for item in self.player.personal_items_hand:
                if (self._item_helps_goal(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Предмет поможет цели, использую '{item['name']}'")
                    return item
        
        # Приоритет 3: Защитные предметы при низких ресурсах
        if self.player.money <= 3 or self.player.nerves <= 4:
            for item in self.player.personal_items_hand:
                if (self._is_defensive_item(item) and 
                    self.player.can_use_personal_item(item) and
                    self._can_use_item_now(item, turn_context)):
                    print(f"AI ({self.player.name}): Низкие ресурсы, использую защитный предмет '{item['name']}'")
                    return item
        
        return None
    
    def decide_use_aggressive_item(self, turn_context, other_players):
        """Решает, использовать ли агрессивный предмет против соперника."""
        if not self.player.personal_items_hand or not other_players:
            return None
            
        # Приоритет 1: Месть тем, кто обижал нас
        if hasattr(self, 'grudges') and self.grudges:
            for enemy_id, grudge_level in self.grudges.items():
                if grudge_level >= 2:  # Серьезная обида
                    target = next((p for p in other_players if p.id == enemy_id), None)
                    if target:
                        for item in self.player.personal_items_hand:
                            if (self._is_aggressive_item(item) and 
                                self.player.can_use_personal_item(item) and
                                self._should_target_enemy(item, target)):
                                print(f"AI ({self.player.name}): МЕСТЬ! Использую '{item['name']}' против {target.name} (обида: {grudge_level})")
                                return ('aggressive_item', item, target)
        
        # Приоритет 2: Атака лидера, если мы отстаем
        leader = max(other_players, key=lambda p: self._estimate_player_progress(p))
        if (self._estimate_player_progress(leader) > self._estimate_player_progress(self.player) + 3):
            for item in self.player.personal_items_hand:
                if (self._is_aggressive_item(item) and 
                    self.player.can_use_personal_item(item) and
                    self._should_target_leader(item, leader)):
                    print(f"AI ({self.player.name}): Атакую лидера {leader.name} предметом '{item['name']}'")
                    return ('aggressive_item', item, leader)
        
        # Приоритет 3: Превентивная атака на близкого к победе
        for player in other_players:
            if self._is_close_to_winning_estimate(player):
                for item in self.player.personal_items_hand:
                    if (self._is_aggressive_item(item) and 
                        self.player.can_use_personal_item(item)):
                        print(f"AI ({self.player.name}): Превентивная атака! {player.name} близок к победе, использую '{item['name']}'")
                        return ('aggressive_item', item, player)
        
        return None

    def decide_play_action_card(self, turn_context):
        """Decides which action card(s) to play from hand, if any, based on goal and current status."""
        cards_to_play = []
        
        # Сначала проверяем одноразовые предметы
        personal_item = self.decide_use_personal_item(turn_context)
        if personal_item:
            return ('personal_item', personal_item)
        
        # Проверяем агрессивные предметы против соперников
        # (Пока не реализуем в начале хода, только как реакции)
        
        # Priority 1: Manage low nerves (can play multiple nerve cards)
        if self.player.nerves < self.nerve_threshold:
            for card in self.player.action_cards:
                if card.get('effects', {}).get('nerves', 0) > 0 and self._can_play_now(card, turn_context):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Nerves are low ({self.player.nerves}), playing '{card['name']}' to restore them.")
                    # If nerves are very low, play multiple cards
                    if self.player.nerves < 2 and len(cards_to_play) < 2:
                        continue
                    else:
                        break

        # Priority 2: Play cards that directly advance the win condition (if goal is chosen)
        if self.player.win_condition and not cards_to_play:
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and self._card_helps_goal(card):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Playing '{card['name']}' to advance win condition '{self.player.win_condition['key']}'.")
                    break
        elif not self.player.win_condition and not cards_to_play:
            # Без цели фокусируемся на документах для быстрого достижения уровня выбора цели
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and card.get('effects', {}).get('documents_cards', 0) > 0:
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Нет цели - накапливаю документы, играю '{card['name']}'.")
                    break

        # Priority 3: Play utility cards that provide general benefits
        if not cards_to_play:
            for card in self.player.action_cards:
                if self._can_play_now(card, turn_context) and self._is_utility_card(card):
                    cards_to_play.append(card)
                    print(f"AI ({self.player.name}): Playing utility card '{card['name']}'.")
                    break

        return cards_to_play if cards_to_play else None
    
    def _item_helps_nerves(self, item):
        """Проверяет, помогает ли предмет с нервами."""
        effects = item.get('effects', {})
        profile_effects = item.get('profile_modifiers', {}).get(self.player.id, {})
        return (effects.get('nerves', 0) > 0 or 
                profile_effects.get('nerves', 0) > 0)
    
    def _item_helps_goal(self, item):
        """Проверяет, помогает ли предмет достижению цели."""
        if not self.player.win_condition:
            return False
            
        effects = item.get('effects', {})
        profile_effects = item.get('profile_modifiers', {}).get(self.player.id, {})
        
        requirements = self.goal_requirements
        
        # Проверяем каждое требование цели
        for req, target_value in requirements.items():
            current_value = getattr(self.player, req, 0)
            if isinstance(current_value, str):
                continue
                
            if current_value < target_value:
                # Нужно улучшить этот параметр
                item_bonus = effects.get(req, 0) + profile_effects.get(req, 0)
                if item_bonus > 0:
                    return True
        
        return False
    
    def _is_defensive_item(self, item):
        """Проверяет, является ли предмет защитным."""
        effects = item.get('effects', {})
        special_effects = item.get('special_effects', [])
        
        # Защитные эффекты
        defensive_keywords = ['immunity', 'protection', 'shield', 'block', 'prevent']
        for keyword in defensive_keywords:
            if keyword in str(special_effects).lower():
                return True
        
        # Предметы, которые дают стабильность
        return (effects.get('nerves', 0) >= 2 or 
                effects.get('money', 0) >= 3)
    
    def _can_use_item_now(self, item, turn_context):
        """Проверяет, можно ли использовать предмет сейчас."""
        when_to_play = item.get('when_to_play', 'anytime')
        return when_to_play == 'anytime' or when_to_play == turn_context
    
    def _is_aggressive_item(self, item):
        """Проверяет, является ли предмет агрессивным."""
        item_type = item.get('type', '')
        target_type = item.get('target', '')
        special_effects = item.get('special_effects', [])
        
        # Агрессивные типы
        if item_type in ['attack', 'sabotage', 'interference']:
            return True
            
        # Предметы с целью на других игроков
        if target_type in ['other_player', 'enemy', 'target_player']:
            return True
            
        # Специальные агрессивные эффекты
        aggressive_effects = ['challenge_target', 'reduce_resources', 'block_action', 'steal_effect']
        return any(effect in special_effects for effect in aggressive_effects)
    
    def _should_target_enemy(self, item, target):
        """Определяет, стоит ли использовать предмет против конкретного врага."""
        # Проверяем, подходит ли цель под условия предмета
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
        """Определяет, стоит ли атаковать лидера этим предметом."""
        # Лидеров стоит атаковать предметами, которые замедляют прогресс
        effects = item.get('target_effects', {})
        special_effects = item.get('special_effects', [])
        
        # Предметы, которые хороши против лидеров
        anti_leader_effects = ['reduce_money', 'reduce_documents', 'force_challenge', 'block_progress']
        return (any(effect in effects for effect in ['money', 'documents_cards', 'nerves']) or
                any(effect in special_effects for effect in anti_leader_effects))
    
    def _estimate_player_progress(self, player):
        """Оценивает прогресс игрока к победе."""
        if not player.win_condition:
            # Без цели оцениваем общий прогресс
            return player.money + player.nerves + player.document_level * 3
        
        requirements = player.win_condition.get('requires', {})
        progress = 0
        
        for req, target_value in requirements.items():
            current_value = getattr(player, req, 0)
            if isinstance(current_value, (int, float)):
                progress += min(current_value / target_value, 1.0) * 10
        
        return progress
    
    def _is_close_to_winning_estimate(self, player):
        """Оценивает, близок ли игрок к победе."""
        if not player.win_condition:
            return False
            
        requirements = player.win_condition.get('requires', {})
        progress_ratio = 0
        total_requirements = len(requirements)
        
        for req, target_value in requirements.items():
            current_value = getattr(player, req, 0)
            if isinstance(current_value, (int, float)):
                progress_ratio += min(current_value / target_value, 1.0)
        
        # Близок к победе если выполнено 75%+ требований
        return (progress_ratio / total_requirements) >= 0.75
    
    def add_grudge(self, enemy_player_id, severity=1):
        """Добавляет обиду на игрока."""
        if enemy_player_id not in self.grudges:
            self.grudges[enemy_player_id] = 0
        self.grudges[enemy_player_id] += severity
        
        enemy_name = enemy_player_id  # Упрощаем пока без ссылки на игру
        print(f"💢 {self.player.name} запомнил обиду на {enemy_name} (уровень: {self.grudges[enemy_player_id]})")
    
    def reduce_grudge(self, player_id, amount=1):
        """Уменьшает обиду на игрока (например, после успешной мести)."""
        if player_id in self.grudges:
            self.grudges[player_id] = max(0, self.grudges[player_id] - amount)
            if self.grudges[player_id] == 0:
                del self.grudges[player_id]

    def _can_play_now(self, card, turn_context):
        """Checks if a card can be played in the current context."""
        when_to_play = card.get('when_to_play', 'anytime')
        return when_to_play == 'anytime' or when_to_play == turn_context
    
    def _is_utility_card(self, card):
        """Checks if a card provides general utility benefits."""
        effects = card.get('effects', {})
        # Cards that provide general benefits like money, documents, or special abilities
        return (effects.get('money', 0) > 0 or 
                effects.get('documents_cards', 0) > 0 or
                effects.get('steal_permanent_effect', False) or
                any(key.endswith('_bonus') for key in effects.keys()) or
                any(key.startswith('block_') for key in effects.keys()))

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
        """Decides whether to draw a green card or a personal item."""
        # If personal items hand is full, must draw green
        if len(self.player.personal_items_hand) >= self.player.max_personal_items_hand:
            print(f"AI ({self.player.name}): Personal items hand is full, must draw green card.")
            return 'draw_green'

        # If personal items hand is empty, prefer to get one
        if len(self.player.personal_items_hand) == 0:
            print(f"AI ({self.player.name}): No personal items, getting one.")
            return 'draw_personal_item'

        # If goal is money-based and low on money, personal items might help
        if 'money' in self.goal_requirements and int(self.goal_requirements['money']) > self.player.money:
            if len(self.player.personal_items_hand) < 3:
                print(f"AI ({self.player.name}): Goal is financial, getting personal item for help.")
                return 'draw_personal_item'

        # Default to drawing a green card to advance game state
        print(f"AI ({self.player.name}): Decided to draw a green card to advance game state.")
        return 'draw_green'


    def _calculate_potential_levels(self):
        """Рассчитывает, сколько уровней документов можно получить с текущими картами."""
        cards_available = self.player.document_cards
        current_level = int(self.player.document_level)
        levels_possible = 0
        
        while cards_available > 0:
            # Линейная прогрессия: уровень N требует N карт (максимум 6)
            required_docs = min(current_level + 1, 6)
            if cards_available >= required_docs:
                cards_available -= required_docs
                current_level += 1
                levels_possible += 1
            else:
                break
        
        return levels_possible

    def decide_green_card_use(self, card):
        """Decides whether to exchange a document card or play its event effect based on the goal."""
        # Если цели нет - всегда стремимся к документам для быстрого достижения уровня выбора
        if not self.player.win_condition:
            if card.get('category') == 'documents':
                # Проверяем, можем ли получить хотя бы один уровень (линейная прогрессия)
                required_docs_for_upgrade = min(int(self.player.document_level) + 1, 6)
                if self.player.document_cards >= required_docs_for_upgrade:
                    # Подсчитываем, сколько уровней можем получить
                    potential_levels = self._calculate_potential_levels()
                    print(f"AI ({self.player.name}): Нет цели - обмениваю документы на {potential_levels} уровней.")
                    return 'exchange'
                else:
                    print(f"AI ({self.player.name}): Нет цели - играю событие для получения документов.")
                    return 'event'
            else:
                print(f"AI ({self.player.name}): Нет цели - играю событие '{card['name']}'.")
                return 'event'
        
        # Если цель есть - стандартная логика
        is_doc_goal = 'document_level' in self.goal_requirements

        # If the goal is document-related, prioritize exchanging cards to level up.
        if is_doc_goal and card.get('category') == 'documents':
            required_docs_for_upgrade = min(int(self.player.document_level) + 1, 6)
            if self.player.document_cards >= required_docs_for_upgrade:
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
            
        # Check goal-specific needs (only if goal is chosen)
        if self.player.win_condition:
            goal_key = self.player.win_condition['key']
            requires = self.player.win_condition.get('requires', {})
        else:
            # Без цели - фокус на документах
            if self.player.document_cards == 1:  # Близко к обмену
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
            # Без цели оставляем только базовую сумму для выживания
            extra_money = self.player.money - 10  # Минимум для выживания
            
        # Rich players should be more generous with money
        if self.player.money > 100:
            extra_money = self.player.money - goal_money if self.player.win_condition else self.player.money - 20
            if extra_money > 0:
                items["money"] = min(8, extra_money)  # Can offer more money
        elif extra_money > 0:
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
                if self.player.win_condition:
                    goal_money = self.player.win_condition.get('requires', {}).get('money', 0)
                    if self.player.money < goal_money:
                        value_to_us += amount
                else:
                    # Без цели деньги всегда ценны для выживания
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
        if not player.win_condition:
            return False  # Нет цели - не может быть близко к победе
        goal = player.win_condition
        requires = goal.get('requires', {})
        
        # Check if player is close to any goal requirement
        close_factors = 0
        total_factors = 0
        
        if 'money' in requires:
            money_progress = player.money / int(requires['money'])
            if money_progress >= 0.8:  # 80% of required money
                close_factors += 1
            total_factors += 1
            
        if 'document_level' in requires:
            doc_progress = int(player.document_level) / int(requires['document_level'])
            if doc_progress >= 0.8:  # 80% of required document level
                close_factors += 1
            total_factors += 1
            
        if 'language_level' in requires:
            lang_progress = player.language_level / int(requires['language_level'])
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
        if not self.player.win_condition:
            # Без цели - считаем что дела идут хорошо, если много документов/денег/нервов
            return (self.player.money > 20 and self.player.nerves > 10 and self.player.document_level >= 1)
        goal = self.player.win_condition
        requires = goal.get('requires', {})
        
        progress_factors = 0
        total_factors = 0
        
        if 'money' in requires:
            progress_factors += min(1.0, self.player.money / int(requires['money']))
            total_factors += 1
            
        if 'document_level' in requires:
            progress_factors += min(1.0, int(self.player.document_level) / int(requires['document_level']))
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
        self.profile = profile['id']  # For group targeting
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
        self._document_level = int(0)
        self.action_cards = []
        self.max_action_cards = game_constants['game_constants']['max_action_cards']
        self.personal_items_hand = []  # Personal items in hand (max 5)
        self.max_personal_items_hand = game_constants['game_constants']['max_personal_items_hand']
        self.document_cards = 1  # Number of collected document cards (balanced start)
        self.housing_search = False  # Whether player is actively searching for housing

        self.win_condition = win_condition
        self.goal_chosen = False  # Флаг выбранной цели
        self.is_eliminated = False
        self.eliminated_on_turn = None
        self.ai = AI(self, config)
        
        # Система временных бонусов и иммунитетов
        self.temporary_bonuses = {
            'social': 0, 'housing': 0, 'work': 0, 'language': 0,
            'movement': 0, 'comfort': 0, 'health': 0, 'shopping': 0,
            'communication': 0, 'confidence': 0, 'cultural': 0, 'durability': 0,
            'eco': 0, 'emergency': 0, 'energy': 0, 'entertainment': 0,
            'humor': 0, 'hygiene': 0, 'mobility': 0, 'reliability': 0,
            'safety': 0, 'self_sufficiency': 0, 'storage': 0, 'style': 0,
            'utility': 0, 'vacation': 0, 'sports': 0
        }
        self.immunities = set()  # {'health_penalty', 'heat_penalty', etc.}
        self.special_abilities = set()  # {'documents_fast_track', 'language_dice_advantage', etc.}

    @property
    def document_level(self):
        """Always return document_level as int"""
        return int(self._document_level)
    
    @document_level.setter
    def document_level(self, value):
        """Always store document_level as int"""
        self._document_level = int(value)

    def __repr__(self):
        goal_text = self.win_condition['key'] if self.win_condition else "Не выбрана"
        return (f"Player(Name: {self.name}, Money: {self.money}, Nerves: {self.nerves}, "
                f"Lang Lvl: {self.language_level}, Housing: {self.housing} (Lvl {self.housing_level}), "
                f"Docs Lvl: {self.document_level}, Doc Cards: {self.document_cards}, "
                f"Personal Items: {len(self.personal_items_hand)}/{self.max_personal_items_hand}, "
                f"Goal: {goal_text})")

    def add_action_card(self, card):
        if len(self.action_cards) < self.max_action_cards:
            self.action_cards.append(card)
            print(f"{self.name} received action card: {card['name']}.")
        else:
            print(f"{self.name}'s action card hand is full, cannot draw more.")
    
    def add_personal_items(self, count, game=None):
        """Добавляет одноразовые шмотки в руку игрока."""
        if count <= 0:
            return
            
        items_to_add = min(count, self.max_personal_items_hand - len(self.personal_items_hand))
        if items_to_add > 0:
            for _ in range(items_to_add):
                if game and 'item' in game.decks:
                    # Берем настоящий предмет из колоды
                    item = game.decks['item'].draw()
                    if item:
                        self.personal_items_hand.append(item)
                        print(f"{self.name} получил '{item['name']}'")
                    else:
                        # Если колода пуста, добавляем заглушку
                        self.personal_items_hand.append({"name": "Personal Item", "type": "utility"})
                        print(f"{self.name} получил базовый предмет (колода пуста)")
                else:
                    # Фоллбэк для случаев без доступа к игре
                    self.personal_items_hand.append({"name": "Personal Item", "type": "utility"})
            
            if not game:
                print(f"{self.name} получил {items_to_add} одноразовых предметов.")
        
        if count > items_to_add:
            excess = count - items_to_add
            print(f"{self.name} не смог взять {excess} предметов - рука полная!")
    
    def check_personal_items_hand_limit(self):
        """Проверяет лимит руки и возвращает количество карт для сброса."""
        excess = len(self.personal_items_hand) - self.max_personal_items_hand
        return max(0, excess)
    
    def discard_personal_items(self, count):
        """Сбрасывает указанное количество одноразовых предметов."""
        if count <= 0:
            return
        
        actual_discard = min(count, len(self.personal_items_hand))
        for _ in range(actual_discard):
            discarded = self.personal_items_hand.pop()
            print(f"{self.name} сбросил: {discarded.get('name', 'Personal Item')}")
        
        return actual_discard
    
    def force_discard_excess_personal_items(self):
        """Принудительно сбрасывает лишние одноразовые предметы."""
        excess = self.check_personal_items_hand_limit()
        if excess > 0:
            print(f"⚠️  {self.name} должен сбросить {excess} одноразовых предметов (лимит: {self.max_personal_items_hand})")
            self.discard_personal_items(excess)
            return True
        return False
    
    def can_use_personal_item(self, item):
        """Проверяет, может ли игрок использовать предмет."""
        if not item:
            return False
            
        # Проверяем стоимость
        cost = item.get('cost', {})
        for resource, amount in cost.items():
            if resource == 'money' and self.money < amount:
                return False
            elif resource == 'nerves' and self.nerves < amount:
                return False
            elif resource == 'document_cards' and self.document_cards < amount:
                return False
        
        return True
    
    def use_personal_item(self, item, target_player=None):
        """Использует одноразовый предмет."""
        if not self.can_use_personal_item(item):
            return False
            
        if item not in self.personal_items_hand:
            return False
        
        print(f"📦 {self.name} использует '{item['name']}'")
        
        # Платим стоимость
        cost = item.get('cost', {})
        for resource, amount in cost.items():
            if resource == 'money':
                self.money = max(0, self.money - amount)
            elif resource == 'nerves':
                self.nerves = max(1, self.nerves - amount)
            elif resource == 'document_cards':
                self.document_cards = max(0, self.document_cards - amount)
        
        # Убираем предмет из руки
        self.personal_items_hand.remove(item)
        
        return True
    
    def add_temporary_bonus(self, bonus_type, amount):
        """Добавляет временный бонус к игроку."""
        if bonus_type in self.temporary_bonuses:
            self.temporary_bonuses[bonus_type] += amount
            print(f"System: {self.name} gained {amount} {bonus_type} bonus (total: {self.temporary_bonuses[bonus_type]})")
    
    def add_immunity(self, immunity_type):
        """Добавляет иммунитет к определенному типу штрафа."""
        self.immunities.add(immunity_type)
        print(f"System: {self.name} gained immunity to {immunity_type}")
    
    def add_special_ability(self, ability_type):
        """Добавляет специальную способность."""
        self.special_abilities.add(ability_type)
        print(f"System: {self.name} gained special ability: {ability_type}")
    
    def has_immunity(self, immunity_type):
        """Проверяет, есть ли у игрока иммунитет к определенному типу штрафа."""
        return immunity_type in self.immunities
    
    def has_special_ability(self, ability_type):
        """Проверяет, есть ли у игрока специальная способность."""
        return ability_type in self.special_abilities
    
    def get_bonus(self, bonus_type):
        """Возвращает текущий бонус определенного типа."""
        return self.temporary_bonuses.get(bonus_type, 0)
    
    def clear_temporary_effects(self):
        """Очищает все временные эффекты в конце хода."""
        for bonus_type in self.temporary_bonuses:
            if self.temporary_bonuses[bonus_type] > 0:
                print(f"System: {self.name} lost {self.temporary_bonuses[bonus_type]} {bonus_type} bonus")
                self.temporary_bonuses[bonus_type] = 0
        # Иммунитеты и специальные способности остаются до конца игры


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
        self.interaction_manager = InteractionManager(self.players)
        self.end_reason = None
        self.analytics = GameAnalytics()
        self.analytics.start_game(self.players)

    def setup_decks(self):
        self.decks = {
            'action': Deck(self.game_data['action_cards']['additional_action_cards']),
            'green': Deck(self.game_data['green_cards']['green_cards']),
            'red': Deck(self.game_data['health_cards']['health_cards'] + self.game_data['housing_cards']['housing_cards']),
            'white': Deck(self.game_data['white_cards']['random_events']) if 'white_cards' in self.game_data else Deck([]),
        }
        
        # Добавляем колоду предметов
        if 'personal_items' in self.game_data:
            all_items = self.game_data['personal_items']['personal_items'].copy()
            # Добавляем карты для кражи эффектов
            if 'steal_effect_cards' in self.game_data['personal_items']:
                all_items.extend(self.game_data['personal_items']['steal_effect_cards'])
            self.decks['item'] = Deck(all_items)

    def setup_players(self):
        self.players = []
        num_players = self.config['game_parameters']['number_of_players']
        profiles = random.sample(self.config['character_profiles'], num_players)
        # win_conditions = list(self.config['win_conditions'].items())  # Убираем раннее назначение

        for i in range(num_players):
            profile = profiles[i]
            # Игроки начинают БЕЗ цели - выберут на 5-м уровне документов
            player_win_condition = None  
            player = Player(profile, player_win_condition, self.config, self.game_data['game_constants'])

            # Give starting item cards (3 per player) - заменяем старую систему action_cards
            if 'item' in self.decks:
                for _ in range(3):
                    item_card = self.decks['item'].draw()
                    if item_card:
                        player.add_action_card(item_card)

            self.players.append(player)
        
        # Initialize trade manager and interaction manager after players are created
        self.trade_manager = TradeManager(self.players)
        self.interaction_manager = InteractionManager(self.players)

    def run(self):
        """Main loop for a single game, handling turns until a winner is found or a limit is reached."""
        num_players = self.config['game_parameters']['number_of_players']
        while not self.game_over:
            self.turn += 1

            # Lap completion for balanced progression (every 4-5 turns for slower game)
            lap_frequency = max(4, min(6, self.board.size // (num_players * 2))) if num_players > 0 else 5
            if self.turn > 1 and self.turn % lap_frequency == 0:
                print(f"System: Turn {self.turn} - Lap completed! (frequency: every {lap_frequency} turns)")
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
            # 15 turns per player for balanced gameplay
            max_turns = len(self.players) * 15
            
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
                
                # Auto-gain documents each lap for consistent progression
                player.document_cards += 1
                print(f"System: {player.name} automatically gains 1 document card (total: {player.document_cards})")
                

    def take_turn(self, player):
        """Manages the sequence of actions for a single player's turn."""
        print(f"\n--- Turn {self.turn}, Player: {player.name} ---")
        print(f"State before turn: {player}")
        
        # Analytics: Track turn start
        self.analytics.track_turn_start(player, self.turn)

        # 1. AI decides to play pre-turn action card(s) or personal items
        decision = player.ai.decide_play_action_card('start_of_turn')
        if decision:
            if isinstance(decision, tuple) and decision[0] == 'personal_item':
                # Используем одноразовый предмет
                _, item_to_use = decision
                if player.use_personal_item(item_to_use):
                    self.apply_personal_item_effects(player, item_to_use)
            else:
                # Обрабатываем карты действий
                cards_to_play = decision
                if not isinstance(cards_to_play, list):
                    cards_to_play = [cards_to_play]
                
                for card_to_play in cards_to_play:
                    # INTERVENTION POINT: Pre-turn action
                    event = InteractiveEvent(
                        action_type="pre_turn_action",
                        acting_player=player,
                        effects=card_to_play.get('effects', {}),
                        description=f"{player.name} plays '{card_to_play['name']}' before turn"
                    )
                    event = self.interaction_manager.announce_event(event)
                    
                    if not event.is_blocked:
                        self.apply_card_effect(player, card_to_play, 'event')
                    player.action_cards.remove(card_to_play)
                    self.decks['action'].discard(card_to_play)

        # 2. Roll dice and move
        roll = random.randint(1, 6)
        
        # INTERVENTION POINT: Movement modification
        movement_event = InteractiveEvent(
            action_type="movement",
            acting_player=player,
            effects={"movement": roll},
            description=f"{player.name} rolled {roll} and will move to position {(player.position + roll) % self.board.size}"
        )
        movement_event = self.interaction_manager.announce_event(movement_event)
        
        if not movement_event.is_blocked:
            final_roll = movement_event.effects.get("movement", roll)
            player.position = (player.position + final_roll) % self.board.size
        else:
            print(f"🚫 {player.name}'s movement was blocked!")

        # Analytics: Track cell visit
        cell_type = self.board.get_cell_type(player.position)
        self.analytics.track_cell_visit(player, player.position, cell_type)

        # 3. Trade phase (before cell effect)
        self.handle_trade_phase(player)

        # 4. Handle cell effect

        if cell_type == 'green':
            decision = player.ai.decide_on_green_space()
            if decision == 'draw_green':
                card = self.decks['green'].draw()
                if card:
                    use_decision = 'event' # Default for non-exchange cards
                    if card.get('exchange_instruction'):
                        use_decision = player.ai.decide_green_card_use(card)
                        
                        # INTERVENTION POINT: Document exchange attempt
                        if use_decision == 'exchange':
                            exchange_event = InteractiveEvent(
                                action_type="document_exchange",
                                acting_player=player,
                                effects={"document_level": 1},
                                description=f"{player.name} attempts document exchange with '{card['name']}'"
                            )
                            exchange_event = self.interaction_manager.announce_event(exchange_event)
                            
                            if not exchange_event.is_blocked:
                                self.apply_card_effect(player, card, use_decision)
                            else:
                                print(f"🚫 {player.name}'s document exchange was blocked!")
                        else:
                            self.apply_card_effect(player, card, use_decision)
                    else:
                        self.apply_card_effect(player, card, use_decision)
            elif decision == 'draw_personal_item':
                # Дать игроку одноразовую шмотку
                player.add_personal_items(1, self)
                print(f"{player.name} получил одноразовую шмотку вместо зелёной карты.")

        elif cell_type in ['red', 'white']:
            card = self.decks[cell_type].draw()
            if card:
                # INTERVENTION POINT: Challenge/Event card
                challenge_event = InteractiveEvent(
                    action_type="challenge_event",
                    acting_player=player,
                    effects=card.get('effects', {}),
                    description=f"{player.name} faces '{card['name']}' ({cell_type} card)"
                )
                challenge_event = self.interaction_manager.announce_event(challenge_event)
                
                if not challenge_event.is_blocked:
                    # Apply potentially modified effects
                    modified_card = card.copy()
                    modified_card['effects'] = challenge_event.effects
                    self.apply_card_effect(player, modified_card, 'event')
                else:
                    print(f"🚫 {player.name}'s challenge was blocked!")

        # INTERVENTION POINT: Money/resource gains
        if hasattr(player, '_temp_money_gain') and player._temp_money_gain > 0:
            money_event = InteractiveEvent(
                action_type="money_gain",
                acting_player=player,
                effects={"money": player._temp_money_gain},
                description=f"{player.name} gains {player._temp_money_gain} money"
            )
            money_event = self.interaction_manager.announce_event(money_event)
            
            if not money_event.is_blocked:
                final_money = money_event.effects.get("money", player._temp_money_gain)
                player.money += final_money
            else:
                print(f"🚫 {player.name}'s money gain was blocked!")
            delattr(player, '_temp_money_gain')

        # 5. Check if player reached level 5 documents and needs to choose goal
        self.check_goal_selection(player)
        
        # INTERVENTION POINT: Close to winning
        if self.is_close_to_winning(player):
            win_event = InteractiveEvent(
                action_type="close_to_win",
                acting_player=player,
                description=f"{player.name} is close to winning!"
            )
            self.interaction_manager.announce_event(win_event)
        
        # 6. Check for win/loss conditions
        self.check_win_condition(player)
        if not self.game_over:
            self.check_elimination(player)

        # 7. Check and enforce personal items hand limit
        if player.force_discard_excess_personal_items():
            print(f"📦 {player.name} now has {len(player.personal_items_hand)}/{player.max_personal_items_hand} personal items")

        print(f"State after turn:  {player}")
        
        # Analytics: Track goal progress
        if hasattr(player, 'win_condition') and player.win_condition:
            goal_requirements = player.win_condition['requires']
            current_progress = {
                'money': player.money,
                'document_level': int(player.document_level),
                'language_level': player.language_level,
                'housing_level': getattr(player, 'housing_level', 1),
                'housing_type': getattr(player, 'housing', 'room'),
                'nerves': player.nerves
            }
            self.analytics.track_goal_progress(player, goal_requirements, current_progress)
    
    def apply_personal_item_effects(self, player, item):
        """Применяет эффекты одноразового предмета к игроку."""
        # Базовые эффекты
        effects = item.get('effects', {})
        
        # Эффекты для конкретного персонажа
        profile_effects = item.get('profile_modifiers', {}).get(player.id, {})
        
        # Объединяем эффекты
        combined_effects = effects.copy()
        for key, value in profile_effects.items():
            combined_effects[key] = combined_effects.get(key, 0) + value
        
        print(f"  ✨ Эффекты '{item['name']}':")
        for effect, value in combined_effects.items():
            if effect == 'nerves':
                old_nerves = player.nerves
                player.nerves = max(1, min(10, player.nerves + value))
                print(f"    🧠 Нервы: {old_nerves} → {player.nerves} ({value:+})")
            elif effect == 'money':
                old_money = player.money
                player.money = max(0, player.money + value)
                print(f"    💰 Деньги: {old_money} → {player.money} ({value:+})")
            elif effect == 'documents_cards':
                old_docs = player.document_cards
                player.document_cards = max(0, player.document_cards + value)
                print(f"    📄 Карты документов: {old_docs} → {player.document_cards} ({value:+})")
            elif effect == 'language_level':
                if value > 0:
                    old_lang = player.language_level
                    player.language_level = min(3, player.language_level + value)
                    print(f"    🗣️ Язык: {old_lang} → {player.language_level} ({value:+})")
            elif effect == 'housing_upgrade' and value:
                self.handle_housing_upgrade(player)
        
        # Специальные эффекты
        special_effects = item.get('special_effects', [])
        if special_effects:
            print(f"    🌟 Специальные эффекты: {', '.join(special_effects)}")
            for special_effect in special_effects:
                self.handle_special_item_effect(player, special_effect)
    
    def apply_aggressive_item_effects(self, attacker, target, item):
        """Применяет эффекты агрессивного предмета к цели."""
        print(f"⚔️ {attacker.name} использует '{item['name']}' против {target.name}!")
        
        # Добавляем обиду цели на атакующего
        target.ai.add_grudge(attacker.id, 2)
        
        # Проверяем тип агрессивного эффекта
        special_effects = item.get('special_effects', [])
        target_effects = item.get('target_effects', {})
        
        if 'challenge_target' in special_effects:
            # Принудительный челлендж для цели
            self.force_challenge_on_target(target, item)
        
        if 'reduce_resources' in special_effects:
            # Прямое отнимание ресурсов
            for resource, amount in target_effects.items():
                if resource == 'money':
                    old_money = target.money
                    target.money = max(0, target.money - amount)
                    print(f"  💸 {target.name}: деньги {old_money} → {target.money} (-{amount})")
                elif resource == 'nerves':
                    old_nerves = target.nerves
                    target.nerves = max(1, target.nerves - amount)
                    print(f"  😰 {target.name}: нервы {old_nerves} → {target.nerves} (-{amount})")
                elif resource == 'documents_cards':
                    old_docs = target.document_cards
                    target.document_cards = max(0, target.document_cards - amount)
                    print(f"  📄 {target.name}: карты документов {old_docs} → {target.document_cards} (-{amount})")
        
        if 'steal_effect' in special_effects:
            # Кража ресурсов в пользу атакующего
            self.steal_resources_from_target(attacker, target, target_effects)
    
    def force_challenge_on_target(self, target, item):
        """Принуждает цель пройти специальный челлендж."""
        challenge_name = item.get('challenge_name', f"Последствия '{item['name']}'")
        print(f"🎯 {target.name} должен пройти челлендж: {challenge_name}")
        
        # Создаем специальный челлендж
        roll = random.randint(1, 6)
        difficulty = item.get('challenge_difficulty', 4)
        
        print(f"  🎲 {target.name} бросает кубик: {roll} (нужно {difficulty}+)")
        
        if roll >= difficulty:
            # Успех - минимальные последствия
            success_effects = item.get('challenge_success', {'documents_cards': 1})
            print(f"  ✅ Успех! {target.name} избежал серьезных последствий")
            for effect, value in success_effects.items():
                if effect == 'documents_cards':
                    target.document_cards += value
                    print(f"    📄 +{value} карта документов (доказал невиновность)")
        else:
            # Провал - серьезные последствия  
            fail_effects = item.get('challenge_fail', {'money': -5, 'nerves': -2})
            print(f"  ❌ Провал! {target.name} получает серьезные последствия")
            for effect, value in fail_effects.items():
                if effect == 'money':
                    old_money = target.money
                    target.money = max(0, target.money + value)  # value уже негативное
                    print(f"    💸 Штраф: деньги {old_money} → {target.money} ({value})")
                elif effect == 'nerves':
                    old_nerves = target.nerves
                    target.nerves = max(1, target.nerves + value)  # value уже негативное
                    print(f"    😰 Стресс: нервы {old_nerves} → {target.nerves} ({value})")
    
    def steal_resources_from_target(self, attacker, target, steal_effects):
        """Кража ресурсов от цели в пользу атакующего."""
        print(f"  🎭 {attacker.name} крадет ресурсы у {target.name}:")
        
        for resource, amount in steal_effects.items():
            if resource == 'money':
                stolen = min(amount, target.money)
                target.money -= stolen
                attacker.money += stolen
                print(f"    💰 Украдено денег: {stolen}")
            elif resource == 'documents_cards':
                stolen = min(amount, target.document_cards)
                target.document_cards -= stolen
                attacker.document_cards += stolen
                print(f"    📄 Украдено карт документов: {stolen}")
    
    def handle_special_item_effect(self, player, effect):
        """Обрабатывает специальные эффекты предметов."""
        if effect == 'immunity_stress':
            player.add_immunity('stress_penalty')
        elif effect == 'immunity_cold':
            player.add_immunity('cold_penalty')
        elif effect == 'immunity_heat':
            player.add_immunity('heat_penalty')
        elif effect == 'document_boost':
            player.add_special_ability('documents_fast_track')
        elif effect == 'language_boost':
            player.add_special_ability('language_dice_advantage')
        # Добавить больше специальных эффектов по мере необходимости
    
    def _determine_card_type(self, card):
        """Determine the type of card for analytics"""
        card_id = card.get('id', '')
        if card_id.startswith('action_'):
            return 'action_cards'
        elif card_id.startswith('item_'):
            return 'personal_items'
        elif card_id.startswith('health_'):
            return 'health_cards'
        elif card_id.startswith('housing_'):
            return 'housing_cards'
        elif card_id.startswith('event_'):
            return 'white_cards'
        else:
            # Try to determine by category
            category = card.get('category', '')
            if category in ['health']:
                return 'health_cards'
            elif category in ['housing']:
                return 'housing_cards'
            elif category in ['food', 'social', 'technology', 'lifestyle']:
                return 'personal_items'
            else:
                return 'green_cards'
    
    def is_close_to_winning(self, player):
        """Check if player is close to winning their goal."""
        if not player.goal_chosen or not player.win_condition:
            return False
            
        requirements = player.win_condition['requires']
        
        # Check how close player is to meeting all requirements
        close_factors = 0
        total_factors = len(requirements)
        
        for req_type, req_value in requirements.items():
            if req_type == 'money' and player.money >= req_value * 0.8:
                close_factors += 1
            elif req_type == 'document_level':
                try:
                    req_value = int(req_value)  # Ensure req_value is int
                    if player.document_level >= req_value - 1:
                        close_factors += 1
                except (ValueError, TypeError) as e:
                    print(f"❌ ERROR in check_goal_progress: {e}")
                    print(f"   player.document_level = {player.document_level} (type: {type(player.document_level)})")
                    print(f"   req_value = {req_value} (type: {type(req_value)})")
            elif req_type == 'housing_level' and player.housing_level >= req_value:
                close_factors += 1
            elif req_type == 'language_level' and player.language_level >= req_value:
                close_factors += 1
                
        # Player is "close" if they meet 80% of requirements
        return close_factors / total_factors >= 0.8
    
    def is_global_event_card(self, card):
        """Определяет, является ли карта глобальным событием"""
        # Карты с conditions (условиями для групп игроков) - это события для всех
        if 'conditions' in card and 'character_id' in card.get('conditions', {}):
            return True
        
        # Карты с типом instant И без cost - это события для всех
        if card.get('type') == 'instant' and 'cost' not in card:
            return True
        
        # ВСЕ остальные карты - это личные предметы (включая карты с cost, utility, interference и т.д.)
        return False
    
    def apply_global_event(self, card):
        """Применяет событие ко всем игрокам"""
        print(f"System: Global event '{card['name']}' affects all players")
        
        # Применяем эффект ко всем игрокам
        for target_player in self.players:
            if not target_player.is_eliminated:
                # Проверяем условия для конкретного игрока
                if 'conditions' in card:
                    conditions = card['conditions']
                    if 'character_id' in conditions:
                        if target_player.profile not in conditions['character_id']:
                            continue  # Этот игрок не подходит под условия
                
                # Применяем эффект к игроку
                self.apply_card_effect(target_player, card, 'event')
    
    def check_goal_selection(self, player):
        """Check if player needs to select a goal when reaching document level 5."""
        try:
            if not player.goal_chosen and player.document_level >= 5:  # Выбор цели после достижения 5-го уровня документов
                # Выбираем случайную цель
                win_conditions = list(self.config['win_conditions'].items())
                win_key, win_data = random.choice(win_conditions)
                player.win_condition = {"key": win_key, **win_data}
                player.goal_chosen = True
                
                # Обновляем AI с новой целью
                player.ai.goal_requirements = player.win_condition.get('requires', {})
                
                print(f"🎯 {player.name} достиг 5-го уровня документов и выбрал цель: {win_key}!")
        except (ValueError, TypeError) as e:
            print(f"❌ ERROR in check_goal_selection: {e}")
            print(f"   player.document_level = {player.document_level} (type: {type(player.document_level)})")
    
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
        # Analytics: Track card played (if not global event)
        if decision != 'global_event' and player is not None:
            card_type = self._determine_card_type(card)
            self.analytics.track_card_played(card, card_type, player)
        
        # 0. Handle global events (when player is None)
        if decision == 'global_event':
            self.apply_global_event(card)
            return
            
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
            
        # Document exchange with dice roll (2+ for success) and money cost
        if player.document_cards >= 2 and player.money >= 1:
            roll = random.randint(1, 6)
            print(f"System: {player.name} attempts document exchange with roll: {roll}")
            
            if roll >= 2:  # Success (simplified from 3+ to 2+)
                player.document_level = player.document_level + 1
                player.document_cards -= 2
                player.money -= 1  # Cost 1 money per exchange
                print(f"System: {player.name} successfully exchanged documents! New level: {player.document_level} (cost: 1 money)")
            else:  # Failure
                player.document_cards -= 1
                player.money -= 1  # Still costs money even on failure
                print(f"System: {player.name} failed document exchange. Lost 1 document card and 1 money.")
        else:
            if player.document_cards < 2:
                print(f"System: {player.name} doesn't have enough document cards (need 2, has {player.document_cards})")
            if player.money < 1:
                print(f"System: {player.name} doesn't have enough money for document exchange (need 1, has {player.money})")
            return # Exchange action is complete

        # 2. Check conditions for event/challenge
        if 'conditions' in card and not self.check_conditions(player, card['conditions']):
            return

        # 3. Handle dice challenges for event
        if 'challenge' in card:
            self.handle_dice_challenge(player, card['challenge'])
            return

        # 4. Handle special effects (like global document level penalties)
        if 'special_effects' in card:
            self.handle_special_effects(card['special_effects'])
            # Special effects may affect multiple players globally, so continue with regular effects too
        
        # 5. Handle group-targeted events
        if 'target_groups' in card:
            if player.profile not in card['target_groups']:
                print(f"System: {card['name']} doesn't affect {player.name} ({player.profile})")
                return
            
            # Apply individual modifiers if exists
            if 'individual_modifiers' in card and player.profile in card['individual_modifiers']:
                modifiers = card['individual_modifiers'][player.profile]
                effects = chosen_effect or card.get('effects', {}).copy()
                # Override with individual modifiers
                for key, value in modifiers.items():
                    effects[key] = value
                print(f"System: Applied individual modifier for {player.profile}: {modifiers}")
            else:
                effects = chosen_effect or card.get('effects', {})
        else:
            # 6. Apply direct effects for event
            effects = chosen_effect or card.get('effects', {})
        
        # 7. Apply profile_modifiers if this is an item card
        if 'profile_modifiers' in card and player.profile in card['profile_modifiers']:
            profile_modifiers = card['profile_modifiers'][player.profile]
            print(f"System: Applying profile modifiers for {player.profile}: {profile_modifiers}")
            # Override effects with profile-specific modifiers
            for key, value in profile_modifiers.items():
                if key in effects:
                    effects[key] = value
                else:
                    effects[key] = value
            
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
            elif key == 'personal_items':
                player.add_personal_items(value, self)
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
                    player.document_level = player.document_level + 1
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
            
            # === НОВЫЕ ЭФФЕКТЫ: БОНУСЫ ===
            elif key in ['social_bonus', 'housing_bonus', 'work_bonus', 'language_bonus', 
                        'movement_bonus', 'comfort_bonus', 'health_bonus', 'shopping_bonus',
                        'communication_bonus', 'confidence_bonus', 'cultural_bonus', 'durability_bonus',
                        'eco_bonus', 'emergency_bonus', 'energy_bonus', 'entertainment_bonus',
                        'humor_bonus', 'hygiene_bonus', 'mobility_bonus', 'reliability_bonus',
                        'safety_bonus', 'self_sufficiency_bonus', 'storage_bonus', 'style_bonus',
                        'utility_bonus', 'vacation_bonus', 'sports_bonus']:
                bonus_type = key.replace('_bonus', '')
                player.add_temporary_bonus(bonus_type, value)
            
            # === НОВЫЕ ЭФФЕКТЫ: ИММУНИТЕТЫ ===
            elif key in ['block_health_penalty', 'block_heat_penalty', 'block_cold_penalty',
                        'block_rain_penalty', 'block_sun_penalty', 'block_weather_penalty',
                        'block_air_penalty', 'block_glare_penalty', 'block_hangover_penalty',
                        'block_illness_penalty', 'block_roommate_penalty', 'block_shortage_penalty',
                        'block_spoilage_penalty']:
                if value:  # Only if True
                    immunity_type = key.replace('block_', '')
                    player.add_immunity(immunity_type)
            
            # === НОВЫЕ ЭФФЕКТЫ: СПЕЦИАЛЬНЫЕ СПОСОБНОСТИ ===
            elif key in ['documents_fast_track', 'language_dice_advantage', 'reroll_language_dice',
                        'skip_document_queue', 'language_upgrade_discount', 'permanent_language_bonus',
                        'stress_immunity', 'immunity_next_housing']:
                if value:  # Only if True
                    player.add_special_ability(key)
            
            # === НОВЫЕ ЭФФЕКТЫ: ДОПОЛНИТЕЛЬНЫЕ КАРТЫ ===
            elif key == 'draw_card':
                for _ in range(value):
                    drawn_card = self.decks['action'].draw()
                    if drawn_card:
                        player.add_action_card(drawn_card)
            
            # === НОВЫЕ ЭФФЕКТЫ: ВОЗДЕЙСТВИЕ НА ДРУГИХ ИГРОКОВ ===
            elif key == 'target_money':
                # Этот эффект применяется к цели, а не к игроку
                pass  # Обрабатывается в InteractiveEvent
            
            # === НОВЫЕ ЭФФЕКТЫ: БЛОКИРОВКА ДЕЙСТВИЙ ===
            elif key == 'block_action':
                # Этот эффект применяется в InteractiveEvent
                pass
            
            # === НОВЫЕ ЭФФЕКТЫ: КРАЖА ПОСТОЯННЫХ ЭФФЕКТОВ ===
            elif key == 'steal_permanent_effect':
                if value:  # Only if True
                    self.handle_steal_permanent_effect(player, card)

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
                    if not eval(f"{int(player.document_level)} {value}"):
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

    def handle_special_effects(self, special_effects):
        """Handle special card effects that can affect multiple players globally."""
        for effect_name, effect_data in special_effects.items():
            if effect_name == "document_level_penalty":
                condition = effect_data.get("condition", "")
                effect = effect_data.get("effect", "")
                
                affected_players = []
                for player in self.players:
                    # Check condition: document_level == 5
                    try:
                        if "document_level == 5" in condition and player.document_level == 5:
                            # Apply effect: document_level -= 1
                            if "document_level -= 1" in effect:
                                old_level = player.document_level
                                player.document_level = max(0, player.document_level - 1)
                                affected_players.append(f"{player.name} ({old_level}→{player.document_level})")
                    except (ValueError, TypeError) as e:
                        print(f"❌ ERROR in handle_special_effects: {e}")
                        print(f"   player.document_level = {player.document_level} (type: {type(player.document_level)})")
                
                if affected_players:
                    print(f"System: Immigration law update! Document levels reduced: {', '.join(affected_players)}")
                else:
                    print(f"System: Immigration law update had no effect (no players with document level = 5)")

    def check_win_condition(self, player):
        """Checks if a player has met their victory condition."""
        if self.game_over:
            return
        
        # Нельзя выиграть без выбранной цели
        if not player.win_condition:
            return

        goal = player.win_condition['requires']
        met_all_conditions = True
        for key, required_value in goal.items():
            player_value = getattr(player, key, None)
            # Special handling for document_level to ensure it's always int
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
                # Ensure both values are the same type for comparison
                try:
                    if isinstance(required_value, (int, float)):
                        player_value = float(player_value)
                    elif isinstance(required_value, str):
                        player_value = str(player_value)
                    
                    if player_value < required_value:
                        met_all_conditions = False
                        break
                except (ValueError, TypeError) as e:
                    # If conversion fails, assume condition not met
                    print(f"❌ ERROR in check_win_condition: {e}")
                    print(f"   key = {key}, player_value = {player_value} (type: {type(player_value)})")
                    print(f"   required_value = {required_value} (type: {type(required_value)})")
                    met_all_conditions = False
                    break

        if met_all_conditions:
            self.game_over = True
            self.winner = player
            self.end_reason = 'win'
            
            # Analytics: End game
            self.analytics.end_game(player, self.end_reason)

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
                self.end_reason = 'elimination'
                
                # Analytics: End game
                self.analytics.end_game(self.winner, self.end_reason)
    
    def run_simulation(self, max_turns: int = 200):
        """Run a complete game simulation"""
        print(f"Starting game simulation with {len(self.players)} players")
        
        individual_turn_count = 0
        round_number = 0
        
        while not self.game_over and individual_turn_count < max_turns:
            round_number += 1
            
            # Each player takes a turn
            for player in self.players:
                if self.game_over or player.is_eliminated:
                    continue
                
                individual_turn_count += 1
                self.turn = individual_turn_count  # Track individual turns, not rounds
                
                self.take_turn(player)
                
                if self.game_over:
                    break
                    
                # Stop if we hit the turn limit
                if individual_turn_count >= max_turns:
                    break
            
            # Handle end-of-round effects (salary/rent) after all players
            if not self.game_over:
                self.handle_end_of_round()
        
        # Handle timeout
        if not self.game_over and self.turn >= max_turns:
            self.game_over = True
            self.end_reason = 'timeout'
            
            # Find player closest to winning as winner
            best_player = None
            best_progress = 0
            
            for player in self.players:
                if not player.is_eliminated and hasattr(player, 'win_condition') and player.win_condition:
                    progress = self._calculate_win_progress(player)
                    if progress > best_progress:
                        best_progress = progress
                        best_player = player
            
            self.winner = best_player
            self.analytics.end_game(self.winner, self.end_reason)
        
        print(f"Game ended after {self.turn} turns. Winner: {self.winner.name if self.winner else 'None'}")
        print(f"End reason: {self.end_reason}")
        
        return {
            'winner': self.winner,
            'turns': self.turn,
            'end_reason': self.end_reason,
            'analytics': self.analytics
        }
    
    def _calculate_win_progress(self, player) -> float:
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
                    print(f"❌ CONVERSION ERROR in _calculate_win_progress: {e}")
                    print(f"   key={key}, player_value={player_value} (type: {type(player_value)}), required_value={required_value} (type: {type(required_value)})")
                    progress += 0.0
        
        return progress / requirements if requirements > 0 else 0.0
    
    def handle_end_of_round(self):
        """Handle end-of-round effects like salary and rent"""
        for player in self.players:
            if player.is_eliminated:
                continue
                
            # Pay salary
            if hasattr(player, 'salary_type') and player.salary_type == 'dice':
                salary = random.randint(1, 6) + player.salary_base
            else:
                salary = player.salary
            
            old_money = player.money
            player.money += salary
            
            # Analytics: Track salary
            self.analytics.track_resource_change(player, 'money', salary, 'salary')
            
            # Give 1 document card each round
            player.document_cards += 1
            self.analytics.track_resource_change(player, 'document_cards', 1, 'round_income')
            
            # Pay housing costs
            housing_cost = player.housing_cost
            player.money -= housing_cost
            
            # Analytics: Track housing cost
            self.analytics.track_resource_change(player, 'money', -housing_cost, 'housing_cost')
            
            print(f"End of round: {player.name} +{salary} salary -{housing_cost} rent = {player.money - old_money} net")

    def handle_steal_permanent_effect(self, stealing_player, steal_card):
        """Handle stealing permanent effects from other players."""
        stealable_effects = steal_card.get('stealable_effects', [])
        
        # Find players with stealable effects
        targets = []
        for player in self.players:
            if player != stealing_player and not player.is_eliminated:
                for effect in stealable_effects:
                    if player.has_special_ability(effect):
                        targets.append((player, effect))
        
        if not targets:
            print(f"System: {steal_card['name']} - no players with stealable effects found")
            return
        
        # Choose a random target and effect
        target_player, effect_to_steal = random.choice(targets)
        
        # Remove effect from target
        target_player.special_abilities.discard(effect_to_steal)
        
        # Add effect to stealing player
        stealing_player.add_special_ability(effect_to_steal)
        
        print(f"System: {stealing_player.name} stole '{effect_to_steal}' from {target_player.name} using {steal_card['name']}!")
        
        # Analytics: Track effect theft
        self.analytics.track_effect_theft(stealing_player, target_player, effect_to_steal, steal_card)


