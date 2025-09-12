import json


def load_json_file(filepath):
    """Loads a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_game_data():
    """Loads all necessary game data files."""
    data = {}
    data['action_cards'] = load_json_file('actionCards/additional_action_card.json')
    
    # Загружаем колоды предметов из разных файлов
    try:
        utility_items = load_json_file('itemCards/utility_items.json')
        defensive_items = load_json_file('itemCards/defensive_items.json') 
        aggressive_items = load_json_file('itemCards/aggressive_items.json')
        steal_effect_items = load_json_file('itemCards/steal_effect_items.json')
        
        # Объединяем все предметы
        all_items = []
        all_items.extend(utility_items['utility_items'])
        all_items.extend(defensive_items['defensive_items'])
        all_items.extend(aggressive_items['aggressive_items'])
        all_items.extend(steal_effect_items['steal_effect_items'])
        
        data['personal_items'] = {
            'personal_items': all_items,
            'steal_effect_cards': steal_effect_items['steal_effect_items']
        }
        
        print(f"✅ Загружено предметов: {len(all_items)} (utility: {len(utility_items['utility_items'])}, defensive: {len(defensive_items['defensive_items'])}, aggressive: {len(aggressive_items['aggressive_items'])}, steal: {len(steal_effect_items['steal_effect_items'])})")
        
    except FileNotFoundError as e:
        print(f"Warning: item files not found: {e}, skipping item deck")
        pass

    data['green_cards'] = load_json_file('greenCards/documents_work_cards.json')
    data['health_cards'] = load_json_file('redCards/health_cards.json')
    data['housing_cards'] = load_json_file('redCards/housing_cards.json')
    white_data = load_json_file('whiteCards/random_events.json')
    data['white_cards'] = {'random_events': white_data['random_events']}
    data['game_constants'] = load_json_file('Common/game_constants.json')
    return data


