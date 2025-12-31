"""
Unit tests for Referee components.

Tests game logic, match manager, and state machines.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from agents.referee.game_logic import EvenOddGame
from agents.referee.match_manager import MatchState
from SHARED.league_sdk.models import ParityChoice, GameStatus


class TestEvenOddGame:
    """Test Even/Odd game logic"""

    def test_draw_number_in_range(self):
        """Test that drawn numbers are within range"""
        game = EvenOddGame(number_range_min=1, number_range_max=10)

        # Draw multiple numbers and verify range
        for _ in range(100):
            number = game.draw_number()
            assert 1 <= number <= 10

    def test_determine_parity_even(self):
        """Test parity determination for even numbers"""
        game = EvenOddGame()

        assert game.determine_parity(2) == ParityChoice.EVEN
        assert game.determine_parity(4) == ParityChoice.EVEN
        assert game.determine_parity(6) == ParityChoice.EVEN
        assert game.determine_parity(8) == ParityChoice.EVEN
        assert game.determine_parity(10) == ParityChoice.EVEN

    def test_determine_parity_odd(self):
        """Test parity determination for odd numbers"""
        game = EvenOddGame()

        assert game.determine_parity(1) == ParityChoice.ODD
        assert game.determine_parity(3) == ParityChoice.ODD
        assert game.determine_parity(5) == ParityChoice.ODD
        assert game.determine_parity(7) == ParityChoice.ODD
        assert game.determine_parity(9) == ParityChoice.ODD

    def test_winner_player_a_chooses_even(self):
        """Test Player A wins with even choice on even number"""
        game = EvenOddGame()

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=4  # even
        )

        assert result.status == GameStatus.WIN
        assert result.winner_player_id == "P01"
        assert result.drawn_number == 4
        assert result.number_parity == ParityChoice.EVEN
        assert score["P01"] == 3
        assert score["P02"] == 0

    def test_winner_player_b_chooses_odd(self):
        """Test Player B wins with odd choice on odd number"""
        game = EvenOddGame()

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=5  # odd
        )

        assert result.status == GameStatus.WIN
        assert result.winner_player_id == "P02"
        assert result.drawn_number == 5
        assert result.number_parity == ParityChoice.ODD
        assert score["P01"] == 0
        assert score["P02"] == 3

    def test_draw_both_choose_even_on_even(self):
        """Test draw when both choose even and number is even"""
        game = EvenOddGame()

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.EVEN,
            drawn_number=6  # even
        )

        assert result.status == GameStatus.DRAW
        assert result.winner_player_id is None
        assert result.drawn_number == 6
        assert score["P01"] == 1
        assert score["P02"] == 1

    def test_draw_both_choose_odd_on_odd(self):
        """Test draw when both choose odd and number is odd"""
        game = EvenOddGame()

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.ODD, ParityChoice.ODD,
            drawn_number=7  # odd
        )

        assert result.status == GameStatus.DRAW
        assert result.winner_player_id is None
        assert result.drawn_number == 7
        assert score["P01"] == 1
        assert score["P02"] == 1

    def test_draw_both_choose_even_on_odd(self):
        """Test draw when both choose even but number is odd"""
        game = EvenOddGame(draw_on_both_wrong=True)

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.EVEN,
            drawn_number=3  # odd
        )

        assert result.status == GameStatus.DRAW
        assert result.winner_player_id is None
        assert result.drawn_number == 3
        assert result.number_parity == ParityChoice.ODD
        assert score["P01"] == 1
        assert score["P02"] == 1

    def test_draw_both_choose_odd_on_even(self):
        """Test draw when both choose odd but number is even"""
        game = EvenOddGame(draw_on_both_wrong=True)

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.ODD, ParityChoice.ODD,
            drawn_number=2  # even
        )

        assert result.status == GameStatus.DRAW
        assert result.winner_player_id is None
        assert result.drawn_number == 2
        assert result.number_parity == ParityChoice.EVEN
        assert score["P01"] == 1
        assert score["P02"] == 1

    def test_both_wrong_no_points_when_disabled(self):
        """Test both wrong = 0 points when draw_on_both_wrong=False"""
        game = EvenOddGame(draw_on_both_wrong=False)

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.EVEN,
            drawn_number=3  # odd - both wrong
        )

        assert result.status == GameStatus.DRAW
        assert score["P01"] == 0
        assert score["P02"] == 0

    def test_custom_number_range(self):
        """Test custom number range"""
        game = EvenOddGame(number_range_min=100, number_range_max=200)

        # Draw multiple numbers and verify custom range
        for _ in range(50):
            number = game.draw_number()
            assert 100 <= number <= 200

    def test_all_scenarios_coverage(self):
        """Test all possible game scenarios"""
        game = EvenOddGame()

        scenarios = [
            # (player_a_choice, player_b_choice, number, expected_winner, expected_status)
            (ParityChoice.EVEN, ParityChoice.ODD, 2, "P01", GameStatus.WIN),  # A wins
            (ParityChoice.EVEN, ParityChoice.ODD, 3, "P02", GameStatus.WIN),  # B wins
            (ParityChoice.ODD, ParityChoice.EVEN, 5, "P01", GameStatus.WIN),  # A wins
            (ParityChoice.ODD, ParityChoice.EVEN, 6, "P02", GameStatus.WIN),  # B wins
            (ParityChoice.EVEN, ParityChoice.EVEN, 4, None, GameStatus.DRAW),  # Both correct
            (ParityChoice.ODD, ParityChoice.ODD, 7, None, GameStatus.DRAW),  # Both correct
            (ParityChoice.EVEN, ParityChoice.EVEN, 5, None, GameStatus.DRAW),  # Both wrong
            (ParityChoice.ODD, ParityChoice.ODD, 8, None, GameStatus.DRAW),  # Both wrong
        ]

        for choice_a, choice_b, number, expected_winner, expected_status in scenarios:
            result, score = game.determine_winner(
                "P01", "P02", choice_a, choice_b, drawn_number=number
            )
            assert result.status == expected_status
            assert result.winner_player_id == expected_winner


class TestMatchStateMachine:
    """Test match state machine"""

    def test_match_states_enum(self):
        """Test all match states are defined"""
        expected_states = [
            "CREATED",
            "WAITING_FOR_PLAYERS",
            "COLLECTING_CHOICES",
            "DRAWING_NUMBER",
            "FINISHED",
            "CANCELLED",
        ]

        for state in expected_states:
            assert hasattr(MatchState, state)
            assert MatchState[state].value == state

    def test_match_state_transitions(self):
        """Test valid state transitions"""
        # Valid transition sequence
        states = [
            MatchState.CREATED,
            MatchState.WAITING_FOR_PLAYERS,
            MatchState.COLLECTING_CHOICES,
            MatchState.DRAWING_NUMBER,
            MatchState.FINISHED,
        ]

        # Verify all states are different
        assert len(set(states)) == len(states)

        # Verify specific state values
        assert MatchState.CREATED.value == "CREATED"
        assert MatchState.FINISHED.value == "FINISHED"


class TestRefereeGameScenarios:
    """Test complete game scenarios"""

    def test_simple_win_scenario(self):
        """Test a simple win scenario"""
        game = EvenOddGame()

        # Player A chooses even, Player B chooses odd
        # Number is 8 (even) -> Player A wins
        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=8
        )

        assert result.status == GameStatus.WIN
        assert result.winner_player_id == "P01"
        assert result.choices["P01"] == ParityChoice.EVEN
        assert result.choices["P02"] == ParityChoice.ODD
        assert score["P01"] == 3
        assert score["P02"] == 0
        assert "P01 chose 'even'" in result.reason

    def test_simple_draw_scenario(self):
        """Test a simple draw scenario"""
        game = EvenOddGame()

        # Both choose even, number is even -> Draw
        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.EVEN,
            drawn_number=10
        )

        assert result.status == GameStatus.DRAW
        assert result.winner_player_id is None
        assert score["P01"] == 1
        assert score["P02"] == 1
        assert "Both players chose 'even'" in result.reason

    def test_edge_case_number_1(self):
        """Test with minimum number (1 - odd)"""
        game = EvenOddGame(number_range_min=1, number_range_max=10)

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.ODD, ParityChoice.EVEN,
            drawn_number=1
        )

        assert result.status == GameStatus.WIN
        assert result.winner_player_id == "P01"
        assert result.number_parity == ParityChoice.ODD

    def test_edge_case_number_10(self):
        """Test with maximum number (10 - even)"""
        game = EvenOddGame(number_range_min=1, number_range_max=10)

        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=10
        )

        assert result.status == GameStatus.WIN
        assert result.winner_player_id == "P01"
        assert result.number_parity == ParityChoice.EVEN

    def test_multiple_rounds_fairness(self):
        """Test that game logic is deterministic"""
        game = EvenOddGame()

        # Same inputs should produce same outputs
        result1, score1 = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=6
        )

        result2, score2 = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=6
        )

        assert result1.status == result2.status
        assert result1.winner_player_id == result2.winner_player_id
        assert score1 == score2


class TestGameLogicEdgeCases:
    """Test edge cases and error conditions"""

    def test_different_player_ids(self):
        """Test that player IDs are correctly assigned"""
        game = EvenOddGame()

        result, score = game.determine_winner(
            "PLAYER_ALPHA", "PLAYER_BETA",
            ParityChoice.EVEN, ParityChoice.ODD,
            drawn_number=4
        )

        assert result.winner_player_id == "PLAYER_ALPHA"
        assert "PLAYER_ALPHA" in score
        assert "PLAYER_BETA" in score

    def test_parity_determination_boundary(self):
        """Test parity determination at boundaries"""
        game = EvenOddGame()

        # Test 0 (even)
        assert game.determine_parity(0) == ParityChoice.EVEN

        # Test negative numbers
        assert game.determine_parity(-2) == ParityChoice.EVEN
        assert game.determine_parity(-1) == ParityChoice.ODD

        # Test large numbers
        assert game.determine_parity(1000) == ParityChoice.EVEN
        assert game.determine_parity(1001) == ParityChoice.ODD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
