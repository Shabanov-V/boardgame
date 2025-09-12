import json


def load_json_file(filepath):
    """Loads a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_game_data():
    """Loads all necessary game data files."""
    data = {}
    data['action_cards'] = load_json_file('boardgame/actionCartds/action_cards.json')
    
    # Загружаем колоду предметов, если она есть
    try:
        data['item_cards'] = load_json_file('boardgame/itemCards/personal_items.json')
    except FileNotFoundError:
        print("Warning: item_cards.json not found, skipping item deck")
        pass

    data['green_cards'] = load_json_file('boardgame/greenCards/documents_work_cards.json')
    data['health_cards'] = load_json_file('boardgame/redCards/health_cards.json')
    data['housing_cards'] = load_json_file('boardgame/redCards/housing_cards.json')
    data['random_events'] = load_json_file('boardgame/whiteCards/random_events.json')
    data['game_constants'] = load_json_file('boardgame/Common/game_constants.json')
    return data


