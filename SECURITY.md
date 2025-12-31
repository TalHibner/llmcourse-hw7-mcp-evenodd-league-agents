# Security Policy

## Supported Versions

The following versions of the MCP Even/Odd League system are currently supported with security updates:

| Version | Supported          | End of Support |
| ------- | ------------------ | -------------- |
| 1.0.x   | :white_check_mark: | Active         |
| < 1.0   | :x:                | Not supported  |

## Reporting a Vulnerability

We take the security of the MCP Even/Odd League system seriously. If you discover a security vulnerability, please follow these steps:

### Reporting Process

1. **DO NOT** report security vulnerabilities through public GitHub issues
2. **DO NOT** disclose the vulnerability publicly until it has been addressed
3. **DO** send details to: [Insert your contact email or create security@your-domain]

### What to Include in Your Report

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)
- Your contact information for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours of report
- **Status Update**: Within 7 days with assessment
- **Fix Timeline**: Critical issues within 30 days, others within 90 days
- **Disclosure**: Coordinated disclosure after fix is released

### Recognition

We appreciate security researchers who help us keep our project secure. With your permission, we will:
- Acknowledge your contribution in the CHANGELOG
- Credit you in the security advisory (unless you prefer to remain anonymous)

---

## Security Best Practices

### 1. JWT Token Management

#### Generating a Secure Secret Key

**CRITICAL**: Never use the default auto-generated secret in production.

```bash
# Generate a cryptographically secure 32-byte secret
python -c "import secrets; print(secrets.token_hex(32))"
```

**Example output:**
```
a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4
```

**Set in environment:**
```bash
export LEAGUE_JWT_SECRET="a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4"
```

Or add to `.env` file:
```bash
LEAGUE_JWT_SECRET=a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4a7f9c8e1d4b2a6e8f3c7d9a2b5e8f1c4
```

#### Token Expiration Configuration

**Default**: 24 hours (development)
**Recommended for Production**: 1-4 hours

```bash
# Short-lived tokens for better security
export JWT_EXPIRY_HOURS=2
```

**Why shorter expiration is better:**
- Limits the window of opportunity for token theft
- Forces re-authentication more frequently
- Reduces impact of compromised tokens

#### Token Storage Best Practices

**DO:**
- ✅ Store secrets in environment variables
- ✅ Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- ✅ Rotate secrets regularly (monthly recommended)
- ✅ Use different secrets for dev/staging/production

**DON'T:**
- ❌ Hardcode secrets in source code
- ❌ Commit `.env` files to version control
- ❌ Share secrets via email or chat
- ❌ Log token values (our logger automatically redacts them)

#### Secret Rotation Procedure

```bash
# 1. Generate new secret
NEW_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# 2. Update environment variable (zero-downtime with dual verification)
export LEAGUE_JWT_SECRET="$NEW_SECRET"

# 3. Restart all agents
python scripts/restart_agents.py

# 4. Verify all agents are using new secret
python scripts/verify_auth.py

# 5. Monitor logs for authentication failures
tail -f data/logs/system/*.log.jsonl | grep "INVALID_TOKEN"
```

### 2. Network Security

#### HTTPS Configuration (Production Required)

**Development** (HTTP only):
```python
# agents/league_manager/main.py
uvicorn.run(app, host="localhost", port=8000)
```

**Production** (HTTPS with TLS):
```python
# agents/league_manager/main.py
import uvicorn

uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="/path/to/privkey.pem",
    ssl_certfile="/path/to/fullchain.pem",
    ssl_version=ssl.PROTOCOL_TLS,
    ssl_cert_reqs=ssl.CERT_REQUIRED
)
```

**Obtaining SSL Certificates:**

1. **Let's Encrypt** (Free, automated):
   ```bash
   sudo certbot certonly --standalone -d your-domain.com
   # Certificates stored in /etc/letsencrypt/live/your-domain.com/
   ```

2. **Self-signed** (Testing only):
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

#### Firewall Configuration

**AWS Security Groups Example:**
```
Inbound Rules:
- Port 8000: Allow from trusted IPs only (League Manager)
- Ports 8001-8010: Internal network only (Referees)
- Ports 8101-8200: Internal network only (Players)

Outbound Rules:
- Port 443: HTTPS to external services
- Internal ports: Full access within VPC
```

**iptables Example (Linux):**
```bash
# Allow League Manager only from specific IP
sudo iptables -A INPUT -p tcp --dport 8000 -s 203.0.113.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP

# Allow internal agent communication
sudo iptables -A INPUT -p tcp --dport 8001:8200 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001:8200 -j DROP
```

#### Rate Limiting

**Installation:**
```bash
pip install slowapi
```

**Implementation:**
```python
# agents/league_manager/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/register/player")
@limiter.limit("10/minute")  # Limit to 10 registrations per minute per IP
async def register_player(request: Request, registration: LeagueRegisterRequest):
    # ... registration logic
    pass
```

**Recommended Rate Limits:**
- Registration endpoints: 10 requests/minute per IP
- Match endpoints: 100 requests/minute per IP
- Standings queries: 60 requests/minute per IP

### 3. Data Security

#### Log Sanitization

Our logging system automatically redacts sensitive fields:

```python
# SHARED/league_sdk/logger.py:45-60
SENSITIVE_FIELDS = ["auth_token", "password", "secret", "api_key"]

def sanitize_log_data(self, data: Dict) -> Dict:
    """Remove sensitive information from log data"""
    sanitized = data.copy()
    for key in SENSITIVE_FIELDS:
        if key in sanitized:
            sanitized[key] = "***REDACTED***"
    return sanitized
```

**Example log output:**
```json
{
  "timestamp": "2025-12-31T20:00:00Z",
  "level": "INFO",
  "event": "PLAYER_REGISTERED",
  "player_id": "P01",
  "auth_token": "***REDACTED***"
}
```

#### Data Encryption at Rest

**For Production Environments:**

1. **Linux (LUKS encryption):**
   ```bash
   # Encrypt data directory
   sudo cryptsetup luksFormat /dev/sdb1
   sudo cryptsetup luksOpen /dev/sdb1 encrypted_data
   sudo mkfs.ext4 /dev/mapper/encrypted_data
   sudo mount /dev/mapper/encrypted_data /path/to/data
   ```

2. **Cloud Provider Encryption:**
   - **AWS**: Enable EBS encryption, S3 server-side encryption
   - **Azure**: Enable Azure Disk Encryption
   - **GCP**: Enable encryption at rest for Persistent Disks

#### Secure File Permissions

```bash
# Restrict access to configuration and data directories
chmod 700 config/ data/
chmod 600 config/**/*.yaml config/**/*.json
chmod 600 .env

# Verify permissions
ls -la config/ data/
# Should show: drwx------ (700) for directories
#              -rw------- (600) for files
```

### 4. Dependency Security

#### Regular Security Updates

```bash
# Update all dependencies to latest versions
pip install --upgrade pip setuptools wheel
pip list --outdated

# Update specific security-critical packages
pip install --upgrade pyjwt fastapi uvicorn pydantic httpx
```

#### Security Scanning

**Using Safety:**
```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Generate detailed report
safety check --json > security_report.json
```

**Using pip-audit:**
```bash
# Install pip-audit
pip install pip-audit

# Audit installed packages
pip-audit

# Output in JSON format
pip-audit --format json
```

#### Dependency Pinning

**requirements.txt** with exact versions:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
httpx==0.26.0
pyjwt==2.8.0
python-dotenv==1.0.0
```

**Update process:**
1. Test updates in development environment
2. Run full test suite: `pytest`
3. Run security scan: `safety check`
4. Update `requirements.txt` with new versions
5. Deploy to staging for validation
6. Deploy to production with rollback plan

### 5. Input Validation

All inputs are validated using Pydantic models:

```python
# SHARED/league_sdk/models.py
class LeagueRegisterRequest(BaseModel):
    sender: str = Field(..., pattern=r'^player:P\d{2}$')
    conversation_id: str = Field(..., min_length=1, max_length=100)
    player_meta: PlayerMetadata

    @field_validator('sender')
    def validate_sender(cls, v):
        if not v.startswith('player:'):
            raise ValueError('Sender must start with "player:"')
        return v
```

**Protection against:**
- ✅ SQL Injection (N/A - no SQL database)
- ✅ XSS (Cross-Site Scripting) - JSON-only API
- ✅ Command Injection - No shell execution of user input
- ✅ Path Traversal - Path validation in repositories
- ✅ Malformed JSON - Pydantic validates all inputs

### 6. Authentication and Authorization

#### Authentication Flow

```
1. Player Registration (No Auth Required):
   Player → League Manager: LeagueRegisterRequest
   League Manager → Player: LeagueRegisterResponse (includes JWT)

2. Match Invitation (Token Required):
   Referee → Player: GameInvitation (includes auth_token)

3. Token Validation:
   Player validates token:
   - Signature verification (HS256)
   - Expiration check
   - Agent ID verification

4. Player Response:
   Player → Referee: GameJoinAck (includes auth_token)

5. Referee Validation:
   Referee validates token matches expected player_id
```

**Implementation:** See `SHARED/league_sdk/auth.py:50-96`

#### Authorization Checks

```python
# agents/referee/handlers.py
def verify_player_token(self, token: str, expected_player_id: str) -> bool:
    """Verify token belongs to expected player"""
    payload = self.jwt_auth.validate_token(token)
    if not payload:
        return False

    # Check agent_id matches expected player
    if payload.get('agent_id') != expected_player_id:
        self.logger.warning(
            "TOKEN_MISMATCH",
            expected=expected_player_id,
            actual=payload.get('agent_id')
        )
        return False

    # Check league_id matches current league
    if payload.get('league_id') != self.league_id:
        return False

    return True
```

---

## Known Security Considerations

### Development Mode

The system is designed for **educational and development use**. The following security limitations exist:

#### Current Limitations

| Risk | Development | Production Recommendation |
|------|-------------|---------------------------|
| Default JWT Secret | ⚠️ Auto-generated (insecure) | ✅ Strong, manually set secret |
| HTTP Transport | ⚠️ Unencrypted | ✅ HTTPS with valid TLS certificates |
| Registration Auth | ⚠️ No authentication | ✅ Add API keys or admin tokens |
| Rate Limiting | ⚠️ Disabled | ✅ Enable with slowapi |
| Audit Logging | ⚠️ Basic logging | ✅ Enhanced security audit trail |
| Network Exposure | ⚠️ localhost only | ✅ Firewall rules + reverse proxy |

#### Development Mode is Acceptable For:
- ✅ Educational purposes and homework assignments
- ✅ Local development and testing
- ✅ Proof-of-concept demonstrations
- ✅ Academic research projects

#### Production Deployment Requires:
- ✅ Strong JWT secret (32+ characters, cryptographically random)
- ✅ HTTPS with valid SSL certificates
- ✅ Authentication on all endpoints
- ✅ Rate limiting (10-100 req/min depending on endpoint)
- ✅ Firewall rules restricting access
- ✅ Regular security updates
- ✅ Monitoring and alerting
- ✅ Data encryption at rest
- ✅ Regular security audits

### Production Hardening Checklist

Before deploying to production, complete this checklist:

**JWT & Secrets:**
- [ ] Set strong `LEAGUE_JWT_SECRET` (32+ chars)
- [ ] Configure short token expiration (1-4 hours)
- [ ] Store secrets in secure vault (not .env files)
- [ ] Set up secret rotation schedule

**Network Security:**
- [ ] Enable HTTPS with valid certificates
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Use reverse proxy (nginx, traefik, or cloud load balancer)
- [ ] Enable rate limiting on all endpoints
- [ ] Restrict League Manager access to trusted IPs
- [ ] Use internal network for agent-to-agent communication

**Data Security:**
- [ ] Enable encryption at rest for data directory
- [ ] Set restrictive file permissions (700 for dirs, 600 for files)
- [ ] Configure log retention and rotation
- [ ] Enable audit logging for security events
- [ ] Set up automated backups

**Application Security:**
- [ ] Update all dependencies to latest secure versions
- [ ] Run security scanner (`safety check`, `pip-audit`)
- [ ] Enable request/response validation
- [ ] Configure CORS if needed (restrict to known origins)
- [ ] Disable debug mode and auto-reload
- [ ] Remove development tools from production environment

**Monitoring & Incident Response:**
- [ ] Set up monitoring for failed authentication attempts
- [ ] Configure alerts for security events
- [ ] Implement log aggregation (ELK, Splunk, or CloudWatch)
- [ ] Create incident response plan
- [ ] Document rollback procedures

---

## Vulnerability Disclosure History

### Version 1.0.0
**Status**: No vulnerabilities reported as of 2025-12-31

We maintain a transparent security posture. All disclosed vulnerabilities will be listed here with:
- CVE ID (if assigned)
- Severity rating (Critical/High/Medium/Low)
- Affected versions
- Fixed version
- Mitigation steps

---

## Security Testing

### Running Security Tests

```bash
# JWT authentication tests (26 tests)
pytest tests/test_jwt_auth.py -v

# Test coverage includes:
# - Token generation with various parameters
# - Token validation (valid, expired, invalid)
# - Signature verification
# - Agent access control
# - Token expiration handling
# - Registry management
```

### Security Test Coverage

| Component | Tests | Coverage | File |
|-----------|-------|----------|------|
| JWT Auth | 26 | 96% | `tests/test_jwt_auth.py` |
| Token Generation | 8 | 100% | Lines 15-45 |
| Token Validation | 10 | 100% | Lines 47-90 |
| Access Verification | 8 | 92% | Lines 92-130 |

### Manual Security Testing

```bash
# 1. Test expired token handling
python -c "
from SHARED.league_sdk.auth import JWTAuthenticator
import time

auth = JWTAuthenticator(token_expiry_hours=1/3600)  # 1 second
token = auth.generate_token('P01', 'TEST', 'player')
print(f'Valid: {auth.validate_token(token) is not None}')
time.sleep(2)
print(f'After expiry: {auth.validate_token(token) is not None}')
"

# 2. Test invalid signature
python -c "
from SHARED.league_sdk.auth import JWTAuthenticator

auth1 = JWTAuthenticator(secret_key='secret1')
auth2 = JWTAuthenticator(secret_key='secret2')
token = auth1.generate_token('P01', 'TEST', 'player')
print(f'Valid with correct secret: {auth1.validate_token(token) is not None}')
print(f'Valid with wrong secret: {auth2.validate_token(token) is not None}')
"
```

---

## Security Contact

For security-related questions or concerns:

- **General Questions**: Open a GitHub discussion (public)
- **Vulnerability Reports**: [Insert security email] (private)
- **Documentation Issues**: Open a GitHub issue

---

## Compliance and Certifications

This project is designed for educational use and does not claim compliance with:
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- PCI DSS (Payment Card Industry Data Security Standard)
- SOC 2 (Service Organization Control 2)

For production use requiring compliance, additional security controls must be implemented.

---

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Python Security Best Practices**: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

**Last Updated**: 2025-12-31
**Version**: 1.0.0
**Maintained By**: MCP Development Team
