from simulator.utils.logger import Logger

class EliminationManager:
    """Manages player elimination conditions and processes."""
    
    def __init__(self, game_data, logger: Logger, players=None):
        self.elimination_threshold = game_data['game_constants']['game_constants'].get('elimination_threshold', -1)
        self.players = players
        self.logger = logger

    def check_elimination(self, player, current_turn):
        """Check if a player should be eliminated."""
        # Check nerves
        if player.nerves <= self.elimination_threshold:
            self._eliminate_player(player, current_turn, "низких нервов")
            return True
            
        # Check money after salary and rent
        elif player.money < 0:
            self._eliminate_player(player, current_turn, "долгов")
            return True
                
        return False
    
    def emergency_sell_cards(self, player):
        """Emergency sale of cards when bankrupt."""
        emergency_money = 0
        money_needed = abs(player.money)
        
        # First try to sell document cards to other players
        if player.document_cards > 0:
            for other_player in self.players:
                if other_player != player and not other_player.is_eliminated:
                    # Offer to sell document cards for 2 money each
                    cards_to_sell = min(player.document_cards, money_needed // 2)
                    if cards_to_sell > 0 and other_player.money >= cards_to_sell * 2:
                        player.document_cards -= cards_to_sell
                        player.money += cards_to_sell * 2
                        other_player.money -= cards_to_sell * 2
                        emergency_money += cards_to_sell * 2
                        money_needed -= cards_to_sell * 2
                        self.logger.log(f"💳 {player.name} продал {cards_to_sell} карт документов {other_player.name} за {cards_to_sell * 2} денег")
                        
                        if player.money >= 0:
                            break
        
        # If still need money, sell personal items for 1 money each
        if player.money < 0 and len(player.personal_items_hand) > 0:
            items_to_sell = min(len(player.personal_items_hand), abs(player.money))
            player.personal_items_hand = player.personal_items_hand[:-items_to_sell]  # Remove last items
            player.money += items_to_sell
            emergency_money += items_to_sell
            self.logger.log(f"🎒 {player.name} продал {items_to_sell} личных предметов за {items_to_sell} денег")
        
        return emergency_money
    
    def _eliminate_player(self, player, current_turn, reason):
        """Mark a player as eliminated."""
        player.is_eliminated = True
        if player.eliminated_on_turn is None:
            player.eliminated_on_turn = current_turn
        self.logger.log(f"💀 {player.name} выбыл из-за {reason} ({player.money} денег, {player.nerves} нервов)")
    
    def check_game_over(self, players):
        """Check if game should end due to eliminations."""
        active_players = [p for p in players if not p.is_eliminated]
        if len(active_players) <= 1 and len(players) > 1:
            return True, active_players[0] if active_players else None
        return False, None

