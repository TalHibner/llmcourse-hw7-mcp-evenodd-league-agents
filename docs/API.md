# API Documentation

**Version**: 1.0.0
**Protocol**: league.v2 (JSON-RPC 2.0)
**Last Updated**: 2025-12-31

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [JSON-RPC Format](#json-rpc-format)
4. [League Manager API](#league-manager-api)
5. [Referee API](#referee-api)
6. [Player API](#player-api)
7. [Message Types Reference](#message-types-reference)
8. [Error Codes](#error-codes)
9. [Examples](#examples)
10. [Rate Limits](#rate-limits)

---

## Overview

The MCP Even/Odd League system uses **JSON-RPC 2.0** over HTTP for all agent communication. All agents expose a single `/mcp` endpoint that handles multiple message types based on the protocol specification.

### Base URLs

| Agent Type | Default Port | Base URL | Interactive Docs |
|------------|--------------|----------|------------------|
| League Manager | 8000 | `http://localhost:8000` | `http://localhost:8000/docs` |
| Referee | 8001-8010 | `http://localhost:800X` | `http://localhost:800X/docs` |
| Player | 8101-8200 | `http://localhost:81XX` | `http://localhost:81XX/docs` |

**Note**: Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) for each agent.

### Communication Pattern

```
Player ←→ League Manager: Registration, Standings
League Manager ←→ Referee: Match Assignment, Results
Referee ←→ Player: Game Execution (Invitations, Moves)
```

---

## Authentication

### JWT Token-Based Authentication

The system uses **JWT (JSON Web Tokens)** for agent authentication:

1. **Registration**: Agents register with League Manager (no authentication required)
2. **Token Generation**: League Manager generates a signed JWT token
3. **Token Distribution**: Token is included in all subsequent messages
4. **Token Validation**: Receiving agents validate signature and claims

### Token Structure

```json
{
  "sub": "P01",
  "agent_id": "P01",
  "league_id": "TEST_LEAGUE",
  "agent_type": "player",
  "iat": 1735682400,
  "exp": 1735768800,
  "nbf": 1735682400,
  "jti": "a7f9c8e1d4b2a6e8..."
}
```

### Token Claims

| Claim | Description | Example |
|-------|-------------|---------|
| `sub` | Subject (agent ID) | "P01" |
| `agent_id` | Agent identifier | "P01" |
| `league_id` | League identifier | "TEST_LEAGUE" |
| `agent_type` | Agent type | "player", "referee", "league_manager" |
| `iat` | Issued at (Unix timestamp) | 1735682400 |
| `exp` | Expiration time (Unix timestamp) | 1735768800 |
| `nbf` | Not before (Unix timestamp) | 1735682400 |
| `jti` | JWT ID (unique identifier) | "a7f9c8e1..." |

### Authentication Flow

```python
# 1. Player registers (no auth required)
POST http://localhost:8000/mcp
{
  "jsonrpc": "2.0",
  "method": "register_player",
  "params": {
    "message_type": "LEAGUE_REGISTER_REQUEST",
    "sender": "player:P01",
    "player_meta": {...}
  }
}

# 2. League Manager responds with token
{
  "jsonrpc": "2.0",
  "result": {
    "response": {
      "status": "ACCEPTED",
      "player_id": "P01",
      "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
}

# 3. Player includes token in all subsequent requests
POST http://localhost:8001/mcp
{
  "jsonrpc": "2.0",
  "method": "join_game",
  "params": {
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    ...
  }
}
```

**Implementation**: See `SHARED/league_sdk/auth.py` for token generation and validation.

---

## JSON-RPC Format

All API calls follow **JSON-RPC 2.0** specification (https://www.jsonrpc.org/specification).

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": {
    "message_type": "MESSAGE_TYPE",
    "sender": "agent_type:agent_id",
    "timestamp": "2025-12-31T20:00:00Z",
    ...
  },
  "id": 1
}
```

### Success Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "response": {...}
  },
  "id": 1
}
```

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "detail": "Additional error information"
    }
  },
  "id": 1
}
```

---

## League Manager API

**Base URL**: `http://localhost:8000`
**Endpoint**: `/mcp`

### POST /mcp

Main JSON-RPC endpoint handling multiple message types.

#### 1. Referee Registration

**Method**: `register_referee`
**Message Type**: `REFEREE_REGISTER_REQUEST`
**Authentication**: None (registration endpoint)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "register_referee",
  "params": {
    "message_type": "REFEREE_REGISTER_REQUEST",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T20:00:00+00:00",
    "conversation_id": "register_REF01",
    "referee_meta": {
      "display_name": "Referee 01",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8001/mcp",
      "max_concurrent_matches": 10
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "response": {
      "sender": "league_manager:LEAGUE_MANAGER_01",
      "timestamp": "2025-12-31T20:00:01+00:00",
      "conversation_id": "register_REF01",
      "status": "ACCEPTED",
      "referee_id": "REF01",
      "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "league_id": "TEST_LEAGUE"
    }
  },
  "id": 1
}
```

**Status Codes:**
- `200 OK`: Registration successful
- `400 Bad Request`: Invalid request format
- `409 Conflict`: Referee already registered
- `503 Service Unavailable`: League at capacity

---

#### 2. Player Registration

**Method**: `register_player`
**Message Type**: `LEAGUE_REGISTER_REQUEST`
**Authentication**: None (registration endpoint)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "register_player",
  "params": {
    "message_type": "LEAGUE_REGISTER_REQUEST",
    "sender": "player:P01",
    "timestamp": "2025-12-31T20:00:00+00:00",
    "conversation_id": "register_P01",
    "player_meta": {
      "display_name": "AlphaBot",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8101/mcp"
    },
    "league_id": "TEST_LEAGUE"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "response": {
      "sender": "league_manager:LEAGUE_MANAGER_01",
      "timestamp": "2025-12-31T20:00:01+00:00",
      "conversation_id": "register_P01",
      "status": "ACCEPTED",
      "player_id": "P01",
      "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "league_id": "TEST_LEAGUE"
    }
  },
  "id": 1
}
```

**Player Metadata Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Human-readable player name (max 100 chars) |
| `version` | string | Yes | Player agent version (semantic versioning) |
| `game_types` | array | Yes | Supported game types (e.g., ["even_odd"]) |
| `contact_endpoint` | string | Yes | HTTP endpoint URL for receiving messages |

---

#### 3. Match Result Report

**Method**: `report_match_result`
**Message Type**: `MATCH_RESULT_REPORT`
**Authentication**: JWT token required

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "report_match_result",
  "params": {
    "message_type": "MATCH_RESULT_REPORT",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T20:05:00+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "round_id": "R01",
    "league_id": "TEST_LEAGUE",
    "result": {
      "status": "WIN",
      "winner_id": "P01",
      "final_score": {"P01": 3, "P02": 0},
      "game_duration_seconds": 5.2,
      "reason": "P01 chose EVEN, number was 4"
    },
    "score": {"P01": 3, "P02": 0},
    "transcript": [...]
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "message": "Match result recorded"
  },
  "id": 1
}
```

**Game Status Values:**
- `WIN`: One player won
- `DRAW`: Match ended in a draw
- `CANCELLED`: Match was cancelled (timeout, error, etc.)

---

#### 4. Start League

**Method**: `start_league`
**Message Type**: N/A (Internal command)
**Authentication**: Admin token (if configured)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "start_league",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "total_rounds": 3,
    "total_matches": 6,
    "message": "League started"
  },
  "id": 1
}
```

---

## Referee API

**Base URL**: `http://localhost:8001` (or 8002-8010)
**Endpoint**: `/mcp`

### POST /mcp

#### 1. Game Join Acknowledgment

**Method**: `join_game`
**Message Type**: `GAME_JOIN_ACK`
**Authentication**: JWT token required
**Sent By**: Player

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "join_game",
  "params": {
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P01",
    "timestamp": "2025-12-31T20:01:00+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "player_id": "P01",
    "ready": true
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "message": "Player joined"
  },
  "id": 1
}
```

**Timeout**: 5 seconds from invitation
**Behavior**: If player doesn't join within timeout, match is cancelled

---

#### 2. Parity Choice Response

**Method**: `choose_parity`
**Message Type**: `CHOOSE_PARITY_RESPONSE`
**Authentication**: JWT token required
**Sent By**: Player

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "choose_parity",
  "params": {
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "sender": "player:P01",
    "timestamp": "2025-12-31T20:01:05+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "player_id": "P01",
    "choice": "even"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "message": "Choice recorded"
  },
  "id": 1
}
```

**Valid Choices:**
- `"even"`: Player chooses even numbers
- `"odd"`: Player chooses odd numbers

**Timeout**: 30 seconds from choice call
**Behavior**: If player doesn't respond within timeout, match is forfeited

---

## Player API

**Base URL**: `http://localhost:8101` (or 8102-8200)
**Endpoint**: `/mcp`

### POST /mcp

#### 1. Round Announcement

**Method**: `receive_round_announcement`
**Message Type**: `ROUND_ANNOUNCEMENT`
**Authentication**: None
**Sent By**: League Manager

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "receive_round_announcement",
  "params": {
    "message_type": "ROUND_ANNOUNCEMENT",
    "sender": "league_manager:LEAGUE_MANAGER_01",
    "timestamp": "2025-12-31T20:00:00+00:00",
    "conversation_id": "round_R01",
    "auth_token": "",
    "round_id": "R01",
    "league_id": "TEST_LEAGUE",
    "matches": [
      {
        "match_id": "R01M01",
        "player_a_id": "P01",
        "player_b_id": "P02",
        "referee_id": "REF01"
      }
    ],
    "expected_start_time": "2025-12-31T20:01:00+00:00"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success"
  },
  "id": 1
}
```

---

#### 2. Game Invitation

**Method**: `receive_game_invitation`
**Message Type**: `GAME_INVITATION`
**Authentication**: JWT token included
**Sent By**: Referee

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "receive_game_invitation",
  "params": {
    "message_type": "GAME_INVITATION",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T20:01:00+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "opponent_id": "P02",
    "role_in_match": "PLAYER_A"
  },
  "id": 1
}
```

**Response (Async):**
Player responds by calling Referee's `/mcp` endpoint with `GAME_JOIN_ACK`.

**Roles:**
- `PLAYER_A`: First player in match
- `PLAYER_B`: Second player in match

---

#### 3. Choose Parity Call

**Method**: `receive_parity_call`
**Message Type**: `CHOOSE_PARITY_CALL`
**Authentication**: JWT token included
**Sent By**: Referee

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "receive_parity_call",
  "params": {
    "message_type": "CHOOSE_PARITY_CALL",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T20:01:02+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "deadline": "2025-12-31T20:01:32+00:00"
  },
  "id": 1
}
```

**Response (Async):**
Player responds by calling Referee's `/mcp` endpoint with `CHOOSE_PARITY_RESPONSE`.

---

#### 4. Game Over

**Method**: `receive_game_over`
**Message Type**: `GAME_OVER`
**Authentication**: JWT token included
**Sent By**: Referee

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "receive_game_over",
  "params": {
    "message_type": "GAME_OVER",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T20:01:35+00:00",
    "conversation_id": "match_R01M01",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "match_id": "R01M01",
    "result": {
      "status": "WIN",
      "winner_id": "P01",
      "final_score": {"P01": 3, "P02": 0},
      "drawn_number": 4,
      "player_a_choice": "even",
      "player_b_choice": "odd",
      "game_duration_seconds": 5.2
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success"
  },
  "id": 1
}
```

---

#### 5. Standings Update

**Method**: `receive_standings_update`
**Message Type**: `LEAGUE_STANDINGS_UPDATE`
**Authentication**: None
**Sent By**: League Manager

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "receive_standings_update",
  "params": {
    "message_type": "LEAGUE_STANDINGS_UPDATE",
    "sender": "league_manager:LEAGUE_MANAGER_01",
    "timestamp": "2025-12-31T20:01:40+00:00",
    "conversation_id": "standings_R01",
    "auth_token": "",
    "league_id": "TEST_LEAGUE",
    "round_id": "R01",
    "standings": [
      {
        "rank": 1,
        "player_id": "P01",
        "display_name": "AlphaBot",
        "played": 1,
        "wins": 1,
        "draws": 0,
        "losses": 0,
        "points": 3
      },
      {
        "rank": 2,
        "player_id": "P02",
        "display_name": "BetaBot",
        "played": 1,
        "wins": 0,
        "draws": 0,
        "losses": 1,
        "points": 0
      }
    ]
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success"
  },
  "id": 1
}
```

---

## Message Types Reference

All 16 core message types defined in the league.v2 protocol:

### Registration (4 messages)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `REFEREE_REGISTER_REQUEST` | Referee → League Manager | Referee requests to join league |
| `REFEREE_REGISTER_RESPONSE` | League Manager → Referee | Registration confirmation with token |
| `LEAGUE_REGISTER_REQUEST` | Player → League Manager | Player requests to join league |
| `LEAGUE_REGISTER_RESPONSE` | League Manager → Player | Registration confirmation with token |

### Round Management (2 messages)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `ROUND_ANNOUNCEMENT` | League Manager → Players | Announces new round with match schedule |
| `ROUND_COMPLETED` | League Manager → Players | Round finished notification |

### Game Execution (5 messages)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `GAME_INVITATION` | Referee → Player | Invitation to join match |
| `GAME_JOIN_ACK` | Player → Referee | Player accepts invitation |
| `CHOOSE_PARITY_CALL` | Referee → Player | Request for parity choice |
| `CHOOSE_PARITY_RESPONSE` | Player → Referee | Player's parity choice |
| `GAME_OVER` | Referee → Players | Match result notification |

### League Management (3 messages)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `MATCH_RESULT_REPORT` | Referee → League Manager | Final match result |
| `LEAGUE_STANDINGS_UPDATE` | League Manager → Players | Updated standings |
| `LEAGUE_COMPLETED` | League Manager → All | League finished, champion declared |

### Errors (2 messages)

| Message Type | Direction | Description |
|--------------|-----------|-------------|
| `LEAGUE_ERROR` | League Manager → Agent | League-level error |
| `GAME_ERROR` | Referee → Player | Match-level error |

---

## Error Codes

JSON-RPC 2.0 standard error codes plus custom codes:

| Code | Message | Description |
|------|---------|-------------|
| `-32700` | Parse error | Invalid JSON received |
| `-32600` | Invalid Request | JSON-RPC format error |
| `-32601` | Method not found | Unknown method name |
| `-32602` | Invalid params | Invalid method parameters |
| `-32603` | Internal error | Server-side error |
| `1001` | Authentication failed | Invalid or expired token |
| `1002` | Authorization failed | Token valid but insufficient permissions |
| `1003` | Agent not found | Referenced agent ID doesn't exist |
| `1004` | Match not found | Referenced match ID doesn't exist |
| `1005` | Timeout | Operation timed out |
| `1006` | League full | Maximum players/referees reached |
| `1007` | Invalid choice | Invalid parity choice |
| `1008` | Match cancelled | Match was cancelled |

---

## Examples

### Complete Match Flow

```python
# 1. Player joins league
POST http://localhost:8000/mcp
{
  "jsonrpc": "2.0",
  "method": "register_player",
  "params": {
    "message_type": "LEAGUE_REGISTER_REQUEST",
    "sender": "player:P01",
    "player_meta": {
      "display_name": "AlphaBot",
      "contact_endpoint": "http://localhost:8101/mcp"
    }
  }
}
# Response includes auth_token

# 2. League Manager announces round
POST http://localhost:8101/mcp
{
  "jsonrpc": "2.0",
  "method": "receive_round_announcement",
  "params": {
    "message_type": "ROUND_ANNOUNCEMENT",
    "round_id": "R01",
    "matches": [{"match_id": "R01M01", "player_a_id": "P01", ...}]
  }
}

# 3. Referee invites player
POST http://localhost:8101/mcp
{
  "jsonrpc": "2.0",
  "method": "receive_game_invitation",
  "params": {
    "message_type": "GAME_INVITATION",
    "match_id": "R01M01",
    "auth_token": "...",
    "opponent_id": "P02"
  }
}

# 4. Player joins game
POST http://localhost:8001/mcp
{
  "jsonrpc": "2.0",
  "method": "join_game",
  "params": {
    "message_type": "GAME_JOIN_ACK",
    "match_id": "R01M01",
    "auth_token": "...",
    "ready": true
  }
}

# 5. Referee requests choice
POST http://localhost:8101/mcp
{
  "jsonrpc": "2.0",
  "method": "receive_parity_call",
  "params": {
    "message_type": "CHOOSE_PARITY_CALL",
    "match_id": "R01M01",
    "deadline": "2025-12-31T20:01:32+00:00"
  }
}

# 6. Player makes choice
POST http://localhost:8001/mcp
{
  "jsonrpc": "2.0",
  "method": "choose_parity",
  "params": {
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "match_id": "R01M01",
    "choice": "even"
  }
}

# 7. Referee announces result
POST http://localhost:8101/mcp
{
  "jsonrpc": "2.0",
  "method": "receive_game_over",
  "params": {
    "message_type": "GAME_OVER",
    "result": {
      "winner_id": "P01",
      "drawn_number": 4
    }
  }
}
```

### Using Python httpx

```python
import httpx
from datetime import datetime, timezone

async def register_player():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "register_player",
                "params": {
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "sender": "player:P01",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "conversation_id": "register_P01",
                    "player_meta": {
                        "display_name": "MyBot",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": "http://localhost:8101/mcp"
                    },
                    "league_id": "TEST_LEAGUE"
                },
                "id": 1
            },
            timeout=10.0
        )

        result = response.json()
        auth_token = result["result"]["response"]["auth_token"]
        player_id = result["result"]["response"]["player_id"]

        return player_id, auth_token
```

---

## Rate Limits

Default rate limits (can be configured via environment variables):

| Endpoint Type | Limit | Window | Notes |
|---------------|-------|--------|-------|
| Registration | 10 req/min | Per IP | Prevents spam registrations |
| Match Operations | 100 req/min | Per token | Normal game operations |
| Standings Queries | 60 req/min | Per token | Read-only endpoint |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1735682520
```

**Rate Limit Exceeded Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "data": {
      "retry_after": 30
    }
  }
}
```

---

## Interactive API Documentation

Each agent provides interactive API documentation:

- **Swagger UI**: `http://localhost:<port>/docs`
- **ReDoc**: `http://localhost:<port>/redoc`

Example: http://localhost:8000/docs for League Manager

---

## SDK Usage

**Python SDK** (recommended):

```python
from SHARED.league_sdk.mcp_client import MCPClient
from SHARED.league_sdk.models import LeagueRegisterRequest, PlayerMeta

async def example():
    async with MCPClient() as client:
        request = LeagueRegisterRequest(
            sender="player:P01",
            player_meta=PlayerMeta(
                display_name="MyBot",
                contact_endpoint="http://localhost:8101/mcp"
            ),
            league_id="TEST_LEAGUE"
        )

        response = await client.call_tool(
            endpoint="http://localhost:8000/mcp",
            method="register_player",
            params=request.model_dump()
        )

        return response
```

---

## Further Reading

- **Protocol Specification**: See `doc/protocol-spec.md`
- **Message Examples**: See `doc/message-examples/`
- **Architecture Diagrams**: See `doc/diagrams/`
- **Security**: See `SECURITY.md`

---

**Last Updated**: 2025-12-31
**Maintainer**: MCP Development Team
**Feedback**: Open a GitHub issue for questions or corrections
