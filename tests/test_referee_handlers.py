"""
Tests for referee handlers.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from agents.referee.handlers import RefereeHandlers
from SHARED.league_sdk.models import (
    GameJoinAck, ChooseParityResponse, ParityChoice
)


class TestRefereeHandlers:
    """Tests for RefereeHandlers"""

    def setup_method(self):
        """Setup for each test"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            self.logger = JsonLogger(component="test")

    def test_init(self):
        """Test handler initialization"""
        handler = RefereeHandlers(logger=self.logger)

        assert handler.logger == self.logger
        assert handler.active_matches == {}

    def test_register_match(self):
        """Test match registration"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)

        assert "R1M1" in handler.active_matches
        assert handler.active_matches["R1M1"] == mock_match_manager

    def test_unregister_match(self):
        """Test match unregistration"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)
        handler.unregister_match("R1M1")

        assert "R1M1" not in handler.active_matches

    def test_unregister_nonexistent_match(self):
        """Test unregistering a match that doesn't exist"""
        handler = RefereeHandlers(logger=self.logger)

        # Should not raise an error
        handler.unregister_match("NONEXISTENT")
        assert True

    def test_handle_game_join_ack_accepted(self):
        """Test handling join ack - accepted"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)

        ack = GameJoinAck(
            sender="player:P01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            accept=True,
            arrival_timestamp=datetime.now(timezone.utc)
        )

        result = handler.handle_game_join_ack(ack)

        assert result["status"] == "acknowledged"
        mock_match_manager.handle_join_ack.assert_called_once_with("P01", True)

    def test_handle_game_join_ack_rejected(self):
        """Test handling join ack - rejected"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)

        ack = GameJoinAck(
            sender="player:P01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            accept=False,
            arrival_timestamp=datetime.now(timezone.utc)
        )

        result = handler.handle_game_join_ack(ack)

        assert result["status"] == "acknowledged"
        mock_match_manager.handle_join_ack.assert_called_once_with("P01", False)

    def test_handle_game_join_ack_no_match(self):
        """Test handling join ack for non-registered match"""
        handler = RefereeHandlers(logger=self.logger)

        ack = GameJoinAck(
            sender="player:P01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            accept=True,
            arrival_timestamp=datetime.now(timezone.utc)
        )

        # Should not raise an error
        result = handler.handle_game_join_ack(ack)
        assert result["status"] == "acknowledged"

    def test_handle_parity_response_even(self):
        """Test handling parity response - EVEN"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)

        response = ChooseParityResponse(
            sender="player:P01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            parity_choice=ParityChoice.EVEN
        )

        result = handler.handle_parity_response(response)

        assert result["status"] == "acknowledged"
        mock_match_manager.handle_parity_choice.assert_called_once_with(
            "P01", ParityChoice.EVEN
        )

    def test_handle_parity_response_odd(self):
        """Test handling parity response - ODD"""
        handler = RefereeHandlers(logger=self.logger)

        mock_match_manager = Mock()
        handler.register_match("R1M1", mock_match_manager)

        response = ChooseParityResponse(
            sender="player:P02",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            parity_choice=ParityChoice.ODD
        )

        result = handler.handle_parity_response(response)

        assert result["status"] == "acknowledged"
        mock_match_manager.handle_parity_choice.assert_called_once_with(
            "P02", ParityChoice.ODD
        )

    def test_handle_parity_response_no_match(self):
        """Test handling parity response for non-registered match"""
        handler = RefereeHandlers(logger=self.logger)

        response = ChooseParityResponse(
            sender="player:P01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="R1M1",
            auth_token="",
            match_id="R1M1",
            parity_choice=ParityChoice.EVEN
        )

        # Should not raise an error
        result = handler.handle_parity_response(response)
        assert result["status"] == "acknowledged"

    def test_multiple_match_registration(self):
        """Test registering multiple matches"""
        handler = RefereeHandlers(logger=self.logger)

        mock_mm1 = Mock()
        mock_mm2 = Mock()
        mock_mm3 = Mock()

        handler.register_match("R1M1", mock_mm1)
        handler.register_match("R1M2", mock_mm2)
        handler.register_match("R2M1", mock_mm3)

        assert len(handler.active_matches) == 3
        assert handler.active_matches["R1M1"] == mock_mm1
        assert handler.active_matches["R1M2"] == mock_mm2
        assert handler.active_matches["R2M1"] == mock_mm3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
