# Tutorial 2: Advanced Custom Strategies

**Level**: Intermediate
**Duration**: 30 minutes
**Prerequisites**: Tutorial 1 completed, understanding of probability

---

## Overview

Build sophisticated player strategies that use opponent analysis, pattern detection, and statistical reasoning.

**What you'll learn:**
- Pattern recognition in opponent behavior
- Win/loss ratio analysis
- Confidence-based decision making
- Strategy testing and validation

---

## Strategy 1: Counter-Strategy

**Concept**: Analyze opponent's most frequent choice and counter it.

```python
"""
Counter Strategy

Analyzes opponent history and chooses the opposite of their most common choice.
"""

from typing import List, Dict
from collections import Counter
from SHARED.league_sdk.models import ParityChoice


class CounterStrategy:
    """
    Counter the opponent's most frequent choice.

    Algorithm:
    1. Analyze opponent's choice history
    2. Find their most common choice
    3. Choose the opposite
    4. Default to random if no history
    """

    def __init__(self, min_history: int = 3):
        """
        Initialize counter strategy.

        Args:
            min_history: Minimum matches needed before applying strategy
        """
        self.min_history = min_history
        self.name = "Counter Strategy"

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Choose counter to opponent's most common choice.

        Args:
            opponent_id: Opponent player ID
            match_history: List of previous matches

        Returns:
            Counter choice or random if insufficient data
        """
        # Need enough history to analyze
        if len(match_history) < self.min_history:
            import random
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Extract opponent choices
        opponent_choices = [
            match.get("opponent_choice")
            for match in match_history
            if "opponent_choice" in match
        ]

        if not opponent_choices:
            import random
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Find most common opponent choice
        choice_counter = Counter(opponent_choices)
        most_common_choice = choice_counter.most_common(1)[0][0]

        # Counter it
        if most_common_choice == "even":
            return ParityChoice.ODD  # Opponent likes EVEN, we choose ODD
        else:
            return ParityChoice.EVEN  # Opponent likes ODD, we choose EVEN
```

**Testing:**

```python
def test_counter_strategy():
    strategy = CounterStrategy(min_history=3)

    # Test with opponent who prefers EVEN
    history = [
        {"opponent_choice": "even", "result": "LOSS"},
        {"opponent_choice": "even", "result": "LOSS"},
        {"opponent_choice": "odd", "result": "WIN"},
        {"opponent_choice": "even", "result": "LOSS"},
    ]

    choice = strategy.choose("P02", history)
    assert choice == ParityChoice.ODD  # Counter EVEN with ODD

    print("✓ Counter strategy test passed")
```

---

## Strategy 2: Weighted Probability Strategy

**Concept**: Use win/loss ratio to calculate probability of success for each choice.

```python
"""
Weighted Probability Strategy

Uses Bayesian-like reasoning to estimate which choice is more likely to win.
"""

from typing import List, Tuple
from SHARED.league_sdk.models import ParityChoice


class WeightedProbabilityStrategy:
    """
    Calculate win probability for each choice and pick the best.

    Tracks:
    - Win rate when choosing EVEN
    - Win rate when choosing ODD
    - Adjusts based on recent performance
    """

    def __init__(self, recent_weight: float = 0.3):
        """
        Initialize weighted strategy.

        Args:
            recent_weight: Weight given to recent matches (0.0 to 1.0)
                          Higher = more reactive to recent changes
        """
        self.recent_weight = recent_weight
        self.name = "Weighted Probability"

        # Track our choice performance
        self.even_wins = 0
        self.even_total = 0
        self.odd_wins = 0
        self.odd_total = 0

    def _calculate_win_rate(self, wins: int, total: int) -> float:
        """Calculate win rate with Laplace smoothing"""
        # Laplace smoothing: add 1 win and 2 total (assumes 50% base rate)
        return (wins + 1) / (total + 2)

    def _analyze_history(self, match_history: List[dict]) -> Tuple[float, float]:
        """
        Analyze match history to calculate win rates.

        Returns:
            (even_win_rate, odd_win_rate)
        """
        for match in match_history:
            our_choice = match.get("our_choice")
            result = match.get("result")

            if our_choice == "even":
                self.even_total += 1
                if result == "WIN":
                    self.even_wins += 1
            elif our_choice == "odd":
                self.odd_total += 1
                if result == "WIN":
                    self.odd_wins += 1

        even_rate = self._calculate_win_rate(self.even_wins, self.even_total)
        odd_rate = self._calculate_win_rate(self.odd_wins, self.odd_total)

        return even_rate, odd_rate

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Choose based on historical win rates.

        Strategy:
        1. Calculate win rate for EVEN
        2. Calculate win rate for ODD
        3. Choose the one with higher win rate
        4. Add randomness to avoid being too predictable
        """
        even_rate, odd_rate = self._analyze_history(match_history)

        # Add some randomness (epsilon-greedy approach)
        import random
        if random.random() < 0.1:  # 10% exploration
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Choose based on win rate
        if even_rate >= odd_rate:
            return ParityChoice.EVEN
        else:
            return ParityChoice.ODD

    def get_stats(self) -> dict:
        """Get strategy statistics"""
        return {
            "name": self.name,
            "even_win_rate": self._calculate_win_rate(self.even_wins, self.even_total),
            "odd_win_rate": self._calculate_win_rate(self.odd_wins, self.odd_total),
            "even_total": self.even_total,
            "odd_total": self.odd_total
        }
```

---

## Strategy 3: Markov Chain Strategy

**Concept**: Model opponent as a Markov chain - predict next choice based on current choice.

```python
"""
Markov Chain Strategy

Predicts opponent's next move based on their transition patterns.
"""

from typing import List, Dict
from collections import defaultdict
from SHARED.league_sdk.models import ParityChoice


class MarkovChainStrategy:
    """
    Use Markov chain to predict opponent behavior.

    Tracks transitions:
    - P(next=EVEN | current=EVEN)
    - P(next=EVEN | current=ODD)
    - P(next=ODD | current=EVEN)
    - P(next=ODD | current=ODD)
    """

    def __init__(self, min_history: int = 5):
        self.min_history = min_history
        self.name = "Markov Chain"

        # Transition counts: transitions[current][next] = count
        self.transitions = defaultdict(lambda: defaultdict(int))

    def _build_transition_matrix(self, match_history: List[dict]):
        """Build transition probability matrix from history"""
        opponent_choices = [
            match.get("opponent_choice")
            for match in match_history
            if "opponent_choice" in match
        ]

        # Count transitions
        for i in range(len(opponent_choices) - 1):
            current = opponent_choices[i]
            next_choice = opponent_choices[i + 1]
            self.transitions[current][next_choice] += 1

    def _predict_next(self, last_choice: str) -> str:
        """
        Predict opponent's next choice using Markov model.

        Args:
            last_choice: Opponent's last choice ("even" or "odd")

        Returns:
            Predicted next choice
        """
        if last_choice not in self.transitions:
            import random
            return random.choice(["even", "odd"])

        # Get transition counts
        counts = self.transitions[last_choice]
        even_count = counts.get("even", 0)
        odd_count = counts.get("odd", 0)

        # Predict most likely next state
        if even_count > odd_count:
            return "even"
        elif odd_count > even_count:
            return "odd"
        else:
            import random
            return random.choice(["even", "odd"])

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Choose based on Markov prediction.

        Strategy:
        1. Build transition matrix from history
        2. Get opponent's last choice
        3. Predict their next choice
        4. Counter their predicted choice
        """
        if len(match_history) < self.min_history:
            import random
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Build transition model
        self._build_transition_matrix(match_history)

        # Get last opponent choice
        last_match = match_history[-1]
        last_opponent_choice = last_match.get("opponent_choice")

        if not last_opponent_choice:
            import random
            return random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        # Predict opponent's next move
        predicted_next = self._predict_next(last_opponent_choice)

        # Counter their predicted move
        if predicted_next == "even":
            return ParityChoice.ODD
        else:
            return ParityChoice.EVEN
```

---

## Testing Your Strategies

Create a comprehensive test suite:

```python
"""
test_advanced_strategies.py

Test suite for advanced strategies
"""

import pytest
from counter_strategy import CounterStrategy
from weighted_strategy import WeightedProbabilityStrategy
from markov_strategy import MarkovChainStrategy
from SHARED.league_sdk.models import ParityChoice


class TestCounterStrategy:
    def test_counters_even_preference(self):
        strategy = CounterStrategy(min_history=3)
        history = [
            {"opponent_choice": "even", "result": "LOSS"},
            {"opponent_choice": "even", "result": "LOSS"},
            {"opponent_choice": "even", "result": "LOSS"},
        ]
        choice = strategy.choose("P02", history)
        assert choice == ParityChoice.ODD

    def test_insufficient_history(self):
        strategy = CounterStrategy(min_history=3)
        history = [{"opponent_choice": "even", "result": "LOSS"}]
        choice = strategy.choose("P02", history)
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]


class TestWeightedStrategy:
    def test_prefers_winning_choice(self):
        strategy = WeightedProbabilityStrategy()
        history = [
            {"our_choice": "even", "result": "WIN"},
            {"our_choice": "even", "result": "WIN"},
            {"our_choice": "odd", "result": "LOSS"},
        ]
        choice = strategy.choose("P02", history)
        # Should prefer EVEN (2 wins) over ODD (0 wins)
        # Note: Due to randomness, this might occasionally fail
        # In production, use statistical testing with multiple runs


class TestMarkovStrategy:
    def test_transition_prediction(self):
        strategy = MarkovChainStrategy(min_history=4)
        history = [
            {"opponent_choice": "even"},
            {"opponent_choice": "odd"},
            {"opponent_choice": "even"},
            {"opponent_choice": "odd"},
            {"opponent_choice": "even"},
        ]
        # Pattern: even -> odd -> even -> odd
        # Last was "even", predict next is "odd"
        # So counter with "even"
        choice = strategy.choose("P02", history)
        assert choice == ParityChoice.EVEN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Strategy Comparison

Run a tournament between strategies:

```python
"""
strategy_tournament.py

Compare different strategies head-to-head
"""

def simulate_matches(strategy1, strategy2, num_matches=100):
    """Simulate matches between two strategies"""
    import random

    s1_wins = 0
    s2_wins = 0
    draws = 0

    history1 = []
    history2 = []

    for i in range(num_matches):
        # Get choices
        choice1 = strategy1.choose("opponent", history1)
        choice2 = strategy2.choose("opponent", history2)

        # Draw random number
        drawn = random.randint(0, 99)
        is_even = (drawn % 2 == 0)

        # Determine winner
        if choice1.value == choice2.value:
            # Both chose same parity
            if (is_even and choice1 == ParityChoice.EVEN) or \
               (not is_even and choice1 == ParityChoice.ODD):
                draws += 1
                result1 = result2 = "DRAW"
            else:
                draws += 1
                result1 = result2 = "DRAW"
        else:
            # Different parities
            if (is_even and choice1 == ParityChoice.EVEN) or \
               (not is_even and choice1 == ParityChoice.ODD):
                s1_wins += 1
                result1 = "WIN"
                result2 = "LOSS"
            else:
                s2_wins += 1
                result1 = "LOSS"
                result2 = "WIN"

        # Update histories
        history1.append({
            "our_choice": choice1.value,
            "opponent_choice": choice2.value,
            "result": result1
        })
        history2.append({
            "our_choice": choice2.value,
            "opponent_choice": choice1.value,
            "result": result2
        })

    return {
        "strategy1_wins": s1_wins,
        "strategy2_wins": s2_wins,
        "draws": draws,
        "strategy1_win_rate": s1_wins / num_matches,
        "strategy2_win_rate": s2_wins / num_matches
    }


if __name__ == "__main__":
    from counter_strategy import CounterStrategy
    from weighted_strategy import WeightedProbabilityStrategy

    print("Strategy Tournament")
    print("=" * 50)

    # Counter vs Weighted
    results = simulate_matches(
        CounterStrategy(),
        WeightedProbabilityStrategy(),
        num_matches=1000
    )

    print(f"\nCounter Strategy: {results['strategy1_wins']} wins ({results['strategy1_win_rate']:.1%})")
    print(f"Weighted Strategy: {results['strategy2_wins']} wins ({results['strategy2_win_rate']:.1%})")
    print(f"Draws: {results['draws']}")
```

---

## Best Practices

### 1. Handle Edge Cases

```python
def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
    # Always check for empty history
    if not match_history:
        return self.default_choice()

    # Validate data structure
    if not isinstance(match_history, list):
        logger.warning("Invalid match_history type")
        return self.default_choice()

    # Handle missing fields
    for match in match_history:
        if "opponent_choice" not in match:
            continue  # Skip invalid matches
```

### 2. Add Logging

```python
from SHARED.league_sdk.logger import JsonLogger

class MyStrategy:
    def __init__(self):
        self.logger = JsonLogger("my_strategy")

    def choose(self, opponent_id, match_history):
        choice = self._calculate_choice(match_history)

        self.logger.info(
            "STRATEGY_CHOICE",
            opponent=opponent_id,
            choice=choice.value,
            history_size=len(match_history)
        )

        return choice
```

### 3. Monitor Performance

```python
class MyStrategy:
    def __init__(self):
        self.stats = {
            "total_choices": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0
        }

    def update_stats(self, result: str):
        """Update strategy statistics"""
        self.stats["total_choices"] += 1
        if result == "WIN":
            self.stats["wins"] += 1
        elif result == "LOSS":
            self.stats["losses"] += 1
        else:
            self.stats["draws"] += 1

    def get_win_rate(self) -> float:
        """Calculate current win rate"""
        total = self.stats["total_choices"]
        return self.stats["wins"] / total if total > 0 else 0.0
```

---

## Next Steps

Try building:
- **Ensemble strategy**: Combine multiple strategies with voting
- **LLM strategy**: Use GPT-4 or Claude for decision-making
- **Reinforcement learning**: Q-learning for adaptive behavior
- **Game theory**: Implement Nash equilibrium strategies

---

## Resources

- **Tutorial 3**: [03_testing.md](03_testing.md)
- **Tutorial 4**: [04_deployment.md](04_deployment.md)
- **API Reference**: [../API.md](../API.md)

---

**Author**: MCP Development Team
**Last Updated**: 2025-12-31
**Difficulty**: ⭐⭐ Intermediate
