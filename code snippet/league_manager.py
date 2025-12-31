"""League Manager Class Implementation"""

class LeagueManager:
    def __init__(self):
        self.referees = {}  # referee_id -> referee_info
        self.players = {}   # player_id -> player_info
        self.next_referee_id = 1
    
    def register_referee(self, params):
        """Register a new referee to the league"""
        referee_meta = params.get("referee_meta", {})
        referee_id = f"REF{self.next_referee_id:02d}"
        self.next_referee_id += 1
        
        self.referees[referee_id] = {
            "referee_id": referee_id,
            "display_name": referee_meta.get("display_name"),
            "endpoint": referee_meta.get("contact_endpoint"),
            "game_types": referee_meta.get("game_types", []),
            "max_concurrent": referee_meta.get("max_concurrent_matches", 1)
        }
        
        return {
            "message_type": "REFEREE_REGISTER_RESPONSE",
            "status": "ACCEPTED",
            "referee_id": referee_id,
            "reason": None
        }
