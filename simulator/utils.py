import json


def load_json_file(filepath):
    """Loads a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_game_data():
    """Loads all necessary game data files."""
    data = {}
    # Correcting the typo in the directory name 'actionCartds'
    try:
        data['action_cards'] = load_json_file('actionCartds/action_cards.json')
    except FileNotFoundError:
        print("Warning: Could not find 'actionCartds/action_cards.json', trying 'actionCards/action_cards.json'")
        data['action_cards'] = load_json_file('actionCards/action_cards.json')

    data['green_cards'] = load_json_file('greenCards/documents_work_cards.json')
    data['health_cards'] = load_json_file('redCards/health_cards.json')
    data['housing_cards'] = load_json_file('redCards/housing_cards.json')
    data['random_events'] = load_json_file('whiteCards/random_events.json')
    data['game_constants'] = load_json_file('Common/game_constants.json')
    return data


