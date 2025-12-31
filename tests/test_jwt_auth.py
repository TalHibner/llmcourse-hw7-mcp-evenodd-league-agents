"""
Tests for JWT authentication module.
"""

import pytest
import time
from datetime import datetime, timedelta, timezone

from SHARED.league_sdk.auth import JWTAuthenticator, get_jwt_authenticator


class TestJWTAuthenticator:
    """Test JWT authentication functionality"""

    def test_authenticator_initialization(self):
        """Test JWT authenticator initialization"""
        auth = JWTAuthenticator()

        assert auth.secret_key is not None
        assert auth.token_expiry_hours == 24
        assert auth.algorithm == "HS256"
        assert len(auth.token_registry) == 0

    def test_authenticator_with_custom_secret(self):
        """Test JWT authenticator with custom secret key"""
        custom_secret = "my-secret-key-12345"
        auth = JWTAuthenticator(secret_key=custom_secret)

        assert auth.secret_key == custom_secret

    def test_authenticator_with_custom_expiry(self):
        """Test JWT authenticator with custom expiry time"""
        auth = JWTAuthenticator(token_expiry_hours=48)

        assert auth.token_expiry_hours == 48

    def test_generate_token_for_player(self):
        """Test generating JWT token for a player"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token is in registry
        assert token in auth.token_registry
        assert auth.token_registry[token]["agent_id"] == "P01"
        assert auth.token_registry[token]["league_id"] == "LEAGUE01"
        assert auth.token_registry[token]["agent_type"] == "player"

    def test_generate_token_for_referee(self):
        """Test generating JWT token for a referee"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="REF01",
            league_id="LEAGUE01",
            agent_type="referee"
        )

        assert token is not None
        metadata = auth.token_registry[token]
        assert metadata["agent_id"] == "REF01"
        assert metadata["agent_type"] == "referee"

    def test_generate_token_with_additional_claims(self):
        """Test generating token with additional custom claims"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player",
            additional_claims={
                "display_name": "Player One",
                "strategy": "random"
            }
        )

        payload = auth.validate_token(token)
        assert payload is not None
        assert payload["display_name"] == "Player One"
        assert payload["strategy"] == "random"

    def test_validate_valid_token(self):
        """Test validating a valid JWT token"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        payload = auth.validate_token(token)

        assert payload is not None
        assert payload["agent_id"] == "P01"
        assert payload["league_id"] == "LEAGUE01"
        assert payload["agent_type"] == "player"
        assert "sub" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload

    def test_validate_invalid_token(self):
        """Test validating an invalid JWT token"""
        auth = JWTAuthenticator()

        # Invalid token string
        payload = auth.validate_token("invalid-token-12345")

        assert payload is None

    def test_validate_token_wrong_secret(self):
        """Test validating token with wrong secret key"""
        auth1 = JWTAuthenticator(secret_key="secret1")
        auth2 = JWTAuthenticator(secret_key="secret2")

        # Generate token with auth1
        token = auth1.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        # Try to validate with auth2 (different secret)
        payload = auth2.validate_token(token)

        assert payload is None

    def test_validate_expired_token(self):
        """Test validating an expired JWT token"""
        # Create authenticator with very short expiry (1 second)
        auth = JWTAuthenticator(token_expiry_hours=1/3600)  # 1 second

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        # Wait for token to expire
        time.sleep(2)

        payload = auth.validate_token(token)

        assert payload is None

    def test_revoke_token(self):
        """Test revoking a token"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        # Token should be in registry
        assert token in auth.token_registry

        # Revoke token
        result = auth.revoke_token(token)

        assert result is True
        assert token not in auth.token_registry

    def test_revoke_nonexistent_token(self):
        """Test revoking a token that doesn't exist"""
        auth = JWTAuthenticator()

        result = auth.revoke_token("nonexistent-token")

        assert result is False

    def test_get_token_info(self):
        """Test getting token metadata"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        info = auth.get_token_info(token)

        assert info is not None
        assert info["agent_id"] == "P01"
        assert info["league_id"] == "LEAGUE01"
        assert info["agent_type"] == "player"
        assert "issued_at" in info
        assert "expires_at" in info

    def test_get_token_info_nonexistent(self):
        """Test getting info for nonexistent token"""
        auth = JWTAuthenticator()

        info = auth.get_token_info("nonexistent-token")

        assert info is None

    def test_verify_agent_access_valid(self):
        """Test verifying agent access with valid token"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        # Verify with all requirements
        result = auth.verify_agent_access(
            token=token,
            required_agent_id="P01",
            required_league_id="LEAGUE01",
            required_agent_type="player"
        )

        assert result is True

    def test_verify_agent_access_wrong_agent_id(self):
        """Test verifying access with wrong agent ID"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        result = auth.verify_agent_access(
            token=token,
            required_agent_id="P02"  # Wrong agent ID
        )

        assert result is False

    def test_verify_agent_access_wrong_league_id(self):
        """Test verifying access with wrong league ID"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        result = auth.verify_agent_access(
            token=token,
            required_league_id="LEAGUE02"  # Wrong league ID
        )

        assert result is False

    def test_verify_agent_access_wrong_agent_type(self):
        """Test verifying access with wrong agent type"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        result = auth.verify_agent_access(
            token=token,
            required_agent_type="referee"  # Wrong agent type
        )

        assert result is False

    def test_verify_agent_access_no_requirements(self):
        """Test verifying access without specific requirements"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        # No specific requirements - just check token is valid
        result = auth.verify_agent_access(token=token)

        assert result is True

    def test_verify_agent_access_invalid_token(self):
        """Test verifying access with invalid token"""
        auth = JWTAuthenticator()

        result = auth.verify_agent_access(token="invalid-token")

        assert result is False

    def test_unique_tokens(self):
        """Test that each token generated is unique"""
        auth = JWTAuthenticator()

        token1 = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        token2 = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        assert token1 != token2

    def test_token_payload_structure(self):
        """Test that token payload has correct structure"""
        auth = JWTAuthenticator()

        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        payload = auth.validate_token(token)

        # Standard JWT claims
        assert "sub" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert "nbf" in payload
        assert "jti" in payload

        # Custom claims
        assert "agent_id" in payload
        assert "league_id" in payload
        assert "agent_type" in payload

        # Check values
        assert payload["sub"] == "P01"
        assert payload["agent_id"] == "P01"
        assert payload["league_id"] == "LEAGUE01"
        assert payload["agent_type"] == "player"


class TestGetJWTAuthenticator:
    """Test the factory function for JWT authenticator"""

    def test_get_jwt_authenticator_default(self):
        """Test getting authenticator with defaults"""
        auth = get_jwt_authenticator()

        assert isinstance(auth, JWTAuthenticator)
        assert auth.token_expiry_hours == 24

    def test_get_jwt_authenticator_custom_expiry(self):
        """Test getting authenticator with custom expiry"""
        auth = get_jwt_authenticator(token_expiry_hours=48)

        assert auth.token_expiry_hours == 48

    def test_get_jwt_authenticator_custom_secret(self):
        """Test getting authenticator with custom secret"""
        secret = "my-custom-secret"
        auth = get_jwt_authenticator(secret_key=secret)

        assert auth.secret_key == secret

    def test_get_jwt_authenticator_env_variable(self, monkeypatch):
        """Test getting authenticator using environment variable"""
        monkeypatch.setenv("JWT_SECRET_KEY", "env-secret-key")

        auth = get_jwt_authenticator()

        assert auth.secret_key == "env-secret-key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
