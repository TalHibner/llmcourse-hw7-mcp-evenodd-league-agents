"""
Async integration tests for league manager handlers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from agents.league_manager.handlers import ResultHandler
from agents.league_manager.standings import StandingsCalculator
from SHARED.league_sdk.models import (
    MatchResultReport, GameResult, GameStatus, ParityChoice, StandingEntry
)


class TestResultHandlerAsync:
    """Async tests for ResultHandler"""

    @pytest.mark.asyncio
    async def test_handle_match_result_full_flow(self):
        """Test full match result handling with standings update and broadcast"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            with patch('SHARED.league_sdk.repositories.StandingsRepository') as MockStandingsRepo:
                with patch('SHARED.league_sdk.repositories.RoundsRepository') as MockRoundsRepo:
                    from SHARED.league_sdk.logger import JsonLogger

                    logger = JsonLogger(component="test")

                    # Mock repositories
                    mock_standings_repo = MockStandingsRepo.return_value
                    mock_rounds_repo = MockRoundsRepo.return_value

                    # Set up current standings
                    current_standings = [
                        StandingEntry(
                            rank=1, player_id="P01", display_name="Player 1",
                            played=0, wins=0, draws=0, losses=0, points=0
                        ),
                        StandingEntry(
                            rank=2, player_id="P02", display_name="Player 2",
                            played=0, wins=0, draws=0, losses=0, points=0
                        ),
                    ]
                    mock_standings_repo.get_standings.return_value = current_standings

                    # Create calculator
                    calculator = StandingsCalculator()

                    # Create handler
                    handler = ResultHandler(
                        league_id="TEST",
                        logger=logger,
                        standings_calculator=calculator,
                        standings_repo=mock_standings_repo,
                        rounds_repo=mock_rounds_repo
                    )

                    # Create match result
                    result = GameResult(
                        status=GameStatus.WIN,
                        winner_player_id="P01",
                        drawn_number=4,
                        number_parity=ParityChoice.EVEN,
                        choices={"P01": ParityChoice.EVEN, "P02": ParityChoice.ODD},
                        reason="P01 wins"
                    )

                    report = MatchResultReport(
                        sender="referee:REF01",
                        timestamp=datetime.now(timezone.utc),
                        conversation_id="R01M01",
                        auth_token="",
                        league_id="TEST",
                        match_id="R01M01",
                        round_id="R01",
                        result=result,
                        score={"P01": 3, "P02": 0}
                    )

                    player_endpoints = {
                        "P01": "http://localhost:8101/mcp",
                        "P02": "http://localhost:8102/mcp"
                    }

                    # Mock MCP client
                    mock_mcp_instance = AsyncMock()
                    mock_mcp_instance.call_tool = AsyncMock(return_value={"status": "ok"})

                    with patch('agents.league_manager.handlers.MCPClient') as MockMCPClient:
                        MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
                        MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

                        # Handle the result
                        await handler.handle_match_result(report, player_endpoints)

                        # Verify standings were updated
                        mock_standings_repo.update_standings.assert_called_once()
                        updated_standings = mock_standings_repo.update_standings.call_args[0][0]

                        # Verify round was marked complete
                        mock_rounds_repo.mark_match_completed.assert_called_once_with("R01", "R01M01")

                        # Verify MCP client was called for each player
                        assert mock_mcp_instance.call_tool.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_match_result_broadcast_failure(self):
        """Test match result handling when broadcast fails"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            with patch('SHARED.league_sdk.repositories.StandingsRepository') as MockStandingsRepo:
                with patch('SHARED.league_sdk.repositories.RoundsRepository') as MockRoundsRepo:
                    from SHARED.league_sdk.logger import JsonLogger

                    logger = JsonLogger(component="test")

                    # Mock repositories
                    mock_standings_repo = MockStandingsRepo.return_value
                    mock_rounds_repo = MockRoundsRepo.return_value

                    current_standings = [
                        StandingEntry(
                            rank=1, player_id="P01", display_name="Player 1",
                            played=0, wins=0, draws=0, losses=0, points=0
                        ),
                    ]
                    mock_standings_repo.get_standings.return_value = current_standings

                    calculator = StandingsCalculator()

                    handler = ResultHandler(
                        league_id="TEST",
                        logger=logger,
                        standings_calculator=calculator,
                        standings_repo=mock_standings_repo,
                        rounds_repo=mock_rounds_repo
                    )

                    result = GameResult(
                        status=GameStatus.DRAW,
                        winner_player_id=None,
                        drawn_number=3,
                        number_parity=ParityChoice.ODD,
                        choices={"P01": ParityChoice.EVEN, "P02": ParityChoice.EVEN},
                        reason="Both chose EVEN"
                    )

                    report = MatchResultReport(
                        sender="referee:REF01",
                        timestamp=datetime.now(timezone.utc),
                        conversation_id="R01M01",
                        auth_token="",
                        league_id="TEST",
                        match_id="R01M01",
                        round_id="R01",
                        result=result,
                        score={"P01": 1, "P02": 1}
                    )

                    player_endpoints = {
                        "P01": "http://localhost:8101/mcp"
                    }

                    # Mock MCP client that fails
                    mock_mcp_instance = AsyncMock()
                    mock_mcp_instance.call_tool = AsyncMock(side_effect=Exception("Network error"))

                    with patch('agents.league_manager.handlers.MCPClient') as MockMCPClient:
                        MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
                        MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

                        # Should not raise exception even if broadcast fails
                        await handler.handle_match_result(report, player_endpoints)

                        # Verify standings were still updated
                        mock_standings_repo.update_standings.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_match_result_gather_fails(self):
        """Test match result handling when asyncio.gather itself fails"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            with patch('SHARED.league_sdk.repositories.StandingsRepository') as MockStandingsRepo:
                with patch('SHARED.league_sdk.repositories.RoundsRepository') as MockRoundsRepo:
                    from SHARED.league_sdk.logger import JsonLogger

                    logger = JsonLogger(component="test")

                    mock_standings_repo = MockStandingsRepo.return_value
                    mock_rounds_repo = MockRoundsRepo.return_value

                    current_standings = [
                        StandingEntry(
                            rank=1, player_id="P01", display_name="Player 1",
                            played=0, wins=0, draws=0, losses=0, points=0
                        ),
                    ]
                    mock_standings_repo.get_standings.return_value = current_standings

                    calculator = StandingsCalculator()

                    handler = ResultHandler(
                        league_id="TEST",
                        logger=logger,
                        standings_calculator=calculator,
                        standings_repo=mock_standings_repo,
                        rounds_repo=mock_rounds_repo
                    )

                    result = GameResult(
                        status=GameStatus.WIN,
                        winner_player_id="P01",
                        drawn_number=4,
                        number_parity=ParityChoice.EVEN,
                        choices={"P01": ParityChoice.EVEN, "P02": ParityChoice.ODD},
                        reason="P01 wins"
                    )

                    report = MatchResultReport(
                        sender="referee:REF01",
                        timestamp=datetime.now(timezone.utc),
                        conversation_id="R01M01",
                        auth_token="",
                        league_id="TEST",
                        match_id="R01M01",
                        round_id="R01",
                        result=result,
                        score={"P01": 3, "P02": 0}
                    )

                    player_endpoints = {
                        "P01": "http://localhost:8101/mcp"
                    }

                    # Mock asyncio.gather to raise an exception
                    import asyncio
                    with patch('asyncio.gather', side_effect=RuntimeError("Gather failed")):
                        with patch('agents.league_manager.handlers.MCPClient') as MockMCPClient:
                            mock_mcp_instance = AsyncMock()
                            MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
                            MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

                            # Should handle exception gracefully
                            await handler.handle_match_result(report, player_endpoints)

                            # Verify standings were still updated
                            mock_standings_repo.update_standings.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
