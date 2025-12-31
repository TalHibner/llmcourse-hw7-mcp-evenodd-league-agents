"""League Configuration Dataclasses"""
from dataclasses import dataclass
from typing import List

@dataclass
class ScoringConfig:
    """Scoring configuration for league"""
    win_points: int
    draw_points: int
    loss_points: int
    technical_loss_points: int
    tiebreakers: List[str]

@dataclass
class LeagueConfig:
    """League-specific configuration"""
    schema_version: str
    league_id: str
    display_name: str
    game_type: str
    status: str
    scoring: ScoringConfig
    # ...additional fields as needed
