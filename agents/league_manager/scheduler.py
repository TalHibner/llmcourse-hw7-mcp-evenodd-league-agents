"""
Round-Robin scheduler for league matches.

Generates fair match pairings ensuring each player faces every other player.
"""

from typing import List, Tuple
from SHARED.league_sdk.models import MatchInfo


class RoundRobinScheduler:
    """
    Round-Robin tournament scheduler.

    Generates a schedule where each player plays against every other player exactly once.
    """

    def __init__(self, player_ids: List[str], referee_ids: List[str]):
        """
        Initialize scheduler.

        Args:
            player_ids: List of player IDs
            referee_ids: List of referee IDs
        """
        self.player_ids = player_ids
        self.referee_ids = referee_ids

    def generate_schedule(self) -> List[List[MatchInfo]]:
        """
        Generate complete round-robin schedule.

        Returns:
            List of rounds, where each round is a list of MatchInfo objects
        """
        num_players = len(self.player_ids)

        if num_players < 2:
            return []

        # Generate all pairings
        pairings = self._generate_round_robin_pairings()

        # Group pairings into rounds (parallel matches)
        rounds = self._group_into_rounds(pairings)

        # Assign referees and create MatchInfo objects
        match_schedule = []
        for round_idx, round_pairings in enumerate(rounds):
            round_id = f"R{round_idx + 1}"
            matches = []

            for match_idx, (player_a, player_b) in enumerate(round_pairings):
                match_id = f"{round_id}M{match_idx + 1}"

                # Round-robin referee assignment
                referee_idx = match_idx % len(self.referee_ids)
                referee_id = self.referee_ids[referee_idx]

                # Get referee endpoint from config
                from SHARED.league_sdk.config_loader import get_config_loader
                config_loader = get_config_loader()
                referee_config = config_loader.get_referee_by_id(referee_id)
                referee_endpoint = referee_config.endpoint if referee_config else f"http://localhost:800{referee_idx + 1}/mcp"

                match_info = MatchInfo(
                    match_id=match_id,
                    game_type="even_odd",
                    player_A_id=player_a,
                    player_B_id=player_b,
                    referee_endpoint=referee_endpoint
                )
                matches.append(match_info)

            match_schedule.append(matches)

        return match_schedule

    def _generate_round_robin_pairings(self) -> List[Tuple[str, str]]:
        """
        Generate all unique pairings for round-robin.

        Returns:
            List of (player_a, player_b) tuples
        """
        pairings = []
        num_players = len(self.player_ids)

        for i in range(num_players):
            for j in range(i + 1, num_players):
                pairings.append((self.player_ids[i], self.player_ids[j]))

        return pairings

    def _group_into_rounds(
        self,
        pairings: List[Tuple[str, str]]
    ) -> List[List[Tuple[str, str]]]:
        """
        Group pairings into rounds ensuring no player plays twice in same round.

        Args:
            pairings: List of (player_a, player_b) tuples

        Returns:
            List of rounds, where each round is a list of pairings
        """
        rounds = []
        remaining = pairings.copy()

        while remaining:
            current_round = []
            used_players = set()

            # Greedy assignment: take pairings where neither player is used
            to_remove = []
            for pairing in remaining:
                player_a, player_b = pairing
                if player_a not in used_players and player_b not in used_players:
                    current_round.append(pairing)
                    used_players.add(player_a)
                    used_players.add(player_b)
                    to_remove.append(pairing)

            # Remove assigned pairings
            for pairing in to_remove:
                remaining.remove(pairing)

            if current_round:
                rounds.append(current_round)

        return rounds
