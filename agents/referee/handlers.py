"""
Message handlers for Referee agent.

Handles game join acknowledgments and parity responses.
"""

from typing import Dict
from SHARED.league_sdk.models import GameJoinAck, ChooseParityResponse
from SHARED.league_sdk.logger import JsonLogger
from .match_manager import MatchManager


class RefereeHandlers:
    """Handlers for referee messages"""

    def __init__(self, logger: JsonLogger):
        """
        Initialize handlers.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.active_matches: Dict[str, MatchManager] = {}

    def register_match(self, match_id: str, match_manager: MatchManager) -> None:
        """Register an active match"""
        self.active_matches[match_id] = match_manager

    def unregister_match(self, match_id: str) -> None:
        """Unregister a completed match"""
        if match_id in self.active_matches:
            del self.active_matches[match_id]

    def handle_game_join_ack(self, ack: GameJoinAck) -> Dict:
        """
        Handle GAME_JOIN_ACK message.

        Args:
            ack: Join acknowledgment message

        Returns:
            Response dictionary
        """
        match_id = ack.match_id
        player_id = ack.sender.split(":")[-1]

        self.logger.info(
            "GAME_JOIN_ACK_RECEIVED",
            match_id=match_id,
            player_id=player_id,
            accept=ack.accept
        )

        # Forward to match manager
        if match_id in self.active_matches:
            match_manager = self.active_matches[match_id]
            match_manager.handle_join_ack(player_id, ack.accept)

        return {"status": "acknowledged"}

    def handle_parity_response(self, response: ChooseParityResponse) -> Dict:
        """
        Handle CHOOSE_PARITY_RESPONSE message.

        Args:
            response: Parity choice response

        Returns:
            Response dictionary
        """
        match_id = response.match_id
        player_id = response.sender.split(":")[-1]
        choice = response.parity_choice

        self.logger.info(
            "PARITY_RESPONSE_RECEIVED",
            match_id=match_id,
            player_id=player_id,
            choice=choice.value
        )

        # Forward to match manager
        if match_id in self.active_matches:
            match_manager = self.active_matches[match_id]
            match_manager.handle_parity_choice(player_id, choice)

        return {"status": "acknowledged"}
