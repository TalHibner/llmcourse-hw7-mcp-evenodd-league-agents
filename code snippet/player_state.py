"""Player State Management"""

class PlayerState:
    """
    Maintains player's internal state including:
    - Personal statistics
    - Match history
    - Information about opponents
    """
    def __init__(self, player_id):
        self.player_id = player_id
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.history = []
    
    def update(self, result):
        """Update state based on match result"""
        self.history.append(result)
        if result["winner"] == self.player_id:
            self.wins += 1
        elif result["winner"] == "DRAW":
            self.draws += 1
        else:
            self.losses += 1
