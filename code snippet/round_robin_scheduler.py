"""Round-Robin Match Scheduler"""
from itertools import combinations

def create_schedule(players):
    """
    Create a Round-Robin match schedule for all players.
    Each pair of players plays exactly once.
    
    Args:
        players: List of player IDs
        
    Returns:
        List of match dictionaries
    """
    matches = []
    round_num = 1
    match_num = 1
    
    for p1, p2 in combinations(players, 2):
        matches.append({
            "match_id": f"R{round_num}M{match_num}",
            "player_A_id": p1,
            "player_B_id": p2
        })
        match_num += 1
    
    return matches
