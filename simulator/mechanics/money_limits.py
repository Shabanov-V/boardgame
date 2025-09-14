"""Money limit mechanics for the game."""

class MoneyLimitManager:
    """Manages money limits and penalties."""
    
    def __init__(self, max_money_multiplier=2):
        """Initialize the manager.
        
        Args:
            max_money_multiplier (int): Multiplier for max money relative to highest goal requirement
        """
        self.max_money_multiplier = max_money_multiplier
        self._max_money_requirement = 35  # Hardcoded from family_reunion goal
        self.money_limit = self._max_money_requirement * max_money_multiplier
        
    def check_money_limit(self, player):
        """Check if player exceeds money limit and apply penalty.
        
        Args:
            player: Player object to check
            
        Returns:
            tuple: (excess_amount, penalty_amount) or (0, 0) if no penalty
        """
        if player.money > self.money_limit:
            excess = player.money - self.money_limit
            penalty = excess // 2  # Lose half of excess
            player.money = self.money_limit - penalty
            return excess, penalty
        return 0, 0



