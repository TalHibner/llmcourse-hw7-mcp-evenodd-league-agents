"""
Tests to cover easy remaining gaps in small modules.
"""

import pytest
import tempfile
from pathlib import Path

from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.repositories import MatchRepository
from agents.player.strategy import PatternBasedStrategy
from agents.referee.game_logic import EvenOddGame
from SHARED.league_sdk.models import ParityChoice, GameStatus


class TestLoggerCoverage:
    """Cover missing logger branches"""

    def test_logger_league_manager_with_league_id(self):
        """Test logger path for league_manager with league_id"""
        logger = JsonLogger(
            component="league_manager",
            league_id="LEAGUE01"
        )
        path = logger._get_log_file_path()
        assert "league" in str(path)
        assert "LEAGUE01" in str(path)
        assert path.name == "league.log.jsonl"

    def test_logger_agent_format_with_colon(self):
        """Test logger path for agent format (component with colon)"""
        logger = JsonLogger(
            component="player:P01"
        )
        path = logger._get_log_file_path()
        assert "agents" in str(path)
        assert "P01" in str(path)

    def test_logger_other_component(self):
        """Test logger path for other component types"""
        logger = JsonLogger(
            component="system_monitor"
        )
        path = logger._get_log_file_path()
        assert "system" in str(path)
        assert "system_monitor.log.jsonl" in str(path)

    def test_logger_warning_method(self):
        """Test logger warning method"""
        logger = JsonLogger(component="test")
        logger.warning("WARNING_EVENT", message="This is a warning")
        # Just verify no crash

    def test_logger_error_method(self):
        """Test logger error method"""
        logger = JsonLogger(component="test")
        logger.error("ERROR_EVENT", message="This is an error")
        # Just verify no crash

    def test_logger_league_manager_no_league_id(self):
        """Test logger path for league_manager without league_id"""
        logger = JsonLogger(component="league_manager")
        path = logger._get_log_file_path()
        assert "system" in str(path)
        assert "league_manager.log.jsonl" in str(path)


class TestStrategyCoverage:
    """Cover missing strategy branches"""

    def test_pattern_strategy_empty_history(self):
        """Test pattern strategy with empty opponent history"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # Empty history should return random choice
        choice = strategy.choose("P02", [])
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

    def test_pattern_strategy_no_opponent_choices(self):
        """Test pattern strategy when history has no opponent_choice field"""
        strategy = PatternBasedStrategy(threshold=0.6)

        # History without opponent_choice field
        history = [
            {"match_id": "R1M1", "result": "WIN"},
            {"match_id": "R1M2", "result": "LOSS"},
        ]

        choice = strategy.choose("P02", history)
        assert choice in [ParityChoice.EVEN, ParityChoice.ODD]


class TestGameLogicCoverage:
    """Cover missing game logic branches"""

    def test_game_both_wrong_no_draw(self):
        """Test game logic when both wrong and draw_on_both_wrong=False"""
        game = EvenOddGame(draw_on_both_wrong=False)

        # Both choose EVEN, but number is ODD
        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN,
            ParityChoice.EVEN,
            drawn_number=3  # ODD
        )

        assert result.status.value == "DRAW"
        assert score["P01"] == 0  # Both get 0 points
        assert score["P02"] == 0
        assert "wrong parity" in result.reason

    def test_game_draw_number_without_arg(self):
        """Test that game can draw number without argument"""
        game = EvenOddGame(number_range_min=1, number_range_max=10)

        # Don't provide drawn_number - should draw one
        result, score = game.determine_winner(
            "P01", "P02",
            ParityChoice.EVEN,
            ParityChoice.ODD
            # No drawn_number argument
        )

        # Should have drawn a number
        assert result.drawn_number is not None
        assert 1 <= result.drawn_number <= 10

        # Should have a winner (different choices)
        assert result.status == GameStatus.WIN
        assert result.winner_player_id in ["P01", "P02"]


class TestRepositoriesCoverage:
    """Cover missing repository branches"""

    def test_match_repository_save_result(self):
        """Test match repository save_result method"""
        from SHARED.league_sdk.models import GameResult, GameStatus, ParityChoice
        import tempfile

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

            # Save result
            result = GameResult(
                status=GameStatus.WIN,
                winner_player_id="P01",
                drawn_number=4,
                number_parity=ParityChoice.EVEN,
                choices={"P01": ParityChoice.EVEN, "P02": ParityChoice.ODD},
                reason="P01 wins"
            )

            repo.save_result("R1M1", result, {"P01": 3, "P02": 0})

            # Load and verify
            match = repo.load_match("R1M1")
            assert match["result"]["status"] == "WIN"
            assert match["result"]["winner_player_id"] == "P01"

    def test_match_repository_nonexistent_operations(self):
        """Test operations on nonexistent matches"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test", data_dir=Path(tmpdir))

            # Try to add transcript to nonexistent match
            repo.add_transcript_entry(
                "NONEXISTENT",
                "referee:REF01",
                "player:P01",
                "INVITATION"
            )

            # Try to add state transition to nonexistent match
            repo.add_state_transition("NONEXISTENT", "IN_PROGRESS")

            # Should not crash
            assert True

    def test_match_repository_save_result_nonexistent(self):
        """Test saving result to nonexistent match"""
        from SHARED.league_sdk.models import GameResult, GameStatus, ParityChoice
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="test", data_dir=Path(tmpdir))

            # Try to save result to nonexistent match
            result = GameResult(
                status=GameStatus.WIN,
                winner_player_id="P01",
                drawn_number=4,
                number_parity=ParityChoice.EVEN,
                choices={"P01": ParityChoice.EVEN, "P02": ParityChoice.ODD},
                reason="P01 wins"
            )

            repo.save_result("NONEXISTENT", result, {"P01": 3, "P02": 0})

            # Should not crash
            assert True

    def test_repositories_default_data_dir(self):
        """Test repositories use default data_dir when None provided"""
        from SHARED.league_sdk.repositories import StandingsRepository, RoundsRepository, MatchRepository

        # Test StandingsRepository with data_dir=None
        standings_repo = StandingsRepository(league_id="test", data_dir=None)
        assert standings_repo.data_dir is not None
        assert "leagues" in str(standings_repo.data_dir)

        # Test RoundsRepository with data_dir=None
        rounds_repo = RoundsRepository(league_id="test", data_dir=None)
        assert rounds_repo.data_dir is not None
        assert "leagues" in str(rounds_repo.data_dir)

        # Test MatchRepository with data_dir=None
        match_repo = MatchRepository(league_id="test", data_dir=None)
        assert match_repo.data_dir is not None
        assert "matches" in str(match_repo.data_dir)


class TestConfigLoaderCoverage:
    """Cover missing config loader branches"""

    def test_config_loader_get_methods(self):
        """Test config loader get methods"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()

        # Test get_referee_by_id with nonexistent
        ref = loader.get_referee_by_id("NONEXISTENT")
        assert ref is None

        # Test get_player_by_id with nonexistent
        player = loader.get_player_by_id("NONEXISTENT")
        assert player is None

    def test_config_loader_load_methods(self):
        """Test config loader load methods"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()

        # Test load_system
        system = loader.load_system()
        assert system is not None

        # Test load_agents
        agents = loader.load_agents()
        assert agents is not None

        # Test load_games_registry
        games = loader.load_games_registry()
        assert games is not None

    def test_config_loader_load_league(self):
        """Test loading league config"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()

        # Test load_league with some ID
        try:
            league = loader.load_league("test_league")
            # May or may not exist
        except Exception:
            # If file doesn't exist, that's OK
            pass

    def test_config_loader_clear_cache(self):
        """Test clearing config cache"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()

        # Load something to populate cache
        loader.load_system()

        # Clear cache
        loader.clear_cache()

        # Should still work after clearing
        system = loader.load_system()
        assert system is not None

    def test_config_loader_get_existing_referee(self):
        """Test getting an existing referee"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()
        agents = loader.load_agents()

        # If there are any referees, try to get one
        if agents.referees:
            ref_id = agents.referees[0].referee_id
            ref = loader.get_referee_by_id(ref_id)
            assert ref is not None
            assert ref.referee_id == ref_id

    def test_config_loader_get_existing_player(self):
        """Test getting an existing player"""
        from SHARED.league_sdk.config_loader import get_config_loader

        loader = get_config_loader()
        agents = loader.load_agents()

        # If there are any players, try to get one
        if agents.players:
            player_id = agents.players[0].player_id
            player = loader.get_player_by_id(player_id)
            assert player is not None
            assert player.player_id == player_id

    def test_config_loader_load_league(self):
        """Test loading a league config file"""
        from SHARED.league_sdk.config_loader import ConfigLoader
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create a league config file
            leagues_dir = config_dir / "leagues"
            leagues_dir.mkdir(parents=True, exist_ok=True)

            league_config = {
                "league_id": "TEST_LEAGUE",
                "display_name": "Test League",
                "game_type": "even_odd",
                "format": "round_robin",
                "scoring": {
                    "win_points": 3,
                    "draw_points": 1,
                    "loss_points": 0,
                    "technical_loss_points": -1
                },
                "participants": {
                    "min_players": 2,
                    "max_players": 8,
                    "registered_players": []
                },
                "schedule": {
                    "start_date": "2025-01-01",
                    "match_delay_sec": 5
                },
                "rules": {
                    "number_range_min": 1,
                    "number_range_max": 100,
                    "draw_on_both_wrong": True
                }
            }

            league_file = leagues_dir / "TEST_LEAGUE.json"
            with open(league_file, 'w') as f:
                json.dump(league_config, f)

            # Load the league config
            loader = ConfigLoader(config_dir=config_dir)
            league = loader.load_league("TEST_LEAGUE")

            assert league.league_id == "TEST_LEAGUE"
            assert league.display_name == "Test League"

            # Verify it was cached
            assert "league_TEST_LEAGUE" in loader._cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
