"""Agent Configuration Dataclasses"""
from dataclasses import dataclass
from typing import List

@dataclass
class RefereeConfig:
    """Referee agent configuration"""
    referee_id: str
    display_name: str
    endpoint: str
    version: str
    game_types: List[str]
    max_concurrent_matches: int
    active: bool = True

@dataclass
class PlayerConfig:
    """Player agent configuration"""
    player_id: str
    display_name: str
    version: str
    preferred_leagues: List[str]
    game_types: List[str]
    default_endpoint: str
    active: bool = True
