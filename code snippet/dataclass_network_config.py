"""Network Configuration Dataclass"""
from dataclasses import dataclass
from typing import List

@dataclass
class NetworkConfig:
    """Network configuration for the league system"""
    base_host: str
    default_league_manager_port: int
    default_referee_port_range: List[int]
    default_player_port_range: List[int]
