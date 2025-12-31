"""
Player match history manager.

Manages persistent match history and provides query methods.
"""

from typing import List, Dict
from SHARED.league_sdk.repositories import PlayerHistoryRepository


class HistoryManager:
    """
    Manage player match history.

    Provides methods to add matches and query history.
    """

    def __init__(self, player_id: str):
        """
        Initialize history manager.

        Args:
            player_id: Player identifier
        """
        self.player_id = player_id
        self.repository = PlayerHistoryRepository(player_id)

    def add_match(
        self,
        match_id: str,
        opponent_id: str,
        result: str,
        points: int,
        my_choice: str,
        opponent_choice: str,
        drawn_number: int
    ) -> None:
        """
        Add a match to history.

        Args:
            match_id: Match identifier
            opponent_id: Opponent's player ID
            result: Match result (WIN, DRAW, LOSS)
            points: Points earned
            my_choice: Player's choice
            opponent_choice: Opponent's choice
            drawn_number: Number that was drawn
        """
        self.repository.add_match_result(
            match_id=match_id,
            opponent_id=opponent_id,
            result=result,
            points=points,
            my_choice=my_choice,
            opponent_choice=opponent_choice,
            drawn_number=drawn_number
        )

    def get_opponent_history(self, opponent_id: str) -> List[Dict]:
        """
        Get match history against a specific opponent.

        Args:
            opponent_id: Opponent's player ID

        Returns:
            List of match records
        """
        return self.repository.get_opponent_history(opponent_id)

    def get_all_history(self) -> Dict:
        """
        Get complete match history.

        Returns:
            Complete history dictionary
        """
        return self.repository.load()

    def get_stats(self) -> Dict:
        """
        Get aggregate statistics from history.

        Returns:
            Statistics dictionary
        """
        history = self.repository.load()
        return {
            "total_matches": history.get("total_matches", 0),
            "total_wins": history.get("total_wins", 0),
            "total_draws": history.get("total_draws", 0),
            "total_losses": history.get("total_losses", 0)
        }
