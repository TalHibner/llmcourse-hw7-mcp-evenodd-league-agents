"""System Configuration Dataclasses"""
from dataclasses import dataclass
from typing import List

@dataclass
class NetworkConfig:
    """Network configuration"""
    base_host: str
    default_league_manager_port: int
    default_referee_port_range: List[int]
    default_player_port_range: List[int]

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_auth_tokens: bool
    token_length: int
    token_ttl_hours: int

@dataclass
class TimeoutsConfig:
    """Timeout configuration"""
    register_referee_timeout_sec: int
    register_player_timeout_sec: int
    game_join_ack_timeout_sec: int
    move_timeout_sec: int
    generic_response_timeout_sec: int

@dataclass
class SystemConfig:
    """Global system configuration"""
    schema_version: str
    system_id: str
    protocol_version: str
    default_league_id: str
    network: NetworkConfig
    security: SecurityConfig
    timeouts: TimeoutsConfig
    # ...additional fields as needed
