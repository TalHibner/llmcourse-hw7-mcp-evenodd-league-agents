class AuthenticatedClient:
    def __init__(self, credentials: AgentCredentials):
        self.creds = credentials
    
    def send_message(self, endpoint: str, message_type: str,
                     params: dict) -> dict:
        """Send authenticated message."""
        payload = {
            "jsonrpc": "2.0",
            "method": "mcp_message",
            "params": {
                "protocol": "league.v2",
                "message_type": message_type,
                "sender": f"player:{self.creds.agent_id}",
                "auth_token": self.creds.auth_token,
                "league_id": self.creds.league_id,
                **params
            },
            "id": 1
    }
        response = requests.post(endpoint, json=payload)
        return response.json()