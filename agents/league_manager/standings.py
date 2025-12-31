"""
Standings calculator for league rankings.

Calculates player rankings based on wins, draws, and points.
"""

from typing import Dict, List
from SHARED.league_sdk.models import StandingEntry, GameStatus


class StandingsCalculator:
    """
    Calculate and update league standings.

    Rankings are determined by:
    1. Total points (primary)
    2. Number of wins (tiebreaker)
    3. Player ID alphabetically (final tiebreaker)
    """

    def __init__(
        self,
        win_points: int = 3,
        draw_points: int = 1,
        loss_points: int = 0
    ):
        """
        Initialize standings calculator.

        Args:
            win_points: Points awarded for a win
            draw_points: Points awarded for a draw
            loss_points: Points awarded for a loss
        """
        self.win_points = win_points
        self.draw_points = draw_points
        self.loss_points = loss_points

    def initialize_standings(
        self,
        player_ids: List[str],
        player_names: Dict[str, str]
    ) -> List[StandingEntry]:
        """
        Initialize standings with zero stats for all players.

        Args:
            player_ids: List of player IDs
            player_names: Mapping of player_id to display_name

        Returns:
            List of StandingEntry objects
        """
        standings = []
        for player_id in sorted(player_ids):  # Alphabetical for consistency
            standings.append(StandingEntry(
                rank=1,
                player_id=player_id,
                display_name=player_names.get(player_id, player_id),
                played=0,
                wins=0,
                draws=0,
                losses=0,
                points=0
            ))
        return standings

    def update_standings(
        self,
        current_standings: List[StandingEntry],
        match_result: Dict[str, any]
    ) -> List[StandingEntry]:
        """
        Update standings based on match result.

        Args:
            current_standings: Current standings list
            match_result: Match result dictionary with status and score

        Returns:
            Updated standings list
        """
        # Create mutable dict from standings
        standings_dict = {
            entry.player_id: entry.model_dump()
            for entry in current_standings
        }

        # Extract result info
        status = match_result.get("status")
        score = match_result.get("score", {})

        # Update each player's stats
        for player_id, points in score.items():
            if player_id not in standings_dict:
                continue

            player_stats = standings_dict[player_id]
            player_stats["played"] += 1

            if status == GameStatus.WIN:
                if points == self.win_points:
                    player_stats["wins"] += 1
                    player_stats["points"] += self.win_points
                else:
                    player_stats["losses"] += 1
                    player_stats["points"] += self.loss_points

            elif status == GameStatus.DRAW:
                player_stats["draws"] += 1
                player_stats["points"] += self.draw_points

            elif status == GameStatus.CANCELLED:
                # Don't update stats for cancelled matches
                player_stats["played"] -= 1

        # Convert back to list and calculate ranks
        standings_list = [
            StandingEntry(**stats) for stats in standings_dict.values()
        ]

        return self.calculate_ranks(standings_list)

    def calculate_ranks(
        self,
        standings: List[StandingEntry]
    ) -> List[StandingEntry]:
        """
        Calculate ranks based on points, wins, and player ID.

        Args:
            standings: List of standings entries

        Returns:
            Sorted standings with updated ranks
        """
        # Sort by: points (desc), wins (desc), player_id (asc)
        sorted_standings = sorted(
            standings,
            key=lambda x: (-x.points, -x.wins, x.player_id)
        )

        # Assign ranks
        for rank, entry in enumerate(sorted_standings, start=1):
            entry.rank = rank

        return sorted_standings

    def get_champion(self, standings: List[StandingEntry]) -> StandingEntry:
        """
        Get the league champion (rank 1).

        Args:
            standings: Current standings

        Returns:
            Champion's StandingEntry
        """
        ranked_standings = self.calculate_ranks(standings)
        return ranked_standings[0]
