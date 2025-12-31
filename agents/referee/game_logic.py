"""
Even/Odd game logic module.

Implements the rules for determining winners in the Even/Odd game.
"""

import random
from typing import Dict, Optional, Tuple
from SHARED.league_sdk.models import ParityChoice, GameResult, GameStatus


class EvenOddGame:
    """
    Even/Odd game logic.

    Rules:
    1. Both players choose "even" or "odd"
    2. A random number is drawn from range
    3. Winner is the player who chose the correct parity
    4. If both choose same parity and it's correct: DRAW
    5. If both choose same parity and it's wrong: DRAW
    6. If different parities: winner gets 3 points, loser gets 0
    """

    def __init__(
        self,
        number_range_min: int = 1,
        number_range_max: int = 10,
        draw_on_both_wrong: bool = True
    ):
        """
        Initialize game logic.

        Args:
            number_range_min: Minimum number in range
            number_range_max: Maximum number in range
            draw_on_both_wrong: Whether both wrong choices result in draw
        """
        self.number_range_min = number_range_min
        self.number_range_max = number_range_max
        self.draw_on_both_wrong = draw_on_both_wrong

    def draw_number(self) -> int:
        """Draw a random number from the range"""
        return random.randint(self.number_range_min, self.number_range_max)

    def determine_parity(self, number: int) -> ParityChoice:
        """Determine if a number is even or odd"""
        return ParityChoice.EVEN if number % 2 == 0 else ParityChoice.ODD

    def determine_winner(
        self,
        player_a_id: str,
        player_b_id: str,
        player_a_choice: ParityChoice,
        player_b_choice: ParityChoice,
        drawn_number: Optional[int] = None
    ) -> Tuple[GameResult, Dict[str, int]]:
        """
        Determine the winner based on choices and drawn number.

        Args:
            player_a_id: Player A's ID
            player_b_id: Player B's ID
            player_a_choice: Player A's parity choice
            player_b_choice: Player B's parity choice
            drawn_number: Optional pre-drawn number (if None, will draw new one)

        Returns:
            Tuple of (GameResult, score_dict)
        """
        # Draw number if not provided
        if drawn_number is None:
            drawn_number = self.draw_number()

        # Determine actual parity
        actual_parity = self.determine_parity(drawn_number)

        # Create choices dict
        choices = {
            player_a_id: player_a_choice,
            player_b_id: player_b_choice
        }

        # Check if both chose the same
        if player_a_choice == player_b_choice:
            # Both chose same parity
            if player_a_choice == actual_parity:
                # Both correct -> DRAW
                return (
                    GameResult(
                        status=GameStatus.DRAW,
                        winner_player_id=None,
                        drawn_number=drawn_number,
                        number_parity=actual_parity,
                        choices=choices,
                        reason=f"Both players chose '{player_a_choice.value}' and number {drawn_number} is {actual_parity.value}"
                    ),
                    {player_a_id: 1, player_b_id: 1}
                )
            else:
                # Both wrong -> DRAW (if configured)
                if self.draw_on_both_wrong:
                    return (
                        GameResult(
                            status=GameStatus.DRAW,
                            winner_player_id=None,
                            drawn_number=drawn_number,
                            number_parity=actual_parity,
                            choices=choices,
                            reason=f"Both players chose '{player_a_choice.value}' but number {drawn_number} is {actual_parity.value}"
                        ),
                        {player_a_id: 1, player_b_id: 1}
                    )
                else:
                    # Both wrong -> no winner, 0 points each
                    return (
                        GameResult(
                            status=GameStatus.DRAW,
                            winner_player_id=None,
                            drawn_number=drawn_number,
                            number_parity=actual_parity,
                            choices=choices,
                            reason=f"Both players chose wrong parity"
                        ),
                        {player_a_id: 0, player_b_id: 0}
                    )
        else:
            # Different choices - determine winner
            if player_a_choice == actual_parity:
                # Player A wins
                return (
                    GameResult(
                        status=GameStatus.WIN,
                        winner_player_id=player_a_id,
                        drawn_number=drawn_number,
                        number_parity=actual_parity,
                        choices=choices,
                        reason=f"{player_a_id} chose '{player_a_choice.value}', number {drawn_number} is {actual_parity.value}"
                    ),
                    {player_a_id: 3, player_b_id: 0}
                )
            else:
                # Player B wins
                return (
                    GameResult(
                        status=GameStatus.WIN,
                        winner_player_id=player_b_id,
                        drawn_number=drawn_number,
                        number_parity=actual_parity,
                        choices=choices,
                        reason=f"{player_b_id} chose '{player_b_choice.value}', number {drawn_number} is {actual_parity.value}"
                    ),
                    {player_a_id: 0, player_b_id: 3}
                )
