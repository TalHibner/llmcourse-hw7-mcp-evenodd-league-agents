"""
Match state machine manager.

Manages the lifecycle of a match from invitation to completion.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Optional
from SHARED.league_sdk.models import (
    GameInvitation, GameJoinAck, ChooseParityCall,
    ChooseParityResponse, GameOver, MatchResultReport,
    ParityChoice, GameResult, GameStatus
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.repositories import MatchRepository
from SHARED.league_sdk.mcp_client import MCPClient
from .game_logic import EvenOddGame


class MatchState(str, Enum):
    """Match lifecycle states"""
    CREATED = "CREATED"
    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    COLLECTING_CHOICES = "COLLECTING_CHOICES"
    DRAWING_NUMBER = "DRAWING_NUMBER"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class MatchManager:
    """
    Manages a single match.

    Handles state transitions, timeouts, and game logic.
    """

    def __init__(
        self,
        match_id: str,
        round_id: str,
        league_id: str,
        referee_id: str,
        player_a_id: str,
        player_b_id: str,
        player_a_endpoint: str,
        player_b_endpoint: str,
        league_manager_endpoint: str,
        logger: JsonLogger,
        match_repo: MatchRepository,
        game_logic: EvenOddGame,
        join_timeout_sec: int = 5,
        move_timeout_sec: int = 30
    ):
        """Initialize match manager"""
        self.match_id = match_id
        self.round_id = round_id
        self.league_id = league_id
        self.referee_id = referee_id
        self.player_a_id = player_a_id
        self.player_b_id = player_b_id
        self.player_a_endpoint = player_a_endpoint
        self.player_b_endpoint = player_b_endpoint
        self.league_manager_endpoint = league_manager_endpoint
        self.logger = logger
        self.match_repo = match_repo
        self.game_logic = game_logic
        self.join_timeout_sec = join_timeout_sec
        self.move_timeout_sec = move_timeout_sec

        self.state = MatchState.CREATED
        self.player_choices: Dict[str, ParityChoice] = {}
        self.join_acks: Dict[str, bool] = {}

    async def run_match(self) -> None:
        """Run the complete match"""
        try:
            # Create match record
            self.match_repo.create_match(
                self.match_id, self.round_id, self.league_id,
                self.referee_id, self.player_a_id, self.player_b_id
            )

            # Send invitations
            await self._send_invitations()

            # Wait for join acknowledgments
            joined = await self._wait_for_joins()
            if not joined:
                await self._cancel_match("Players failed to join")
                return

            # Collect parity choices
            choices_collected = await self._collect_choices()
            if not choices_collected:
                await self._cancel_match("Failed to collect choices")
                return

            # Determine winner
            await self._determine_and_announce_winner()

            # Report result to league manager
            await self._report_result()

        except Exception as e:
            self.logger.error("MATCH_ERROR", match_id=self.match_id, error=str(e))
            await self._cancel_match(f"Error: {str(e)}")

    async def _send_invitations(self) -> None:
        """Send game invitations to both players"""
        self.state = MatchState.WAITING_FOR_PLAYERS
        self.match_repo.add_state_transition(self.match_id, self.state.value)

        async with MCPClient(logger=self.logger) as client:
            # Invitation to Player A
            inv_a = GameInvitation(
                sender=f"referee:{self.referee_id}",
                timestamp=datetime.now(timezone.utc),
                conversation_id=self.match_id,
                auth_token="",
                match_id=self.match_id,
                game_type="even_odd",
                role_in_match="PLAYER_A",
                opponent_id=self.player_b_id
            )

            # Invitation to Player B
            inv_b = GameInvitation(
                sender=f"referee:{self.referee_id}",
                timestamp=datetime.now(timezone.utc),
                conversation_id=self.match_id,
                auth_token="",
                match_id=self.match_id,
                game_type="even_odd",
                role_in_match="PLAYER_B",
                opponent_id=self.player_a_id
            )

            # Send invitations
            await asyncio.gather(
                client.call_tool(
                    self.player_a_endpoint,
                    "receive_game_invitation",
                    inv_a.model_dump()
                ),
                client.call_tool(
                    self.player_b_endpoint,
                    "receive_game_invitation",
                    inv_b.model_dump()
                )
            )

            self.logger.info("INVITATIONS_SENT", match_id=self.match_id)

    async def _wait_for_joins(self) -> bool:
        """Wait for both players to join"""
        try:
            await asyncio.wait_for(
                self._wait_for_both_joins(),
                timeout=self.join_timeout_sec
            )
            return True
        except asyncio.TimeoutError:
            self.logger.warning("JOIN_TIMEOUT", match_id=self.match_id)
            return False

    async def _wait_for_both_joins(self) -> None:
        """Helper to wait for both joins"""
        while len(self.join_acks) < 2:
            await asyncio.sleep(0.1)

    def handle_join_ack(self, player_id: str, accept: bool) -> None:
        """Handle player join acknowledgment"""
        self.join_acks[player_id] = accept
        self.logger.info(
            "JOIN_ACK_RECEIVED",
            match_id=self.match_id,
            player_id=player_id,
            accept=accept
        )

    async def _collect_choices(self) -> bool:
        """Request and collect parity choices from both players"""
        self.state = MatchState.COLLECTING_CHOICES
        self.match_repo.add_state_transition(self.match_id, self.state.value)

        deadline = datetime.now(timezone.utc) + timedelta(seconds=self.move_timeout_sec)

        async with MCPClient(logger=self.logger) as client:
            # Request choices
            call_a = ChooseParityCall(
                sender=f"referee:{self.referee_id}",
                timestamp=datetime.now(timezone.utc),
                conversation_id=self.match_id,
                auth_token="",
                match_id=self.match_id,
                game_type="even_odd",
                deadline=deadline
            )

            call_b = ChooseParityCall(
                sender=f"referee:{self.referee_id}",
                timestamp=datetime.now(timezone.utc),
                conversation_id=self.match_id,
                auth_token="",
                match_id=self.match_id,
                game_type="even_odd",
                deadline=deadline
            )

            # Send requests
            await asyncio.gather(
                client.call_tool(
                    self.player_a_endpoint,
                    "receive_parity_call",
                    call_a.model_dump()
                ),
                client.call_tool(
                    self.player_b_endpoint,
                    "receive_parity_call",
                    call_b.model_dump()
                )
            )

        # Wait for both choices
        try:
            await asyncio.wait_for(
                self._wait_for_both_choices(),
                timeout=self.move_timeout_sec
            )
            return True
        except asyncio.TimeoutError:
            self.logger.warning("CHOICE_TIMEOUT", match_id=self.match_id)
            return False

    async def _wait_for_both_choices(self) -> None:
        """Helper to wait for both choices"""
        while len(self.player_choices) < 2:
            await asyncio.sleep(0.1)

    def handle_parity_choice(self, player_id: str, choice: ParityChoice) -> None:
        """Handle player parity choice"""
        self.player_choices[player_id] = choice
        self.logger.info(
            "CHOICE_RECEIVED",
            match_id=self.match_id,
            player_id=player_id,
            choice=choice.value
        )

    async def _determine_and_announce_winner(self) -> None:
        """Determine winner and announce to both players"""
        self.state = MatchState.DRAWING_NUMBER
        self.match_repo.add_state_transition(self.match_id, self.state.value)

        # Determine winner
        result, score = self.game_logic.determine_winner(
            self.player_a_id,
            self.player_b_id,
            self.player_choices[self.player_a_id],
            self.player_choices[self.player_b_id]
        )

        # Save result
        self.match_repo.save_result(self.match_id, result, score)

        self.state = MatchState.FINISHED
        self.match_repo.add_state_transition(self.match_id, self.state.value)

        # Announce to both players
        game_over = GameOver(
            sender=f"referee:{self.referee_id}",
            timestamp=datetime.now(timezone.utc),
            conversation_id=self.match_id,
            auth_token="",
            match_id=self.match_id,
            game_result=result
        )

        async with MCPClient(logger=self.logger) as client:
            await asyncio.gather(
                client.call_tool(
                    self.player_a_endpoint,
                    "receive_game_over",
                    game_over.model_dump()
                ),
                client.call_tool(
                    self.player_b_endpoint,
                    "receive_game_over",
                    game_over.model_dump()
                ),
                return_exceptions=True
            )

        self.logger.info(
            "MATCH_COMPLETED",
            match_id=self.match_id,
            winner=result.winner_player_id,
            status=result.status
        )

    async def _report_result(self) -> None:
        """Report match result to league manager"""
        match_data = self.match_repo.load_match(self.match_id)
        if not match_data or not match_data.get("result"):
            return

        result_data = match_data["result"]
        result = GameResult(**{k: v for k, v in result_data.items() if k != "score"})
        score = result_data["score"]

        report = MatchResultReport(
            sender=f"referee:{self.referee_id}",
            timestamp=datetime.now(timezone.utc),
            conversation_id=self.match_id,
            auth_token="",
            match_id=self.match_id,
            round_id=self.round_id,
            league_id=self.league_id,
            result=result,
            score=score
        )

        async with MCPClient(logger=self.logger) as client:
            await client.call_tool(
                self.league_manager_endpoint,
                "report_match_result",
                report.model_dump()
            )

        self.logger.info("RESULT_REPORTED", match_id=self.match_id)

    async def _cancel_match(self, reason: str) -> None:
        """Cancel the match"""
        self.state = MatchState.CANCELLED
        self.match_repo.add_state_transition(self.match_id, self.state.value)

        self.logger.warning("MATCH_CANCELLED", match_id=self.match_id, reason=reason)

        # Report cancellation
        result = GameResult(
            status=GameStatus.CANCELLED,
            winner_player_id=None,
            drawn_number=None,
            number_parity=None,
            choices=None,
            reason=reason
        )
        score = {self.player_a_id: 0, self.player_b_id: 0}

        self.match_repo.save_result(self.match_id, result, score)
        await self._report_result()
