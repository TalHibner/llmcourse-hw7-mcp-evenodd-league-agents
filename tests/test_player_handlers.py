"""
Comprehensive tests for player handlers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from agents.player.handlers import PlayerHandlers
from SHARED.league_sdk.models import (
    RoundAnnouncement, GameInvitation, GameJoinAck,
    ChooseParityCall, ChooseParityResponse, GameOver,
    LeagueStandingsUpdate, RoundCompleted, LeagueCompleted,
    ParityChoice, MatchInfo, GameResult, GameStatus, StandingEntry
)


class TestPlayerHandlersComprehensive:
    """Comprehensive tests for PlayerHandlers"""

    def setup_method(self):
        """Setup for each test"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            self.logger = JsonLogger(component="test")

    def test_init(self):
        """Test handler initialization"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        assert handler.player_id == "P01"
        assert handler.display_name == "Test Player"
        assert handler.state is not None
        assert handler.history is not None
        assert handler.strategy is not None

    def test_handle_round_announcement(self):
        """Test round announcement handling"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        announcement = RoundAnnouncement(
            sender="league_manager:LM01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="round1",
            auth_token="",
            league_id="TEST",
            round_id="R01",
            matches=[
                MatchInfo(
                    match_id="R01M01",
                    player_A_id="P01",
                    player_B_id="P02",
                    referee_endpoint="http://localhost:8001/mcp"
                ),
                MatchInfo(
                    match_id="R01M02",
                    player_A_id="P03",
                    player_B_id="P04",
                    referee_endpoint="http://localhost:8001/mcp"
                )
            ]
        )

        result = handler.handle_round_announcement(announcement)
        assert result["status"] == "acknowledged"


    def test_handle_game_over_win(self):
        """Test game over handling - WIN"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        # Setup match state
        handler.state.start_match("R01M01", "P02", "PLAYER_A")
        handler.state.set_choice("even")

        game_over = GameOver(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="",
            match_id="R01M01",
            game_result=GameResult(
                status=GameStatus.WIN,
                winner_player_id="P01",
                drawn_number=4,
                number_parity=ParityChoice.EVEN,
                choices={
                    "P01": ParityChoice.EVEN,
                    "P02": ParityChoice.ODD
                },
                reason="P01 chose EVEN, number 4 is EVEN"
            )
        )

        result = handler.handle_game_over(game_over)
        assert result["status"] == "acknowledged"

        stats = handler.get_stats()
        assert stats["total_matches"] == 1
        assert stats["wins"] == 1
        assert stats["total_points"] == 3

    def test_handle_game_over_draw(self):
        """Test game over handling - DRAW"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        handler.state.start_match("R01M01", "P02", "PLAYER_A")
        handler.state.set_choice("even")

        game_over = GameOver(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="",
            match_id="R01M01",
            game_result=GameResult(
                status=GameStatus.DRAW,
                winner_player_id=None,
                drawn_number=3,
                number_parity=ParityChoice.ODD,
                choices={
                    "P01": ParityChoice.EVEN,
                    "P02": ParityChoice.EVEN
                },
                reason="Both chose EVEN"
            )
        )

        result = handler.handle_game_over(game_over)
        assert result["status"] == "acknowledged"

        stats = handler.get_stats()
        assert stats["total_matches"] == 1
        assert stats["draws"] == 1
        assert stats["total_points"] == 1

    def test_handle_game_over_loss(self):
        """Test game over handling - LOSS"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        handler.state.start_match("R01M01", "P02", "PLAYER_A")
        handler.state.set_choice("odd")

        game_over = GameOver(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="",
            match_id="R01M01",
            game_result=GameResult(
                status=GameStatus.WIN,
                winner_player_id="P02",
                drawn_number=4,
                number_parity=ParityChoice.EVEN,
                choices={
                    "P01": ParityChoice.ODD,
                    "P02": ParityChoice.EVEN
                },
                reason="P02 chose EVEN, number 4 is EVEN"
            )
        )

        result = handler.handle_game_over(game_over)
        assert result["status"] == "acknowledged"

        stats = handler.get_stats()
        assert stats["total_matches"] == 1
        assert stats["losses"] == 1
        assert stats["total_points"] == 0

    def test_handle_standings_update(self):
        """Test standings update handling"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        update = LeagueStandingsUpdate(
            sender="league_manager:LM01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="standings1",
            auth_token="",
            league_id="TEST",
            round_id="R01",
            standings=[
                StandingEntry(
                    rank=1,
                    player_id="P01",
                    display_name="Test Player",
                    points=3,
                    played=1,
                    wins=1,
                    draws=0,
                    losses=0
                ),
                StandingEntry(
                    rank=2,
                    player_id="P02",
                    display_name="Player Two",
                    points=0,
                    played=1,
                    wins=0,
                    draws=0,
                    losses=1
                )
            ]
        )

        result = handler.handle_standings_update(update)
        assert result["status"] == "acknowledged"

    def test_handle_round_completed(self):
        """Test round completed handling"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        completed = RoundCompleted(
            sender="league_manager:LM01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="round_complete",
            auth_token="",
            league_id="TEST",
            round_id="R01",
            completed_matches=["R01M01", "R01M02"],
            next_round_id="R02"
        )

        result = handler.handle_round_completed(completed)
        assert result["status"] == "acknowledged"

    def test_handle_league_completed(self):
        """Test league completed handling"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        completed = LeagueCompleted(
            sender="league_manager:LM01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="league_complete",
            auth_token="",
            league_id="TEST",
            champion=StandingEntry(
                rank=1,
                player_id="P01",
                display_name="Test Player",
                points=9,
                played=3,
                wins=3,
                draws=0,
                losses=0
            ),
            final_standings=[
                StandingEntry(
                    rank=1,
                    player_id="P01",
                    display_name="Test Player",
                    points=9,
                    played=3,
                    wins=3,
                    draws=0,
                    losses=0
                ),
                StandingEntry(
                    rank=2,
                    player_id="P02",
                    display_name="Player Two",
                    points=3,
                    played=3,
                    wins=1,
                    draws=0,
                    losses=2
                )
            ],
            total_rounds=3,
            total_matches=3
        )

        result = handler.handle_league_completed(completed)
        assert result["status"] == "acknowledged"

    def test_get_stats(self):
        """Test get stats"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        stats = handler.get_stats()
        assert stats["total_matches"] == 0
        assert stats["wins"] == 0
        assert stats["draws"] == 0
        assert stats["losses"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
