"""
Unit tests for SHARED/league_sdk components.

Tests models, config_loader, logger, mcp_client, and repositories.
"""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from SHARED.league_sdk.models import (
    MessageEnvelope,
    MessageType,
    RefereeMeta,
    PlayerMeta,
    MatchInfo,
    StandingEntry,
    ParityChoice,
    GameStatus,
    RegistrationStatus,
)
from SHARED.league_sdk.config_loader import (
    ConfigLoader,
    SystemConfig,
    AgentsConfig,
    NetworkConfig,
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.repositories import (
    StandingsRepository,
    RoundsRepository,
    MatchRepository,
    PlayerHistoryRepository,
)


class TestModels:
    """Test Pydantic models"""

    def test_message_envelope_valid(self):
        """Test valid message envelope creation"""
        envelope = MessageEnvelope(
            protocol="league.v2",
            message_type=MessageType.GAME_INVITATION,
            sender="referee:REF01",
            timestamp=datetime.now(),
            conversation_id="conv-123",
            auth_token="token-abc",
        )
        assert envelope.protocol == "league.v2"
        assert envelope.message_type == MessageType.GAME_INVITATION
        assert envelope.sender == "referee:REF01"

    def test_message_envelope_invalid_sender(self):
        """Test message envelope with invalid sender format"""
        with pytest.raises(ValueError, match="Sender must be in format"):
            MessageEnvelope(
                protocol="league.v2",
                message_type=MessageType.GAME_INVITATION,
                sender="INVALID",  # Missing colon
                timestamp=datetime.now(),
                conversation_id="conv-123",
                auth_token="token-abc",
            )

    def test_referee_meta(self):
        """Test RefereeMeta model"""
        ref_meta = RefereeMeta(
            display_name="Test Referee",
            version="1.0.0",
            game_types=["even_odd"],
            contact_endpoint="http://localhost:8001/mcp",
            max_concurrent_matches=2,
        )
        assert ref_meta.display_name == "Test Referee"
        assert ref_meta.max_concurrent_matches == 2
        assert "even_odd" in ref_meta.game_types

    def test_player_meta(self):
        """Test PlayerMeta model"""
        player_meta = PlayerMeta(
            display_name="Test Player",
            version="1.0.0",
            game_types=["even_odd"],
            contact_endpoint="http://localhost:8101/mcp",
        )
        assert player_meta.display_name == "Test Player"
        assert player_meta.contact_endpoint == "http://localhost:8101/mcp"

    def test_match_info(self):
        """Test MatchInfo model"""
        match = MatchInfo(
            match_id="R1M1",
            game_type="even_odd",
            player_A_id="P01",
            player_B_id="P02",
            referee_endpoint="http://localhost:8001/mcp",
        )
        assert match.match_id == "R1M1"
        assert match.player_A_id == "P01"
        assert match.player_B_id == "P02"

    def test_standing_entry(self):
        """Test StandingEntry model"""
        entry = StandingEntry(
            player_id="P01",
            display_name="Player One",
            rank=1,
            points=9,
            wins=3,
            draws=0,
            losses=0,
            played=3,
        )
        assert entry.rank == 1
        assert entry.points == 9
        assert entry.wins == 3
        assert entry.played == 3

    def test_parity_choice_enum(self):
        """Test ParityChoice enum"""
        assert ParityChoice.EVEN.value == "even"
        assert ParityChoice.ODD.value == "odd"

    def test_game_status_enum(self):
        """Test GameStatus enum"""
        assert GameStatus.WIN.value == "WIN"
        assert GameStatus.DRAW.value == "DRAW"
        assert GameStatus.CANCELLED.value == "CANCELLED"


class TestConfigLoader:
    """Test configuration loader"""

    def test_load_system_config(self):
        """Test loading system configuration"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            config_data = {
                "protocol_version": "league.v2",
                "network": {
                    "base_host": "localhost",
                    "league_manager_port": 8000,
                    "referee_port_range": [8001, 8010],
                    "player_port_range": [8101, 8200],
                },
                "timeouts": {
                    "move_timeout_sec": 30,
                    "game_join_ack_timeout_sec": 5,
                    "generic_response_timeout_sec": 10,
                    "http_request_timeout_sec": 15,
                },
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_strategy": "exponential",
                    "backoff_base_sec": 1,
                },
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "timeout_sec": 30,
                    "half_open_max_calls": 1,
                },
                "logging": {"level": "INFO", "format": "jsonl", "rotation_mb": 10},
            }
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            # Load config
            with open(config_path) as f:
                data = json.load(f)
            config = SystemConfig(**data)

            # Verify
            assert config.protocol_version == "league.v2"
            assert config.network.league_manager_port == 8000
            assert config.timeouts.move_timeout_sec == 30
            assert config.retry_policy.max_retries == 3
        finally:
            config_path.unlink()

    def test_network_config(self):
        """Test NetworkConfig model"""
        network = NetworkConfig(
            base_host="localhost",
            league_manager_port=8000,
            referee_port_range=[8001, 8010],
            player_port_range=[8101, 8200],
        )
        assert network.base_host == "localhost"
        assert network.league_manager_port == 8000
        assert len(network.referee_port_range) == 2

    def test_config_loader_get_instance(self):
        """Test config loader singleton pattern"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader1 = get_config_loader()
        loader2 = get_config_loader()

        # Should return same instance
        assert loader1 is loader2

    def test_timeouts_config(self):
        """Test TimeoutsConfig model"""
        from SHARED.league_sdk.config_loader import TimeoutsConfig

        timeouts = TimeoutsConfig(
            move_timeout_sec=30,
            game_join_ack_timeout_sec=5,
            generic_response_timeout_sec=10,
            http_request_timeout_sec=15
        )
        assert timeouts.move_timeout_sec == 30
        assert timeouts.game_join_ack_timeout_sec == 5

    def test_retry_policy_config(self):
        """Test RetryPolicyConfig model"""
        from SHARED.league_sdk.config_loader import RetryPolicyConfig

        retry = RetryPolicyConfig(
            max_retries=3,
            backoff_strategy="exponential",
            backoff_base_sec=1
        )
        assert retry.max_retries == 3
        assert retry.backoff_strategy == "exponential"

    def test_circuit_breaker_config(self):
        """Test CircuitBreakerConfig model"""
        from SHARED.league_sdk.config_loader import CircuitBreakerConfig

        cb = CircuitBreakerConfig(
            failure_threshold=5,
            timeout_sec=30,
            half_open_max_calls=1
        )
        assert cb.failure_threshold == 5
        assert cb.timeout_sec == 30

    def test_logging_config(self):
        """Test LoggingConfig model"""
        from SHARED.league_sdk.config_loader import LoggingConfig

        logging_cfg = LoggingConfig(
            level="INFO",
            format="jsonl",
            rotation_mb=10
        )
        assert logging_cfg.level == "INFO"
        assert logging_cfg.format == "jsonl"


class TestJsonLogger:
    """Test JSON logger"""

    def test_logger_initialization(self):
        """Test logger can be initialized"""
        logger = JsonLogger(component="test-component")
        assert logger.component == "test-component"

    def test_logger_info(self):
        """Test info logging"""
        logger = JsonLogger(component="test-component")

        # Test that logger has the log method
        logger.info("test_event", detail="test detail")

        # Verify log file was created
        assert logger.log_file.exists()

        # Read and verify log entry
        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["level"] == "INFO"
                assert log_data["event_type"] == "test_event"
                assert log_data["component"] == "test-component"

    def test_logger_error(self):
        """Test error logging"""
        logger = JsonLogger(component="test-component-error")

        logger.error("error_event", error_msg="Something went wrong")

        # Verify log file was created
        assert logger.log_file.exists()

        # Read and verify log entry
        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["level"] == "ERROR"
                assert log_data["event_type"] == "error_event"

    def test_logger_debug(self):
        """Test debug logging"""
        logger = JsonLogger(component="debug-test")
        logger.debug("debug_event", context="testing")

        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["level"] == "DEBUG"

    def test_logger_warning(self):
        """Test warning logging"""
        logger = JsonLogger(component="warning-test")
        logger.warning("warning_event", reason="potential issue")

        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["level"] == "WARNING"

    def test_logger_message_sent(self):
        """Test logging sent messages"""
        logger = JsonLogger(component="message-test")
        logger.log_message_sent("TEST_MSG", "player:P01", extra_data="value")

        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["event_type"] == "MESSAGE_SENT"
                assert log_data["details"]["message_type"] == "TEST_MSG"

    def test_logger_message_received(self):
        """Test logging received messages"""
        logger = JsonLogger(component="message-test")
        logger.log_message_received("TEST_MSG", "player:P02")

        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["event_type"] == "MESSAGE_RECEIVED"

    def test_logger_state_change(self):
        """Test logging state changes"""
        logger = JsonLogger(component="state-test")
        logger.log_state_change("IDLE", "ACTIVE", reason="match started")

        with open(logger.log_file) as f:
            lines = f.readlines()
            if lines:
                log_data = json.loads(lines[-1])
                assert log_data["event_type"] == "STATE_CHANGE"
                assert log_data["details"]["old_state"] == "IDLE"
                assert log_data["details"]["new_state"] == "ACTIVE"


class TestRepositories:
    """Test data repositories"""

    def test_standings_repository_save_and_load(self):
        """Test saving and loading standings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create repository with temp directory
            repo = StandingsRepository(league_id="test_league", data_dir=Path(tmpdir))

            standings_data = {
                "league_id": "test_league",
                "version": 1,
                "standings": [
                    {
                        "player_id": "P01",
                        "display_name": "Player One",
                        "rank": 1,
                        "points": 6,
                        "wins": 2,
                        "draws": 0,
                        "losses": 0,
                        "played": 2,
                    }
                ],
            }

            # Save
            repo.save(standings_data)

            # Load
            loaded = repo.load()

            assert loaded["league_id"] == "test_league"
            assert loaded["version"] >= 1
            assert len(loaded["standings"]) == 1
            assert loaded["standings"][0]["player_id"] == "P01"

    def test_rounds_repository_save_and_load(self):
        """Test saving and loading rounds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RoundsRepository(league_id="test_league", data_dir=Path(tmpdir))

            rounds_data = {
                "league_id": "test_league",
                "rounds": [
                    {
                        "round_id": "R1",
                        "matches": [
                            {
                                "match_id": "R1M1",
                                "player_A_id": "P01",
                                "player_B_id": "P02",
                            }
                        ],
                    }
                ],
            }

            # Save
            repo.save(rounds_data)

            # Load
            loaded = repo.load()

            assert loaded["league_id"] == "test_league"
            assert len(loaded["rounds"]) == 1
            assert loaded["rounds"][0]["round_id"] == "R1"

    def test_match_repository_create_and_load(self):
        """Test creating and loading match data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test_league", data_dir=Path(tmpdir))

            # Create match using the actual API
            repo.create_match(
                match_id="R1M1",
                round_id="R1",
                league_id="test_league",
                referee_id="REF01",
                player_a_id="P01",
                player_b_id="P02",
            )

            # Load
            loaded = repo.load_match("R1M1")

            assert loaded["match_id"] == "R1M1"
            assert loaded["players"]["PLAYER_A"] == "P01"
            assert loaded["players"]["PLAYER_B"] == "P02"
            assert loaded["referee_id"] == "REF01"

    def test_player_history_repository(self):
        """Test player history repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = PlayerHistoryRepository(player_id="P01", data_dir=Path(tmpdir))

            history_data = {
                "player_id": "P01",
                "total_matches": 2,
                "total_wins": 1,
                "total_draws": 1,
                "total_losses": 0,
                "matches": [
                    {
                        "match_id": "R1M1",
                        "opponent_id": "P02",
                        "result": "WIN",
                        "my_choice": "even",
                        "opponent_choice": "odd",
                        "number_drawn": 4,
                        "points_earned": 3,
                    }
                ],
            }

            # Save
            repo.save(history_data)

            # Load
            loaded = repo.load()

            assert loaded["player_id"] == "P01"
            assert loaded["total_matches"] == 2
            assert loaded["total_wins"] == 1
            assert len(loaded["matches"]) == 1


    def test_standings_repository_get_standings(self):
        """Test getting standings as StandingEntry objects"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = StandingsRepository(league_id="test_league", data_dir=Path(tmpdir))

            standings_data = {
                "league_id": "test_league",
                "version": 1,
                "standings": [
                    {
                        "player_id": "P01",
                        "display_name": "Player One",
                        "rank": 1,
                        "points": 6,
                        "wins": 2,
                        "draws": 0,
                        "losses": 0,
                        "played": 2,
                    }
                ],
            }

            repo.save(standings_data)
            standings = repo.get_standings()

            assert len(standings) == 1
            assert isinstance(standings[0], StandingEntry)
            assert standings[0].player_id == "P01"

    def test_standings_repository_update_standings(self):
        """Test updating standings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = StandingsRepository(league_id="test_league", data_dir=Path(tmpdir))

            new_standings = [
                StandingEntry(
                    player_id="P01",
                    display_name="Player One",
                    rank=1,
                    points=9,
                    wins=3,
                    draws=0,
                    losses=0,
                    played=3,
                )
            ]

            repo.update_standings(new_standings)
            loaded = repo.load()

            assert len(loaded["standings"]) == 1
            assert loaded["standings"][0]["points"] == 9

    def test_standings_repository_increment_rounds(self):
        """Test incrementing rounds completed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = StandingsRepository(league_id="test_league", data_dir=Path(tmpdir))

            # Initial state
            data = repo.load()
            assert data["rounds_completed"] == 0

            # Increment
            repo.increment_rounds_completed()
            data = repo.load()
            assert data["rounds_completed"] == 1

            # Increment again
            repo.increment_rounds_completed()
            data = repo.load()
            assert data["rounds_completed"] == 2

    def test_rounds_repository_add_round(self):
        """Test adding a round"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RoundsRepository(league_id="test_league", data_dir=Path(tmpdir))

            matches = [
                MatchInfo(
                    match_id="R1M1",
                    game_type="even_odd",
                    player_A_id="P01",
                    player_B_id="P02",
                    referee_endpoint="http://localhost:8001/mcp",
                )
            ]

            repo.add_round("R1", matches)
            data = repo.load()

            assert len(data["rounds"]) == 1
            assert data["rounds"][0]["round_id"] == "R1"
            assert len(data["rounds"][0]["matches"]) == 1

    def test_rounds_repository_mark_match_completed(self):
        """Test marking a match as completed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RoundsRepository(league_id="test_league", data_dir=Path(tmpdir))

            matches = [
                MatchInfo(
                    match_id="R1M1",
                    game_type="even_odd",
                    player_A_id="P01",
                    player_B_id="P02",
                    referee_endpoint="http://localhost:8001/mcp",
                )
            ]

            repo.add_round("R1", matches)
            repo.mark_match_completed("R1", "R1M1")

            data = repo.load()
            assert "R1M1" in data["rounds"][0]["completed_matches"]

    def test_rounds_repository_mark_round_completed(self):
        """Test marking a round as completed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RoundsRepository(league_id="test_league", data_dir=Path(tmpdir))

            matches = [
                MatchInfo(
                    match_id="R1M1",
                    game_type="even_odd",
                    player_A_id="P01",
                    player_B_id="P02",
                    referee_endpoint="http://localhost:8001/mcp",
                )
            ]

            repo.add_round("R1", matches)
            repo.mark_round_completed("R1")

            data = repo.load()
            assert data["rounds"][0]["completed_at"] is not None

    def test_rounds_repository_get_round(self):
        """Test getting a specific round"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RoundsRepository(league_id="test_league", data_dir=Path(tmpdir))

            matches = [
                MatchInfo(
                    match_id="R1M1",
                    game_type="even_odd",
                    player_A_id="P01",
                    player_B_id="P02",
                    referee_endpoint="http://localhost:8001/mcp",
                )
            ]

            repo.add_round("R1", matches)
            round_data = repo.get_round("R1")

            assert round_data is not None
            assert round_data["round_id"] == "R1"

            # Test non-existent round
            non_existent = repo.get_round("R99")
            assert non_existent is None

    def test_match_repository_save_and_load(self):
        """Test saving and loading match data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test_league", data_dir=Path(tmpdir))

            match_data = {
                "match_id": "R1M1",
                "status": "IN_PROGRESS",
                "score": {"P01": 0, "P02": 0}
            }

            repo.save_match("R1M1", match_data)
            loaded = repo.load_match("R1M1")

            assert loaded is not None
            assert loaded["match_id"] == "R1M1"
            assert loaded["status"] == "IN_PROGRESS"

    def test_match_repository_load_nonexistent(self):
        """Test loading a match that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test_league", data_dir=Path(tmpdir))
            loaded = repo.load_match("NONEXISTENT")
            assert loaded is None


class TestMessageTypes:
    """Test all 16 message types are defined"""

    def test_all_message_types_exist(self):
        """Verify all 16 core message types are defined"""
        expected_types = [
            "REFEREE_REGISTER_REQUEST",
            "REFEREE_REGISTER_RESPONSE",
            "LEAGUE_REGISTER_REQUEST",
            "LEAGUE_REGISTER_RESPONSE",
            "ROUND_ANNOUNCEMENT",
            "ROUND_COMPLETED",
            "GAME_INVITATION",
            "GAME_JOIN_ACK",
            "CHOOSE_PARITY_CALL",
            "CHOOSE_PARITY_RESPONSE",
            "GAME_OVER",
            "MATCH_RESULT_REPORT",
            "LEAGUE_STANDINGS_UPDATE",
            "LEAGUE_COMPLETED",
            "LEAGUE_ERROR",
            "GAME_ERROR",
        ]

        for msg_type in expected_types:
            assert hasattr(MessageType, msg_type)
            assert MessageType[msg_type].value == msg_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
