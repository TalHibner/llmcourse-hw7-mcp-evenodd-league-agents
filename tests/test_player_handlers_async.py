"""
Async integration tests for player handlers.
Tests async methods with proper MCP client mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from agents.player.handlers import PlayerHandlers
from SHARED.league_sdk.models import (
    GameInvitation, ChooseParityCall, ParityChoice
)


class TestPlayerHandlersAsync:
    """Async integration tests for PlayerHandlers"""

    def setup_method(self):
        """Setup for each test"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            self.logger = JsonLogger(component="test")

    @pytest.mark.asyncio
    async def test_handle_game_invitation_full_flow(self):
        """Test full game invitation flow with config and MCP"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        # Mock the config loader
        mock_ref_config = Mock()
        mock_ref_config.referee_id = "REF01"
        mock_ref_config.endpoint = "http://localhost:8001/mcp"

        mock_agents_config = Mock()
        mock_agents_config.referees = [mock_ref_config]

        mock_config_loader = Mock()
        mock_config_loader.load_agents.return_value = mock_agents_config

        # Mock MCPClient
        mock_mcp_instance = AsyncMock()
        mock_mcp_instance.call_tool = AsyncMock(return_value={"status": "ok"})

        invitation = GameInvitation(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="test_token",
            match_id="R01M01",
            opponent_id="P02",
            role_in_match="PLAYER_A"
        )

        with patch('SHARED.league_sdk.config_loader.get_config_loader', return_value=mock_config_loader):
            with patch('agents.player.handlers.MCPClient') as MockMCPClient:
                # Set up the context manager
                MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
                MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

                result = await handler.handle_game_invitation(invitation)

                assert result["status"] == "joined"
                assert handler.state.current_match_id == "R01M01"
                assert handler.state.current_opponent_id == "P02"
                assert handler.state.current_role == "PLAYER_A"

                # Verify MCP client was called
                mock_mcp_instance.call_tool.assert_called_once()
                call_args = mock_mcp_instance.call_tool.call_args
                assert call_args[1]["endpoint"] == "http://localhost:8001/mcp"
                assert call_args[1]["method"] == "receive_game_join_ack"

    @pytest.mark.asyncio
    async def test_handle_parity_call_full_flow(self):
        """Test full parity call flow with strategy and MCP"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        # Set up match state
        handler.state.start_match("R01M01", "P02", "PLAYER_A")
        handler.current_referee_endpoint = "http://localhost:8001/mcp"

        # Mock MCPClient
        mock_mcp_instance = AsyncMock()
        mock_mcp_instance.call_tool = AsyncMock(return_value={"status": "ok"})

        from datetime import timedelta
        deadline = datetime.now(timezone.utc) + timedelta(seconds=30)

        call = ChooseParityCall(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="test_token",
            match_id="R01M01",
            deadline=deadline
        )

        with patch('agents.player.handlers.MCPClient') as MockMCPClient:
            # Set up the context manager
            MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
            MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

            result = await handler.handle_parity_call(call)

            assert result["status"] == "choice_sent"
            assert handler.state.current_choice in ["even", "odd"]

            # Verify MCP client was called
            mock_mcp_instance.call_tool.assert_called_once()
            call_args = mock_mcp_instance.call_tool.call_args
            assert call_args[1]["endpoint"] == "http://localhost:8001/mcp"
            assert call_args[1]["method"] == "receive_parity_response"

            # Verify the choice was sent
            params = call_args[1]["params"]
            assert params["match_id"] == "R01M01"
            assert params["parity_choice"] in [ParityChoice.EVEN, ParityChoice.ODD]

    @pytest.mark.asyncio
    async def test_handle_parity_call_with_opponent_history(self):
        """Test parity call uses opponent history"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="pattern",
            logger=self.logger
        )

        # Set up match state
        handler.state.start_match("R01M01", "P02", "PLAYER_A")
        handler.current_referee_endpoint = "http://localhost:8001/mcp"

        # Add some history against P02
        handler.history.add_match(
            match_id="R00M01",
            opponent_id="P02",
            result="WIN",
            points=3,
            my_choice="even",
            opponent_choice="odd",
            drawn_number=4
        )

        # Mock MCPClient
        mock_mcp_instance = AsyncMock()
        mock_mcp_instance.call_tool = AsyncMock(return_value={"status": "ok"})

        from datetime import timedelta
        deadline = datetime.now(timezone.utc) + timedelta(seconds=30)

        call = ChooseParityCall(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="test_token",
            match_id="R01M01",
            deadline=deadline
        )

        with patch('agents.player.handlers.MCPClient') as MockMCPClient:
            MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
            MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

            result = await handler.handle_parity_call(call)

            assert result["status"] == "choice_sent"
            # Strategy should have been called with history
            assert handler.state.current_choice is not None

    @pytest.mark.asyncio
    async def test_handle_game_invitation_no_matching_referee(self):
        """Test game invitation when referee not found in config"""
        handler = PlayerHandlers(
            player_id="P01",
            display_name="Test Player",
            strategy_name="random",
            logger=self.logger
        )

        # Mock empty referee list
        mock_agents_config = Mock()
        mock_agents_config.referees = []

        mock_config_loader = Mock()
        mock_config_loader.load_agents.return_value = mock_agents_config

        # Mock MCPClient
        mock_mcp_instance = AsyncMock()
        mock_mcp_instance.call_tool = AsyncMock(return_value={"status": "ok"})

        invitation = GameInvitation(
            sender="referee:REF99",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R01M01",
            auth_token="test_token",
            match_id="R01M01",
            opponent_id="P02",
            role_in_match="PLAYER_A"
        )

        with patch('SHARED.league_sdk.config_loader.get_config_loader', return_value=mock_config_loader):
            with patch('agents.player.handlers.MCPClient') as MockMCPClient:
                MockMCPClient.return_value.__aenter__.return_value = mock_mcp_instance
                MockMCPClient.return_value.__aexit__.return_value = AsyncMock()

                result = await handler.handle_game_invitation(invitation)

                # Should still work, just endpoint won't be set from config
                assert result["status"] == "joined"
                assert handler.state.current_match_id == "R01M01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
