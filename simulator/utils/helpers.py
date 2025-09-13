"""Helper functions for game logic."""

def calculate_win_progress(player) -> float:
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
                print(f"❌ CONVERSION ERROR in calculate_win_progress: {e}")
                print(f"   key={key}, player_value={player_value} (type: {type(player_value)}), required_value={required_value} (type: {type(required_value)})")
                progress += 0.0
    
    return progress / requirements if requirements > 0 else 0.0

def check_conditions(player, conditions):
    """Check if a player meets all conditions specified on a card."""
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
                return False
        elif key == 'housing_search':
            if value != player.housing_search:
                return False
        elif key == 'money_range':
            try:
                if not eval(f"{player.money} {value}"):
                    return False
            except:
                return False
    return True

def determine_card_type(card):
    """Determine the type of card for analytics."""
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

def is_global_event_card(card):
    """Determine if a card is a global event."""
    # Cards with conditions (conditions for groups of players) are events for all
    if 'conditions' in card and 'character_id' in card.get('conditions', {}):
        return True
    
    # Cards with type instant AND without cost are events for all
    if card.get('type') == 'instant' and 'cost' not in card:
        return True
    
    # All other cards are personal items (including cards with cost, utility, interference etc.)
    return False

