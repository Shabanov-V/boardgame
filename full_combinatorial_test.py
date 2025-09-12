
import json
import itertools
import random
import time
from pathlib import Path

def load_config():
    with open('simulator/config.json', 'r') as f:
        config = json.load(f)
    with open('whiteCards/random_events.json', 'r') as f:
        events = json.load(f)
    return config, events

def simulate_game(characters, config, events):
    """Упрощенная симуляция игры для тестирования баланса"""
    # Инициализация игроков
    players = []
    for char_id in characters:
        char_config = next(c for c in config['character_profiles'] if c['id'] == char_id)
        player = {
            'id': char_id,
            'name': char_config['name'],
            'money': char_config['starting_money'],
            'nerves': char_config['starting_nerves'],
            'language_level': char_config['starting_language'],
            'document_level': 0,
            'documents_cards': char_config.get('starting_document_cards', 3),
            'housing': char_config['starting_housing']
        }
        players.append(player)
    
    # Симуляция 100 ходов
    for turn in range(100):
        # Случайное событие
        event = random.choice(events['random_events'])
        
        # Применяем эффекты к игрокам
        for player in players:
            apply_event_effects(player, event)
        
        # Проверяем победителей
        for player in players:
            if check_win_condition(player, config):
                return player['id']
    
    # Если никто не выиграл, выбираем лучшего по очкам
    best_player = max(players, key=lambda p: p['money'] + p['nerves'] + p['document_level'] * 5)
    return best_player['id']

def apply_event_effects(player, event):
    """Применяет эффекты события к игроку"""
    char_id = player['id']
    
    # Проверяем individual_modifiers
    if 'individual_modifiers' in event and char_id in event['individual_modifiers']:
        effects = event['individual_modifiers'][char_id]
        for effect, value in effects.items():
            if effect in player:
                if isinstance(player[effect], (int, float)):
                    player[effect] = max(0, player[effect] + value)
    
    # Проверяем общие effects
    elif 'effects' in event:
        # Проверяем условия применения
        applies = True
        if 'conditions' in event:
            conditions = event['conditions']
            if 'character_id' in conditions:
                target_chars = conditions['character_id']
                if isinstance(target_chars, str):
                    target_chars = [target_chars]
                applies = char_id in target_chars
        
        if applies:
            effects = event['effects']
            for effect, value in effects.items():
                if effect in player:
                    if isinstance(player[effect], (int, float)):
                        player[effect] = max(0, player[effect] + value)

def check_win_condition(player, config):
    """Проверяет условия победы"""
    # Упрощенная проверка
    if player['document_level'] >= 7 and player['language_level'] >= 3:
        return True  # Гражданство
    if player['money'] >= 30 and player['document_level'] >= 6:
        return True  # Бизнес
    if player['money'] >= 25 and player['nerves'] >= 10:
        return True  # Отпуск
    return False

def run_combinatorial_test():
    print('🚀 ЗАПУСК ПОЛНОГО КОМБИНАТОРНОГО ТЕСТИРОВАНИЯ')
    print('='*60)
    
    config, events = load_config()
    characters = [c['id'] for c in config['character_profiles']]
    
    results = {}
    total_combinations = 0
    total_games = 0
    
    start_time = time.time()
    
    for group_size in range(2, 7):  # 2-6 игроков
        print(f'
📊 Тестирование групп из {group_size} игроков...')
        
        combinations = list(itertools.combinations(characters, group_size))
        games_per_combo = 20
        
        for i, combo in enumerate(combinations, 1):
            if i % 10 == 0:
                elapsed = time.time() - start_time
                progress = (i / len(combinations)) * 100
                print(f'  Прогресс: {i}/{len(combinations)} ({progress:.1f}%) - {elapsed:.1f}с')
            
            combo_results = {}
            for char in combo:
                combo_results[char] = 0
            
            # Запускаем игры для этой комбинации
            for game in range(games_per_combo):
                winner = simulate_game(list(combo), config, events)
                combo_results[winner] += 1
                total_games += 1
            
            # Сохраняем результаты
            combo_key = f'{group_size}_players_' + '_'.join(sorted(combo))
            results[combo_key] = {
                'players': list(combo),
                'games': games_per_combo,
                'wins': combo_results
            }
            
            total_combinations += 1
    
    # Анализ результатов
    print('
�� АНАЛИЗ РЕЗУЛЬТАТОВ')
    print('='*30)
    
    character_stats = {}
    for char in characters:
        character_stats[char] = {'wins': 0, 'games': 0}
    
    for combo_key, combo_result in results.items():
        for char in combo_result['players']:
            character_stats[char]['wins'] += combo_result['wins'][char]
            character_stats[char]['games'] += combo_result['games']
    
    # Вычисляем винрейты
    print('
👤 ОБЩИЕ ВИНРЕЙТЫ ПЕРСОНАЖЕЙ:')
    print('-'*40)
    
    win_rates = []
    for char in characters:
        if character_stats[char]['games'] > 0:
            winrate = (character_stats[char]['wins'] / character_stats[char]['games']) * 100
            wins = character_stats[char]['wins']
            games = character_stats[char]['games']
            
            char_name = next(c['name'] for c in config['character_profiles'] if c['id'] == char)
            print(f'{char_name:20}: {winrate:5.1f}% ({wins}/{games})')
            win_rates.append(winrate)
    
    # Общая статистика
    if win_rates:
        spread = max(win_rates) - min(win_rates)
        avg_rate = sum(win_rates) / len(win_rates)
        
        print(f'
📊 ИТОГОВАЯ СТАТИСТИКА:')
        print(f'Средний винрейт: {avg_rate:.1f}%')
        print(f'Разброс винрейта: {spread:.1f}%')
        print(f'Всего игр: {total_games:,}')
        print(f'Комбинаций: {total_combinations}')
        
        elapsed_total = time.time() - start_time
        print(f'Время тестирования: {elapsed_total:.1f} секунд')
        
        if spread <= 5:
            print('🎉 ИДЕАЛЬНЫЙ БАЛАНС!')
        elif spread <= 8:
            print('✅ ОТЛИЧНЫЙ баланс')
        elif spread <= 12:
            print('👍 ХОРОШИЙ баланс')
        else:
            print('⚠️ ТРЕБУЕТСЯ БАЛАНСИРОВКА')
    
    # Сохраняем детальные результаты
    output_file = 'simulator/output/full_combinatorial_results.json'
    Path('simulator/output').mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'character_statistics': character_stats,
            'detailed_results': results,
            'summary': {
                'total_games': total_games,
                'total_combinations': total_combinations,
                'win_rate_spread': spread if win_rates else 0,
                'average_win_rate': avg_rate if win_rates else 0,
                'testing_time_seconds': elapsed_total
            }
        }, f, indent=2)
    
    print(f'
💾 Результаты сохранены: {output_file}')
    return results

if __name__ == '__main__':
    run_combinatorial_test()
