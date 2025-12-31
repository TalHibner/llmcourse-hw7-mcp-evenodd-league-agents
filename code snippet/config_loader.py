"""Configuration Loader with Lazy Loading and Caching"""
import json
from pathlib import Path
from typing import Dict, Optional

# Import configuration models (adjust paths as needed)
# from config_models_system import SystemConfig
# from config_models_agents import RefereeConfig, PlayerConfig, AgentsConfig
# from config_models_league import LeagueConfig
# from config_models_games import GamesRegistry

CONFIG_ROOT = Path("SHARED/config")

class ConfigLoader:
    """
    Configuration loader implementing Lazy Loading pattern.
    Config files are loaded only when needed and cached for reuse.
    """
    
    def __init__(self, root: Path = CONFIG_ROOT):
        self.root = root
        self._system = None      # lazy cache for system config
        self._agents = None      # lazy cache for agents config
        self._leagues: Dict = {} # lazy cache: league_id -> LeagueConfig
    
    def load_system(self):  # -> SystemConfig
        """Load global system configuration."""
        if self._system:
            return self._system
        
        path = self.root / "system.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        
        # Create SystemConfig from data
        # self._system = SystemConfig(...)
        self._system = data  # Placeholder
        return self._system
    
    def load_agents(self):  # -> AgentsConfig
        """Load all agents configuration."""
        if self._agents:
            return self._agents
        
        path = self.root / "agents" / "agents_config.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        
        # Create AgentsConfig from data
        # self._agents = AgentsConfig(...)
        self._agents = data  # Placeholder
        return self._agents
    
    def load_league(self, league_id: str):  # -> LeagueConfig
        """Load specific league configuration."""
        if league_id in self._leagues:
            return self._leagues[league_id]
        
        path = self.root / "leagues" / f"{league_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        
        # Create LeagueConfig from data
        # league_config = LeagueConfig(...)
        league_config = data  # Placeholder
        self._leagues[league_id] = league_config
        return league_config
    
    def load_games_registry(self):  # -> GamesRegistry
        """Load games registry configuration."""
        path = self.root / "games" / "games_registry.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data  # Placeholder
    
    # Helper methods
    def get_referee_by_id(self, referee_id: str):  # -> RefereeConfig
        """Get a referee configuration by ID."""
        agents = self.load_agents()
        for ref in agents.get("referees", []):
            if ref.get("referee_id") == referee_id:
                return ref
        raise ValueError(f"Referee not found: {referee_id}")
    
    def get_player_by_id(self, player_id: str):  # -> PlayerConfig
        """Get a player configuration by ID."""
        agents = self.load_agents()
        for player in agents.get("players", []):
            if player.get("player_id") == player_id:
                return player
        raise ValueError(f"Player not found: {player_id}")
