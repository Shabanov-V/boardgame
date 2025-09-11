#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ одной игры VIVA BUREAUCRACIA!
Запускает одну игру с максимально подробными логами на русском языке
"""

import sys
import os
import random
import json
from pathlib import Path

# Добавляем путь к симулятору
sys.path.append(str(Path(__file__).parent / "simulator"))

# Меняем рабочую директорию для корректной загрузки данных
os.chdir(Path(__file__).parent)

from core import Game
from utils import load_game_data

class DetailedGameAnalyzer:
    """Детальный анализатор игрового процесса"""
    
    def __init__(self):
        self.log_entries = []
        self.turn_details = []
        self.trade_history = []
        self.elimination_history = []
        
    def log(self, message, category="INFO"):
        """Добавляет сообщение в лог"""
        log_entry = {
            "category": category,
            "message": message,
            "timestamp": len(self.log_entries)
        }
        self.log_entries.append(log_entry)
        print(f"[{category}] {message}")
        
    def analyze_player_state(self, player):
        """Анализирует состояние игрока"""
        analysis = {
            "имя": player.name,
            "деньги": player.money,
            "нервы": player.nerves,
            "язык": player.language_level,
            "жилье": f"{player.housing} (уровень {player.housing_level})",
            "документы": player.document_level,
            "карт_документов": len(player.document_cards) if hasattr(player, 'document_cards') else 0,
            "карт_действий": len(player.action_cards) if hasattr(player, 'action_cards') else 0,
            "позиция": player.position,
            "цель": player.win_condition['key'],
            "элиминирован": getattr(player, 'is_eliminated', False)
        }
        return analysis
        
    def analyze_turn_decision(self, player, decision_type, details):
        """Анализирует решение игрока"""
        self.log(f"🧠 РЕШЕНИЕ: {player.name} выбрал '{decision_type}' - {details}", "DECISION")
        
    def analyze_card_effect(self, player, card, effect_type):
        """Анализирует эффект карты"""
        self.log(f"🎴 КАРТА: {player.name} использует '{card['name']}' как {effect_type}", "CARD")
        if 'effects' in card:
            effects = []
            for key, value in card['effects'].items():
                if value > 0:
                    effects.append(f"+{value} {key}")
                elif value < 0:
                    effects.append(f"{value} {key}")
                else:
                    effects.append(f"{key}: {value}")
            self.log(f"   ✨ Эффекты: {', '.join(effects)}", "EFFECT")
            
    def analyze_goal_progress(self, player):
        """Анализирует прогресс к цели"""
        goal = player.win_condition
        current_state = self.analyze_player_state(player)
        
        self.log(f"🎯 ПРОГРЕСС К ЦЕЛИ '{goal['key']}' для {player.name}:", "GOAL")
        
        if 'requires' in goal:
            for req, needed in goal['requires'].items():
                if req == 'money':
                    current = current_state['деньги']
                    progress = min(100, (current / needed) * 100)
                    self.log(f"   💰 Деньги: {current}/{needed} ({progress:.1f}%)", "PROGRESS")
                elif req == 'document_level':
                    current = current_state['документы']
                    progress = min(100, (current / needed) * 100) if needed > 0 else 100
                    self.log(f"   📋 Документы: {current}/{needed} ({progress:.1f}%)", "PROGRESS")
                elif req == 'language_level':
                    current = current_state['язык']
                    progress = min(100, (current / needed) * 100) if needed > 0 else 100
                    self.log(f"   🗣️ Язык: {current}/{needed} ({progress:.1f}%)", "PROGRESS")
                elif req == 'nerves':
                    current = current_state['нервы']
                    progress = min(100, (current / needed) * 100) if needed > 0 else 100
                    self.log(f"   😤 Нервы: {current}/{needed} ({progress:.1f}%)", "PROGRESS")
                elif req == 'housing_type':
                    current = current_state['жилье']
                    status = "✅" if needed in current else "❌"
                    self.log(f"   🏠 Жилье: {current} (нужно: {needed}) {status}", "PROGRESS")
                    
    def analyze_trade(self, initiator, partner, offered, requested, successful, was_honest=True):
        """Анализирует торговую сделку"""
        trade_data = {
            "инициатор": initiator.name,
            "партнер": partner.name,
            "предложено": offered,
            "запрошено": requested,
            "успешно": successful,
            "честно": was_honest,
            "ход": len(self.turn_details)
        }
        self.trade_history.append(trade_data)
        
        if successful:
            honesty = "честно" if was_honest else "с обманом"
            self.log(f"🤝 ТОРГОВЛЯ: {initiator.name} ↔ {partner.name} ({honesty})", "TRADE")
            self.log(f"   📤 {initiator.name} отдает: {offered}", "TRADE")
            self.log(f"   📥 {initiator.name} получает: {requested}", "TRADE")
            if not was_honest:
                self.log(f"   😈 ОБМАН! Сделка прошла нечестно", "DECEPTION")
        else:
            self.log(f"❌ ТОРГОВЛЯ ОТКЛОНЕНА: {partner.name} отказался от предложения {initiator.name}", "TRADE")
            
    def analyze_elimination(self, player, reason, turn):
        """Анализирует элиминацию игрока"""
        elim_data = {
            "игрок": player.name,
            "причина": reason,
            "ход": turn,
            "состояние": self.analyze_player_state(player)
        }
        self.elimination_history.append(elim_data)
        self.log(f"💀 ЭЛИМИНАЦИЯ: {player.name} выбыл на ходу {turn} по причине: {reason}", "ELIMINATION")
        
    def run_detailed_game(self):
        """Запускает игру с детальным анализом"""
        self.log("🎮 ЗАПУСК ДЕТАЛЬНОГО АНАЛИЗА ИГРЫ VIVA BUREAUCRACIA!", "START")
        self.log("=" * 80, "START")
        
        # Загружаем данные
        try:
            config_path = Path(__file__).parent / "simulator" / "config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            game_data = load_game_data()
            self.log("✅ Данные игры успешно загружены", "SETUP")
            
        except Exception as e:
            self.log(f"❌ Ошибка загрузки данных: {e}", "ERROR")
            return None
            
        # Создаем игру
        try:
            game = Game(config, game_data)
            self.log(f"🎲 Игра создана с {len(game.players)} игроками", "SETUP")
            
            # Анализируем начальное состояние
            self.log("\n📊 НАЧАЛЬНОЕ СОСТОЯНИЕ ИГРОКОВ:", "SETUP")
            for player in game.players:
                state = self.analyze_player_state(player)
                self.log(f"   👤 {state['имя']}: {state['деньги']}💰 {state['нервы']}😤 {state['язык']}🗣️ {state['жилье']}🏠", "SETUP")
                self.log(f"      🎯 Цель: {player.win_condition['description']}", "SETUP")
                
        except Exception as e:
            self.log(f"❌ Ошибка создания игры: {e}", "ERROR")
            return None
            
        # Запускаем игру с мониторингом
        self.log("\n🚀 НАЧАЛО ИГРЫ!", "GAME")
        self.log("=" * 80, "GAME")
        
        try:
            turn_count = 0
            max_turns = 200  # Предел безопасности
            
            while not game.game_over and turn_count < max_turns:
                turn_count += 1
                self.log(f"\n🎲 ХОД {turn_count}", "TURN")
                self.log("-" * 40, "TURN")
                
                # Сохраняем состояние до хода
                turn_data = {
                    "номер": turn_count,
                    "состояние_до": {p.name: self.analyze_player_state(p) for p in game.players if not getattr(p, 'is_eliminated', False)}
                }
                
                # Выполняем ход
                current_player = game.players[game.current_player_index]
                if not getattr(current_player, 'is_eliminated', False):
                    self.log(f"👤 Ход игрока: {current_player.name}", "TURN")
                    
                    # Анализируем прогресс к цели перед ходом
                    self.analyze_goal_progress(current_player)
                    
                    # Выполняем ход (здесь нужно вызвать метод хода игры)
                    # game.execute_turn(current_player)
                    
                    # Анализируем состояние после хода
                    turn_data["состояние_после"] = {p.name: self.analyze_player_state(p) for p in game.players if not getattr(p, 'is_eliminated', False)}
                    
                self.turn_details.append(turn_data)
                
                # Переходим к следующему игроку
                game.current_player_index = (game.current_player_index + 1) % len(game.players)
                
            # Результат игры
            if game.game_over:
                if hasattr(game, 'winner') and game.winner:
                    self.log(f"🏆 ПОБЕДИТЕЛЬ: {game.winner.name}!", "RESULT")
                    self.log(f"🎯 Цель: {game.winner.win_condition['description']}", "RESULT")
                    final_state = self.analyze_player_state(game.winner)
                    self.log(f"📊 Финальное состояние: {final_state}", "RESULT")
                else:
                    self.log("⏰ Игра завершилась по лимиту времени", "RESULT")
            else:
                self.log("⚠️ Игра остановлена по лимиту ходов", "RESULT")
                
        except Exception as e:
            self.log(f"❌ Ошибка во время игры: {e}", "ERROR")
            import traceback
            self.log(f"🔍 Детали ошибки: {traceback.format_exc()}", "ERROR")
            
        # Генерируем отчет
        self.generate_final_report()
        
        return {
            "логи": self.log_entries,
            "ходы": self.turn_details,
            "торговля": self.trade_history,
            "элиминации": self.elimination_history
        }
        
    def generate_final_report(self):
        """Генерирует финальный отчет"""
        self.log("\n📊 ФИНАЛЬНЫЙ ОТЧЕТ АНАЛИЗА", "REPORT")
        self.log("=" * 80, "REPORT")
        
        self.log(f"🎲 Общее количество ходов: {len(self.turn_details)}", "REPORT")
        self.log(f"🤝 Количество торговых сделок: {len(self.trade_history)}", "REPORT")
        self.log(f"💀 Количество элиминаций: {len(self.elimination_history)}", "REPORT")
        
        if self.trade_history:
            successful_trades = sum(1 for t in self.trade_history if t['успешно'])
            honest_trades = sum(1 for t in self.trade_history if t['успешно'] and t['честно'])
            self.log(f"✅ Успешных сделок: {successful_trades}", "REPORT")
            self.log(f"😇 Честных сделок: {honest_trades}", "REPORT")
            self.log(f"😈 Обманных сделок: {successful_trades - honest_trades}", "REPORT")
            
        if self.elimination_history:
            self.log("💀 Детали элиминаций:", "REPORT")
            for elim in self.elimination_history:
                self.log(f"   {elim['игрок']} (ход {elim['ход']}): {elim['причина']}", "REPORT")
                
        self.log("✅ Анализ завершен!", "REPORT")

def main():
    """Главная функция"""
    print("🎮 VIVA BUREAUCRACIA! - Детальный анализ игры")
    print("=" * 60)
    
    analyzer = DetailedGameAnalyzer()
    result = analyzer.run_detailed_game()
    
    # Сохраняем результат в файл
    if result:
        output_file = Path(__file__).parent / "detailed_game_log.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Детальный лог сохранен в: {output_file}")
    
    return result

if __name__ == "__main__":
    main()
