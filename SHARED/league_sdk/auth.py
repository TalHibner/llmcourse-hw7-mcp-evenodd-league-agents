"""
JWT-based authentication for the MCP League system.

Provides secure token generation and validation using JSON Web Tokens (JWT).
"""

import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path


class JWTAuthenticator:
    """
    JWT-based authentication handler.

    Generates and validates JWT tokens for agents (players and referees)
    in the league system.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_expiry_hours: int = 24,
        algorithm: str = "HS256"
    ):
        """
        Initialize JWT authenticator.

        Args:
            secret_key: Secret key for JWT signing. If None, generates a random key.
            token_expiry_hours: Token expiration time in hours (default: 24)
            algorithm: JWT signing algorithm (default: HS256)
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.token_expiry_hours = token_expiry_hours
        self.algorithm = algorithm
        self.token_registry: Dict[str, Dict[str, Any]] = {}  # token -> metadata

    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)

    def generate_token(
        self,
        agent_id: str,
        league_id: str,
        agent_type: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a JWT token for an agent.

        Args:
            agent_id: Unique identifier for the agent (e.g., "P01", "REF01")
            league_id: League identifier
            agent_type: Type of agent ("player" or "referee")
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(hours=self.token_expiry_hours)

        # Standard JWT claims
        payload = {
            "sub": agent_id,  # Subject (agent ID)
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiration
            "nbf": int(now.timestamp()),  # Not before
            "jti": secrets.token_hex(16),  # JWT ID (unique identifier)

            # Custom claims
            "agent_id": agent_id,
            "league_id": league_id,
            "agent_type": agent_type,
        }

        # Add any additional claims
        if additional_claims:
            payload.update(additional_claims)

        # Encode the token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # Store token metadata
        self.token_registry[token] = {
            "agent_id": agent_id,
            "league_id": league_id,
            "agent_type": agent_type,
            "issued_at": now.isoformat(),
            "expires_at": expiry.isoformat()
        }

        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return its payload.

        Args:
            token: JWT token string to validate

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "require": ["sub", "iat", "exp", "agent_id", "league_id"]
                }
            )

            return payload

        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Invalid token (bad signature, malformed, etc.)
            return None
        except Exception:
            # Any other error
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (remove from registry).

        Args:
            token: JWT token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        if token in self.token_registry:
            del self.token_registry[token]
            return True
        return False

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a token from the registry.

        Args:
            token: JWT token

        Returns:
            Token metadata if found, None otherwise
        """
        return self.token_registry.get(token)

    def verify_agent_access(
        self,
        token: str,
        required_agent_id: Optional[str] = None,
        required_league_id: Optional[str] = None,
        required_agent_type: Optional[str] = None
    ) -> bool:
        """
        Verify that a token grants access with specific requirements.

        Args:
            token: JWT token to verify
            required_agent_id: If provided, token must belong to this agent
            required_league_id: If provided, token must be for this league
            required_agent_type: If provided, token must be this agent type

        Returns:
            True if token is valid and meets all requirements, False otherwise
        """
        payload = self.validate_token(token)

        if not payload:
            return False

        # Check agent ID requirement
        if required_agent_id and payload.get("agent_id") != required_agent_id:
            return False

        # Check league ID requirement
        if required_league_id and payload.get("league_id") != required_league_id:
            return False

        # Check agent type requirement
        if required_agent_type and payload.get("agent_type") != required_agent_type:
            return False

        return True


def get_jwt_authenticator(
    secret_key: Optional[str] = None,
    token_expiry_hours: int = 24
) -> JWTAuthenticator:
    """
    Factory function to get a JWT authenticator instance.

    Args:
        secret_key: Optional secret key. If None, will use environment variable
                   JWT_SECRET_KEY or generate a random one
        token_expiry_hours: Token expiration in hours

    Returns:
        JWTAuthenticator instance
    """
    import os

    # Use provided key, environment variable, or generate new one
    key = secret_key or os.getenv("JWT_SECRET_KEY")

    return JWTAuthenticator(
        secret_key=key,
        token_expiry_hours=token_expiry_hours
    )
