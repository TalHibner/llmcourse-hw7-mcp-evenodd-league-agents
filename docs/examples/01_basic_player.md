# Tutorial 1: Creating Your First Player Agent

**Level**: Beginner
**Duration**: 15 minutes
**Prerequisites**: Python 3.10+, basic understanding of classes

---

## Overview

This tutorial walks you through creating a simple player agent that participates in the MCP Even/Odd League. You'll learn:

- How to create a custom player strategy
- How to register with the League Manager
- How to respond to game invitations
- How to make parity choices

---

## Step 1: Understanding the Player Agent

A player agent consists of three main components:

1. **Strategy**: Logic for choosing "even" or "odd"
2. **Handlers**: Methods that respond to messages from referees
3. **Server**: FastAPI server that receives messages

```
┌──────────────────────┐
│   Player Agent       │
│                      │
│  ┌──────────────┐   │
│  │  Strategy    │◄──┼── Makes choices
│  └──────────────┘   │
│                      │
│  ┌──────────────┐   │
│  │  Handlers    │◄──┼── Receives messages
│  └──────────────┘   │
│                      │
│  ┌──────────────┐   │
│  │FastAPI Server│◄──┼── HTTP endpoint
│  └──────────────┘   │
└──────────────────────┘
```

---

## Step 2: Create a Simple Strategy

Create a new file: `my_player_strategy.py`

```python
"""
My First Player Strategy

A simple strategy that always chooses "even".
"""

from typing import List
from SHARED.league_sdk.models import ParityChoice


class AlwaysEvenStrategy:
    """
    A beginner strategy that always chooses EVEN.

    This is the simplest possible strategy - good for learning!
    """

    def __init__(self):
        """Initialize the strategy."""
        self.name = "Always Even"

    def choose(
        self,
        opponent_id: str,
        match_history: List[dict]
    ) -> ParityChoice:
        """
        Make a parity choice.

        Args:
            opponent_id: ID of the opponent (e.g., "P02")
            match_history: List of previous matches against this opponent

        Returns:
            ParityChoice.EVEN (always)

        Example:
            >>> strategy = AlwaysEvenStrategy()
            >>> choice = strategy.choose("P02", [])
            >>> print(choice)
            ParityChoice.EVEN
        """
        # Always return EVEN
        return ParityChoice.EVEN
```

**Why this works:**
- Simple and predictable
- Good for testing
- Easy to understand
- No dependencies on match history

**When to use:**
- Learning the system
- Testing infrastructure
- Baseline comparison

---

## Step 3: Test Your Strategy Locally

Create a test file: `test_my_strategy.py`

```python
import pytest
from my_player_strategy import AlwaysEvenStrategy
from SHARED.league_sdk.models import ParityChoice


def test_always_even_strategy():
    """Test that strategy always returns EVEN"""
    strategy = AlwaysEvenStrategy()

    # Test with no history
    choice = strategy.choose("P02", [])
    assert choice == ParityChoice.EVEN

    # Test with history (should still return EVEN)
    history = [
        {"opponent_choice": "odd", "result": "LOSS"},
        {"opponent_choice": "even", "result": "DRAW"}
    ]
    choice = strategy.choose("P02", history)
    assert choice == ParityChoice.EVEN

    print("✓ All tests passed!")


if __name__ == "__main__":
    test_always_even_strategy()
```

**Run the test:**
```bash
python test_my_strategy.py
```

**Expected output:**
```
✓ All tests passed!
```

---

## Step 4: Integrate with Player Agent

Update `agents/player/strategy.py` to include your strategy:

```python
# Add your import
from my_player_strategy import AlwaysEvenStrategy

# Update the strategy factory
def get_strategy(strategy_name: str):
    """Get strategy instance by name"""
    strategies = {
        "random": RandomStrategy(),
        "pattern": PatternBasedStrategy(),
        "always_even": AlwaysEvenStrategy(),  # Add this line
    }
    return strategies.get(strategy_name, RandomStrategy())
```

---

## Step 5: Start Your Player

Start the player agent with your new strategy:

```bash
# Set environment variables
export PLAYER_ID=P01
export PORT=8101
export STRATEGY=always_even

# Start the player
python -m agents.player.main
```

**Expected output:**
```
INFO: Player starting player_id=P01 port=8101 strategy=always_even
INFO: Player registered with league player_id=P01 auth_token=***REDACTED***
INFO: Uvicorn running on http://localhost:8101 (Press CTRL+C to quit)
```

---

## Step 6: Watch Your Player in Action

In another terminal, start the league:

```bash
python scripts/start_league.py
```

**You should see:**
1. Your player registers with the League Manager
2. Receives round announcements
3. Gets invited to matches
4. Makes choices (always "even")
5. Receives game results

**Sample log output** (`data/logs/agents/P01.log.jsonl`):

```json
{"timestamp": "2025-12-31T20:00:00Z", "level": "INFO", "event": "PLAYER_REGISTERED", "player_id": "P01"}
{"timestamp": "2025-12-31T20:00:05Z", "level": "INFO", "event": "GAME_INVITATION_RECEIVED", "match_id": "R01M01", "opponent": "P02"}
{"timestamp": "2025-12-31T20:00:06Z", "level": "INFO", "event": "PARITY_CHOSEN", "choice": "even"}
{"timestamp": "2025-12-31T20:00:10Z", "level": "INFO", "event": "GAME_RESULT", "result": "WIN", "drawn_number": 4}
```

---

## Step 7: Improve Your Strategy

Now let's make a smarter strategy that adapts to losses:

```python
class AdaptiveStrategy:
    """
    Adaptive strategy that switches after a loss.

    - Starts with EVEN
    - Switches to ODD after a loss
    - Switches back to EVEN after a win
    """

    def __init__(self):
        self.last_choice = ParityChoice.EVEN

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """
        Make an adaptive choice based on previous result.

        Strategy:
        - If no history: choose EVEN
        - If last result was LOSS: switch choice
        - If last result was WIN: keep same choice
        - If last result was DRAW: random
        """
        # No history - start with EVEN
        if not match_history:
            return ParityChoice.EVEN

        # Get last match result
        last_match = match_history[-1]
        last_result = last_match.get("result")

        if last_result == "LOSS":
            # Switch choice after a loss
            self.last_choice = (
                ParityChoice.ODD if self.last_choice == ParityChoice.EVEN
                else ParityChoice.EVEN
            )
        elif last_result == "WIN":
            # Keep same choice after a win
            pass
        else:  # DRAW
            # Random choice after a draw
            import random
            self.last_choice = random.choice([ParityChoice.EVEN, ParityChoice.ODD])

        return self.last_choice
```

---

## Common Issues and Solutions

### Issue 1: "Connection refused"

**Problem**: Player can't connect to League Manager

**Solution**:
```bash
# Make sure League Manager is running first
python -m agents.league_manager.main

# Wait for "League Manager listening on port 8000"
# Then start your player
```

### Issue 2: "Import error"

**Problem**: Can't import `SHARED.league_sdk`

**Solution**:
```bash
# Make sure you're in the project root
cd /path/to/llmcourse-hw7-mcp-evenodd-league-agents

# Activate virtual environment
source venv/bin/activate

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 3: "Strategy not found"

**Problem**: Strategy name doesn't exist

**Solution**:
```python
# Check available strategies in agents/player/strategy.py
AVAILABLE_STRATEGIES = {
    "random": RandomStrategy,
    "pattern": PatternBasedStrategy,
    "always_even": AlwaysEvenStrategy,  # Your custom strategy
}

# Use exact name
export STRATEGY=always_even  # ✓ Correct
export STRATEGY=AlwaysEven   # ✗ Wrong
```

---

## Next Steps

Now that you have a working player, try:

1. **Tutorial 2**: Create a pattern-based strategy that analyzes opponent history
2. **Tutorial 3**: Add logging to your strategy to debug decision-making
3. **Tutorial 4**: Create an LLM-based strategy using GPT-4 or Claude

---

## Complete Example Code

**File**: `agents/player/custom_strategies/always_even.py`

```python
"""Always Even Strategy - Tutorial Example"""

from typing import List
from SHARED.league_sdk.models import ParityChoice


class AlwaysEvenStrategy:
    """Simple strategy that always chooses EVEN"""

    def __init__(self):
        self.name = "Always Even"
        self.choices_made = 0

    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        """Always return EVEN"""
        self.choices_made += 1
        return ParityChoice.EVEN

    def get_stats(self):
        """Get strategy statistics"""
        return {
            "name": self.name,
            "choices_made": self.choices_made
        }
```

---

## Summary

You've learned:
- ✅ How to create a simple player strategy
- ✅ How to test your strategy locally
- ✅ How to integrate with the player agent
- ✅ How to start and run your player
- ✅ How to improve your strategy with adaptive logic

**Congratulations! You've created your first player agent!** 🎉

---

## Resources

- **Next Tutorial**: [02_custom_strategy.md](02_custom_strategy.md)
- **API Reference**: [../API.md](../API.md)
- **Strategy Examples**: `agents/player/strategy.py`
- **Full Documentation**: [../../README.md](../../README.md)

---

**Author**: MCP Development Team
**Last Updated**: 2025-12-31
**Difficulty**: ⭐ Beginner
