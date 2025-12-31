"""
Configuration loader with lazy loading and caching.

Loads JSON configuration files from SHARED/config/ directory.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# Config Models
class NetworkConfig(BaseModel):
    """Network configuration"""
    base_host: str
    league_manager_port: int
    referee_port_range: List[int]
    player_port_range: List[int]


class TimeoutsConfig(BaseModel):
    """Timeout configuration"""
    move_timeout_sec: int
    game_join_ack_timeout_sec: int
    generic_response_timeout_sec: int
    http_request_timeout_sec: int


class RetryPolicyConfig(BaseModel):
    """Retry policy configuration"""
    max_retries: int
    backoff_strategy: str
    backoff_base_sec: int


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration"""
    failure_threshold: int
    timeout_sec: int
    half_open_max_calls: int


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str
    format: str
    rotation_mb: int


class SystemConfig(BaseModel):
    """System-wide configuration"""
    protocol_version: str
    network: NetworkConfig
    timeouts: TimeoutsConfig
    retry_policy: RetryPolicyConfig
    circuit_breaker: CircuitBreakerConfig
    logging: LoggingConfig


class RefereeConfig(BaseModel):
    """Referee agent configuration"""
    referee_id: str
    display_name: str
    endpoint: str
    version: str
    game_types: List[str]
    max_concurrent_matches: int
    active: bool = True


class PlayerConfig(BaseModel):
    """Player agent configuration"""
    player_id: str
    display_name: str
    endpoint: str
    version: str
    game_types: List[str]
    strategy: str


class LeagueManagerConfig(BaseModel):
    """League Manager configuration"""
    manager_id: str
    display_name: str
    endpoint: str
    version: str


class AgentsConfig(BaseModel):
    """All agents configuration"""
    league_manager: LeagueManagerConfig
    referees: List[RefereeConfig]
    players: List[PlayerConfig]


class ScoringConfig(BaseModel):
    """Scoring configuration"""
    win_points: int
    draw_points: int
    loss_points: int
    technical_loss_points: int


class ParticipantsConfig(BaseModel):
    """Participants configuration"""
    min_players: int
    max_players: int
    registered_players: List[str] = []


class ScheduleConfig(BaseModel):
    """Schedule configuration"""
    start_date: str
    match_delay_sec: int


class RulesConfig(BaseModel):
    """Game rules configuration"""
    number_range_min: int
    number_range_max: int
    draw_on_both_wrong: bool


class LeagueConfig(BaseModel):
    """League-specific configuration"""
    league_id: str
    display_name: str
    game_type: str
    format: str
    scoring: ScoringConfig
    participants: ParticipantsConfig
    schedule: ScheduleConfig
    rules: RulesConfig


class GameTypeConfig(BaseModel):
    """Game type configuration"""
    game_type_id: str
    display_name: str
    description: str
    min_players: int
    max_players: int


class GamesRegistry(BaseModel):
    """Games registry"""
    games: List[GameTypeConfig]


class ConfigLoader:
    """
    Configuration loader with lazy loading and caching.

    Loads configuration files from SHARED/config/ directory and caches them.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_dir: Optional custom config directory path
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        self.config_dir = config_dir
        self._cache: Dict[str, Any] = {}

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file"""
        with open(path, 'r') as f:
            return json.load(f)

    def load_system(self) -> SystemConfig:
        """Load system configuration"""
        if 'system' not in self._cache:
            path = self.config_dir / "system.json"
            data = self._load_json(path)
            self._cache['system'] = SystemConfig(**data)
        return self._cache['system']

    def load_agents(self) -> AgentsConfig:
        """Load agents configuration"""
        if 'agents' not in self._cache:
            path = self.config_dir / "agents" / "agents_config.json"
            data = self._load_json(path)
            self._cache['agents'] = AgentsConfig(**data)
        return self._cache['agents']

    def load_league(self, league_id: str) -> LeagueConfig:
        """Load league-specific configuration"""
        cache_key = f'league_{league_id}'
        if cache_key not in self._cache:
            path = self.config_dir / "leagues" / f"{league_id}.json"
            data = self._load_json(path)
            self._cache[cache_key] = LeagueConfig(**data)
        return self._cache[cache_key]

    def load_games_registry(self) -> GamesRegistry:
        """Load games registry"""
        if 'games' not in self._cache:
            path = self.config_dir / "games" / "games_registry.json"
            data = self._load_json(path)
            self._cache['games'] = GamesRegistry(**data)
        return self._cache['games']

    def get_referee_by_id(self, referee_id: str) -> Optional[RefereeConfig]:
        """Get referee configuration by ID"""
        agents = self.load_agents()
        for referee in agents.referees:
            if referee.referee_id == referee_id:
                return referee
        return None

    def get_player_by_id(self, player_id: str) -> Optional[PlayerConfig]:
        """Get player configuration by ID"""
        agents = self.load_agents()
        for player in agents.players:
            if player.player_id == player_id:
                return player
        return None

    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self._cache.clear()


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
