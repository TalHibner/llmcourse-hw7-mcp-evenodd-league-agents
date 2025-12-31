"""
Message handlers for Player agent.

Handles all incoming MCP messages.
"""

from datetime import datetime, timezone
from typing import Dict
from SHARED.league_sdk.models import (
    RoundAnnouncement, GameInvitation, GameJoinAck,
    ChooseParityCall, ChooseParityResponse, GameOver,
    LeagueStandingsUpdate, RoundCompleted, LeagueCompleted,
    ParityChoice
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.mcp_client import MCPClient
from .state import PlayerState
from .history import HistoryManager
from .strategy import StrategyFactory


class PlayerHandlers:
    """Handlers for all player messages"""

    def __init__(
        self,
        player_id: str,
        display_name: str,
        strategy_name: str,
        logger: JsonLogger
    ):
        """
        Initialize handlers.

        Args:
            player_id: Player identifier
            display_name: Player display name
            strategy_name: Strategy name
            logger: Logger instance
        """
        self.player_id = player_id
        self.display_name = display_name
        self.logger = logger

        # State and history
        self.state = PlayerState(player_id, display_name)
        self.history = HistoryManager(player_id)

        # Strategy
        self.strategy = StrategyFactory.create(strategy_name)

        # Referee endpoint for current match
        self.current_referee_endpoint = None

    def handle_round_announcement(self, announcement: RoundAnnouncement) -> Dict:
        """
        Handle ROUND_ANNOUNCEMENT message.

        Args:
            announcement: Round announcement

        Returns:
            Response dictionary
        """
        self.logger.info(
            "ROUND_ANNOUNCED",
            round_id=announcement.round_id,
            num_matches=len(announcement.matches)
        )

        # Check if we're in any match this round
        for match in announcement.matches:
            if match.player_A_id == self.player_id or match.player_B_id == self.player_id:
                self.logger.info(
                    "MATCH_ASSIGNED",
                    match_id=match.match_id,
                    opponent=match.player_B_id if match.player_A_id == self.player_id else match.player_A_id
                )

        return {"status": "acknowledged"}

    async def handle_game_invitation(self, invitation: GameInvitation) -> Dict:
        """
        Handle GAME_INVITATION message.

        Args:
            invitation: Game invitation

        Returns:
            Response dictionary
        """
        self.logger.info(
            "GAME_INVITATION_RECEIVED",
            match_id=invitation.match_id,
            opponent=invitation.opponent_id,
            role=invitation.role_in_match
        )

        # Update state
        self.state.start_match(
            invitation.match_id,
            invitation.opponent_id,
            invitation.role_in_match
        )

        # Extract referee endpoint from sender
        self.current_referee_endpoint = invitation.sender.split(":")[0]
        # Actually we need to get it from config
        from SHARED.league_sdk.config_loader import get_config_loader
        config = get_config_loader()
        agents = config.load_agents()

        # Find referee endpoint (sender format is "referee:REF01")
        referee_id = invitation.sender.split(":")[-1]
        for ref in agents.referees:
            if ref.referee_id == referee_id:
                self.current_referee_endpoint = ref.endpoint
                break

        # Send JOIN_ACK
        ack = GameJoinAck(
            sender=f"player:{self.player_id}",
            timestamp=datetime.now(timezone.utc),
            conversation_id=invitation.match_id,
            auth_token="",
            match_id=invitation.match_id,
            accept=True,
            arrival_timestamp=datetime.now(timezone.utc)
        )

        # Send to referee
        async with MCPClient(logger=self.logger) as client:
            await client.call_tool(
                endpoint=self.current_referee_endpoint,
                method="receive_game_join_ack",
                params=ack.model_dump()
            )

        self.logger.info("GAME_JOIN_ACK_SENT", match_id=invitation.match_id)

        return {"status": "joined"}

    async def handle_parity_call(self, call: ChooseParityCall) -> Dict:
        """
        Handle CHOOSE_PARITY_CALL message.

        Args:
            call: Parity choice request

        Returns:
            Response dictionary
        """
        self.logger.info(
            "PARITY_CALL_RECEIVED",
            match_id=call.match_id
        )

        # Get opponent history
        opponent_id = self.state.current_opponent_id
        opponent_history = self.history.get_opponent_history(opponent_id) if opponent_id else []

        # Use strategy to choose
        choice = self.strategy.choose(opponent_id, opponent_history)

        # Update state
        self.state.set_choice(choice.value)

        self.logger.info(
            "PARITY_CHOSEN",
            match_id=call.match_id,
            choice=choice.value
        )

        # Send response
        response = ChooseParityResponse(
            sender=f"player:{self.player_id}",
            timestamp=datetime.now(timezone.utc),
            conversation_id=call.match_id,
            auth_token="",
            match_id=call.match_id,
            parity_choice=choice
        )

        # Send to referee
        async with MCPClient(logger=self.logger) as client:
            await client.call_tool(
                endpoint=self.current_referee_endpoint,
                method="receive_parity_response",
                params=response.model_dump()
            )

        self.logger.info("PARITY_RESPONSE_SENT", match_id=call.match_id)

        return {"status": "choice_sent"}

    def handle_game_over(self, game_over: GameOver) -> Dict:
        """
        Handle GAME_OVER message.

        Args:
            game_over: Game result

        Returns:
            Response dictionary
        """
        result = game_over.game_result

        self.logger.info(
            "GAME_OVER_RECEIVED",
            match_id=game_over.match_id,
            status=result.status,
            winner=result.winner_player_id
        )

        # Determine my result
        if result.winner_player_id == self.player_id:
            my_result = "WIN"
            my_points = 3
        elif result.winner_player_id is None:
            my_result = "DRAW"
            my_points = 1
        else:
            my_result = "LOSS"
            my_points = 0

        # Update state
        self.state.update_stats(my_result, my_points)

        # Add to history
        if result.choices:
            my_choice = result.choices.get(self.player_id, "unknown")
            opponent_choice = result.choices.get(self.state.current_opponent_id, "unknown")

            self.history.add_match(
                match_id=game_over.match_id,
                opponent_id=self.state.current_opponent_id,
                result=my_result,
                points=my_points,
                my_choice=my_choice,
                opponent_choice=opponent_choice,
                drawn_number=result.drawn_number or 0
            )

        # Clear match state
        self.state.clear_match_state()

        self.logger.info(
            "MATCH_COMPLETED",
            match_id=game_over.match_id,
            result=my_result,
            points=my_points
        )

        return {"status": "acknowledged"}

    def handle_standings_update(self, update: LeagueStandingsUpdate) -> Dict:
        """
        Handle LEAGUE_STANDINGS_UPDATE message.

        Args:
            update: Standings update

        Returns:
            Response dictionary
        """
        self.logger.info(
            "STANDINGS_UPDATE_RECEIVED",
            round_id=update.round_id,
            num_players=len(update.standings)
        )

        # Find my standing
        my_standing = None
        for standing in update.standings:
            if standing.player_id == self.player_id:
                my_standing = standing
                break

        if my_standing:
            self.logger.info(
                "MY_STANDING",
                rank=my_standing.rank,
                points=my_standing.points,
                wins=my_standing.wins,
                draws=my_standing.draws,
                losses=my_standing.losses
            )

        return {"status": "acknowledged"}

    def handle_round_completed(self, completed: RoundCompleted) -> Dict:
        """
        Handle ROUND_COMPLETED message.

        Args:
            completed: Round completion notification

        Returns:
            Response dictionary
        """
        self.logger.info(
            "ROUND_COMPLETED",
            round_id=completed.round_id,
            next_round=completed.next_round_id
        )

        return {"status": "acknowledged"}

    def handle_league_completed(self, completed: LeagueCompleted) -> Dict:
        """
        Handle LEAGUE_COMPLETED message.

        Args:
            completed: League completion notification

        Returns:
            Response dictionary
        """
        self.logger.info(
            "LEAGUE_COMPLETED",
            champion=completed.champion.player_id,
            total_rounds=completed.total_rounds,
            total_matches=completed.total_matches
        )

        # Find my final standing
        my_standing = None
        for standing in completed.final_standings:
            if standing.player_id == self.player_id:
                my_standing = standing
                break

        if my_standing:
            self.logger.info(
                "FINAL_STANDING",
                rank=my_standing.rank,
                points=my_standing.points,
                wins=my_standing.wins,
                draws=my_standing.draws,
                losses=my_standing.losses
            )

        return {"status": "acknowledged"}

    def get_stats(self) -> Dict:
        """Get current player statistics"""
        return self.state.get_stats()
