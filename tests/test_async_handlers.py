"""
Comprehensive async handler tests with proper mocking.
Tests all handler classes and their methods.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

from agents.league_manager.handlers import RegistrationHandler, ResultHandler
from agents.referee.match_manager import MatchManager, MatchState
from SHARED.league_sdk.models import (
    RefereeRegisterRequest,
    LeagueRegisterRequest,
    RefereeMeta,
    PlayerMeta,
    RegistrationStatus,
    MatchResultReport,
    GameStatus,
)


class TestRegistrationHandlerComprehensive:
    """Comprehensive registration handler tests"""

    def test_generate_token_uniqueness(self):
        """Test that JWT tokens are unique"""
        with patch('SHARED.league_sdk.logger.JsonLogger.__init__', return_value=None):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            tokens = set()
            for i in range(100):
                token = handler.generate_auth_token(f"AGENT_{i}", agent_type="player")
                assert token not in tokens
                tokens.add(token)

    def test_auth_token_validation(self):
        """Test JWT token validation"""
        with patch('SHARED.league_sdk.logger.JsonLogger.__init__', return_value=None):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            token = handler.generate_auth_token("REF01", agent_type="referee")

            # Validate token and check payload
            payload = handler.validate_token(token)
            assert payload is not None
            assert payload["agent_id"] == "REF01"
            assert payload["league_id"] == "test_league"
            assert payload["agent_type"] == "referee"

    def test_referee_registration_accepts(self):
        """Test referee registration is accepted"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            # Register referee
            request = RefereeRegisterRequest(
                sender="referee:REF_UNKNOWN",
                referee_meta=RefereeMeta(
                    display_name="Ref 1",
                    version="1.0.0",
                    game_types=["even_odd"],
                    contact_endpoint="http://localhost:8001/mcp",
                ),
                conversation_id="conv-1",
                timestamp=datetime.now(),
            )
            response = handler.handle_referee_registration(request)
            assert response.status == RegistrationStatus.ACCEPTED
            assert response.referee_id == "REF01"  # Auto-generated
            assert response.auth_token is not None
            assert len(handler.registered_referees) == 1

    def test_player_registration_accepts(self):
        """Test player registration is accepted"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            # Register player
            request = LeagueRegisterRequest(
                sender="player:P_UNKNOWN",
                player_meta=PlayerMeta(
                    display_name="Player 1",
                    version="1.0.0",
                    game_types=["even_odd"],
                    contact_endpoint="http://localhost:8101/mcp",
                ),
                conversation_id="conv-1",
                timestamp=datetime.now(),
            )
            response = handler.handle_player_registration(request)
            assert response.status == RegistrationStatus.ACCEPTED
            assert response.player_id == "P01"  # Auto-generated
            assert response.auth_token is not None
            assert len(handler.registered_players) == 1

    def test_multiple_unique_registrations(self):
        """Test multiple unique registrations"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            # Register 5 referees
            for i in range(5):
                request = RefereeRegisterRequest(
                    sender=f"referee:REF_UNKNOWN_{i}",
                    referee_meta=RefereeMeta(
                        display_name=f"Referee {i}",
                        version="1.0.0",
                        game_types=["even_odd"],
                        contact_endpoint=f"http://localhost:800{i}/mcp",
                    ),
                    conversation_id=f"conv-{i}",
                    timestamp=datetime.now(),
                )
                response = handler.handle_referee_registration(request)
                assert response.status == RegistrationStatus.ACCEPTED

            assert len(handler.registered_referees) == 5

            # Register 10 players
            for i in range(10):
                request = LeagueRegisterRequest(
                    sender=f"player:P_UNKNOWN_{i}",
                    player_meta=PlayerMeta(
                        display_name=f"Player {i}",
                        version="1.0.0",
                        game_types=["even_odd"],
                        contact_endpoint=f"http://localhost:81{i:02d}/mcp",
                    ),
                    conversation_id=f"conv-p{i}",
                    timestamp=datetime.now(),
                )
                response = handler.handle_player_registration(request)
                assert response.status == RegistrationStatus.ACCEPTED

            assert len(handler.registered_players) == 10

    def test_validate_auth_token(self):
        """Test JWT auth token validation"""
        with patch('SHARED.league_sdk.logger.JsonLogger._write_log'):
            from SHARED.league_sdk.logger import JsonLogger
            logger = JsonLogger(component="test")
            handler = RegistrationHandler("test_league", logger)

            # Generate JWT token for agent
            token = handler.generate_auth_token("REF01", agent_type="referee")

            # Valid token with correct agent
            assert handler.validate_auth_token(token, "REF01") is True

            # Invalid token
            assert handler.validate_auth_token("invalid_token", "REF01") is False

            # Valid token but wrong agent
            assert handler.validate_auth_token(token, "REF02") is False


class TestResultHandlerComprehensive:
    """Comprehensive result handler tests"""

    def test_result_handler_init(self):
        """Test result handler initialization"""
        with patch('SHARED.league_sdk.logger.JsonLogger.__init__', return_value=None):
            with patch('SHARED.league_sdk.repositories.StandingsRepository.__init__', return_value=None):
                with patch('SHARED.league_sdk.repositories.RoundsRepository.__init__', return_value=None):
                    from SHARED.league_sdk.logger import JsonLogger
                    from SHARED.league_sdk.repositories import StandingsRepository, RoundsRepository
                    from agents.league_manager.standings import StandingsCalculator

                    logger = JsonLogger(component="test")
                    standings_repo = StandingsRepository(league_id="test")
                    rounds_repo = RoundsRepository(league_id="test")
                    calculator = StandingsCalculator()

                    handler = ResultHandler(
                        league_id="test_league",
                        logger=logger,
                        standings_calculator=calculator,
                        standings_repo=standings_repo,
                        rounds_repo=rounds_repo
                    )

                    assert handler.league_id == "test_league"
                    assert handler.logger == logger
                    assert handler.standings_calculator == calculator


class TestMatchManagerStates:
    """Test match manager state machine"""

    def test_match_state_enum_values(self):
        """Test all match states exist"""
        assert MatchState.CREATED.value == "CREATED"
        assert MatchState.WAITING_FOR_PLAYERS.value == "WAITING_FOR_PLAYERS"
        assert MatchState.COLLECTING_CHOICES.value == "COLLECTING_CHOICES"
        assert MatchState.DRAWING_NUMBER.value == "DRAWING_NUMBER"
        assert MatchState.FINISHED.value == "FINISHED"
        assert MatchState.CANCELLED.value == "CANCELLED"

    def test_match_manager_initial_state(self):
        """Test match manager starts in CREATED state"""
        with patch('SHARED.league_sdk.logger.JsonLogger.__init__', return_value=None):
            with patch('SHARED.league_sdk.repositories.MatchRepository.__init__', return_value=None):
                from SHARED.league_sdk.logger import JsonLogger
                from SHARED.league_sdk.repositories import MatchRepository
                from agents.referee.game_logic import EvenOddGame

                logger = JsonLogger(component="test")
                repo = MatchRepository(league_id="test")
                game = EvenOddGame()

                manager = MatchManager(
                    match_id="R1M1",
                    round_id="R1",
                    league_id="test",
                    referee_id="REF01",
                    player_a_id="P01",
                    player_b_id="P02",
                    player_a_endpoint="http://localhost:8101/mcp",
                    player_b_endpoint="http://localhost:8102/mcp",
                    league_manager_endpoint="http://localhost:8000/mcp",
                    logger=logger,
                    match_repo=repo,
                    game_logic=game,
                )

                assert manager.state == MatchState.CREATED
                assert manager.match_id == "R1M1"
                assert manager.player_a_id == "P01"
                assert manager.player_b_id == "P02"
                assert len(manager.player_choices) == 0
                assert len(manager.join_acks) == 0


class TestRepositoryComprehensive:
    """Comprehensive repository tests"""

    def test_match_repository_state_transition(self):
        """Test match repository state transitions"""
        from SHARED.league_sdk.repositories import MatchRepository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test", data_dir=Path(tmpdir))

            # Create match
            repo.create_match(
                match_id="R1M1",
                round_id="R1",
                league_id="test",
                referee_id="REF01",
                player_a_id="P01",
                player_b_id="P02"
            )

            # Add state transition
            repo.add_state_transition("R1M1", "IN_PROGRESS")

            # Load and verify
            match = repo.load_match("R1M1")
            assert match is not None
            assert len(match["lifecycle"]) > 0

    def test_match_repository_add_transcript_entry(self):
        """Test adding transcript entries"""
        from SHARED.league_sdk.repositories import MatchRepository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test", data_dir=Path(tmpdir))

            repo.create_match(
                match_id="R1M1",
                round_id="R1",
                league_id="test",
                referee_id="REF01",
                player_a_id="P01",
                player_b_id="P02"
            )

            # Add transcript entry
            repo.add_transcript_entry(
                match_id="R1M1",
                sender="referee:REF01",
                recipient="player:P01",
                message_type="MATCH_INVITATION"
            )

            match = repo.load_match("R1M1")
            assert len(match["transcript"]) == 1
            assert match["transcript"][0]["from"] == "referee:REF01"
            assert match["transcript"][0]["to"] == "player:P01"

    def test_player_history_multiple_matches(self):
        """Test player history with multiple matches"""
        from SHARED.league_sdk.repositories import PlayerHistoryRepository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = PlayerHistoryRepository(player_id="P01", data_dir=Path(tmpdir))

            # Add 10 matches
            for i in range(10):
                result = "WIN" if i % 3 == 0 else "DRAW" if i % 3 == 1 else "LOSS"
                points = 3 if result == "WIN" else 1 if result == "DRAW" else 0

                repo.add_match_result(
                    match_id=f"R{i}M1",
                    opponent_id=f"P{(i % 3) + 2:02d}",
                    result=result,
                    points=points,
                    my_choice="even" if i % 2 == 0 else "odd",
                    opponent_choice="odd" if i % 2 == 0 else "even",
                    drawn_number=i + 1
                )

            history = repo.load()
            assert history["total_matches"] == 10
            assert len(history["matches"]) == 10


class TestConfigLoaderComprehensive:
    """Comprehensive config loader tests"""

    def test_config_models_validation(self):
        """Test config model validation"""
        from SHARED.league_sdk.config_loader import (
            RefereeConfig,
            PlayerConfig,
            LeagueManagerConfig,
            ScoringConfig
        )

        ref = RefereeConfig(
            referee_id="REF01",
            display_name="Test Ref",
            endpoint="http://localhost:8001/mcp",
            version="1.0.0",
            game_types=["even_odd"],
            max_concurrent_matches=2
        )
        assert ref.referee_id == "REF01"

        player = PlayerConfig(
            player_id="P01",
            display_name="Test Player",
            endpoint="http://localhost:8101/mcp",
            version="1.0.0",
            game_types=["even_odd"],
            strategy="random"
        )
        assert player.strategy == "random"

        lm = LeagueManagerConfig(
            manager_id="LM01",
            display_name="League Manager",
            endpoint="http://localhost:8000/mcp",
            version="1.0.0"
        )
        assert lm.manager_id == "LM01"

        scoring = ScoringConfig(
            win_points=3,
            draw_points=1,
            loss_points=0,
            technical_loss_points=0
        )
        assert scoring.win_points == 3
        assert scoring.technical_loss_points == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
