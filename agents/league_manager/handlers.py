"""
Message handlers for League Manager.

Handles registration requests and match result reports.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import asyncio

from SHARED.league_sdk.models import (
    RefereeRegisterRequest, RefereeRegisterResponse,
    LeagueRegisterRequest, LeagueRegisterResponse,
    MatchResultReport, RoundAnnouncement,
    LeagueStandingsUpdate, RoundCompleted, LeagueCompleted,
    RegistrationStatus, StandingEntry
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.repositories import StandingsRepository, RoundsRepository
from SHARED.league_sdk.mcp_client import MCPClient
from SHARED.league_sdk.auth import JWTAuthenticator
from .standings import StandingsCalculator


class RegistrationHandler:
    """Handle referee and player registrations"""

    def __init__(
        self,
        league_id: str,
        logger: JsonLogger,
        jwt_authenticator: Optional[JWTAuthenticator] = None
    ):
        """
        Initialize registration handler.

        Args:
            league_id: League identifier
            logger: Logger instance
            jwt_authenticator: JWT authenticator instance (creates new if None)
        """
        self.league_id = league_id
        self.logger = logger
        self.jwt_auth = jwt_authenticator or JWTAuthenticator()

        # In-memory registries
        self.registered_referees: Dict[str, Dict] = {}
        self.registered_players: Dict[str, Dict] = {}

    def generate_auth_token(self, agent_id: str, agent_type: str) -> str:
        """
        Generate JWT authentication token for agent.

        Args:
            agent_id: Agent identifier (e.g., "P01", "REF01")
            agent_type: Type of agent ("player" or "referee")

        Returns:
            JWT token string
        """
        token = self.jwt_auth.generate_token(
            agent_id=agent_id,
            league_id=self.league_id,
            agent_type=agent_type
        )

        return token

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate a JWT token and return its payload.

        Args:
            token: JWT token to validate

        Returns:
            Token payload if valid, None otherwise
        """
        return self.jwt_auth.validate_token(token)

    def validate_auth_token(self, token: str, agent_id: str) -> bool:
        """
        Validate that a token belongs to a specific agent.

        Args:
            token: JWT token to validate
            agent_id: Agent ID to verify against

        Returns:
            True if token is valid and belongs to the agent, False otherwise
        """
        return self.jwt_auth.verify_agent_access(
            token=token,
            required_agent_id=agent_id,
            required_league_id=self.league_id
        )

    def handle_referee_registration(
        self,
        request: RefereeRegisterRequest
    ) -> RefereeRegisterResponse:
        """
        Handle referee registration request.

        Args:
            request: Registration request

        Returns:
            Registration response
        """
        referee_meta = request.referee_meta
        referee_id = f"REF{len(self.registered_referees) + 1:02d}"

        # Generate JWT auth token
        auth_token = self.generate_auth_token(referee_id, agent_type="referee")

        # Store referee info
        self.registered_referees[referee_id] = {
            "referee_id": referee_id,
            "display_name": referee_meta.display_name,
            "endpoint": referee_meta.contact_endpoint,
            "game_types": referee_meta.game_types,
            "max_concurrent_matches": referee_meta.max_concurrent_matches,
            "auth_token": auth_token
        }

        self.logger.info(
            "REFEREE_REGISTERED",
            referee_id=referee_id,
            display_name=referee_meta.display_name,
            endpoint=referee_meta.contact_endpoint
        )

        return RefereeRegisterResponse(
            sender="league_manager:LEAGUE_MANAGER_01",
            timestamp=datetime.now(timezone.utc),
            conversation_id=request.conversation_id,
            status=RegistrationStatus.ACCEPTED,
            referee_id=referee_id,
            auth_token=auth_token,
            league_id=self.league_id
        )

    def handle_player_registration(
        self,
        request: LeagueRegisterRequest
    ) -> LeagueRegisterResponse:
        """
        Handle player registration request.

        Args:
            request: Registration request

        Returns:
            Registration response
        """
        player_meta = request.player_meta
        player_id = f"P{len(self.registered_players) + 1:02d}"

        # Generate JWT auth token
        auth_token = self.generate_auth_token(player_id, agent_type="player")

        # Store player info
        self.registered_players[player_id] = {
            "player_id": player_id,
            "display_name": player_meta.display_name,
            "endpoint": player_meta.contact_endpoint,
            "game_types": player_meta.game_types,
            "auth_token": auth_token
        }

        self.logger.info(
            "PLAYER_REGISTERED",
            player_id=player_id,
            display_name=player_meta.display_name,
            endpoint=player_meta.contact_endpoint
        )

        return LeagueRegisterResponse(
            sender="league_manager:LEAGUE_MANAGER_01",
            timestamp=datetime.now(timezone.utc),
            conversation_id=request.conversation_id,
            status=RegistrationStatus.ACCEPTED,
            player_id=player_id,
            auth_token=auth_token,
            league_id=self.league_id
        )


class ResultHandler:
    """Handle match result reports"""

    def __init__(
        self,
        league_id: str,
        logger: JsonLogger,
        standings_calculator: StandingsCalculator,
        standings_repo: StandingsRepository,
        rounds_repo: RoundsRepository
    ):
        """
        Initialize result handler.

        Args:
            league_id: League identifier
            logger: Logger instance
            standings_calculator: Standings calculator
            standings_repo: Standings repository
            rounds_repo: Rounds repository
        """
        self.league_id = league_id
        self.logger = logger
        self.standings_calculator = standings_calculator
        self.standings_repo = standings_repo
        self.rounds_repo = rounds_repo

    async def handle_match_result(
        self,
        report: MatchResultReport,
        player_endpoints: Dict[str, str]
    ) -> None:
        """
        Handle match result report.

        Updates standings and broadcasts updates to all players.

        Args:
            report: Match result report
            player_endpoints: Mapping of player_id to endpoint
        """
        self.logger.info(
            "MATCH_RESULT_RECEIVED",
            match_id=report.match_id,
            round_id=report.round_id,
            status=report.result.status
        )

        # Load current standings
        current_standings = self.standings_repo.get_standings()

        # Update standings
        match_result = {
            "status": report.result.status,
            "score": report.score
        }
        updated_standings = self.standings_calculator.update_standings(
            current_standings,
            match_result
        )

        # Save updated standings
        self.standings_repo.update_standings(updated_standings)

        # Mark match as completed in round
        self.rounds_repo.mark_match_completed(report.round_id, report.match_id)

        # Broadcast standings update
        await self._broadcast_standings_update(
            report.round_id,
            updated_standings,
            player_endpoints
        )

        self.logger.info(
            "STANDINGS_UPDATED",
            round_id=report.round_id,
            match_id=report.match_id
        )

    async def _broadcast_standings_update(
        self,
        round_id: str,
        standings: List[StandingEntry],
        player_endpoints: Dict[str, str]
    ) -> None:
        """Broadcast standings update to all players"""
        update_msg = LeagueStandingsUpdate(
            sender="league_manager:LEAGUE_MANAGER_01",
            timestamp=datetime.now(timezone.utc),
            conversation_id=f"standings_{round_id}",
            auth_token="",
            league_id=self.league_id,
            round_id=round_id,
            standings=standings
        )

        # Send to all players in parallel
        tasks = []
        async with MCPClient(logger=self.logger) as client:
            for player_id, endpoint in player_endpoints.items():
                task = client.call_tool(
                    endpoint=endpoint,
                    method="receive_standings_update",
                    params=update_msg.model_dump()
                )
                tasks.append(task)

            # Wait for all broadcasts
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(
                    "STANDINGS_BROADCAST_FAILED",
                    error=str(e)
                )
