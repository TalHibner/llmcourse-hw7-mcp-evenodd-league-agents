def handle_auth_error(response: dict) -> bool:
    """Check for authentication errors."""
    error = response.get("error", {})
    error_code = error.get("error_code", "")

    if error_code == "E011": # AUTH_TOKEN_MISSING
        print("Error: auth_token is required")
        return False
    elif error_code == "E012": # AUTH_TOKEN_INVALID
        print("Error: auth_token is invalid or expired")
        # May need to reregister
        return False
    elif error_code == "E013": # REFEREE_NOT_REGISTERED
        print("Error: Referee must register first")
        return False

    return True # No auth error