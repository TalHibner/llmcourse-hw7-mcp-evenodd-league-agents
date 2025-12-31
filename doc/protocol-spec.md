# MCP League Protocol v2 Specification

**Version:** 2.0
**Status:** Stable
**Last Updated:** December 31, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Message Envelope Format](#message-envelope-format)
3. [Message Types](#message-types)
4. [Error Codes](#error-codes)
5. [Timeout Values](#timeout-values)
6. [Retry Policy](#retry-policy)
7. [Authentication](#authentication)
8. [JSON-RPC 2.0 Transport](#json-rpc-20-transport)

---

## 1. Overview

The MCP League Protocol v2 (league.v2) defines the communication standard for multi-agent tournament systems. It supports:

- Autonomous agent registration (referees and players)
- Tournament lifecycle management (rounds, matches, standings)
- Game execution with timeout enforcement
- Error handling and retry mechanisms
- Authentication via token-based authorization

**Protocol Name:** `league.v2`
**Transport:** JSON-RPC 2.0 over HTTP
**Encoding:** UTF-8
**Content-Type:** `application/json`

---

## 2. Message Envelope Format

All protocol messages MUST include the following envelope fields:

```json
{
  "protocol": "league.v2",
  "message_type": "<MESSAGE_TYPE>",
  "sender": "<type>:<id>",
  "timestamp": "<ISO-8601-UTC>",
  "conversation_id": "<uuid>",
  "auth_token": "<token>"
}
```

### Required Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `protocol` | string | Always `"league.v2"` | Protocol version identifier |
| `message_type` | string | See [Message Types](#message-types) | One of 16 core message types |
| `sender` | string | `<type>:<id>` | Sender identification (e.g., `"player:P01"`, `"referee:REF01"`, `"league_manager"`) |
| `timestamp` | string | ISO-8601 UTC with Z suffix | Message creation time (e.g., `"2025-12-31T10:30:00Z"`) |
| `conversation_id` | string | UUID or unique string | Conversation/transaction identifier |
| `auth_token` | string | Token string or empty | Authentication token (empty for registration requests only) |

### Field Constraints

**sender Format:**
- League Manager: `"league_manager"` or `"league_manager:<id>"`
- Referee: `"referee:<referee_id>"` (e.g., `"referee:REF01"`)
- Player: `"player:<player_id>"` (e.g., `"player:P01"`)

**timestamp Format:**
- MUST be ISO-8601 format
- MUST be in UTC timezone
- MUST end with `Z` suffix
- Example: `"2025-12-31T10:30:00Z"`

**auth_token:**
- Empty string (`""`) for registration requests
- Non-empty for all other messages after registration
- Format: `"tok_<hash>"` (e.g., `"tok_abc123xyz789"`)

---

## 3. Message Types

### 3.1 Registration Messages (4 types)

#### REFEREE_REGISTER_REQUEST
**Direction:** Referee → League Manager
**Purpose:** Referee registers with the league
**Auth Required:** No (auth_token = "")

**Additional Fields:**
```json
{
  "referee_meta": {
    "display_name": "string",
    "version": "string",
    "game_types": ["string"],
    "contact_endpoint": "string (URL)",
    "max_concurrent_matches": "integer"
  }
}
```

---

#### REFEREE_REGISTER_RESPONSE
**Direction:** League Manager → Referee
**Purpose:** Confirm referee registration
**Auth Required:** No

**Additional Fields:**
```json
{
  "status": "ACCEPTED | REJECTED",
  "referee_id": "string (if ACCEPTED)",
  "auth_token": "string (if ACCEPTED)",
  "league_id": "string (if ACCEPTED)",
  "rejection_reason": "string (if REJECTED)"
}
```

---

#### LEAGUE_REGISTER_REQUEST
**Direction:** Player → League Manager
**Purpose:** Player registers for the league
**Auth Required:** No (auth_token = "")

**Additional Fields:**
```json
{
  "player_meta": {
    "display_name": "string",
    "version": "string",
    "game_types": ["string"],
    "contact_endpoint": "string (URL)"
  }
}
```

---

#### LEAGUE_REGISTER_RESPONSE
**Direction:** League Manager → Player
**Purpose:** Confirm player registration
**Auth Required:** No

**Additional Fields:**
```json
{
  "status": "ACCEPTED | REJECTED",
  "player_id": "string (if ACCEPTED)",
  "auth_token": "string (if ACCEPTED)",
  "league_id": "string (if ACCEPTED)",
  "rejection_reason": "string (if REJECTED)"
}
```

---

### 3.2 Round Management Messages (2 types)

#### ROUND_ANNOUNCEMENT
**Direction:** League Manager → All Players
**Purpose:** Announce new round with match assignments
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "round_id": "string or integer",
  "league_id": "string",
  "matches": [
    {
      "match_id": "string",
      "game_type": "string",
      "player_A_id": "string",
      "player_B_id": "string",
      "referee_endpoint": "string (URL)"
    }
  ]
}
```

---

#### ROUND_COMPLETED
**Direction:** League Manager → All Players
**Purpose:** Notify round completion
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "round_id": "string or integer",
  "league_id": "string",
  "completed_matches": ["string"],
  "next_round_id": "string or null"
}
```

---

### 3.3 Game Execution Messages (5 types)

#### GAME_INVITATION
**Direction:** Referee → Player
**Purpose:** Invite player to match
**Auth Required:** Yes
**Timeout:** Player must respond with GAME_JOIN_ACK within 5 seconds

**Additional Fields:**
```json
{
  "match_id": "string",
  "game_type": "string",
  "role_in_match": "PLAYER_A | PLAYER_B",
  "opponent_id": "string"
}
```

---

#### GAME_JOIN_ACK
**Direction:** Player → Referee
**Purpose:** Acknowledge match invitation
**Auth Required:** Yes
**Response Window:** Within 5 seconds of GAME_INVITATION

**Additional Fields:**
```json
{
  "match_id": "string",
  "accept": "boolean",
  "arrival_timestamp": "string (ISO-8601 UTC)"
}
```

---

#### CHOOSE_PARITY_CALL
**Direction:** Referee → Player
**Purpose:** Request player's parity choice
**Auth Required:** Yes
**Timeout:** Player must respond within 30 seconds

**Additional Fields:**
```json
{
  "match_id": "string",
  "game_type": "string",
  "deadline": "string (ISO-8601 UTC)",
  "context": {
    "opponent_id": "string",
    "round_id": "string or integer"
  }
}
```

---

#### CHOOSE_PARITY_RESPONSE
**Direction:** Player → Referee
**Purpose:** Submit parity choice
**Auth Required:** Yes
**Response Window:** Within 30 seconds of CHOOSE_PARITY_CALL

**Additional Fields:**
```json
{
  "match_id": "string",
  "parity_choice": "even | odd"
}
```

**Valid Values:**
- `parity_choice`: MUST be exactly `"even"` or `"odd"` (lowercase)

---

#### GAME_OVER
**Direction:** Referee → Both Players
**Purpose:** Announce match result
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "match_id": "string",
  "game_result": {
    "status": "WIN | DRAW | CANCELLED",
    "winner_player_id": "string or null",
    "drawn_number": "integer",
    "number_parity": "even | odd",
    "choices": {
      "<player_id>": "even | odd"
    },
    "reason": "string"
  }
}
```

---

### 3.4 League Management Messages (3 types)

#### MATCH_RESULT_REPORT
**Direction:** Referee → League Manager
**Purpose:** Report match outcome
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "match_id": "string",
  "round_id": "string or integer",
  "league_id": "string",
  "result": {
    "winner": "string or null",
    "score": {
      "<player_id>": "integer (points)"
    },
    "details": {
      "drawn_number": "integer",
      "choices": {
        "<player_id>": "even | odd"
      }
    }
  }
}
```

**Scoring:**
- Win: 3 points to winner, 0 to loser
- Draw: 1 point to each player
- Technical Loss (timeout): 3 points to opponent, 0 to offender

---

#### LEAGUE_STANDINGS_UPDATE
**Direction:** League Manager → All Players
**Purpose:** Broadcast current standings
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "league_id": "string",
  "round_id": "string or integer",
  "standings": [
    {
      "rank": "integer",
      "player_id": "string",
      "display_name": "string",
      "played": "integer",
      "wins": "integer",
      "draws": "integer",
      "losses": "integer",
      "points": "integer"
    }
  ]
}
```

**Ranking Rules:**
1. Sort by points (descending)
2. Ties broken by wins (descending)
3. Further ties broken alphabetically by player_id

---

#### LEAGUE_COMPLETED
**Direction:** League Manager → All Players
**Purpose:** Announce league completion
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "league_id": "string",
  "total_rounds": "integer",
  "total_matches": "integer",
  "champion": {
    "player_id": "string",
    "display_name": "string",
    "points": "integer"
  },
  "final_standings": [
    {
      "rank": "integer",
      "player_id": "string",
      "display_name": "string",
      "points": "integer"
    }
  ]
}
```

---

### 3.5 Error Messages (2 types)

#### LEAGUE_ERROR
**Direction:** League Manager → Any Agent
**Purpose:** Report league-level error
**Auth Required:** Yes (if applicable)

**Additional Fields:**
```json
{
  "error_code": "string",
  "error_description": "string",
  "context": {
    "additional_info": "any"
  }
}
```

**See [Error Codes](#error-codes) for details**

---

#### GAME_ERROR
**Direction:** Referee → Player(s)
**Purpose:** Report game-level error
**Auth Required:** Yes

**Additional Fields:**
```json
{
  "match_id": "string",
  "error_code": "string",
  "error_description": "string",
  "affected_player": "string or null",
  "action_required": "string",
  "retry_count": "integer",
  "max_retries": "integer",
  "consequence": "string"
}
```

**See [Error Codes](#error-codes) for details**

---

## 4. Error Codes

| Code | Name | Category | Retryable | Description |
|------|------|----------|-----------|-------------|
| E001 | TIMEOUT_ERROR | Game | Yes (3x) | Response not received within timeout window |
| E002 | INVALID_CHOICE | Game | No | Parity choice is not "even" or "odd" |
| E003 | MISSING_REQUIRED_FIELD | Protocol | No | Required message field is missing |
| E004 | INVALID_PARITY_CHOICE | Game | No | Parity choice validation failed |
| E005 | PLAYER_NOT_REGISTERED | League | No | Player ID not found in registry |
| E009 | CONNECTION_ERROR | Network | Yes (3x) | Network connectivity issue |
| E011 | AUTH_TOKEN_MISSING | Auth | No | Auth token missing when required |
| E012 | AUTH_TOKEN_INVALID | Auth | No | Auth token validation failed |
| E013 | PLAYER_NOT_FOUND | League | No | Player does not exist |
| E014 | LEAGUE_NOT_FOUND | League | No | League does not exist |

### Error Handling Guidelines

**Retryable Errors (E001, E009):**
- Retry up to 3 times with exponential backoff
- Delays: 1s, 2s, 4s
- After max retries, treat as technical loss or failure

**Non-Retryable Errors (All Others):**
- Report to user/logs
- Terminate current operation
- May require manual intervention

---

## 5. Timeout Values

| Operation | Timeout | Consequence |
|-----------|---------|-------------|
| **GAME_JOIN_ACK** | 5 seconds | Match cancelled, notified to League Manager |
| **CHOOSE_PARITY_RESPONSE** | 30 seconds | Retry up to 3 times, then technical loss |
| **Generic API Response** | 10 seconds | Retry with exponential backoff |
| **HTTP Request** | 5 seconds | Retry with circuit breaker |

### Timeout Enforcement

- All timeouts are measured from message send time
- Timestamps MUST be UTC for accurate timeout calculation
- Timeouts are enforced by the requesting party (Referee or League Manager)
- Timeout violations trigger error handling (see [Retry Policy](#retry-policy))

---

## 6. Retry Policy

### Exponential Backoff Strategy

**Configuration:**
- `max_retries`: 3
- `backoff_strategy`: "exponential"
- `backoff_base`: 1 second

**Delay Calculation:**
```
delay = base_delay * (2 ^ attempt_number)

Attempt 1: 1 second
Attempt 2: 2 seconds
Attempt 3: 4 seconds
```

### Retry Workflow

```
1. Send request
2. Wait for response (with timeout)
3. If timeout:
   a. retry_count < max_retries?
      - Yes: Wait (exponential delay), then retry
      - No: Report failure
4. If error received:
   a. Error retryable?
      - Yes: Retry (as above)
      - No: Report error, stop
```

### Circuit Breaker

**States:**
- **CLOSED**: Normal operation, requests allowed
- **OPEN**: Too many failures (threshold: 5), reject requests immediately
- **HALF_OPEN**: Testing recovery, allow 1 request

**Transitions:**
- CLOSED → OPEN: After 5 consecutive failures
- OPEN → HALF_OPEN: After 30 seconds
- HALF_OPEN → CLOSED: If test request succeeds
- HALF_OPEN → OPEN: If test request fails

**Per-Endpoint Tracking:**
- Each endpoint has its own circuit breaker state
- Failures on endpoint A don't affect endpoint B

---

## 7. Authentication

### Token Generation

**During Registration:**
1. Agent sends registration request (auth_token = "")
2. League Manager validates request
3. If accepted, generates unique token
4. Returns token in registration response

**Token Format:**
```
tok_<hash>
```
Where `<hash>` is a 32-character hexadecimal string.

**Example:** `"tok_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"`

### Token Usage

**All messages after registration MUST include auth_token**

**Validation:**
- League Manager validates tokens for all incoming messages
- Invalid token → LEAGUE_ERROR (E012: AUTH_TOKEN_INVALID)
- Missing token → LEAGUE_ERROR (E011: AUTH_TOKEN_MISSING)

**Token Lifetime:**
- Valid for the duration of the league
- Does not expire
- Unique per agent

---

## 8. JSON-RPC 2.0 Transport

All messages are transmitted using JSON-RPC 2.0 over HTTP.

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "<method_name>",
  "params": {
    "protocol": "league.v2",
    "message_type": "<MESSAGE_TYPE>",
    "sender": "<type>:<id>",
    "timestamp": "<ISO-8601-UTC>",
    "conversation_id": "<uuid>",
    "auth_token": "<token>",
    ...additional fields...
  },
  "id": <request_id>
}
```

### Response Format (Success)

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "<MESSAGE_TYPE>",
    "sender": "<type>:<id>",
    "timestamp": "<ISO-8601-UTC>",
    "conversation_id": "<uuid>",
    ...additional fields...
  },
  "id": <request_id>
}
```

### Response Format (Error)

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": <error_code>,
    "message": "<error_message>",
    "data": {
      ...additional error details...
    }
  },
  "id": <request_id>
}
```

### HTTP Details

- **Method:** POST
- **Endpoint:** `/mcp`
- **Content-Type:** `application/json`
- **Accept:** `application/json`
- **User-Agent:** `<agent_type>/<version>`

### Example Method Names

| Message Type | JSON-RPC Method |
|--------------|-----------------|
| REFEREE_REGISTER_REQUEST | `register_referee` |
| LEAGUE_REGISTER_REQUEST | `register_player` |
| ROUND_ANNOUNCEMENT | `notify_round` |
| GAME_INVITATION | `handle_game_invitation` |
| CHOOSE_PARITY_CALL | `choose_parity` |
| MATCH_RESULT_REPORT | `report_match_result` |

---

## Appendix A: Complete Message Type Reference

| # | Message Type | Category | Direction | Timeout |
|---|--------------|----------|-----------|---------|
| 1 | REFEREE_REGISTER_REQUEST | Registration | Ref → LM | 10s |
| 2 | REFEREE_REGISTER_RESPONSE | Registration | LM → Ref | - |
| 3 | LEAGUE_REGISTER_REQUEST | Registration | Player → LM | 10s |
| 4 | LEAGUE_REGISTER_RESPONSE | Registration | LM → Player | - |
| 5 | ROUND_ANNOUNCEMENT | Round Mgmt | LM → All Players | - |
| 6 | ROUND_COMPLETED | Round Mgmt | LM → All Players | - |
| 7 | GAME_INVITATION | Game Exec | Ref → Player | - |
| 8 | GAME_JOIN_ACK | Game Exec | Player → Ref | 5s |
| 9 | CHOOSE_PARITY_CALL | Game Exec | Ref → Player | - |
| 10 | CHOOSE_PARITY_RESPONSE | Game Exec | Player → Ref | 30s |
| 11 | GAME_OVER | Game Exec | Ref → Both Players | - |
| 12 | MATCH_RESULT_REPORT | League Mgmt | Ref → LM | 10s |
| 13 | LEAGUE_STANDINGS_UPDATE | League Mgmt | LM → All Players | - |
| 14 | LEAGUE_COMPLETED | League Mgmt | LM → All Players | - |
| 15 | LEAGUE_ERROR | Error | LM → Any | - |
| 16 | GAME_ERROR | Error | Ref → Player | - |

**Legend:**
- LM = League Manager
- Ref = Referee
- Player = Player Agent

---

## Appendix B: Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-31 | Initial specification for Even/Odd League |

---

**End of Protocol Specification**
