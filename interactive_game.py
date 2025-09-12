#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интерактивная игра с AI противниками
"""

import json
import random
import sys
import os
import time
from typing import Dict, List, Optional, Any

# Добавляем путь к модулям симулятора
sys.path.append(os.path.join(os.path.dirname(__file__), 'simulator'))

from core import Game, Player, AI, Deck, Board


class HumanPlayer:
    """Класс для человеческого игрока"""
    
    def __init__(self, player: Player):
        self.player = player
        
    def choose_profile(self, available_profiles: List[Dict]) -> Dict:
        """Выбор профиля персонажа"""
        print("\n🎭 ВЫБОР ПЕРСОНАЖА:")
        print("=" * 50)
        
        for i, profile in enumerate(available_profiles, 1):
            print(f"{i}. {profile['name']}")
            print(f"   💰 Деньги: {profile['starting_money']}")
            print(f"   🧠 Нервы: {profile['starting_nerves']}")
            print(f"   🗣️ Язык: {profile['starting_language']}")
            print(f"   🏠 Жилье: {profile['starting_housing']}")
            print()
            
        while True:
            try:
                choice = int(input("Выберите персонажа (номер): ")) - 1
                if 0 <= choice < len(available_profiles):
                    return available_profiles[choice]
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
    
    def choose_goal(self, goals: Dict) -> str:
        """Выбор цели игры"""
        print("\n🎯 ВЫБОР ЦЕЛИ ИГРЫ:")
        print("=" * 50)
        
        goal_list = list(goals.items())
        for i, (key, goal) in enumerate(goal_list, 1):
            print(f"{i}. {goal['description']}")
            
        while True:
            try:
                choice = int(input("Выберите цель (номер): ")) - 1
                if 0 <= choice < len(goal_list):
                    goal_key, goal_data = goal_list[choice]
                    return goal_key
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
    
    def decide_green_card_use(self, card: Dict) -> str:
        """Решение по использованию зеленой карты"""
        print(f"\n💚 ЗЕЛЕНАЯ КАРТА: {card['name']}")
        print(f"📝 {card['description']}")
        
        if card.get('exchange_instruction'):
            print("\n⚖️ ВАРИАНТЫ:")
            print("1. Обменять на уровень документов")
            print("2. Использовать как событие")
            
            while True:
                try:
                    choice = int(input("Ваш выбор (1-2): "))
                    if choice == 1:
                        return 'exchange'
                    elif choice == 2:
                        return 'event'
                    else:
                        print("❌ Введите 1 или 2!")
                except ValueError:
                    print("❌ Введите число!")
        else:
            input("📜 Нажмите Enter для применения эффекта...")
            return 'event'
    
    def decide_draw_choice(self) -> str:
        """Выбор между зеленой картой, картой действия и предметом"""
        print("\n🎴 ВЫБОР КАРТЫ:")
        print("1. Взять зеленую карту (документы/работа)")
        print("2. Взять карту действия (событие для всех)")
        print("3. Взять предмет (личная шмотка)")
        
        while True:
            try:
                choice = int(input("Ваш выбор (1-3): "))
                if choice == 1:
                    return 'draw_green'
                elif choice == 2:
                    return 'draw_action'
                elif choice == 3:
                    return 'draw_item'
                else:
                    print("❌ Введите 1, 2 или 3!")
            except ValueError:
                print("❌ Введите число!")
    
    def decide_play_action_card(self, when: str = 'start_of_turn') -> Optional[Dict]:
        """Решение о разыгрывании карты действия"""
        available_cards = [card for card in self.player.action_cards 
                          if card.get('when_to_play', 'anytime') in ['anytime', when]]
        
        if not available_cards:
            return None
            
        print(f"\n🎯 КАРТЫ ДЕЙСТВИЯ ({len(available_cards)} доступно):")
        print("0. Не играть карту")
        
        for i, card in enumerate(available_cards, 1):
            cost_str = ""
            if 'cost' in card:
                costs = []
                for resource, amount in card['cost'].items():
                    costs.append(f"{amount} {resource}")
                cost_str = f" (стоит: {', '.join(costs)})"
            
            print(f"{i}. {card['name']}{cost_str}")
            print(f"   📝 {card['description']}")
        
        while True:
            try:
                choice = int(input("Выберите карту (номер): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(available_cards):
                    return available_cards[choice - 1]
                else:
                    print("❌ Неверный номер!")
            except ValueError:
                print("❌ Введите число!")
    
    def decide_interference(self, event):
        """Решение о вмешательстве в действие другого игрока"""
        if event.acting_player == self.player:
            return None
            
        # Найти подходящие карты для вмешательства
        suitable_cards = []
        for i, card in enumerate(self.player.action_cards):
            if card.get('type') == 'interference':
                suitable_cards.append((i, card))
            elif card.get('when_to_play') == 'instant_response':
                suitable_cards.append((i, card))
            elif 'block_' in str(card.get('effects', {})):
                suitable_cards.append((i, card))
        
        if not suitable_cards:
            return None
            
        print(f"\n⚡ ВОЗМОЖНОСТЬ ВМЕШАТЕЛЬСТВА!")
        print(f"📢 {event.description}")
        print(f"\n🃏 Ваши карты для вмешательства:")
        
        for i, (idx, card) in enumerate(suitable_cards, 1):
            cost_text = ""
            if 'cost' in card:
                cost_parts = []
                if 'money' in card['cost']:
                    cost_parts.append(f"{card['cost']['money']} 💰")
                if 'nerves' in card['cost']:
                    cost_parts.append(f"{card['cost']['nerves']} 🧠")
                if cost_parts:
                    cost_text = f" (Стоимость: {', '.join(cost_parts)})"
                    
            print(f"{i}. {card['name']}{cost_text}")
            print(f"   📝 {card['description']}")
            
        print(f"{len(suitable_cards) + 1}. Не вмешиваться")
        
        while True:
            try:
                choice = int(input("Ваш выбор: "))
                if choice == len(suitable_cards) + 1:
                    return None
                elif 1 <= choice <= len(suitable_cards):
                    card_idx, selected_card = suitable_cards[choice - 1]
                    
                    # Проверить, может ли игрок заплатить стоимость
                    cost = selected_card.get('cost', {})
                    if 'money' in cost and self.player.money < cost['money']:
                        print(f"❌ Недостаточно денег! Нужно: {cost['money']}, есть: {self.player.money}")
                        continue
                    if 'nerves' in cost and self.player.nerves <= cost['nerves']:
                        print(f"❌ Недостаточно нервов! Нужно: {cost['nerves']}, есть: {self.player.nerves}")
                        continue
                        
                    return (selected_card, True)
                else:
                    print(f"❌ Введите число от 1 до {len(suitable_cards) + 1}!")
            except ValueError:
                print("❌ Введите число!")
    
    def decide_defense(self, event, interference_card):
        """Решение о защите от вмешательства"""
        # Найти защитные карты
        defense_cards = []
        for i, card in enumerate(self.player.action_cards):
            effects = card.get('effects', {})
            if effects.get('block_sabotage') or effects.get('reflect_sabotage'):
                defense_cards.append((i, card))
        
        if not defense_cards:
            return None
            
        print(f"\n🛡️ ВОЗМОЖНОСТЬ ЗАЩИТЫ!")
        print(f"⚔️ {interference_card['name']} направлена против вас!")
        print(f"\n🃏 Ваши защитные карты:")
        
        for i, (idx, card) in enumerate(defense_cards, 1):
            cost_text = ""
            if 'cost' in card:
                cost_parts = []
                if 'money' in card['cost']:
                    cost_parts.append(f"{card['cost']['money']} 💰")
                if 'nerves' in card['cost']:
                    cost_parts.append(f"{card['cost']['nerves']} 🧠")
                if cost_parts:
                    cost_text = f" (Стоимость: {', '.join(cost_parts)})"
                    
            print(f"{i}. {card['name']}{cost_text}")
            print(f"   📝 {card['description']}")
            
        print(f"{len(defense_cards) + 1}. Не защищаться")
        
        while True:
            try:
                choice = int(input("Ваш выбор: "))
                if choice == len(defense_cards) + 1:
                    return None
                elif 1 <= choice <= len(defense_cards):
                    card_idx, selected_card = defense_cards[choice - 1]
                    
                    # Проверить стоимость
                    cost = selected_card.get('cost', {})
                    if 'money' in cost and self.player.money < cost['money']:
                        print(f"❌ Недостаточно денег! Нужно: {cost['money']}, есть: {self.player.money}")
                        continue
                    if 'nerves' in cost and self.player.nerves <= cost['nerves']:
                        print(f"❌ Недостаточно нервов! Нужно: {cost['nerves']}, есть: {self.player.nerves}")
                        continue
                        
                    return (selected_card, True)
                else:
                    print(f"❌ Введите число от 1 до {len(defense_cards) + 1}!")
            except ValueError:
                print("❌ Введите число!")


class InteractiveGame(Game):
    """Интерактивная версия игры"""
    
    def __init__(self):
        # Загружаем конфигурацию
        config_path = os.path.join(os.path.dirname(__file__), 'simulator', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Загружаем данные карт
        base_path = os.path.dirname(__file__)
        game_data = {}
        
        # Загружаем все типы карт и данные
        card_files = {
            'action_cards': 'actionCartds/action_cards.json',
            'item_cards': 'itemCards/personal_items.json',
            'green_cards': 'greenCards/documents_work_cards.json', 
            'health_cards': 'redCards/health_cards.json',
            'housing_cards': 'redCards/housing_cards.json',
            'random_events': 'whiteCards/random_events.json',
            'game_constants': 'Common/game_constants.json'
        }
        
        for key, filename in card_files.items():
            file_path = os.path.join(base_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                game_data[key] = json.load(f)
        
        super().__init__(config, game_data)
        self.human_player = None
        
        # Добавляем колоду предметов
        from simulator.core import Deck
        self.decks['item'] = Deck(game_data['item_cards']['personal_items'])
        
        # Переопределяем обработку карт действия в AI ходах
        self._original_action_card_handler = None
        
    def setup_game(self):
        """Настройка игры"""
        print("🎮 ДОБРО ПОЖАЛОВАТЬ В ИГРУ 'ЖИЗНЬ В ИСПАНИИ'!")
        print("=" * 60)
        
        # Очищаем список игроков, созданных родительским классом
        self.players = []
        
        # Выбор количества AI противников
        while True:
            try:
                num_ai = int(input("Сколько AI противников? (1-7): "))
                if 1 <= num_ai <= 7:
                    break
                else:
                    print("❌ От 1 до 7 противников!")
            except ValueError:
                print("❌ Введите число!")
        
        # Выбор профиля для игрока
        available_profiles = self.config['character_profiles'].copy()
        
        human_ai = HumanPlayer(None)
        player_profile = human_ai.choose_profile(available_profiles)
        available_profiles.remove(player_profile)
        
        # Создание игрока-человека
        human_player_obj = Player(player_profile, None, self.config, self.game_data['game_constants'])
        human_player_obj.ai = AI(human_player_obj, self.config)
        human_player_obj.name = f"🧑 {player_profile['name']} (ВЫ)"
        self.human_player = HumanPlayer(human_player_obj)
        human_player_obj.human_controller = self.human_player  # Связываем для InteractionManager
        self.players.append(human_player_obj)
        
        # Создание AI игроков
        ai_profiles = random.sample(available_profiles, num_ai)
        for i, profile in enumerate(ai_profiles):
            ai_player = Player(profile, None, self.config, self.game_data['game_constants'])
            ai_player.ai = AI(ai_player, self.config)
            ai_player.name = f"🤖 {profile['name']} (AI-{i+1})"
            self.players.append(ai_player)
        
        # Раздаем каждому игроку по 3 предмета
        self.deal_starting_items()
        
        print(f"\n👥 УЧАСТНИКИ ИГРЫ ({len(self.players)} игроков):")
        for player in self.players:
            print(f"   {player.name}")
        
        input("\n🚀 Нажмите Enter для начала игры...")
    
    def deal_starting_items(self):
        """Раздает каждому игроку по 3 предмета в начале игры"""
        print("\n🎒 РАЗДАЧА СТАРТОВЫХ ПРЕДМЕТОВ...")
        
        for player in self.players:
            # Очищаем карты действия, полученные из старой системы
            player.action_cards = []
            
            items_received = []
            for i in range(3):
                item_card = self.decks['item'].draw()
                if item_card:
                    player.add_action_card(item_card)
                    items_received.append(item_card['name'])
            
            is_human = player == self.human_player.player
            prefix = "🧑 ВЫ" if is_human else f"🤖 {player.name.split(' (')[0]}"
            print(f"   {prefix} получил: {', '.join(items_received)}")
        
        print("✅ Стартовые предметы розданы!")
    
    def display_game_state(self):
        """Отображение состояния игры"""
        print("\n" + "🎮" * 40)
        print(f"🎯 ХОД {self.turn + 1} | ⏱️ Максимум ходов: {len(self.players) * 15}")
        print("🎮" * 40)
        
        # Используем новую панель статуса
        pass  # Панель уже отображается в новом методе
    
    def display_player_status_panel(self, player):
        """Подробная панель статуса для игрока-человека"""
        print(f"\n{'🧑 ВАШ СТАТУС':^80}")
        print("🔸" * 80)
        
        # Основные ресурсы в красивой таблице
        print(f"┌─ 💰 ДЕНЬГИ: {player.money:>3} │ 🧠 НЕРВЫ: {player.nerves:>2} │ 📄 ДОКУМЕНТЫ: {player.document_cards} (уровень {player.document_level}) │ 🗣️ ЯЗЫК: {player.language_level} ─┐")
        print(f"│ 🏠 ЖИЛЬЕ: {player.housing:<12} │ 📍 ПОЗИЦИЯ: {player.position:>2} │ 🎴 ПРЕДМЕТОВ: {len(player.action_cards):>2}                                │")
        print("└─" + "─" * 76 + "─┘")
        
        # Информация о цели и прогрессе
        if player.win_condition:
            print(f"\n🎯 ВАША ЦЕЛЬ: {player.win_condition['description']}")
            self.display_goal_progress(player)
        else:
            print(f"\n🎯 ЦЕЛЬ: ❌ Не выбрана (нужен уровень документов 5)")
            docs_needed = 5 - player.document_level
            print(f"   📄 До выбора цели: {docs_needed} уровней документов")
        
        # Предметы в руке
        if player.action_cards:
            print(f"\n🎒 ПРЕДМЕТЫ В РУКЕ ({len(player.action_cards)}):")
            for i, card in enumerate(player.action_cards, 1):
                cost_info = ""
                if 'cost' in card:
                    costs = []
                    for resource, amount in card['cost'].items():
                        if resource == 'skip_turn':
                            costs.append("пропуск хода")
                        else:
                            costs.append(f"{amount} {resource}")
                    cost_info = f" (💰 {', '.join(costs)})"
                print(f"   {i}. {card['name']}{cost_info}")
        else:
            print(f"\n🎒 ПРЕДМЕТЫ: Пусто")
    
    def display_goal_progress(self, player):
        """Показывает прогресс к выполнению цели"""
        if not player.win_condition:
            return
        
        requirements = player.win_condition['requires']
        print("   📊 ПРОГРЕСС К ЦЕЛИ:")
        
        for req_type, req_value in requirements.items():
            if req_type == 'housing_type':
                current = "✅" if player.housing == req_value else f"❌ нужно: {req_value}"
                print(f"      🏠 Жилье: {current}")
            elif req_type == 'document_level':
                current = player.document_level
                status = "✅" if current >= req_value else f"❌ {current}/{req_value}"
                print(f"      📄 Документы: {status}")
            elif req_type == 'language_level':
                current = player.language_level
                status = "✅" if current >= req_value else f"❌ {current}/{req_value}"
                print(f"      🗣️ Язык: {status}")
            elif req_type == 'money':
                current = player.money
                status = "✅" if current >= req_value else f"❌ {current}/{req_value}"
                print(f"      💰 Деньги: {status}")
            elif req_type == 'nerves':
                current = player.nerves
                status = "✅" if current >= req_value else f"❌ {current}/{req_value}"
                print(f"      🧠 Нервы: {status}")
    
    def get_goal_completion_percentage(self, player):
        """Вычисляет процент выполнения цели"""
        if not player.win_condition:
            return 0.0
        
        requirements = player.win_condition['requires']
        completed_requirements = 0
        total_requirements = len(requirements)
        
        for req_type, req_value in requirements.items():
            if req_type == 'housing_type':
                if player.housing == req_value:
                    completed_requirements += 1
            elif req_type == 'document_level':
                if player.document_level >= req_value:
                    completed_requirements += 1
            elif req_type == 'language_level':
                if player.language_level >= req_value:
                    completed_requirements += 1
            elif req_type == 'money':
                if player.money >= req_value:
                    completed_requirements += 1
            elif req_type == 'nerves':
                if player.nerves >= req_value:
                    completed_requirements += 1
        
        return (completed_requirements / total_requirements) * 100
    
    def play_human_turn(self, player):
        """Обработка хода человека"""
        print(f"\n{'🎯 ВАШ ХОД!':^80}")
        print("🔹" * 80)
        
        # Показываем актуальный статус перед ходом
        print(f"\n📊 ТЕКУЩИЙ СТАТУС:")
        print(f"   💰 Деньги: {player.money} | 🧠 Нервы: {player.nerves} | 📄 Документы: L{player.document_level}({player.document_cards}) | 🗣️ Язык: {player.language_level}")
        
        if player.win_condition:
            completion = self.get_goal_completion_percentage(player)
            print(f"   🎯 Прогресс к цели: {completion:.1f}% ({'🔥 БЛИЗКО К ПОБЕДЕ!' if completion >= 80 else '📈 В процессе'})")
        
        if player.action_cards:
            print(f"   🎒 Предметов в руке: {len(player.action_cards)}")
            print("   📝 Список предметов:")
            for i, card in enumerate(player.action_cards, 1):
                when_play = card.get('when_to_play', 'anytime')
                print(f"      {i}. {card['name']} (играть: {when_play})")
        
        print()
        
        # 1. Выбор карты действия в начале хода
        action_card = self.human_player.decide_play_action_card('start_of_turn')
        if action_card:
            print(f"\n🎯 Играете карту: {action_card['name']}")
            self.apply_card_effect(player, action_card, 'event')
            player.action_cards.remove(action_card)
            self.decks['action'].discard(action_card)
        
        # 2. Бросок кубика и движение
        input("\n🎲 Нажмите Enter для броска кубика...")
        roll = random.randint(1, 6)
        print(f"🎲 Выпало: {roll}")
        
        old_position = player.position
        player.position = (player.position + roll) % self.board.size
        print(f"📍 Переместились с {old_position} на {player.position}")
        
        # 3. Фаза торговли (упрощена для интерактивной игры)
        print("\n💼 Фаза торговли пропущена в интерактивной версии")
        
        # 4. Эффект клетки
        cell_type = self.board.get_cell_type(player.position)
        print(f"\n📍 Попали на клетку: {cell_type}")
        
        if cell_type == 'green':
            choice = self.human_player.decide_draw_choice()
            if choice == 'draw_green':
                card = self.decks['green'].draw()
                if card:
                    print(f"\n💚 Получили зеленую карту: {card['name']}")
                    use_decision = self.human_player.decide_green_card_use(card)
                    self.apply_card_effect(player, card, use_decision)
            elif choice == 'draw_action':
                action_card = self.decks['action'].draw()
                if action_card:
                    self.handle_action_card_draw_human(player, action_card)
            elif choice == 'draw_item':
                item_card = self.decks['item'].draw()
                if item_card:
                    print(f"\n🎒 Получили предмет: {item_card['name']}")
                    print(f"📝 {item_card['description']}")
                    
                    # Показываем стоимость, если есть
                    if 'cost' in item_card:
                        costs = []
                        for resource, amount in item_card['cost'].items():
                            if resource == 'skip_turn':
                                costs.append("пропуск хода")
                            else:
                                costs.append(f"{amount} {resource}")
                        print(f"💰 Стоимость: {', '.join(costs)}")
                    
                    # Показываем когда можно играть
                    when_to_play = item_card.get('when_to_play', 'anytime')
                    if when_to_play == 'start_of_turn':
                        print("⏰ Можно использовать: в начале хода")
                    elif when_to_play == 'anytime':
                        print("⏰ Можно использовать: в любое время")
                    elif when_to_play == 'anytime_or_defensive':
                        print("⏰ Можно использовать: в любое время или как защиту")
                    
                    player.add_action_card(item_card)
                    print(f"🎴 Предмет добавлен в руку (всего предметов: {len(player.action_cards)})")
                    
                    input("📜 Нажмите Enter для продолжения...")
        
        elif cell_type in ['red', 'white']:
            card = self.decks[cell_type].draw()
            if card:
                color_emoji = "❤️" if cell_type == 'red' else "🤍"
                print(f"\n{color_emoji} Получили карту: {card['name']}")
                print(f"📝 {card['description']}")
                input("🎯 Нажмите Enter для применения эффекта...")
                self.apply_card_effect(player, card, 'event')
        
        # 5. Проверка выбора цели
        if not player.win_condition and player.document_level >= 5:
            print(f"\n🎉 Поздравляем! Вы достигли уровня документов {player.document_level}!")
            print("Теперь можно выбрать цель игры!")
            
            goal_key = self.human_player.choose_goal(self.config['win_conditions'])
            goal_data = self.config['win_conditions'][goal_key].copy()
            goal_data['key'] = goal_key
            player.win_condition = goal_data
            print(f"\n🎯 Выбранная цель: {goal_data['description']}")
        
        # 6. Проверка победы
        self.check_win_condition(player)
        if not self.game_over:
            self.check_elimination(player)
    
    def play_ai_turn(self, player):
        """Обработка хода AI (с выводом информации)"""
        print(f"\n🤖 Ход AI: {player.name}")
        print("-" * 60)
        
        # Показываем текущий статус AI игрока
        goal_text = player.win_condition['description'][:40] + "..." if player.win_condition else "Цель не выбрана"
        print(f"   📊 Статус: 💰{player.money} | 🧠{player.nerves} | 📄L{player.document_level}({player.document_cards}) | 🗣️{player.language_level} | 🏠{player.housing}")
        print(f"   🎯 Цель: {goal_text}")
        
        print("   ⏸️  AI делает ход...")
        time.sleep(1)
        
        # Временно перехватываем обработку карт действия
        original_add_action_card = player.add_action_card
        
        def custom_add_action_card(card):
            """Перехватчик для обработки карт действия AI"""
            # Определяем тип карты по содержимому
            is_global_event = self.is_global_event_card(card)
            
            if is_global_event:
                # Это событие для всех - даем возможность реагировать
                print(f"📢 СОБЫТИЕ ДЛЯ ВСЕХ ИГРОКОВ: {card['name']}")
                
                # Применяем эффект ко всем игрокам с возможностью реакции
                self.apply_global_event_with_reactions(card)
                
                self.decks['action'].discard(card)
            
            else:
                # Это одноразовый предмет - добавляем в руку обычным способом
                print(f"🎒 Одноразовый предмет для {player.name}")
                original_add_action_card(card)
        
        player.add_action_card = custom_add_action_card
        
        try:
            # Используем стандартную логику AI из родительского класса
            super().take_turn(player)
        finally:
            # Восстанавливаем оригинальный метод
            player.add_action_card = original_add_action_card
        
        # Показываем результат хода
        print(f"\n   📈 РЕЗУЛЬТАТ ХОДА:")
        print(f"      💰 Деньги: {player.money} | 🧠 Нервы: {player.nerves} | 📄 Документы: L{player.document_level}({player.document_cards})")
        if player.win_condition:
            print(f"      🎯 Прогресс к цели: {self.get_goal_completion_percentage(player):.1f}%")
        
        print("   ✅ Ход завершен")
        time.sleep(0.5)
    
    def handle_action_card_draw_human(self, player, action_card):
        """Обработка получения карты действия для человека"""
        print(f"\n🎯 Получили карту действия: {action_card['name']}")
        print(f"📝 {action_card['description']}")
        
        # Определяем тип карты по содержимому
        is_global_event = self.is_global_event_card(action_card)
        
        if is_global_event:
            # Это событие для всех - даем возможность реагировать
            print(f"\n📢 СОБЫТИЕ ДЛЯ ВСЕХ ИГРОКОВ!")
            input("📜 Нажмите Enter для применения эффекта...")
            
            # Применяем эффект ко всем игрокам с возможностью реакции
            self.apply_global_event_with_reactions(action_card)
            
            self.decks['action'].discard(action_card)
        
        else:
            # Это одноразовый предмет - добавляем в руку
            print(f"\n🎒 ОДНОРАЗОВЫЙ ПРЕДМЕТ!")
            
            # Показываем стоимость, если есть
            if 'cost' in action_card:
                costs = []
                for resource, amount in action_card['cost'].items():
                    costs.append(f"{amount} {resource}")
                print(f"💰 Стоимость: {', '.join(costs)}")
            
            # Показываем когда можно играть
            when_to_play = action_card.get('when_to_play', 'anytime')
            if when_to_play == 'start_of_turn':
                print("⏰ Можно сыграть: в начале хода")
            elif when_to_play == 'anytime':
                print("⏰ Можно сыграть: в любое время")
            
            player.add_action_card(action_card)
            print(f"🎴 Предмет добавлен в руку (всего предметов: {len(player.action_cards)})")
        
        input("📜 Нажмите Enter для продолжения...")

    def is_global_event_card(self, card):
        """Определяет, является ли карта глобальным событием"""
        # Карты с conditions (условиями для групп игроков) - это события для всех
        if 'conditions' in card and 'character_id' in card.get('conditions', {}):
            return True
        
        # Карты с типом instant И без cost - это события для всех
        if card.get('type') == 'instant' and 'cost' not in card:
            return True
        
        # ВСЕ остальные карты - это личные предметы (включая карты с cost, utility, interference и т.д.)
        return False

    def apply_global_event_with_reactions(self, event_card):
        """Применяет событие для всех с возможностью реакций"""
        print(f"\n🌍 ГЛОБАЛЬНОЕ СОБЫТИЕ: {event_card['name']}")
        print(f"📝 {event_card['description']}")
        
        # Собираем всех игроков, которые могут реагировать
        reactive_players = []
        for target_player in self.players:
            if not target_player.is_eliminated:
                reactive_players.append(target_player)
        
        # Фаза реакций - каждый игрок может использовать защитные карты
        protected_players = set()
        
        for reactive_player in reactive_players:
            # Ищем защитные карты в руке игрока
            defensive_cards = [card for card in reactive_player.action_cards 
                             if card.get('type') == 'defensive']
            
            if defensive_cards:
                if reactive_player == self.human_player.player:
                    # Человеческий игрок
                    print(f"\n🛡️ {reactive_player.name}, у вас есть защитные карты!")
                    for i, card in enumerate(defensive_cards):
                        print(f"{i+1}. {card['name']} - {card['description']}")
                    
                    print("0. Не использовать защиту")
                    choice = input("Выберите карту для защиты (0-{0}): ".format(len(defensive_cards)))
                    
                    try:
                        choice_idx = int(choice)
                        if 1 <= choice_idx <= len(defensive_cards):
                            defense_card = defensive_cards[choice_idx - 1]
                            print(f"🛡️ {reactive_player.name} использует {defense_card['name']}!")
                            
                            # Применяем защитный эффект
                            self.apply_card_effect(reactive_player, defense_card, 'action')
                            reactive_player.action_cards.remove(defense_card)
                            protected_players.add(reactive_player)
                    except (ValueError, IndexError):
                        print("🚫 Неверный выбор, защита не применена")
                
                else:
                    # AI игрок
                    # AI решает использовать ли защиту
                    if self.should_ai_use_defense(reactive_player, event_card, defensive_cards):
                        defense_card = defensive_cards[0]  # Берем первую доступную
                        print(f"🛡️ {reactive_player.name} использует {defense_card['name']}!")
                        
                        # Применяем защитный эффект
                        self.apply_card_effect(reactive_player, defense_card, 'action')
                        reactive_player.action_cards.remove(defense_card)
                        protected_players.add(reactive_player)
        
        # Применяем событие ко всем незащищенным игрокам
        print(f"\n⚡ Применяем эффект события...")
        for target_player in reactive_players:
            if target_player in protected_players:
                print(f"🛡️ {target_player.name} защищен от эффекта!")
            else:
                print(f"🎯 Эффект на {target_player.name}")
                self.apply_card_effect(target_player, event_card, 'event')

    def should_ai_use_defense(self, ai_player, event_card, defensive_cards):
        """Определяет, должен ли AI использовать защиту"""
        # Простая логика: используем защиту если событие наносит урон
        event_effects = event_card.get('effects', {})
        
        # Если событие отнимает деньги, нервы или наносит другой урон
        if (event_effects.get('money', 0) < 0 or 
            event_effects.get('nerves', 0) < 0 or
            event_effects.get('document_level', 0) < 0):
            return True
        
        # Если у AI критически мало ресурсов, защищаемся от любых эффектов
        if ai_player.money < 10 or ai_player.nerves < 5:
            return True
            
        return False
    
    def take_turn(self, player):
        """Переопределяем метод для разделения логики человека и AI"""
        if player == self.human_player.player:
            self.play_human_turn(player)
        else:
            self.play_ai_turn(player)
    
    def run(self):
        """Основной цикл игры"""
        self.setup_game()
        
        max_turns = len(self.players) * 15
        lap_frequency = max(4, min(6, self.board.size // (len(self.players) * 2)))
        
        while self.turn < max_turns and not self.game_over:
            # Отображение состояния
            self.display_game_state()
            
            # Обработка круга (выплата зарплаты)
            if self.turn > 0 and self.turn % lap_frequency == 0:
                print(f"\n💰 КОНЕЦ КРУГА! Все получают зарплату и документы!")
                self.handle_lap_completion()
            
            # Ход каждого игрока
            for player in self.players:
                if self.game_over:
                    break
                
                if player.is_eliminated:
                    continue
                
                self.take_turn(player)
                
                if self.game_over:
                    break
            
            self.turn += 1
        
        # Результаты игры
        self.display_results()
    
    def display_results(self):
        """Отображение результатов игры"""
        print("\n" + "🎉" * 20)
        print("🏁 ИГРА ЗАВЕРШЕНА!")
        print("🎉" * 20)
        
        if self.winner:
            if self.winner == self.human_player.player:
                print(f"\n🎊 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ! 🎊")
            else:
                print(f"\n🤖 Победил AI: {self.winner.name}")
            
            print(f"🎯 Цель: {self.winner.win_condition['description']}")
        else:
            print(f"\n⏰ Игра завершена по времени (лимит {self.turn} ходов)")
        
        print(f"\n📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 50)
        
        for player in self.players:
            is_human = player == self.human_player.player
            prefix = "🧑 ВЫ" if is_human else "🤖 AI"
            status = "🏆 ПОБЕДИТЕЛЬ" if player == self.winner else ("💀 Исключен" if player.is_eliminated else "🎮 Играл")
            
            print(f"\n{prefix}: {player.name} - {status}")
            print(f"   💰 Итого денег: {player.money}")
            print(f"   🧠 Итого нервов: {player.nerves}")
            print(f"   📄 Уровень документов: {player.document_level}")
            print(f"   🗣️ Уровень языка: {player.language_level}")
            
            if player.win_condition:
                print(f"   🎯 Цель: {player.win_condition['description']}")


def main():
    """Главная функция"""
    try:
        game = InteractiveGame()
        game.run()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
