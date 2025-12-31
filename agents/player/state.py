"""
Player state tracker.

Tracks player statistics and current match state.
"""

from typing import Dict, Optional


class PlayerState:
    """
    Track player state and statistics.

    Maintains in-memory stats for the current session.
    """

    def __init__(self, player_id: str, display_name: str):
        """
        Initialize player state.

        Args:
            player_id: Player identifier
            display_name: Player display name
        """
        self.player_id = player_id
        self.display_name = display_name

        # Statistics
        self.total_matches = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.total_points = 0

        # Current match state
        self.current_match_id: Optional[str] = None
        self.current_opponent_id: Optional[str] = None
        self.current_role: Optional[str] = None
        self.current_choice: Optional[str] = None

    def start_match(
        self,
        match_id: str,
        opponent_id: str,
        role: str
    ) -> None:
        """
        Start a new match.

        Args:
            match_id: Match identifier
            opponent_id: Opponent's player ID
            role: Player's role in match (PLAYER_A or PLAYER_B)
        """
        self.current_match_id = match_id
        self.current_opponent_id = opponent_id
        self.current_role = role
        self.current_choice = None

    def set_choice(self, choice: str) -> None:
        """Set the player's choice for current match"""
        self.current_choice = choice

    def update_stats(self, result: str, points: int) -> None:
        """
        Update statistics after match.

        Args:
            result: Match result (WIN, DRAW, LOSS)
            points: Points earned
        """
        self.total_matches += 1
        self.total_points += points

        if result == "WIN":
            self.wins += 1
        elif result == "DRAW":
            self.draws += 1
        elif result == "LOSS":
            self.losses += 1

    def clear_match_state(self) -> None:
        """Clear current match state"""
        self.current_match_id = None
        self.current_opponent_id = None
        self.current_role = None
        self.current_choice = None

    def get_stats(self) -> Dict:
        """
        Get current statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "total_matches": self.total_matches,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "total_points": self.total_points,
            "win_rate": self.wins / self.total_matches if self.total_matches > 0 else 0.0
        }
