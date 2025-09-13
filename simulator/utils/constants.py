"""Game constants and configuration."""

# Card types
CARD_TYPES = {
    'action': 'action_cards',
    'green': 'green_cards',
    'red': 'health_cards',
    'white': 'random_events',
    'item': 'personal_items'
}

# Housing types and levels
HOUSING_TYPES = {
    'room': 1,
    'apartment': 2,
    'mortgage': 3
}

# Housing costs
HOUSING_COSTS = {
    'room': 1,
    'apartment': 3,
    'mortgage': 5
}

# Game parameters
MAX_LANGUAGE_LEVEL = 3
MAX_DOCUMENT_LEVEL = 7
MAX_NERVES = 10
MIN_NERVES = 1

# Card effects
BONUS_TYPES = [
    'social', 'housing', 'work', 'language',
    'movement', 'comfort', 'health', 'shopping',
    'communication', 'confidence', 'cultural', 'durability',
    'eco', 'emergency', 'energy', 'entertainment',
    'humor', 'hygiene', 'mobility', 'reliability',
    'safety', 'self_sufficiency', 'storage', 'style',
    'utility', 'vacation', 'sports'
]

IMMUNITY_TYPES = [
    'health_penalty', 'heat_penalty', 'cold_penalty',
    'rain_penalty', 'sun_penalty', 'weather_penalty',
    'air_penalty', 'glare_penalty', 'hangover_penalty',
    'illness_penalty', 'roommate_penalty', 'shortage_penalty',
    'spoilage_penalty'
]

SPECIAL_ABILITIES = [
    'documents_fast_track', 'language_dice_advantage', 'reroll_language_dice',
    'skip_document_queue', 'language_upgrade_discount', 'permanent_language_bonus',
    'stress_immunity', 'immunity_next_housing'
]

# Event types that can be interfered with
INTERFERABLE_ACTIONS = [
    "document_exchange", "money_gain", "document_level_up", 
    "any_positive_effect", "close_to_win", "pre_turn_action",
    "movement", "challenge_event", "resource_gain"
]

# AI parameters
DEFAULT_NERVE_THRESHOLD = 3
DEFAULT_LIE_PROBABILITY = 0.3
GRUDGE_THRESHOLD = 2  # Level at which AI will seek revenge

