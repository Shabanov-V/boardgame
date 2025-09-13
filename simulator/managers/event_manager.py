class InteractiveEvent:
    """Represents an event that can be interfered with by other players."""
    def __init__(self, action_type, acting_player, effects=None, description=""):
        self.action_type = action_type  # "document_exchange", "money_gain", etc.
        self.acting_player = acting_player
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

