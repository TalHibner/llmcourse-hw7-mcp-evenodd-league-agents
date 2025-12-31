"""Referee Agent Example - Using ConfigLoader and JsonLogger"""
# from league_sdk import ConfigLoader, JsonLogger

class RefereeAgent:
    """
    Example Referee Agent using the league_sdk.
    Demonstrates ConfigLoader and JsonLogger usage.
    """
    
    def __init__(self, referee_id: str, league_id: str):
        # Load configurations
        loader = ConfigLoader()
        self.system_cfg = loader.load_system()
        self.league_cfg = loader.load_league(league_id)
        self.self_cfg = loader.get_referee_by_id(referee_id)
        
        # Initialize logger
        self.logger = JsonLogger(f"referee:{referee_id}", league_id)
    
    def register_to_league(self):
        """Register this referee to the league manager."""
        payload = {
            "jsonrpc": "2.0",
            "method": "register_referee",
            "params": {
                "protocol": self.system_cfg.protocol_version,
                "message_type": "REFEREE_REGISTER_REQUEST",
                "referee_meta": {
                    "display_name": self.self_cfg.display_name,
                    "version": self.self_cfg.version,
                    "game_types": self.self_cfg.game_types,
                }
            }
        }
        # ... send request to league manager
        self.logger.log_message_sent(
            "REFEREE_REGISTER_REQUEST",
            "league_manager"
        )
