import math

class Statistics:
    """Collects and holds data from all simulation runs."""
    def __init__(self):
        self.games_played = 0
        self.total_turns = 0
        self.game_durations = []  # Store individual game durations for stats
        self.wins_by_character = {}
        self.wins_by_goal = {}
        self.eliminations_by_character = {}
        self.elimination_turns_by_character = {}
        self.goal_assignments = {}
        self.final_states = []
        self.no_winner_due_to_time_limit = 0

    def record_game(self, game):
        """Records the final state of a completed game."""
        self.games_played += 1
        self.total_turns += game.turn
        self.game_durations.append(game.turn)  # Store individual duration

        winner = game.winner
        if winner:
            self.wins_by_character[winner.id] = self.wins_by_character.get(winner.id, 0) + 1
            self.wins_by_goal[winner.win_condition['key']] = self.wins_by_goal.get(winner.win_condition['key'], 0) + 1
        elif getattr(game, 'end_reason', None) == 'time_limit':
            self.no_winner_due_to_time_limit += 1

        for player in game.players:
            # Record goal assignment for this player's character
            char_id = player.id
            goal_key = player.win_condition['key']
            if char_id not in self.goal_assignments:
                self.goal_assignments[char_id] = {}
            self.goal_assignments[char_id][goal_key] = self.goal_assignments[char_id].get(goal_key, 0) + 1

            self.final_states.append({
                'character': player.id,
                'money': player.money,
                'nerves': player.nerves,
                'doc_level': player.document_level,
                'was_eliminated': player.is_eliminated,
                'was_winner': player == winner
            })
            if player.is_eliminated:
                self.eliminations_by_character[player.id] = self.eliminations_by_character.get(player.id, 0) + 1
                if player.eliminated_on_turn is not None:
                    turns = self.elimination_turns_by_character.get(player.id, [])
                    turns.append(player.eliminated_on_turn)
                    self.elimination_turns_by_character[player.id] = turns

    def _calculate_statistics(self, values):
        """Calculate mean, std dev, and 95% confidence interval for a list of values."""
        if not values or len(values) == 0:
            return {
                'mean': 0,
                'std_dev': 0,
                'count': 0,
                'confidence_interval_95': {'lower': 0, 'upper': 0}
            }
        
        n = len(values)
        mean = sum(values) / n
        
        # Calculate standard deviation
        if n > 1:
            variance = sum((x - mean) ** 2 for x in values) / (n - 1)
            std_dev = math.sqrt(variance)
            
            # Calculate 95% confidence interval using t-distribution approximation
            # For n >= 30, t-value ≈ 1.96; for smaller n, use approximation
            if n >= 30:
                t_value = 1.96
            elif n >= 10:
                t_value = 2.26  # Rough approximation for smaller samples
            else:
                t_value = 3.18  # Very conservative for very small samples
                
            margin_of_error = t_value * (std_dev / math.sqrt(n))
            ci_lower = mean - margin_of_error
            ci_upper = mean + margin_of_error
        else:
            std_dev = 0
            ci_lower = ci_upper = mean
            
        return {
            'mean': round(mean, 2),
            'std_dev': round(std_dev, 2),
            'count': n,
            'confidence_interval_95': {
                'lower': round(ci_lower, 2),
                'upper': round(ci_upper, 2)
            }
        }
    
    def _calculate_win_rate_statistics(self, character_id):
        """Calculate win rate statistics for a character."""
        # Find all games this character played
        character_games = [state for state in self.final_states if state['character'] == character_id]
        total_games = len(character_games)
        wins = sum(1 for state in character_games if state['was_winner'])
        
        if total_games == 0:
            return {
                'win_rate': 0,
                'win_rate_std_dev': 0,
                'games_played': 0,
                'confidence_interval_95': {'lower': 0, 'upper': 0}
            }
        
        win_rate = wins / total_games
        
        # For binomial distribution (win/loss), std dev = sqrt(p(1-p)/n)
        if total_games > 1:
            win_rate_std_dev = math.sqrt(win_rate * (1 - win_rate) / total_games)
            
            # 95% confidence interval for proportion
            margin_of_error = 1.96 * win_rate_std_dev
            ci_lower = max(0, win_rate - margin_of_error)
            ci_upper = min(1, win_rate + margin_of_error)
        else:
            win_rate_std_dev = 0
            ci_lower = ci_upper = win_rate
            
        return {
            'win_rate': round(win_rate, 3),
            'win_rate_std_dev': round(win_rate_std_dev, 3),
            'games_played': total_games,
            'confidence_interval_95': {
                'lower': round(ci_lower, 3),
                'upper': round(ci_upper, 3)
            }
        }

    def get_summary(self):
        """Returns a dictionary with the aggregated statistics."""
        # Calculate game duration statistics
        duration_stats = self._calculate_statistics(self.game_durations)
        
        # Build elimination stats with enhanced statistics
        elimination_stats = {}
        for character_id, count in self.eliminations_by_character.items():
            turns = self.elimination_turns_by_character.get(character_id, [])
            elimination_turn_stats = self._calculate_statistics(turns)
            elimination_stats[character_id] = {
                'count': count,
                'average_turn': elimination_turn_stats['mean'],
                'std_dev': elimination_turn_stats['std_dev'],
                'confidence_interval_95': elimination_turn_stats['confidence_interval_95']
            }
        
        # Calculate win rate statistics for each character
        all_characters = set(state['character'] for state in self.final_states)
        win_rate_stats = {}
        for character_id in all_characters:
            win_rate_stats[character_id] = self._calculate_win_rate_statistics(character_id)
            
        # Calculate final resource statistics by character
        resource_stats = {}
        for character_id in all_characters:
            character_states = [state for state in self.final_states if state['character'] == character_id]
            
            money_values = [state['money'] for state in character_states]
            nerves_values = [state['nerves'] for state in character_states]
            doc_level_values = [state['doc_level'] for state in character_states]
            
            resource_stats[character_id] = {
                'final_money': self._calculate_statistics(money_values),
                'final_nerves': self._calculate_statistics(nerves_values),
                'final_doc_level': self._calculate_statistics(doc_level_values)
            }

        summary = {
            "total_simulations": self.games_played,
            "game_duration_statistics": duration_stats,
            "win_rate_statistics": win_rate_stats,
            "resource_statistics": resource_stats,
            "win_rate_by_character": self.wins_by_character,
            "win_rate_by_goal": self.wins_by_goal,
            "goal_assignments_by_character": self.goal_assignments,
            "elimination_rate_by_character": elimination_stats,
            "no_winner_due_to_time_limit": self.no_winner_due_to_time_limit,
            # Keep legacy fields for compatibility
            "average_game_duration_turns": duration_stats['mean']
        }
        return summary


