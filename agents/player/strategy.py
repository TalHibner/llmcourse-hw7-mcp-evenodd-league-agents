"""
Player strategies for choosing parity.

Implements random and pattern-based strategies.
"""

import random
from typing import List, Optional
from SHARED.league_sdk.models import ParityChoice


class RandomStrategy:
    """
    Random strategy.

    Randomly chooses "even" or "odd" with equal probability.
    """

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Make a random choice.

        Args:
            opponent_id: Opponent's player ID
            match_history: History of matches against this opponent

        Returns:
            Parity choice
        """
        return random.choice([ParityChoice.EVEN, ParityChoice.ODD])


class PatternBasedStrategy:
    """
    Pattern-based strategy.

    Analyzes opponent's past choices and adapts accordingly.
    Strategy:
    1. If no history: random choice
    2. If opponent favors even: choose even (bet on number parity alignment)
    3. If opponent favors odd: choose odd
    4. If opponent is balanced: random choice
    """

    def __init__(self, threshold: float = 0.6):
        """
        Initialize pattern-based strategy.

        Args:
            threshold: Threshold for considering a pattern (0.6 = 60%)
        """
        self.threshold = threshold

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Choose based on opponent's patterns.

        Args:
            opponent_id: Opponent's player ID
            match_history: History of matches against this opponent

        Returns:
            Parity choice
        """
        if not match_history:
            # No history: random choice
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Analyze opponent's choices
        opponent_choices = [
            match.get("opponent_choice")
            for match in match_history
            if match.get("opponent_choice")
        ]

        if not opponent_choices:
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Count even vs odd
        even_count = sum(1 for c in opponent_choices if c == "even")
        odd_count = sum(1 for c in opponent_choices if c == "odd")
        total = len(opponent_choices)

        even_ratio = even_count / total if total > 0 else 0.5
        odd_ratio = odd_count / total if total > 0 else 0.5

        # If opponent strongly favors even
        if even_ratio >= self.threshold:
            return ParityChoice.EVEN

        # If opponent strongly favors odd
        if odd_ratio >= self.threshold:
            return ParityChoice.ODD

        # Balanced opponent: random choice
        return random.choice([ParityChoice.EVEN, ParityChoice.ODD])


class StrategyFactory:
    """Factory for creating strategies"""

    @staticmethod
    def create(strategy_name: str) -> object:
        """
        Create strategy instance.

        Args:
            strategy_name: Strategy name ("random" or "pattern_based")

        Returns:
            Strategy instance
        """
        if strategy_name == "random":
            return RandomStrategy()
        elif strategy_name == "pattern_based":
            return PatternBasedStrategy()
        else:
            # Default to random
            return RandomStrategy()
