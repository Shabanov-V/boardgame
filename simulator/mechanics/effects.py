class EffectManager:
    """Manages application of card effects to players."""
    
    @staticmethod
    def apply_effects(player, effects, event_manager=None):
        """Apply a dictionary of effects to a player."""
        for key, value in effects.items():
            if key == 'nerves':
                player.nerves = max(1, min(10, player.nerves + value))
            elif key == 'money':
                if value > 2 and event_manager:
                    # Create money gain event for values > 2
                    event = event_manager.create_event(
                        "money_gain",
                        player,
                        {"money": value},
                        f"{player.name} gains {value} money"
                    )
                    if not event.is_blocked:
                        final_value = event.effects.get("money", value)
                        player.money = max(0, player.money + final_value)
                else:
                    player.money = max(0, player.money + value)
            elif key == 'money_percent':
                # Handle percentage-based money changes
                change = int(player.money * (value / 100))
                if change != 0:
                    if event_manager:
                        event = event_manager.create_event(
                            "money_percent_change",
                            player,
                            {"money": change},
                            f"{player.name} {'gains' if change > 0 else 'loses'} {abs(change)} money ({value}% of current money)"
                        )
                        if not event.is_blocked:
                            final_change = event.effects.get("money", change)
                            player.money = max(0, player.money + final_change)
                    else:
                        player.money = max(0, player.money + change)
            elif key == 'money_divide':
                # Handle dividing money by a value (e.g. divide by 2 = lose half)
                change = -int(player.money * ((value - 1) / value))
                if change != 0:
                    if event_manager:
                        event = event_manager.create_event(
                            "money_divide",
                            player,
                            {"money": change},
                            f"{player.name} loses {abs(change)} money (divided by {value})"
                        )
                        if not event.is_blocked:
                            final_change = event.effects.get("money", change)
                            player.money = max(0, player.money + final_change)
                    else:
                        player.money = max(0, player.money + change)
            elif key == 'documents_cards':
                player.document_cards = max(0, player.document_cards + value)
            elif key == 'language_level_up' and value:
                if player.language_level < 3:
                    player.language_level += 1
            elif key == 'document_level':
                player.document_level = max(0, player.document_level + value)
            elif key == 'language_level':
                player.language_level = max(1, min(3, player.language_level + value))
            elif key == 'housing_cost_modifier':
                if isinstance(value, dict) and 'amount' in value and 'description' in value:
                    player.add_housing_cost_modifier(value['amount'], value['description'])

    @staticmethod
    def apply_bonus(player, bonus_type, value):
        """Apply a temporary bonus to a player."""
        if bonus_type in player.temporary_bonuses:
            player.temporary_bonuses[bonus_type] += value
            print(f"System: {player.name} gained {value} {bonus_type} bonus (total: {player.temporary_bonuses[bonus_type]})")

    @staticmethod
    def apply_immunity(player, immunity_type):
        """Add an immunity to a player."""
        player.immunities.add(immunity_type)
        print(f"System: {player.name} gained immunity to {immunity_type}")

    @staticmethod
    def apply_special_ability(player, ability_type):
        """Add a special ability to a player."""
        player.special_abilities.add(ability_type)
        print(f"System: {player.name} gained special ability: {ability_type}")

    @staticmethod
    def apply_housing_change(player, is_upgrade=True):
        """Handle housing upgrades or downgrades."""
        old_housing = player.housing
        if is_upgrade:
            if player.housing == 'room':
                player.housing = 'apartment'
                player.housing_level = 2
            elif player.housing == 'apartment':
                player.housing = 'mortgage'
                player.housing_level = 3
            print(f"System: {player.name} upgraded housing from {old_housing} to {player.housing}!")
        else:
            if player.housing == 'mortgage':
                player.housing = 'apartment'
                player.housing_level = 2
            elif player.housing == 'apartment':
                player.housing = 'room'
                player.housing_level = 1
            print(f"System: {player.name} downgraded housing from {old_housing} to {player.housing}.")
        
        # Update base housing cost based on new housing type
        housing_rent = player.config['costs']['housing_rent']
        player.base_housing_cost = housing_rent.get(player.housing, 0)

