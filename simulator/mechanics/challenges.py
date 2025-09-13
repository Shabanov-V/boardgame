import random
from ..mechanics.effects import EffectManager

class ChallengeManager:
    """Manages dice roll challenges and their outcomes."""
    
    @staticmethod
    def handle_challenge(player, challenge, event_manager=None):
        """Execute a dice challenge for a player."""
        roll = random.randint(1, 6)
        print(f"🎲 {player.name} rolls {roll} for {challenge.get('description', 'challenge')}")

        # Find the appropriate outcome based on roll
        outcome_key = ChallengeManager._determine_outcome(roll, challenge['outcomes'])
        chosen_outcome = challenge['outcomes'][outcome_key]
        
        # Apply the outcome effects
        if 'effects' in chosen_outcome:
            print(f"Outcome: {chosen_outcome['description']}")
            EffectManager.apply_effects(player, chosen_outcome['effects'], event_manager)
            return True
        return False

    @staticmethod
    def _determine_outcome(roll, outcomes):
        """Determine which outcome applies based on the roll."""
        for outcome, details in outcomes.items():
            condition = details['condition']
            
            # Handle range conditions (e.g., "2-4")
            if '-' in condition:
                low, high = map(int, condition.split('-'))
                if low <= roll <= high:
                    return outcome
                    
            # Handle greater than conditions (e.g., ">3")
            elif '>' in condition:
                val = int(condition.replace('>', '').strip())
                if roll > val:
                    return outcome
                    
            # Handle exact match conditions
            elif str(roll) == condition:
                return outcome
                
        # Default to 'failure' if no condition matches
        return 'failure'

