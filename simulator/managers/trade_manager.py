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
    def __init__(self, players, silent_mode=False):
        self.players = players
        self.pending_offer = None
        self.silent_mode = silent_mode
        
    def log(self, message):
        if not self.silent_mode:
            print(message)


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
        return False
    
    def execute_trade(self, offer, accepting_player):
        """Execute a completed trade between two players."""
        offering_player = offer.offering_player
        
        self.log(f"\nTRADE EXECUTION: {offering_player.name} ↔ {accepting_player.name}")
        self.log(f"Requested: {offer.requested_effects}")
        self.log(f"Offered: {offer.offered_items}")
        
        # Check if offering player can actually deliver what they promised
        can_deliver = self._validate_offered_items(offering_player, offer.actual_items)
        
        if not can_deliver:
            self.log(f"🎭 TRADE SCAM! {offering_player.name} couldn't deliver what they promised!")
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
            self.log(f"✅ Trade completed successfully!")
        else:
            self.log(f"❌ Trade failed to execute properly!")
            
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
                        self.log(f"  {player.name} used action card: {card['name']}")
                else:
                    player.nerves = min(10, player.nerves + amount)
                    
            elif effect_type == "money":
                player.money += multiplier * amount
                player.money = max(0, player.money)
                
            elif effect_type == "document_cards":
                player.document_cards += multiplier * amount
                player.document_cards = max(0, player.document_cards)
                
        return True

