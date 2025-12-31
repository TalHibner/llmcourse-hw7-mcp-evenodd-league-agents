"""
Unit tests for League Manager components.

Tests scheduler, standings calculator, and handlers.
"""

import pytest
from unittest.mock import Mock, patch

from agents.league_manager.scheduler import RoundRobinScheduler
from agents.league_manager.standings import StandingsCalculator
from SHARED.league_sdk.models import StandingEntry, GameStatus


class TestRoundRobinScheduler:
    """Test Round-Robin scheduler"""

    def test_scheduler_with_4_players(self):
        """Test Round-Robin scheduling with 4 players"""
        players = ["P01", "P02", "P03", "P04"]
        referees = ["REF01", "REF02"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # With 4 players: C(4,2) = 6 matches total
        total_matches = sum(len(round_matches) for round_matches in schedule)
        assert total_matches == 6

        # Verify all unique pairings exist
        all_pairings = set()
        for round_matches in schedule:
            for match in round_matches:
                pair = tuple(sorted([match.player_A_id, match.player_B_id]))
                all_pairings.add(pair)

        expected_pairings = {
            ("P01", "P02"),
            ("P01", "P03"),
            ("P01", "P04"),
            ("P02", "P03"),
            ("P02", "P04"),
            ("P03", "P04"),
        }
        assert all_pairings == expected_pairings

    def test_scheduler_with_5_players(self):
        """Test Round-Robin scheduling with 5 players"""
        players = ["P01", "P02", "P03", "P04", "P05"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # With 5 players: C(5,2) = 10 matches total
        total_matches = sum(len(round_matches) for round_matches in schedule)
        assert total_matches == 10

    def test_scheduler_no_duplicate_matches_per_round(self):
        """Verify no player plays twice in the same round"""
        players = ["P01", "P02", "P03", "P04"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        for round_matches in schedule:
            players_in_round = []
            for match in round_matches:
                players_in_round.append(match.player_A_id)
                players_in_round.append(match.player_B_id)

            # No duplicates in round
            assert len(players_in_round) == len(set(players_in_round))

    def test_scheduler_with_2_players(self):
        """Test minimum case: 2 players"""
        players = ["P01", "P02"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # 1 match total, 1 round
        assert len(schedule) == 1
        assert len(schedule[0]) == 1
        match = schedule[0][0]
        assert set([match.player_A_id, match.player_B_id]) == {"P01", "P02"}

    def test_scheduler_with_insufficient_players(self):
        """Test with less than 2 players (edge case)"""
        players = ["P01"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # Should return empty schedule
        assert schedule == []

    def test_scheduler_match_ids(self):
        """Verify match IDs are correctly formatted"""
        players = ["P01", "P02", "P03"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # Check format: R{round}M{match}
        for round_idx, round_matches in enumerate(schedule, start=1):
            for match_idx, match in enumerate(round_matches, start=1):
                expected_id = f"R{round_idx}M{match_idx}"
                assert match.match_id == expected_id

    def test_generate_round_robin_pairings(self):
        """Test pairing generation"""
        players = ["P01", "P02", "P03"]
        referees = ["REF01"]

        scheduler = RoundRobinScheduler(players, referees)
        pairings = scheduler._generate_round_robin_pairings()

        # C(3,2) = 3 pairings
        assert len(pairings) == 3
        assert ("P01", "P02") in pairings
        assert ("P01", "P03") in pairings
        assert ("P02", "P03") in pairings


class TestStandingsCalculator:
    """Test standings calculator"""

    def test_initialize_standings(self):
        """Test initializing standings"""
        calc = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)

        player_ids = ["P01", "P02", "P03"]
        player_names = {
            "P01": "Player One",
            "P02": "Player Two",
            "P03": "Player Three",
        }

        standings = calc.initialize_standings(player_ids, player_names)

        assert len(standings) == 3
        for entry in standings:
            assert entry.played == 0
            assert entry.wins == 0
            assert entry.draws == 0
            assert entry.losses == 0
            assert entry.points == 0

    def test_update_standings_win(self):
        """Test updating standings after a win"""
        calc = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)

        # Initial standings
        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
        ]

        # P01 wins against P02
        match_result = {
            "match_id": "R1M1",
            "status": GameStatus.WIN,
            "score": {"P01": 3, "P02": 0},
            "winner_id": "P01",
        }

        updated = calc.update_standings(standings, match_result)

        # Find P01 and P02 in updated standings
        p01 = next(s for s in updated if s.player_id == "P01")
        p02 = next(s for s in updated if s.player_id == "P02")

        assert p01.wins == 1
        assert p01.points == 3
        assert p01.played == 1
        assert p01.rank == 1

        assert p02.losses == 1
        assert p02.points == 0
        assert p02.played == 1
        assert p02.rank == 2

    def test_update_standings_draw(self):
        """Test updating standings after a draw"""
        calc = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
        ]

        # Draw
        match_result = {
            "match_id": "R1M1",
            "status": GameStatus.DRAW,
            "score": {"P01": 1, "P02": 1},
        }

        updated = calc.update_standings(standings, match_result)

        p01 = next(s for s in updated if s.player_id == "P01")
        p02 = next(s for s in updated if s.player_id == "P02")

        assert p01.draws == 1
        assert p01.points == 1
        assert p02.draws == 1
        assert p02.points == 1

    def test_calculate_ranks_by_points(self):
        """Test ranking by points"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=2, wins=1, draws=0, losses=1, points=3
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=2, wins=2, draws=0, losses=0, points=6
            ),
            StandingEntry(
                rank=1, player_id="P03", display_name="Player Three",
                played=2, wins=0, draws=0, losses=2, points=0
            ),
        ]

        ranked = calc.calculate_ranks(standings)

        assert ranked[0].player_id == "P02"  # 6 points
        assert ranked[0].rank == 1
        assert ranked[1].player_id == "P01"  # 3 points
        assert ranked[1].rank == 2
        assert ranked[2].player_id == "P03"  # 0 points
        assert ranked[2].rank == 3

    def test_calculate_ranks_tiebreaker_wins(self):
        """Test tiebreaker: same points, more wins"""
        calc = StandingsCalculator(win_points=3, draw_points=1)

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=3, wins=1, draws=1, losses=1, points=4
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=4, wins=0, draws=4, losses=0, points=4
            ),
        ]

        ranked = calc.calculate_ranks(standings)

        # Both have 4 points, but P01 has 1 win vs P02's 0 wins
        assert ranked[0].player_id == "P01"
        assert ranked[1].player_id == "P02"

    def test_calculate_ranks_tiebreaker_alphabetical(self):
        """Test final tiebreaker: alphabetical by player_id"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=1, wins=1, draws=0, losses=0, points=3
            ),
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=1, wins=1, draws=0, losses=0, points=3
            ),
        ]

        ranked = calc.calculate_ranks(standings)

        # Same points, same wins -> alphabetical
        assert ranked[0].player_id == "P01"
        assert ranked[1].player_id == "P02"

    def test_get_champion(self):
        """Test getting the champion"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=3, wins=3, draws=0, losses=0, points=9
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=3, wins=1, draws=1, losses=1, points=4
            ),
        ]

        champion = calc.get_champion(standings)

        assert champion.player_id == "P01"
        assert champion.rank == 1
        assert champion.points == 9

    def test_update_standings_cancelled_match(self):
        """Test that cancelled matches don't affect stats"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=1, wins=1, draws=0, losses=0, points=3
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=1, wins=0, draws=0, losses=1, points=0
            ),
        ]

        # Cancelled match with score (to exercise the code path)
        match_result = {
            "match_id": "R2M1",
            "status": GameStatus.CANCELLED,
            "score": {"P01": 0, "P02": 0},
        }

        updated = calc.update_standings(standings, match_result)

        p01 = next(s for s in updated if s.player_id == "P01")
        p02 = next(s for s in updated if s.player_id == "P02")

        # Stats should remain unchanged
        assert p01.played == 1
        assert p01.wins == 1
        assert p02.played == 1
        assert p02.losses == 1

    def test_update_standings_with_unknown_player(self):
        """Test updating standings when score contains unknown player"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
        ]

        # Match result with unknown player P02
        match_result = {
            "match_id": "R1M1",
            "status": GameStatus.WIN,
            "score": {"P01": 3, "P02": 0},  # P02 not in standings
        }

        updated = calc.update_standings(standings, match_result)

        # Only P01 should be updated
        p01 = next(s for s in updated if s.player_id == "P01")
        assert p01.played == 1
        assert p01.wins == 1
        assert len(updated) == 1  # Still only one player


class TestLeagueManagerIntegration:
    """Integration tests for League Manager components"""

    def test_full_4_player_league_standings(self):
        """Simulate a complete 4-player league and verify standings"""
        players = ["P01", "P02", "P03", "P04"]
        referees = ["REF01", "REF02"]

        # Generate schedule
        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # Initialize standings
        calc = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)
        player_names = {
            "P01": "Player One",
            "P02": "Player Two",
            "P03": "Player Three",
            "P04": "Player Four",
        }
        standings = calc.initialize_standings(players, player_names)

        # Simulate match results (deterministic for testing)
        match_results = [
            {"status": GameStatus.WIN, "score": {"P01": 3, "P02": 0}},  # R1M1
            {"status": GameStatus.WIN, "score": {"P03": 3, "P04": 0}},  # R1M2
            {"status": GameStatus.WIN, "score": {"P01": 3, "P03": 0}},  # R2M1
            {"status": GameStatus.DRAW, "score": {"P02": 1, "P04": 1}},  # R2M2
            {"status": GameStatus.WIN, "score": {"P01": 3, "P04": 0}},  # R3M1
            {"status": GameStatus.DRAW, "score": {"P02": 1, "P03": 1}},  # R3M2
        ]

        # Update standings for each match
        for result in match_results:
            standings = calc.update_standings(standings, result)

        # Verify final standings
        final = calc.calculate_ranks(standings)

        # P01: 3 wins = 9 points (rank 1)
        # P02: 2 draws = 2 points (rank 3)
        # P03: 1 win + 1 draw = 4 points (rank 2)
        # P04: 1 draw = 1 point (rank 4)
        assert final[0].player_id == "P01"
        assert final[0].points == 9
        assert final[1].player_id == "P03"
        assert final[1].points == 4
        assert final[2].player_id == "P02"
        assert final[2].points == 2
        assert final[3].player_id == "P04"
        assert final[3].points == 1


class TestStandingsEdgeCases:
    """Test edge cases in standings calculator"""

    def test_standings_with_all_draws(self):
        """Test standings when all matches are draws"""
        calc = StandingsCalculator(win_points=3, draw_points=1)

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=3, wins=0, draws=3, losses=0, points=3
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=3, wins=0, draws=3, losses=0, points=3
            ),
        ]

        ranked = calc.calculate_ranks(standings)

        # With equal points and wins, should rank alphabetically
        assert ranked[0].player_id == "P01"
        assert ranked[1].player_id == "P02"

    def test_standings_with_zero_matches(self):
        """Test standings with zero matches played"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
        ]

        ranked = calc.calculate_ranks(standings)
        assert ranked[0].points == 0
        assert ranked[0].rank == 1

    def test_update_standings_multiple_times(self):
        """Test updating standings multiple times"""
        calc = StandingsCalculator()

        standings = [
            StandingEntry(
                rank=1, player_id="P01", display_name="Player One",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
            StandingEntry(
                rank=1, player_id="P02", display_name="Player Two",
                played=0, wins=0, draws=0, losses=0, points=0
            ),
        ]

        # Multiple match results
        results = [
            {"status": GameStatus.WIN, "score": {"P01": 3, "P02": 0}},
            {"status": GameStatus.DRAW, "score": {"P01": 1, "P02": 1}},
            {"status": GameStatus.WIN, "score": {"P02": 3, "P01": 0}},
        ]

        for result in results:
            standings = calc.update_standings(standings, result)

        # After all results: P01 has 1W+1D=4pts, P02 has 1W+1D=4pts
        # P01 should rank higher with 1 win vs P02's 1 win, so alphabetical
        final = calc.calculate_ranks(standings)
        assert final[0].points == 4
        assert final[1].points == 4


class TestSchedulerEdgeCases:
    """Test edge cases in round-robin scheduler"""

    def test_scheduler_with_many_players(self):
        """Test scheduler with 10 players"""
        players = [f"P{i:02d}" for i in range(1, 11)]
        referees = ["REF01", "REF02", "REF03"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # C(10,2) = 45 matches
        total_matches = sum(len(round_matches) for round_matches in schedule)
        assert total_matches == 45

        # Verify no duplicates
        all_pairs = set()
        for round_matches in schedule:
            for match in round_matches:
                pair = tuple(sorted([match.player_A_id, match.player_B_id]))
                assert pair not in all_pairs
                all_pairs.add(pair)

    def test_scheduler_referee_rotation(self):
        """Test that referees are rotated fairly"""
        players = ["P01", "P02", "P03", "P04"]
        referees = ["REF01", "REF02"]

        scheduler = RoundRobinScheduler(players, referees)
        schedule = scheduler.generate_schedule()

        # Count matches per referee
        ref_counts = {}
        for round_matches in schedule:
            for match in round_matches:
                ref_endpoint = match.referee_endpoint
                ref_counts[ref_endpoint] = ref_counts.get(ref_endpoint, 0) + 1

        # Referees should have roughly equal matches
        counts = list(ref_counts.values())
        assert max(counts) - min(counts) <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
