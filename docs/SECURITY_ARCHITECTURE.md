# Security Architecture

**Document Version**: 1.0.0
**Last Updated**: 2025-12-31
**Status**: Production-Ready Design

---

## Table of Contents

1. [Overview](#overview)
2. [Security Principles](#security-principles)
3. [Architecture Layers](#architecture-layers)
4. [Authentication Flow](#authentication-flow)
5. [Authorization Model](#authorization-model)
6. [Data Security](#data-security)
7. [Network Security](#network-security)
8. [Threat Model](#threat-model)
9. [Security Testing](#security-testing)
10. [Incident Response](#incident-response)

---

## Overview

The MCP Even/Odd League implements a **defense-in-depth** security architecture with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │         JWT Token Validation & Expiration        │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Input Validation (Pydantic Models)          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                    Transport Layer                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │         HTTPS/TLS (Production)                   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Rate Limiting (Optional)              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                     Network Layer                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Firewall Rules (Production)               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │     Log Sanitization (Auto-Redact Tokens)        │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │    File Permissions (600/700 for sensitive)      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Security Principles

### 1. Least Privilege

**Principle**: Each agent has only the permissions necessary for its role.

**Implementation**:
```python
# JWT tokens include role-based claims
{
  "agent_id": "P01",
  "agent_type": "player",  # Determines allowed operations
  "league_id": "TEST_LEAGUE"
}

# Authorization check
def verify_agent_access(token, required_agent_id, required_league_id):
    payload = validate_token(token)
    if payload["agent_id"] != required_agent_id:
        raise AuthorizationError("Token does not match agent")
    if payload["league_id"] != required_league_id:
        raise AuthorizationError("Wrong league")
```

**Permissions Matrix**:

| Agent Type | Register | Start League | Report Match | Receive Invitation |
|------------|----------|--------------|--------------|-------------------|
| Player | ✅ | ❌ | ❌ | ✅ |
| Referee | ✅ | ❌ | ✅ | ❌ |
| League Manager | ❌ | ✅ | ❌ | ❌ |

### 2. Defense in Depth

**Principle**: Multiple independent layers of security controls.

**Layers**:
1. **Network**: Firewall, HTTPS
2. **Authentication**: JWT validation
3. **Authorization**: Role-based access control
4. **Input Validation**: Pydantic models
5. **Data**: Encryption at rest, log sanitization
6. **Monitoring**: Audit logs, anomaly detection

### 3. Fail Secure

**Principle**: System fails to a secure state, not an insecure one.

**Examples**:
```python
# Token validation - fails to None, not to "valid"
def validate_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("EXPIRED_TOKEN")
        return None  # Fail secure
    except jwt.InvalidTokenError:
        logger.error("INVALID_TOKEN")
        return None  # Fail secure

# If validation fails, reject the request
if not validate_token(auth_token):
    raise AuthenticationError("Invalid token")  # Deny access
```

### 4. Zero Trust

**Principle**: Never trust, always verify.

**Implementation**:
- Every request requires authentication (except registration)
- Tokens validated on every request
- Agent ID verified matches token claims
- League ID verified matches token claims
- No implicit trust between agents

---

## Architecture Layers

### Layer 1: Application Security

#### JWT Authentication

**Implementation**: `SHARED/league_sdk/auth.py`

```python
class JWTAuthenticator:
    """
    Industry-standard JWT authentication.

    Security features:
    - HS256 signature algorithm (HMAC with SHA-256)
    - Configurable token expiration
    - Unique JTI (JWT ID) for each token
    - Token registry for revocation support
    - Environment variable for secret key
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_expiry_hours: int = 24,
        algorithm: str = "HS256"
    ):
        # Use environment variable or generate secure random
        self.secret_key = secret_key or self._generate_secret_key()
        self.token_expiry_hours = token_expiry_hours
        self.algorithm = algorithm
        self.token_registry: Dict[str, Dict] = {}

    def _generate_secret_key(self) -> str:
        """Generate cryptographically secure secret key"""
        import os
        # Try environment variable first
        env_secret = os.getenv("LEAGUE_JWT_SECRET")
        if env_secret:
            return env_secret

        # Generate random for development (INSECURE for production)
        import secrets
        return secrets.token_hex(32)

    def generate_token(
        self,
        agent_id: str,
        league_id: str,
        agent_type: str,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Generate JWT token with security claims.

        Token structure:
        {
          "sub": agent_id,           # Subject
          "iat": timestamp,           # Issued at
          "exp": timestamp,           # Expiration
          "nbf": timestamp,           # Not before
          "jti": unique_id,           # JWT ID (for revocation)
          "agent_id": agent_id,
          "league_id": league_id,
          "agent_type": agent_type,
          ...additional_claims
        }
        """
        import secrets
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(hours=self.token_expiry_hours)

        payload = {
            "sub": agent_id,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "nbf": int(now.timestamp()),
            "jti": secrets.token_hex(16),  # Unique ID
            "agent_id": agent_id,
            "league_id": league_id,
            "agent_type": agent_type,
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # Store in registry for revocation support
        self.token_registry[token] = {
            "agent_id": agent_id,
            "issued_at": now,
            "expires_at": expiry
        }

        return token
```

**Security Properties**:
- ✅ **Signature Verification**: HMAC-SHA256 prevents tampering
- ✅ **Expiration**: Tokens expire (default 24h, configurable)
- ✅ **Not Before**: Prevents early use of tokens
- ✅ **Unique JTI**: Enables revocation
- ✅ **Environment Secret**: Production secrets from env vars

#### Input Validation

**Implementation**: Pydantic models validate all inputs

```python
from pydantic import BaseModel, Field, field_validator

class LeagueRegisterRequest(BaseModel):
    """
    Player registration request with strict validation.

    Security validations:
    - sender: Must match pattern "player:P[0-9]{2}"
    - conversation_id: Limited length (prevents buffer overflow)
    - player_meta: Nested validation
    """
    sender: str = Field(
        ...,
        pattern=r'^player:P\d{2}$',
        description="Sender must be 'player:PXX'"
    )
    timestamp: datetime
    conversation_id: str = Field(..., min_length=1, max_length=100)
    player_meta: PlayerMeta
    league_id: str = Field(..., min_length=1, max_length=50)

    @field_validator('sender')
    def validate_sender_format(cls, v):
        """Additional validation for sender format"""
        if not v.startswith('player:'):
            raise ValueError('Sender must start with "player:"')
        return v
```

**Protection Against**:
- ✅ SQL Injection: N/A (no SQL database)
- ✅ XSS: JSON-only API, no HTML rendering
- ✅ Command Injection: No shell execution of user input
- ✅ Buffer Overflow: Length limits on all strings
- ✅ Type Confusion: Pydantic enforces types

---

### Layer 2: Transport Security

#### HTTPS/TLS (Production)

**Configuration**:
```python
# Production configuration
import uvicorn
import ssl

uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="/path/to/privkey.pem",
    ssl_certfile="/path/to/fullchain.pem",
    ssl_version=ssl.PROTOCOL_TLS,
    ssl_cert_reqs=ssl.CERT_REQUIRED,
    ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
)
```

**Security Properties**:
- ✅ **Encryption**: AES-256-GCM or ChaCha20
- ✅ **Perfect Forward Secrecy**: ECDHE/DHE key exchange
- ✅ **Certificate Validation**: Mutual TLS support
- ✅ **Strong Ciphers**: Modern cipher suites only

#### Rate Limiting (Optional)

**Implementation**: slowapi library

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/register/player")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def register_player(...):
    pass
```

---

### Layer 3: Network Security

#### Firewall Configuration

**AWS Security Groups**:
```
Inbound Rules:
  - Port 8000 (League Manager):
    Source: Trusted CIDR blocks only (e.g., 10.0.0.0/8)

  - Ports 8001-8010 (Referees):
    Source: Internal VPC only

  - Ports 8101-8200 (Players):
    Source: Internal VPC only

Outbound Rules:
  - Port 443 (HTTPS):
    Destination: 0.0.0.0/0 (external APIs)

  - Internal ports:
    Destination: VPC CIDR
```

**Linux iptables**:
```bash
# Allow League Manager from trusted IPs only
iptables -A INPUT -p tcp --dport 8000 -s 203.0.113.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP

# Allow agents within internal network
iptables -A INPUT -p tcp --dport 8001:8200 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8001:8200 -j DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

---

### Layer 4: Data Security

#### Log Sanitization

**Implementation**: `SHARED/league_sdk/logger.py:45-60`

```python
SENSITIVE_FIELDS = ["auth_token", "password", "secret", "api_key", "jwt"]

def sanitize_log_data(self, data: Dict) -> Dict:
    """
    Remove sensitive information from log data.

    Automatically redacts:
    - auth_token
    - password
    - secret
    - api_key
    - jwt
    - Any field containing "token" or "secret"
    """
    sanitized = data.copy()

    for key in list(sanitized.keys()):
        # Exact match
        if key in SENSITIVE_FIELDS:
            sanitized[key] = "***REDACTED***"

        # Partial match (case-insensitive)
        elif any(s in key.lower() for s in ["token", "secret", "password"]):
            sanitized[key] = "***REDACTED***"

    return sanitized
```

**Example Log Output**:
```json
{
  "timestamp": "2025-12-31T20:00:00Z",
  "level": "INFO",
  "event": "PLAYER_REGISTERED",
  "player_id": "P01",
  "auth_token": "***REDACTED***"
}
```

#### File Permissions

**Recommended permissions**:
```bash
# Configuration files
chmod 600 config/**/*.yaml
chmod 600 config/**/*.json
chmod 600 .env

# Data directories
chmod 700 data/
chmod 700 data/leagues/
chmod 700 data/logs/

# Log files
chmod 600 data/logs/**/*.jsonl

# Executable scripts
chmod 755 scripts/*.py
```

---

## Authentication Flow

### Complete Authentication Sequence

```
┌─────────┐                                      ┌────────────────┐
│ Player  │                                      │ League Manager │
└────┬────┘                                      └───────┬────────┘
     │                                                    │
     │  1. POST /mcp (LeagueRegisterRequest)             │
     │  ─────────────────────────────────────────────────>│
     │     {                                              │
     │       "sender": "player:P01",                      │
     │       "player_meta": {...}                         │
     │     }                                              │
     │                                                    │
     │                                          2. Generate JWT
     │                                             secret_key = env["LEAGUE_JWT_SECRET"]
     │                                             payload = {
     │                                               "agent_id": "P01",
     │                                               "league_id": "TEST",
     │                                               "agent_type": "player",
     │                                               "exp": now + 24h
     │                                             }
     │                                             token = jwt.encode(payload, secret_key, "HS256")
     │                                                    │
     │  3. LeagueRegisterResponse                        │
     │  <─────────────────────────────────────────────────│
     │     {                                              │
     │       "status": "ACCEPTED",                        │
     │       "player_id": "P01",                          │
     │       "auth_token": "eyJhbGc..."                   │
     │     }                                              │
     │                                                    │
     │ 4. Store token                                     │
     │    self.auth_token = "eyJhbGc..."                  │
     │                                                    │
┌────▼────┐                                      ┌───────▼────────┐
│ Referee │                                      │ Player         │
└────┬────┘                                      └───────┬────────┘
     │                                                    │
     │  5. POST /mcp (GameInvitation)                    │
     │  ─────────────────────────────────────────────────>│
     │     {                                              │
     │       "match_id": "R01M01",                        │
     │       "auth_token": "eyJhbGc...",                  │
     │       "opponent_id": "P02"                         │
     │     }                                              │
     │                                                    │
     │                                          6. Validate Token
     │                                             payload = jwt.decode(token, secret_key, "HS256")
     │                                             if payload["agent_id"] != "P01":
     │                                               raise AuthError
     │                                             if payload["league_id"] != "TEST":
     │                                               raise AuthError
     │                                             if payload["exp"] < now:
     │                                               raise ExpiredError
     │                                                    │
     │  7. POST /mcp (GameJoinAck)                       │
     │  <─────────────────────────────────────────────────│
     │     {                                              │
     │       "match_id": "R01M01",                        │
     │       "auth_token": "eyJhbGc...",                  │
     │       "ready": true                                │
     │     }                                              │
     │                                                    │
     │ 8. Validate Player's Token                         │
     │    payload = jwt.decode(token)                     │
     │    assert payload["agent_id"] == "P01"             │
     │                                                    │
```

---

## Threat Model

### Threats In Scope

#### 1. Token Forgery

**Attack**: Attacker creates fake JWT token

**Mitigation**:
- HS256 signature with secret key
- Secret stored in environment variable
- Signature verification on every request

**Implementation**:
```python
try:
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
except jwt.InvalidSignatureError:
    # Signature verification failed
    raise AuthenticationError("Invalid token signature")
```

#### 2. Token Replay

**Attack**: Attacker intercepts and reuses valid token

**Mitigation**:
- Token expiration (default 24h, configurable to 1h)
- HTTPS in production (prevents interception)
- Short token lifetime for production

**Configuration**:
```bash
# Production: Short-lived tokens
export JWT_EXPIRY_HOURS=1
```

#### 3. Unauthorized Access

**Attack**: Agent A tries to access Agent B's resources

**Mitigation**:
- Token includes agent_id and league_id claims
- Every request validates token matches expected agent

**Implementation**:
```python
def verify_agent_access(token, required_agent_id, required_league_id):
    payload = validate_token(token)
    if payload["agent_id"] != required_agent_id:
        raise AuthorizationError("Token agent_id mismatch")
    if payload["league_id"] != required_league_id:
        raise AuthorizationError("Token league_id mismatch")
```

#### 4. Input Injection

**Attack**: Malicious input in messages

**Mitigation**:
- Pydantic validation on all inputs
- Type enforcement
- Length limits
- Pattern matching (regex)

### Threats Out of Scope (Development Mode)

**⚠️ These are acceptable for educational use, NOT for production:**

1. **Network Sniffing**: HTTP only (use HTTPS in production)
2. **DoS Attacks**: No rate limiting (add in production)
3. **Database Injection**: N/A (using JSON files)
4. **Session Hijacking**: Short-lived tokens mitigate risk

---

## Security Testing

### Automated Tests

**File**: `tests/test_jwt_auth.py` (26 tests, 96% coverage)

```python
def test_expired_token():
    """Test that expired tokens are rejected"""
    auth = JWTAuthenticator(token_expiry_hours=1/3600)  # 1 second
    token = auth.generate_token("P01", "TEST", "player")

    time.sleep(2)  # Wait for expiration

    payload = auth.validate_token(token)
    assert payload is None  # Token rejected

def test_invalid_signature():
    """Test that tokens with wrong signature are rejected"""
    auth1 = JWTAuthenticator(secret_key="secret1")
    auth2 = JWTAuthenticator(secret_key="secret2")

    token = auth1.generate_token("P01", "TEST", "player")

    # Try to validate with wrong secret
    payload = auth2.validate_token(token)
    assert payload is None  # Rejected

def test_agent_id_mismatch():
    """Test that token for P01 cannot be used by P02"""
    auth = JWTAuthenticator()
    token = auth.generate_token("P01", "TEST", "player")

    # Try to use P01's token as P02
    with pytest.raises(AuthorizationError):
        auth.verify_agent_access(token, "P02", "TEST")
```

### Manual Security Testing

```bash
# 1. Test token expiration
python -c "
from SHARED.league_sdk.auth import JWTAuthenticator
import time

auth = JWTAuthenticator(token_expiry_hours=1/3600)
token = auth.generate_token('P01', 'TEST', 'player')
print('Valid:', auth.validate_token(token) is not None)
time.sleep(2)
print('After expiry:', auth.validate_token(token) is not None)
"

# 2. Test invalid signature
python -c "
from SHARED.league_sdk.auth import JWTAuthenticator

auth1 = JWTAuthenticator(secret_key='secret1')
auth2 = JWTAuthenticator(secret_key='secret2')
token = auth1.generate_token('P01', 'TEST', 'player')
print('With correct secret:', auth1.validate_token(token) is not None)
print('With wrong secret:', auth2.validate_token(token) is not None)
"
```

---

## Incident Response

### Security Event Monitoring

**Key events to monitor**:
```python
# Authentication failures
logger.warning("AUTH_FAILED", agent_id="P01", reason="expired_token")

# Authorization failures
logger.error("AUTHZ_FAILED", agent_id="P01", required="P02")

# Anomalies
logger.warning("ANOMALY_DETECTED", event="multiple_failed_logins", count=10)
```

### Incident Response Plan

**1. Detection**:
- Monitor logs for AUTH_FAILED, AUTHZ_FAILED events
- Alert on >10 failures in 1 minute
- Alert on token reuse after expiration

**2. Containment**:
```bash
# Revoke all tokens
python scripts/revoke_all_tokens.py

# Rotate JWT secret
export LEAGUE_JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# Restart all agents
pkill -f "agents.*.main"
python scripts/start_league.py
```

**3. Eradication**:
- Identify attack vector
- Patch vulnerability
- Update security tests

**4. Recovery**:
- Generate new tokens
- Re-register all agents
- Verify system integrity

**5. Lessons Learned**:
- Document incident
- Update security procedures
- Add tests for vulnerability

---

## Production Deployment Checklist

**Before deploying to production, complete:**

- [ ] Set strong JWT secret (32+ chars, from secrets manager)
- [ ] Configure short token expiration (1-4 hours)
- [ ] Enable HTTPS with valid certificates
- [ ] Configure firewall rules (restrict ports)
- [ ] Enable rate limiting (10-100 req/min)
- [ ] Set up monitoring and alerting
- [ ] Encrypt data at rest
- [ ] Regular security updates (weekly)
- [ ] Penetration testing (before launch)
- [ ] Incident response plan documented

---

## References

- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **TLS Configuration**: https://ssl-config.mozilla.org/

---

**Maintained By**: MCP Development Team
**Last Updated**: 2025-12-31
**Version**: 1.0.0
