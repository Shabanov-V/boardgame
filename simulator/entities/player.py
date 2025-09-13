from .ai import AI

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
        
        # Track housing level as an integer alongside the type string
        housing_level_map = {
            'room': 1,
            'apartment': 2,
            'mortgage': 3,
        }
        self.housing_level = housing_level_map.get(self.housing, 0)
        self.salary = profile.get('salary', 0)
        self.salary_type = profile.get('salary_type', 'fixed')
        self.salary_base = profile.get('salary_base', 0)
        self.housing_cost = profile.get('housing_cost', 0)

        self.position = 0
        self._document_level = int(0)
        self.action_cards = []
        self.max_action_cards = game_constants['game_constants']['max_action_cards']
        self.personal_items_hand = []
        self.max_personal_items_hand = game_constants['game_constants']['max_personal_items_hand']
        self.document_cards = 1  # Number of collected document cards
        self.housing_search = False  # Whether player is actively searching for housing
        
        # Add starting personal items
        self.add_personal_items(5)

        self.win_condition = win_condition
        self.goal_chosen = False
        self.is_eliminated = False
        self.eliminated_on_turn = None
        self.ai = AI(self, config)
        
        # Temporary bonuses and immunities system
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
        """Always store document_level as int, max 7"""
        self._document_level = min(int(value), 7)

    def __repr__(self):
        goal_text = self.win_condition['key'] if self.win_condition else "Не выбрана"
        return (f"Player(Name: {self.name}, Money: {self.money}, Nerves: {self.nerves}, "
                f"Lang Lvl: {self.language_level}, Housing: {self.housing} (Lvl {self.housing_level}), "
                f"Docs Lvl: {self.document_level}, Doc Cards: {self.document_cards}, "
                f"Personal Items: {len(self.personal_items_hand)}/{self.max_personal_items_hand}, "
                f"Goal: {goal_text})")

    def add_action_card(self, card):
        """Add an action card to player's hand."""
        if len(self.action_cards) < self.max_action_cards:
            self.action_cards.append(card)
            print(f"{self.name} received action card: {card['name']}.")
        else:
            print(f"{self.name}'s action card hand is full, cannot draw more.")
    
    def add_personal_items(self, count, game=None):
        """Add personal items to player's hand."""
        if count <= 0:
            return
            
        items_to_add = min(count, self.max_personal_items_hand - len(self.personal_items_hand))
        if items_to_add > 0:
            for _ in range(items_to_add):
                if game and 'item' in game.decks:
                    item = game.decks['item'].draw()
                    if item:
                        self.personal_items_hand.append(item)
                        print(f"{self.name} получил '{item['name']}'")
                    else:
                        self.personal_items_hand.append({"name": "Personal Item", "type": "utility"})
                        print(f"{self.name} получил базовый предмет (колода пуста)")
                else:
                    self.personal_items_hand.append({"name": "Personal Item", "type": "utility"})
            
            if not game:
                print(f"{self.name} получил {items_to_add} одноразовых предметов.")
        
        if count > items_to_add:
            excess = count - items_to_add
            print(f"{self.name} не смог взять {excess} предметов - рука полная!")
    
    def check_personal_items_hand_limit(self):
        """Check and return number of cards to discard if over limit."""
        excess = len(self.personal_items_hand) - self.max_personal_items_hand
        return max(0, excess)
    
    def discard_personal_items(self, count):
        """Discard specified number of personal items."""
        if count <= 0:
            return
        
        actual_discard = min(count, len(self.personal_items_hand))
        for _ in range(actual_discard):
            discarded = self.personal_items_hand.pop()
            print(f"{self.name} сбросил: {discarded.get('name', 'Personal Item')}")
        
        return actual_discard
    
    def force_discard_excess_personal_items(self):
        """Force discard excess personal items."""
        excess = self.check_personal_items_hand_limit()
        if excess > 0:
            print(f"⚠️  {self.name} должен сбросить {excess} одноразовых предметов (лимит: {self.max_personal_items_hand})")
            self.discard_personal_items(excess)
            return True
        return False
    
    def can_use_personal_item(self, item):
        """Check if player can use a personal item."""
        if not item:
            return False
            
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
        """Use a personal item."""
        if not self.can_use_personal_item(item):
            return False
            
        if item not in self.personal_items_hand:
            return False
        
        print(f"📦 {self.name} использует '{item['name']}'")
        
        # Pay the cost
        cost = item.get('cost', {})
        for resource, amount in cost.items():
            if resource == 'money':
                self.money = max(0, self.money - amount)
            elif resource == 'nerves':
                self.nerves = max(1, self.nerves - amount)
            elif resource == 'document_cards':
                self.document_cards = max(0, self.document_cards - amount)
        
        # Remove item from hand
        self.personal_items_hand.remove(item)
        
        return True
    
    def add_temporary_bonus(self, bonus_type, amount):
        """Add a temporary bonus."""
        if bonus_type in self.temporary_bonuses:
            self.temporary_bonuses[bonus_type] += amount
            print(f"System: {self.name} gained {amount} {bonus_type} bonus (total: {self.temporary_bonuses[bonus_type]})")
    
    def add_immunity(self, immunity_type):
        """Add an immunity."""
        self.immunities.add(immunity_type)
        print(f"System: {self.name} gained immunity to {immunity_type}")
    
    def add_special_ability(self, ability_type):
        """Add a special ability."""
        self.special_abilities.add(ability_type)
        print(f"System: {self.name} gained special ability: {ability_type}")
    
    def has_immunity(self, immunity_type):
        """Check if player has an immunity."""
        return immunity_type in self.immunities
    
    def has_special_ability(self, ability_type):
        """Check if player has a special ability."""
        return ability_type in self.special_abilities
    
    def get_bonus(self, bonus_type):
        """Get current bonus value."""
        return self.temporary_bonuses.get(bonus_type, 0)
    
    def clear_temporary_effects(self):
        """Clear all temporary effects at end of turn."""
        for bonus_type in self.temporary_bonuses:
            if self.temporary_bonuses[bonus_type] > 0:
                print(f"System: {self.name} lost {self.temporary_bonuses[bonus_type]} {bonus_type} bonus")
                self.temporary_bonuses[bonus_type] = 0
