class Statistics:
    """Collects and holds data from all simulation runs."""
    def __init__(self):
        self.games_played = 0
        self.total_turns = 0
        self.wins_by_character = {}
        self.wins_by_goal = {}
        self.eliminations_by_character = {}
        self.elimination_turns_by_character = {}
        self.final_states = []
        self.no_winner_due_to_time_limit = 0

    def record_game(self, game):
        """Records the final state of a completed game."""
        self.games_played += 1
        self.total_turns += game.turn

        winner = game.winner
        if winner:
            self.wins_by_character[winner.id] = self.wins_by_character.get(winner.id, 0) + 1
            self.wins_by_goal[winner.win_condition['key']] = self.wins_by_goal.get(winner.win_condition['key'], 0) + 1
        elif getattr(game, 'end_reason', None) == 'time_limit':
            self.no_winner_due_to_time_limit += 1

        for player in game.players:
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

    def get_summary(self):
        """Returns a dictionary with the aggregated statistics."""
        # Build elimination stats with average turn
        elimination_stats = {}
        for character_id, count in self.eliminations_by_character.items():
            turns = self.elimination_turns_by_character.get(character_id, [])
            avg_turn = round(sum(turns) / len(turns), 2) if turns else 0
            elimination_stats[character_id] = {
                'count': count,
                'average_turn': avg_turn
            }

        summary = {
            "total_simulations": self.games_played,
            "average_game_duration_turns": round(self.total_turns / self.games_played, 2) if self.games_played > 0 else 0,
            "win_rate_by_character": self.wins_by_character,
            "win_rate_by_goal": self.wins_by_goal,
            "elimination_rate_by_character": elimination_stats,
            "no_winner_due_to_time_limit": self.no_winner_due_to_time_limit,
        }
        return summary


