"""Even/Odd Game Winner Determination Logic"""

def determine_winner(choice_a, choice_b, number):
    """
    Determine the winner of an even/odd game.
    
    Args:
        choice_a: Player A's choice ("even" or "odd")
        choice_b: Player B's choice ("even" or "odd")
        number: The drawn number
        
    Returns:
        "PLAYER_A", "PLAYER_B", or "DRAW"
    """
    is_even = (number % 2 == 0)
    parity = "even" if is_even else "odd"
    
    a_correct = (choice_a == parity)
    b_correct = (choice_b == parity)
    
    if a_correct and not b_correct:
        return "PLAYER_A"
    elif b_correct and not a_correct:
        return "PLAYER_B"
    else:
        return "DRAW"
