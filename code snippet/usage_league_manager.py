"""League Manager Example - Using ConfigLoader and JsonLogger"""
# from league_sdk import ConfigLoader, JsonLogger

class LeagueManager:
    """
    Example League Manager using the league_sdk.
    Demonstrates ConfigLoader and JsonLogger usage.
    """
    
    def __init__(self, league_id: str):
        # Load all configurations
        loader = ConfigLoader()
        self.system_cfg = loader.load_system()
        self.agents_cfg = loader.load_agents()
        self.league_cfg = loader.load_league(league_id)
        
        # Initialize logger
        self.logger = JsonLogger("league_manager", league_id)
        
        # Build lookup maps for fast access
        self.referees_by_id = {
            r.referee_id: r.endpoint
            for r in self.agents_cfg.referees if r.active
        }
    
    def get_timeout_for_move(self) -> int:
        """Get the configured timeout for player moves."""
        return self.system_cfg.timeouts.move_timeout_sec
