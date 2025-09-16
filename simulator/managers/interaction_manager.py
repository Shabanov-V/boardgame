from .event_manager import InteractiveEvent
from simulator.analytics import GameAnalytics

class InteractionManager:
    """Manages instant responses and card interactions between players."""
    def __init__(self, players, analytics: GameAnalytics):
        self.players = players
        self.analytics = analytics
        self.pending_event = None

    def announce_event(self, event):
        """Announce an event and allow other players to respond."""
        if not event.can_be_interfered():
            return event

        self.pending_event = event

        # Ask other players for interference
        interference_applied = False
        interfering_player = None
        interference_card = None

        for player in self.players:
            if player == event.acting_player or player.is_eliminated:
                continue

            # Decide interference
            interference = player.ai.decide_interference(event)
            if interference:
                card, cost_paid = interference
                if self._can_pay_cost(player, card) and cost_paid:
                    print(f"\n⚡ INTERFERENCE: {player.name} plays '{card['name']}' against {event.acting_player.name}")
                    self._pay_cost(player, card)
                    interference_applied = True
                    interfering_player = player
                    interference_card = card
                    event.apply_interference(card, player)
                    player.action_cards.remove(card)
                    self.analytics.track_interaction('interferences', player, event.acting_player, card, True)
                    break

        if not interference_applied:
            self.analytics.track_interaction('interferences', event.acting_player, None, None, False)


        # If interference was applied, check for defense
        if interference_applied and not event.is_blocked:
            defense = event.acting_player.ai.decide_defense(event, interference_card)
            if defense:
                defense_card, cost_paid = defense
                if self._can_pay_cost(event.acting_player, defense_card) and cost_paid:
                    self._pay_cost(event.acting_player, defense_card)
                    reflected = event.apply_defense(defense_card, event.acting_player)
                    event.acting_player.action_cards.remove(defense_card)
                    self.analytics.track_interaction('defenses', event.acting_player, interfering_player, defense_card, True)

                    # If reflected, apply interference effects to interfering player
                    if reflected and interfering_player:
                        effects_to_apply = interference_card.get('effects', {})
                        # This part needs a proper EffectManager call
                        if 'target_nerves' in effects_to_apply:
                            interfering_player.nerves = max(1, interfering_player.nerves + effects_to_apply['target_nerves'])
                        if 'target_money' in effects_to_apply:
                            interfering_player.money = max(0, interfering_player.money + effects_to_apply['target_money'])
            else:
                self.analytics.track_interaction('defenses', event.acting_player, interfering_player, None, False)

        self.pending_event = None
        return event
        
    def _can_pay_cost(self, player, card):
        """Check if player can pay the cost of playing a card."""
        cost = card.get('cost', {})
        
        if 'money' in cost and player.money < cost['money']:
            return False
        if 'nerves' in cost and player.nerves <= cost['nerves']:
            return False
            
        return True
    
    def _pay_cost(self, player, card):
        """Make player pay the cost of playing a card."""
        cost = card.get('cost', {})
        
        if 'money' in cost:
            player.money -= cost['money']
        if 'nerves' in cost:
            player.nerves -= cost['nerves']

