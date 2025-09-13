import random

class Deck:
    """Represents a deck of cards."""
    def __init__(self, cards_data):
        self.cards = list(cards_data)
        self.discard_pile = []
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            if not self.discard_pile:
                return None  # Deck is completely empty
            # Reshuffle discard pile into the deck
            self.cards.extend(self.discard_pile)
            self.discard_pile = []
            self.shuffle()
            print("Reshuffled discard pile into deck.")
        return self.cards.pop(0)

    def discard(self, card):
        self.discard_pile.append(card)

