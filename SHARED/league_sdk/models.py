"""
Pydantic models for MCP league.v2 protocol messages.

This module defines all 16 core message types and supporting data models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


# Enums
class MessageType(str, Enum):
    """All 16 core message types"""
    # Registration (4)
    REFEREE_REGISTER_REQUEST = "REFEREE_REGISTER_REQUEST"
    REFEREE_REGISTER_RESPONSE = "REFEREE_REGISTER_RESPONSE"
    LEAGUE_REGISTER_REQUEST = "LEAGUE_REGISTER_REQUEST"
    LEAGUE_REGISTER_RESPONSE = "LEAGUE_REGISTER_RESPONSE"
    # Round Management (2)
    ROUND_ANNOUNCEMENT = "ROUND_ANNOUNCEMENT"
    ROUND_COMPLETED = "ROUND_COMPLETED"
    # Game Execution (5)
    GAME_INVITATION = "GAME_INVITATION"
    GAME_JOIN_ACK = "GAME_JOIN_ACK"
    CHOOSE_PARITY_CALL = "CHOOSE_PARITY_CALL"
    CHOOSE_PARITY_RESPONSE = "CHOOSE_PARITY_RESPONSE"
    GAME_OVER = "GAME_OVER"
    # League Management (3)
    MATCH_RESULT_REPORT = "MATCH_RESULT_REPORT"
    LEAGUE_STANDINGS_UPDATE = "LEAGUE_STANDINGS_UPDATE"
    LEAGUE_COMPLETED = "LEAGUE_COMPLETED"
    # Errors (2)
    LEAGUE_ERROR = "LEAGUE_ERROR"
    GAME_ERROR = "GAME_ERROR"


class RegistrationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GameStatus(str, Enum):
    WIN = "WIN"
    DRAW = "DRAW"
    CANCELLED = "CANCELLED"


class ParityChoice(str, Enum):
    EVEN = "even"
    ODD = "odd"


# Base Models
class MessageEnvelope(BaseModel):
    """Base envelope for all protocol messages"""
    protocol: Literal["league.v2"] = "league.v2"
    message_type: MessageType
    sender: str  # Format: "<type>:<id>" e.g., "player:P01"
    timestamp: datetime
    conversation_id: str
    auth_token: str = ""  # Empty for registration requests

    @field_validator("sender")
    @classmethod
    def validate_sender_format(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError("Sender must be in format '<type>:<id>'")
        return v


# Supporting Models
class RefereeMeta(BaseModel):
    """Referee metadata for registration"""
    display_name: str
    version: str = "1.0.0"
    game_types: List[str] = ["even_odd"]
    contact_endpoint: str
    max_concurrent_matches: int = 2


class PlayerMeta(BaseModel):
    """Player metadata for registration"""
    display_name: str
    version: str = "1.0.0"
    game_types: List[str] = ["even_odd"]
    contact_endpoint: str


class MatchInfo(BaseModel):
    """Match assignment information"""
    match_id: str
    game_type: str = "even_odd"
    player_A_id: str
    player_B_id: str
    referee_endpoint: str


class StandingEntry(BaseModel):
    """Single player standing entry"""
    rank: int
    player_id: str
    display_name: str
    played: int
    wins: int
    draws: int
    losses: int
    points: int


class GameResult(BaseModel):
    """Game result details"""
    status: GameStatus
    winner_player_id: Optional[str] = None
    drawn_number: Optional[int] = None
    number_parity: Optional[ParityChoice] = None
    choices: Optional[Dict[str, ParityChoice]] = None
    reason: str


# Message Models - Registration (4 types)
class RefereeRegisterRequest(MessageEnvelope):
    """Referee registration request"""
    message_type: Literal[MessageType.REFEREE_REGISTER_REQUEST] = (
        MessageType.REFEREE_REGISTER_REQUEST
    )
    referee_meta: RefereeMeta


class RefereeRegisterResponse(MessageEnvelope):
    """Referee registration response"""
    message_type: Literal[MessageType.REFEREE_REGISTER_RESPONSE] = (
        MessageType.REFEREE_REGISTER_RESPONSE
    )
    status: RegistrationStatus
    referee_id: Optional[str] = None
    auth_token: Optional[str] = None
    league_id: Optional[str] = None
    rejection_reason: Optional[str] = None


class LeagueRegisterRequest(MessageEnvelope):
    """Player league registration request"""
    message_type: Literal[MessageType.LEAGUE_REGISTER_REQUEST] = (
        MessageType.LEAGUE_REGISTER_REQUEST
    )
    player_meta: PlayerMeta


class LeagueRegisterResponse(MessageEnvelope):
    """Player league registration response"""
    message_type: Literal[MessageType.LEAGUE_REGISTER_RESPONSE] = (
        MessageType.LEAGUE_REGISTER_RESPONSE
    )
    status: RegistrationStatus
    player_id: Optional[str] = None
    auth_token: Optional[str] = None
    league_id: Optional[str] = None
    rejection_reason: Optional[str] = None


# Message Models - Round Management (2 types)
class RoundAnnouncement(MessageEnvelope):
    """Round start announcement with match assignments"""
    message_type: Literal[MessageType.ROUND_ANNOUNCEMENT] = MessageType.ROUND_ANNOUNCEMENT
    round_id: str
    league_id: str
    matches: List[MatchInfo]


class RoundCompleted(MessageEnvelope):
    """Round completion notification"""
    message_type: Literal[MessageType.ROUND_COMPLETED] = MessageType.ROUND_COMPLETED
    round_id: str
    league_id: str
    completed_matches: List[str]
    next_round_id: Optional[str] = None


# Message Models - Game Execution (5 types)
class GameInvitation(MessageEnvelope):
    """Game invitation from referee to player"""
    message_type: Literal[MessageType.GAME_INVITATION] = MessageType.GAME_INVITATION
    match_id: str
    game_type: str = "even_odd"
    role_in_match: Literal["PLAYER_A", "PLAYER_B"]
    opponent_id: str


class GameJoinAck(MessageEnvelope):
    """Player's acknowledgment of game invitation"""
    message_type: Literal[MessageType.GAME_JOIN_ACK] = MessageType.GAME_JOIN_ACK
    match_id: str
    accept: bool
    arrival_timestamp: datetime


class ChooseParityCall(MessageEnvelope):
    """Request for player to choose parity"""
    message_type: Literal[MessageType.CHOOSE_PARITY_CALL] = MessageType.CHOOSE_PARITY_CALL
    match_id: str
    game_type: str = "even_odd"
    deadline: datetime
    context: Optional[Dict] = None


class ChooseParityResponse(MessageEnvelope):
    """Player's parity choice response"""
    message_type: Literal[MessageType.CHOOSE_PARITY_RESPONSE] = (
        MessageType.CHOOSE_PARITY_RESPONSE
    )
    match_id: str
    parity_choice: ParityChoice


class GameOver(MessageEnvelope):
    """Game result announcement"""
    message_type: Literal[MessageType.GAME_OVER] = MessageType.GAME_OVER
    match_id: str
    game_result: GameResult


# Message Models - League Management (3 types)
class MatchResultReport(MessageEnvelope):
    """Match result report from referee to league manager"""
    message_type: Literal[MessageType.MATCH_RESULT_REPORT] = MessageType.MATCH_RESULT_REPORT
    match_id: str
    round_id: str
    league_id: str
    result: GameResult
    score: Dict[str, int]  # {player_id: points}


class LeagueStandingsUpdate(MessageEnvelope):
    """League standings update broadcast"""
    message_type: Literal[MessageType.LEAGUE_STANDINGS_UPDATE] = (
        MessageType.LEAGUE_STANDINGS_UPDATE
    )
    league_id: str
    round_id: str
    standings: List[StandingEntry]


class LeagueCompleted(MessageEnvelope):
    """League completion announcement"""
    message_type: Literal[MessageType.LEAGUE_COMPLETED] = MessageType.LEAGUE_COMPLETED
    league_id: str
    champion: StandingEntry
    final_standings: List[StandingEntry]
    total_rounds: int
    total_matches: int


# Message Models - Errors (2 types)
class LeagueError(MessageEnvelope):
    """League-level error message"""
    message_type: Literal[MessageType.LEAGUE_ERROR] = MessageType.LEAGUE_ERROR
    error_code: str  # E012, E013, E014, etc.
    error_description: str
    context: Optional[Dict] = None


class GameError(MessageEnvelope):
    """Game-level error message"""
    message_type: Literal[MessageType.GAME_ERROR] = MessageType.GAME_ERROR
    match_id: str
    error_code: str  # E001, E002, E003, etc.
    error_description: str
    affected_player: Optional[str] = None
    action_required: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    consequence: Optional[str] = None


# Union type for all messages
MCPMessage = Union[
    RefereeRegisterRequest,
    RefereeRegisterResponse,
    LeagueRegisterRequest,
    LeagueRegisterResponse,
    RoundAnnouncement,
    RoundCompleted,
    GameInvitation,
    GameJoinAck,
    ChooseParityCall,
    ChooseParityResponse,
    GameOver,
    MatchResultReport,
    LeagueStandingsUpdate,
    LeagueCompleted,
    LeagueError,
    GameError,
]
