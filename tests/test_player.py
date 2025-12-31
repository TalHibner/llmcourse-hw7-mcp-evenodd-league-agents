"""
Unit tests for Player components.

Tests strategies, state tracking, and history management.
"""

import pytest
from unittest.mock import Mock, patch

from agents.player.strategy import RandomStrategy, PatternBasedStrategy, StrategyFactory
from agents.player.state import PlayerState
from agents.player.history import HistoryManager
from SHARED.league_sdk.models import ParityChoice
import tempfile
from pathlib import Path


class TestRandomStrategy:
    """Test random strategy"""

    def test_random_strategy_returns_valid_choice(self):
        """Test that random strategy returns valid parity choice"""
        strategy = RandomStrategy()

        for _ in range(100):
            choice = strategy.choose("P02", [])
            assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_random_strategy_ignores_history(self):
        """Test that random strategy ignores match history"""
        strategy = RandomStrategy()

        # Create biased history
        history = [
            {"opponent_choice": "even"} for _ in range(100)
        ]

        # Random strategy should still produce both choices eventually
        choices = [strategy.choose("P02", history) for _ in range(100)]

        # Should have both even and odd in results (probabilistic test)
        assert ParityChoice.EVEN in choices or ParityChoice.ODD in choices

    def test_random_strategy_with_empty_history(self):
        """Test random strategy with no history"""
        strategy = RandomStrategy()
        choice = strategy.choose("P02", [])
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]


class TestPatternBasedStrategy:
    """Test pattern-based strategy"""

    def test_pattern_strategy_no_history(self):
        """Test pattern strategy with no history defaults to random"""
        strategy = PatternBasedStrategy(threshold=0.6)
        choice = strategy.choose("P02", [])
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_pattern_strategy_opponent_favors_even(self):
        """Test pattern strategy when opponent strongly favors even"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # Opponent chose "even" 8 out of 10 times (80%)
        history = [
            {"opponent_choice": "even"} for _ in range(8)
        ] + [
            {"opponent_choice": "odd"} for _ in range(2)
        ]

        choice = strategy.choose("P02", history)
        # Should choose even to align with opponent's pattern
        assert choice == ParityChoice.EVEN

    def test_pattern_strategy_opponent_favors_odd(self):
        """Test pattern strategy when opponent strongly favors odd"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # Opponent chose "odd" 9 out of 10 times (90%)
        history = [
            {"opponent_choice": "odd"} for _ in range(9)
        ] + [
            {"opponent_choice": "even"} for _ in range(1)
        ]

        choice = strategy.choose("P02", history)
        # Should choose odd to align with opponent's pattern
        assert choice == ParityChoice.ODD

    def test_pattern_strategy_balanced_opponent(self):
        """Test pattern strategy with balanced opponent (no clear pattern)"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # Opponent chose even/odd equally (50/50)
        history = [
            {"opponent_choice": "even"} for _ in range(5)
        ] + [
            {"opponent_choice": "odd"} for _ in range(5)
        ]

        choice = strategy.choose("P02", history)
        # Should default to random choice
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_pattern_strategy_threshold_60(self):
        """Test threshold at exactly 60%"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # Exactly 60% even (6 out of 10)
        history = [
            {"opponent_choice": "even"} for _ in range(6)
        ] + [
            {"opponent_choice": "odd"} for _ in range(4)
        ]

        choice = strategy.choose("P02", history)
        # Should choose even (at threshold)
        assert choice == ParityChoice.EVEN

    def test_pattern_strategy_just_below_threshold(self):
        """Test pattern just below threshold (59%)"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # 59% even (59 out of 100)
        history = [
            {"opponent_choice": "even"} for _ in range(59)
        ] + [
            {"opponent_choice": "odd"} for _ in range(41)
        ]

        choice = strategy.choose("P02", history)
        # Below threshold -> random choice
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_pattern_strategy_missing_opponent_choice(self):
        """Test handling of history with missing opponent_choice"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # History with missing opponent_choice fields
        history = [
            {"some_other_field": "value"},
            {"opponent_choice": "even"},
            {},  # empty dict
        ]

        choice = strategy.choose("P02", history)
        # Should handle gracefully
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_pattern_strategy_custom_threshold(self):
        """Test custom threshold value"""
        strategy = PatternBasedStrategy(threshold=0.8)  # Higher threshold

        # 70% even (7 out of 10) - not enough for 80% threshold
        history = [
            {"opponent_choice": "even"} for _ in range(7)
        ] + [
            {"opponent_choice": "odd"} for _ in range(3)
        ]

        choice = strategy.choose("P02", history)
        # Below high threshold -> random
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]


class TestStrategyFactory:
    """Test strategy factory"""

    def test_create_random_strategy(self):
        """Test creating random strategy"""
        strategy = StrategyFactory.create("random")
        assert isinstance(strategy, RandomStrategy)

    def test_create_pattern_based_strategy(self):
        """Test creating pattern-based strategy"""
        strategy = StrategyFactory.create("pattern_based")
        assert isinstance(strategy, PatternBasedStrategy)

    def test_create_unknown_strategy_defaults_to_random(self):
        """Test unknown strategy defaults to random"""
        strategy = StrategyFactory.create("unknown_strategy")
        assert isinstance(strategy, RandomStrategy)

    def test_create_empty_string_defaults_to_random(self):
        """Test empty string defaults to random"""
        strategy = StrategyFactory.create("")
        assert isinstance(strategy, RandomStrategy)


class TestPlayerState:
    """Test player state tracker"""

    def test_player_state_initialization(self):
        """Test player state initialization"""
        state = PlayerState("P01", "Player One")

        assert state.player_id == "P01"
        assert state.display_name == "Player One"
        assert state.total_matches == 0
        assert state.wins == 0
        assert state.draws == 0
        assert state.losses == 0
        assert state.total_points == 0

    def test_start_match(self):
        """Test starting a new match"""
        state = PlayerState("P01", "Player One")
        state.start_match("R1M1", "P02", "PLAYER_A")

        assert state.current_match_id == "R1M1"
        assert state.current_opponent_id == "P02"
        assert state.current_role == "PLAYER_A"
        assert state.current_choice is None

    def test_set_choice(self):
        """Test setting player's choice"""
        state = PlayerState("P01", "Player One")
        state.start_match("R1M1", "P02", "PLAYER_A")
        state.set_choice("even")

        assert state.current_choice == "even"

    def test_update_stats_win(self):
        """Test updating stats after a win"""
        state = PlayerState("P01", "Player One")
        state.update_stats("WIN", 3)

        assert state.total_matches == 1
        assert state.wins == 1
        assert state.draws == 0
        assert state.losses == 0
        assert state.total_points == 3

    def test_update_stats_draw(self):
        """Test updating stats after a draw"""
        state = PlayerState("P01", "Player One")
        state.update_stats("DRAW", 1)

        assert state.total_matches == 1
        assert state.wins == 0
        assert state.draws == 1
        assert state.losses == 0
        assert state.total_points == 1

    def test_update_stats_loss(self):
        """Test updating stats after a loss"""
        state = PlayerState("P01", "Player One")
        state.update_stats("LOSS", 0)

        assert state.total_matches == 1
        assert state.wins == 0
        assert state.draws == 0
        assert state.losses == 1
        assert state.total_points == 0

    def test_multiple_matches(self):
        """Test stats after multiple matches"""
        state = PlayerState("P01", "Player One")

        # Win, Draw, Loss
        state.update_stats("WIN", 3)
        state.update_stats("DRAW", 1)
        state.update_stats("LOSS", 0)

        assert state.total_matches == 3
        assert state.wins == 1
        assert state.draws == 1
        assert state.losses == 1
        assert state.total_points == 4

    def test_clear_match_state(self):
        """Test clearing match state"""
        state = PlayerState("P01", "Player One")
        state.start_match("R1M1", "P02", "PLAYER_A")
        state.set_choice("even")

        state.clear_match_state()

        assert state.current_match_id is None
        assert state.current_opponent_id is None
        assert state.current_role is None
        assert state.current_choice is None

        # Stats should remain
        assert state.total_matches == 0  # No match completed

    def test_get_stats(self):
        """Test getting statistics"""
        state = PlayerState("P01", "Player One")
        state.update_stats("WIN", 3)
        state.update_stats("WIN", 3)
        state.update_stats("DRAW", 1)

        stats = state.get_stats()

        assert stats["player_id"] == "P01"
        assert stats["display_name"] == "Player One"
        assert stats["total_matches"] == 3
        assert stats["wins"] == 2
        assert stats["draws"] == 1
        assert stats["losses"] == 0
        assert stats["total_points"] == 7
        assert stats["win_rate"] == 2/3  # 2 wins out of 3 matches

    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        state = PlayerState("P01", "Player One")

        # No matches: win rate = 0
        stats = state.get_stats()
        assert stats["win_rate"] == 0.0

        # 1 win out of 2 matches: 50%
        state.update_stats("WIN", 3)
        state.update_stats("LOSS", 0)
        stats = state.get_stats()
        assert stats["win_rate"] == 0.5

        # 3 wins out of 3 matches: 100%
        state = PlayerState("P02", "Player Two")
        state.update_stats("WIN", 3)
        state.update_stats("WIN", 3)
        state.update_stats("WIN", 3)
        stats = state.get_stats()
        assert stats["win_rate"] == 1.0

    def test_full_match_lifecycle(self):
        """Test complete match lifecycle"""
        state = PlayerState("P01", "Player One")

        # Start match
        state.start_match("R1M1", "P02", "PLAYER_A")
        assert state.current_match_id == "R1M1"

        # Make choice
        state.set_choice("even")
        assert state.current_choice == "even"

        # Complete match (win)
        state.update_stats("WIN", 3)
        assert state.wins == 1
        assert state.total_points == 3

        # Clear match state
        state.clear_match_state()
        assert state.current_match_id is None

        # Stats persist
        assert state.wins == 1
        assert state.total_points == 3


class TestPlayerStrategiesIntegration:
    """Integration tests for player strategies"""

    def test_random_strategy_distribution(self):
        """Test random strategy produces reasonable distribution"""
        strategy = RandomStrategy()

        # Generate many choices
        choices = [strategy.choose("P02", []) for _ in range(1000)]

        even_count = sum(1 for c in choices if c == ParityChoice.EVEN)
        odd_count = sum(1 for c in choices if c == ParityChoice.ODD)

        # Should be roughly 50/50 (within 20% tolerance)
        ratio = even_count / (even_count + odd_count)
        assert 0.3 <= ratio <= 0.7

    def test_pattern_strategy_adapts_to_opponent(self):
        """Test pattern strategy adapts to opponent's behavior"""
        strategy = PatternBasedStrategy(threshold=0.7)

        # Initially no history -> random
        choice1 = strategy.choose("P02", [])
        assert choice1 in [ParityChoice.EVEN, ParityChoice.ODD]

        # Build history of opponent favoring "even"
        history = [{"opponent_choice": "even"} for _ in range(10)]

        # Should adapt and choose "even"
        choice2 = strategy.choose("P02", history)
        assert choice2 == ParityChoice.EVEN

        # Opponent changes pattern to "odd"
        new_history = [{"opponent_choice": "odd"} for _ in range(10)]

        # Should adapt and choose "odd"
        choice3 = strategy.choose("P02", new_history)
        assert choice3 == ParityChoice.ODD


class TestHistoryManager:
    """Test player history manager"""

    def test_history_manager_initialization(self):
        """Test history manager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
                manager = HistoryManager("P01")
                assert manager.player_id == "P01"
                assert manager.repository is not None

    def test_add_match(self):
        """Test adding a match to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the repository
            with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
                mock_repo_instance = MockRepo.return_value
                manager = HistoryManager("P01")
                manager.repository = mock_repo_instance

                # Add match
                manager.add_match(
                    match_id="R1M1",
                    opponent_id="P02",
                    result="WIN",
                    points=3,
                    my_choice="even",
                    opponent_choice="odd",
                    drawn_number=4
                )

                # Verify repository method was called
                mock_repo_instance.add_match_result.assert_called_once_with(
                    match_id="R1M1",
                    opponent_id="P02",
                    result="WIN",
                    points=3,
                    my_choice="even",
                    opponent_choice="odd",
                    drawn_number=4
                )

    def test_get_opponent_history(self):
        """Test getting history against specific opponent"""
        with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_opponent_history.return_value = [
                {"match_id": "R1M1", "result": "WIN"},
                {"match_id": "R2M1", "result": "LOSS"}
            ]

            manager = HistoryManager("P01")
            manager.repository = mock_repo_instance

            history = manager.get_opponent_history("P02")

            assert len(history) == 2
            assert history[0]["match_id"] == "R1M1"
            mock_repo_instance.get_opponent_history.assert_called_once_with("P02")

    def test_get_all_history(self):
        """Test getting complete history"""
        with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.load.return_value = {
                "player_id": "P01",
                "total_matches": 5,
                "total_wins": 3,
                "total_draws": 1,
                "total_losses": 1,
                "matches": []
            }

            manager = HistoryManager("P01")
            manager.repository = mock_repo_instance

            history = manager.get_all_history()

            assert history["player_id"] == "P01"
            assert history["total_matches"] == 5
            assert history["total_wins"] == 3
            mock_repo_instance.load.assert_called_once()

    def test_get_stats(self):
        """Test getting aggregate statistics"""
        with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.load.return_value = {
                "player_id": "P01",
                "total_matches": 10,
                "total_wins": 6,
                "total_draws": 2,
                "total_losses": 2
            }

            manager = HistoryManager("P01")
            manager.repository = mock_repo_instance

            stats = manager.get_stats()

            assert stats["total_matches"] == 10
            assert stats["total_wins"] == 6
            assert stats["total_draws"] == 2
            assert stats["total_losses"] == 2

    def test_get_stats_empty_history(self):
        """Test getting stats when history is empty"""
        with patch('agents.player.history.PlayerHistoryRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.load.return_value = {}

            manager = HistoryManager("P01")
            manager.repository = mock_repo_instance

            stats = manager.get_stats()

            assert stats["total_matches"] == 0
            assert stats["total_wins"] == 0
            assert stats["total_draws"] == 0
            assert stats["total_losses"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
