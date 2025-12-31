# Architecture Design Document
## MCP Even/Odd League Multi-Agent System

**Version:** 1.0
**Date:** December 31, 2025
**Status:** Implementation Ready

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [Component Design](#3-component-design)
4. [Communication Protocol](#4-communication-protocol)
5. [Data Architecture](#5-data-architecture)
6. [State Management](#6-state-management)
7. [Error Handling Strategy](#7-error-handling-strategy)
8. [Security Architecture](#8-security-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [API Specifications](#10-api-specifications)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP EVEN/ODD LEAGUE SYSTEM                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: ORCHESTRATION                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         League Manager (Port 8000)                     │    │
│  │  - Registration • Scheduling • Standings • Reporting   │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP JSON-RPC
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: MATCH MANAGEMENT                                       │
│  ┌──────────────────┐     ┌──────────────────┐                │
│  │  Referee REF01   │     │  Referee REF02   │                │
│  │  (Port 8001)     │     │  (Port 8002)     │                │
│  │  - Match Mgmt    │     │  - Match Mgmt    │                │
│  │  - Game Rules    │     │  - Game Rules    │                │
│  └──────────────────┘     └──────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP JSON-RPC
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: PLAYERS                                                │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐              │
│  │ P01    │  │ P02    │  │ P03    │  │ P04    │              │
│  │ :8101  │  │ :8102  │  │ :8103  │  │ :8104  │              │
│  │Strategy│  │Strategy│  │Strategy│  │Strategy│              │
│  └────────┘  └────────┘  └────────┘  └────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────────┐
│ SHARED INFRASTRUCTURE                                           │
│  - Config Management (SHARED/config/)                           │
│  - Data Persistence (SHARED/data/)                              │
│  - Logging (SHARED/logs/)                                       │
│  - SDK Library (SHARED/league_sdk/)                             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Separation of Concerns**: Three distinct layers (orchestration, judging, gameplay)
2. **Protocol-First**: All communication via league.v2 protocol
3. **Stateless Agents**: All state persisted to SHARED/data/
4. **Configuration-Driven**: Behavior controlled via JSON configs
5. **Resilience**: Timeout handling, retries, circuit breakers
6. **Observability**: Comprehensive JSONL logging

---

## 2. Architecture Layers

### 2.1 Layer 1: Orchestration (League Manager)

**Responsibilities**:
- **Citizen Registry**: Maintain directory of all referees and players
- **Matchmaking**: Generate Round-Robin schedule
- **Source of Truth**: Maintain authoritative standings
- **Coordination**: Announce rounds, collect results, declare champion

**Key Components**:
- Registration Handler
- Round-Robin Scheduler
- Standings Calculator
- Message Broadcaster

**Data Owned**:
- `standings.json` - Current league rankings
- `rounds.json` - Complete round history
- `league.log.jsonl` - System event log

### 2.2 Layer 2: Match Management (Referees)

**Responsibilities**:
- **Match Execution**: Orchestrate individual matches
- **Rule Enforcement**: Apply Even/Odd game rules
- **Timeout Management**: Enforce 5s join, 30s move timeouts
- **Audit Trail**: Record complete match transcript

**Key Components**:
- Match State Machine
- Game Logic Module (Even/Odd rules)
- Timeout Enforcer
- Match Recorder

**Data Owned**:
- `match_<id>.json` - Per-match audit trail

### 2.3 Layer 3: Gameplay (Players)

**Responsibilities**:
- **Strategy Execution**: Choose "even" or "odd"
- **Response Timeliness**: Respond within timeout windows
- **History Tracking**: Learn from past matches
- **Self-Improvement**: Adapt strategy based on opponents

**Key Components**:
- Strategy Engine (random, pattern-based, LLM)
- State Tracker
- History Manager
- Response Handler

**Data Owned**:
- `player_<id>_history.json` - Personal match memory

---

## 3. Component Design

### 3.1 League Manager Components

```
┌─────────────────────────────────────────────────────────────┐
│                    League Manager                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ FastAPI HTTP Server (/mcp endpoint, port 8000)        │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Message Router                                        │ │
│  │  - REFEREE_REGISTER_REQUEST → RegistrationHandler    │ │
│  │  - LEAGUE_REGISTER_REQUEST → RegistrationHandler     │ │
│  │  - MATCH_RESULT_REPORT → ResultHandler               │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Registration     │  │ Round-Robin      │               │
│  │ Handler          │  │ Scheduler        │               │
│  │                  │  │                  │               │
│  │ - Assign IDs     │  │ - Generate       │               │
│  │ - Generate tokens│  │   pairings       │               │
│  │ - Validate meta  │  │ - Assign referees│               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Standings        │  │ Message          │               │
│  │ Calculator       │  │ Broadcaster      │               │
│  │                  │  │                  │               │
│  │ - Update points  │  │ - Send to all    │               │
│  │ - Calculate rank │  │ - Parallel sends │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Data Layer                                            │ │
│  │  - StandingsRepository (standings.json)              │ │
│  │  - RoundsRepository (rounds.json)                    │ │
│  │  - AgentRegistry (in-memory + config)                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Referee Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Referee Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ FastAPI HTTP Server (/mcp endpoint, configurable port│ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Match State Machine                                   │ │
│  │  CREATED → WAITING_FOR_PLAYERS → COLLECTING_CHOICES  │ │
│  │  → DRAWING_NUMBER → FINISHED                         │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Invitation       │  │ Choice           │               │
│  │ Manager          │  │ Collector        │               │
│  │                  │  │                  │               │
│  │ - Send invites   │  │ - Request choices│               │
│  │ - Wait for ACKs  │  │ - Enforce 30s    │               │
│  │ - Enforce 5s     │  │   timeout        │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Game Logic       │  │ Result           │               │
│  │ Module           │  │ Reporter         │               │
│  │                  │  │                  │               │
│  │ - Draw number    │  │ - Send GAME_OVER │               │
│  │ - Determine      │  │ - Send RESULT    │               │
│  │   winner         │  │   to LM          │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Match Recorder                                        │ │
│  │  - Transcript: all messages with timestamps          │ │
│  │  - Lifecycle: state transitions                      │ │
│  │  - Result: final outcome                             │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Player Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Player Agent                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ FastAPI HTTP Server (/mcp endpoint, configurable port│ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Message Handler                                       │ │
│  │  - ROUND_ANNOUNCEMENT → Store match info             │ │
│  │  - GAME_INVITATION → Send JOIN_ACK                   │ │
│  │  - CHOOSE_PARITY_CALL → Invoke Strategy              │ │
│  │  - GAME_OVER → Update stats                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Strategy Engine                                      │  │
│  │                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│  │  │ Random       │  │ Pattern-Based│  │ LLM-Driven│ │  │
│  │  │ Strategy     │  │ Strategy     │  │ Strategy  │ │  │
│  │  │              │  │              │  │ (optional)│ │  │
│  │  │ - coin flip  │  │ - Analyze    │  │ - Context │ │  │
│  │  │   "even" or  │  │   opponent   │  │ - Reason  │ │  │
│  │  │   "odd"      │  │   history    │  │ - Decide  │ │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ State Tracker    │  │ History Manager  │               │
│  │                  │  │                  │               │
│  │ - wins           │  │ - Match records  │               │
│  │ - losses         │  │ - Opponent       │               │
│  │ - draws          │  │   patterns       │               │
│  │ - points         │  │ - Win rate       │               │
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Shared SDK Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED/league_sdk/                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  models.py                                                   │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Pydantic Models for all message types:                ││
│  │  - MessageEnvelope (protocol, message_type, sender...)││
│  │  - RefereeRegisterRequest                             ││
│  │  - RefereeRegisterResponse                            ││
│  │  - LeagueRegisterRequest/Response                     ││
│  │  - RoundAnnouncement, GameInvitation, GameJoinAck     ││
│  │  - ChooseParityCall/Response, GameOver                ││
│  │  - MatchResultReport, LeagueStandingsUpdate           ││
│  │  - RoundCompleted, LeagueCompleted                    ││
│  │  - LeagueError, GameError                             ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  config_loader.py                                            │
│  ┌────────────────────────────────────────────────────────┐│
│  │ ConfigLoader (lazy loading + caching):                ││
│  │  - load_system() → SystemConfig                       ││
│  │  - load_agents() → AgentsConfig                       ││
│  │  - load_league(id) → LeagueConfig                     ││
│  │  - load_games_registry() → GamesRegistry              ││
│  │  - get_referee_by_id(id) → RefereeConfig              ││
│  │  - get_player_by_id(id) → PlayerConfig                ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  logger.py                                                   │
│  ┌────────────────────────────────────────────────────────┐│
│  │ JsonLogger (JSONL format):                            ││
│  │  - debug(event, **details)                            ││
│  │  - info(event, **details)                             ││
│  │  - warning(event, **details)                          ││
│  │  - error(event, **details)                            ││
│  │  - log_message_sent(type, recipient)                  ││
│  │  - log_message_received(type, sender)                 ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  mcp_client.py                                               │
│  ┌────────────────────────────────────────────────────────┐│
│  │ MCPClient (JSON-RPC HTTP client):                     ││
│  │  - call_tool(endpoint, method, params, timeout)       ││
│  │  - Retry logic with exponential backoff               ││
│  │  - Circuit breaker pattern                            ││
│  │  - Error handling and logging                         ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  repositories.py                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Data repositories:                                    ││
│  │  - StandingsRepository (standings CRUD)               ││
│  │  - RoundsRepository (rounds CRUD)                     ││
│  │  - MatchRepository (match details CRUD)               ││
│  │  - PlayerHistoryRepository (player history CRUD)      ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Communication Protocol

### 4.1 Message Envelope Structure

**All messages MUST include this envelope:**

```json
{
  "protocol": "league.v2",
  "message_type": "<MESSAGE_TYPE>",
  "sender": "<type>:<id>",
  "timestamp": "2025-12-31T10:30:00Z",
  "conversation_id": "conv-<uuid>",
  "auth_token": "tok_<hash>"
}
```

**Field Specifications**:
- `protocol`: Always "league.v2"
- `message_type`: One of 16 core message types
- `sender`: Format `<agent_type>:<agent_id>` (e.g., "player:P01", "referee:REF01", "league_manager:LEAGUE_MANAGER_01")
- `timestamp`: ISO-8601 UTC with Z suffix
- `conversation_id`: UUID for tracing related messages
- `auth_token`: JWT or hash token (empty for registration requests)

### 4.2 JSON-RPC 2.0 Format

**Request Format**:
```json
{
  "jsonrpc": "2.0",
  "method": "<tool_name>",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_INVITATION",
    "sender": "referee:REF01",
    "timestamp": "2025-12-31T10:30:00Z",
    "conversation_id": "conv-abc123",
    "auth_token": "tok_xyz789",
    "match_id": "R1M1",
    "role_in_match": "PLAYER_A",
    "opponent_id": "P02",
    "game_type": "even_odd"
  },
  "id": 1
}
```

**Response Format (Success)**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "message": "Invitation accepted"
  },
  "id": 1
}
```

**Response Format (Error)**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "match_id",
      "reason": "Missing required field"
    }
  },
  "id": 1
}
```

### 4.3 Communication Flow Diagrams

#### 4.3.1 Complete League Lifecycle

```
League Manager     Referee REF01     Referee REF02     Player P01     Player P02     Player P03     Player P04
    |                   |                   |               |              |              |              |
    |◄──────────────────|  REFEREE_REGISTER_REQUEST         |              |              |              |
    |───────────────────►|  REFEREE_REGISTER_RESPONSE        |              |              |              |
    |◄──────────────────────────────────────|  REFEREE_REGISTER_REQUEST    |              |              |
    |───────────────────────────────────────►|  REFEREE_REGISTER_RESPONSE   |              |              |
    |                   |                   |               |              |              |              |
    |◄──────────────────────────────────────────────────────|  LEAGUE_REGISTER_REQUEST   |              |
    |───────────────────────────────────────────────────────►|  LEAGUE_REGISTER_RESPONSE  |              |
    |◄──────────────────────────────────────────────────────────────────────|  LEAGUE_REGISTER_REQUEST  |
    |───────────────────────────────────────────────────────────────────────►|  LEAGUE_REGISTER_RESPONSE |
    |◄──────────────────────────────────────────────────────────────────────────────────────|  REGISTER  |
    |───────────────────────────────────────────────────────────────────────────────────────►|  RESPONSE  |
    |◄──────────────────────────────────────────────────────────────────────────────────────────────────|
    |───────────────────────────────────────────────────────────────────────────────────────────────────►|
    |                   |                   |               |              |              |              |
    |─────────────────────────────────────────────────────► ROUND_ANNOUNCEMENT (all players)             |
    |                   |                   |               |              |              |              |
    |  [Match R1M1: P01 vs P02, Referee REF01]             |              |              |              |
    |                   |                   |               |              |              |              |
    |                   |───────────────────────────────────►|  GAME_INVITATION           |              |
    |                   |───────────────────────────────────────────────────►|  GAME_INVITATION          |
    |                   |◄───────────────────────────────────|  GAME_JOIN_ACK              |              |
    |                   |◄───────────────────────────────────────────────────|  GAME_JOIN_ACK            |
    |                   |───────────────────────────────────►|  CHOOSE_PARITY_CALL         |              |
    |                   |───────────────────────────────────────────────────►|  CHOOSE_PARITY_CALL       |
    |                   |◄───────────────────────────────────|  CHOOSE_PARITY_RESPONSE    |              |
    |                   |◄───────────────────────────────────────────────────|  CHOOSE_PARITY_RESPONSE   |
    |                   |  [Draw number, determine winner]  |              |              |              |
    |                   |───────────────────────────────────►|  GAME_OVER  |              |              |
    |                   |───────────────────────────────────────────────────►|  GAME_OVER |              |
    |◄──────────────────|  MATCH_RESULT_REPORT              |              |              |              |
    |                   |                   |               |              |              |              |
    |  [Update standings]                   |               |              |              |              |
    |─────────────────────────────────────────────────────► LEAGUE_STANDINGS_UPDATE (all)|              |
    |                   |                   |               |              |              |              |
    |  [All matches in round complete]      |               |              |              |              |
    |─────────────────────────────────────────────────────► ROUND_COMPLETED (all)        |              |
    |                   |                   |               |              |              |              |
    |  [All rounds complete]                |               |              |              |              |
    |─────────────────────────────────────────────────────► LEAGUE_COMPLETED (all)       |              |
```

#### 4.3.2 Single Match Flow (Detailed)

```
Referee REF01                 Player A (P01)                 Player B (P02)
    |                               |                              |
    |──────────GAME_INVITATION────► |                              |
    |──────────GAME_INVITATION──────────────────────────────────► |
    |                               |                              |
    | [5 second timeout]            |                              |
    |                               |                              |
    |◄─────────GAME_JOIN_ACK────────|                              |
    |◄─────────GAME_JOIN_ACK────────────────────────────────────── |
    |                               |                              |
    | [Both joined → State: COLLECTING_CHOICES]                    |
    |                               |                              |
    |────CHOOSE_PARITY_CALL───────► |                              |
    |────CHOOSE_PARITY_CALL─────────────────────────────────────► |
    |                               |                              |
    | [30 second timeout]           |                              |
    |                               |                              |
    |◄───CHOOSE_PARITY_RESPONSE─────| (choice: "even")             |
    |◄───CHOOSE_PARITY_RESPONSE─────────────────────────────────── | (choice: "odd")
    |                               |                              |
    | [Draw number: 7 (odd)]        |                              |
    | [Winner: P02 (chose "odd")]   |                              |
    |                               |                              |
    |─────────GAME_OVER───────────► | (result: LOSS, 0 points)     |
    |─────────GAME_OVER─────────────────────────────────────────► | (result: WIN, 3 points)
    |                               |                              |
    |  Send MATCH_RESULT_REPORT to League Manager                  |
    |                               |                              |
```

### 4.4 Timeout Specifications

| Message Type | Timeout | Action on Timeout |
|--------------|---------|-------------------|
| GAME_JOIN_ACK | 5 seconds | Match cancelled, notify League Manager |
| CHOOSE_PARITY_RESPONSE | 30 seconds | Retry up to 3 times, then technical loss |
| Generic responses | 10 seconds | Retry with exponential backoff |
| HTTP requests | 5 seconds | Retry with circuit breaker |

---

## 5. Data Architecture

### 5.1 Directory Structure

```
SHARED/
├── config/                          # Configuration files (version controlled)
│   ├── system.json                  # Global system settings
│   ├── agents/
│   │   └── agents_config.json       # All agents registry
│   ├── leagues/
│   │   └── league_2025_even_odd.json  # League-specific config
│   ├── games/
│   │   └── games_registry.json      # Game types registry
│   └── defaults/
│       ├── referee.json             # Default referee settings
│       └── player.json              # Default player settings
│
├── data/                            # Runtime data (NOT version controlled)
│   ├── leagues/
│   │   └── league_2025_even_odd/
│   │       ├── standings.json       # Current standings (source of truth)
│   │       └── rounds.json          # Round history
│   ├── matches/
│   │   └── league_2025_even_odd/
│   │       ├── match_R1M1.json      # Match audit trail
│   │       ├── match_R1M2.json
│   │       └── ...
│   └── players/
│       ├── P01/
│       │   └── history.json         # Player P01 match history
│       ├── P02/
│       │   └── history.json
│       └── ...
│
└── logs/                            # JSONL logs (NOT version controlled)
    ├── league/
    │   └── league_2025_even_odd/
    │       └── league.log.jsonl     # Central league log
    ├── agents/
    │   ├── P01.log.jsonl            # Player P01 log
    │   ├── P02.log.jsonl
    │   ├── REF01.log.jsonl
    │   └── ...
    └── system/
        └── startup.log.jsonl        # System-wide events
```

### 5.2 Configuration Schema

#### 5.2.1 system.json

```json
{
  "protocol_version": "league.v2",
  "network": {
    "base_host": "localhost",
    "league_manager_port": 8000,
    "referee_port_range": [8001, 8010],
    "player_port_range": [8101, 8200]
  },
  "timeouts": {
    "move_timeout_sec": 30,
    "game_join_ack_timeout_sec": 5,
    "generic_response_timeout_sec": 10,
    "http_request_timeout_sec": 5
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "backoff_base_sec": 1
  },
  "circuit_breaker": {
    "failure_threshold": 5,
    "timeout_sec": 30,
    "half_open_max_calls": 1
  },
  "logging": {
    "level": "INFO",
    "format": "jsonl",
    "rotation_mb": 100
  }
}
```

#### 5.2.2 agents_config.json

```json
{
  "league_manager": {
    "manager_id": "LEAGUE_MANAGER_01",
    "display_name": "Central League Manager",
    "endpoint": "http://localhost:8000/mcp",
    "version": "1.0.0"
  },
  "referees": [
    {
      "referee_id": "REF01",
      "display_name": "Referee Alpha",
      "endpoint": "http://localhost:8001/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "max_concurrent_matches": 2,
      "active": true
    },
    {
      "referee_id": "REF02",
      "display_name": "Referee Beta",
      "endpoint": "http://localhost:8002/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "max_concurrent_matches": 2,
      "active": true
    }
  ],
  "players": [
    {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "endpoint": "http://localhost:8101/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "strategy": "random"
    },
    {
      "player_id": "P02",
      "display_name": "Agent Beta",
      "endpoint": "http://localhost:8102/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "strategy": "pattern_based"
    },
    {
      "player_id": "P03",
      "display_name": "Agent Gamma",
      "endpoint": "http://localhost:8103/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "strategy": "random"
    },
    {
      "player_id": "P04",
      "display_name": "Agent Delta",
      "endpoint": "http://localhost:8104/mcp",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "strategy": "random"
    }
  ]
}
```

#### 5.2.3 league_2025_even_odd.json

```json
{
  "league_id": "league_2025_even_odd",
  "display_name": "2025 Even/Odd Championship",
  "game_type": "even_odd",
  "format": "round_robin",
  "scoring": {
    "win_points": 3,
    "draw_points": 1,
    "loss_points": 0,
    "technical_loss_points": 0
  },
  "participants": {
    "min_players": 2,
    "max_players": 10,
    "registered_players": []
  },
  "schedule": {
    "start_date": "2025-12-31T00:00:00Z",
    "match_delay_sec": 5
  },
  "rules": {
    "number_range_min": 1,
    "number_range_max": 10,
    "draw_on_both_wrong": true
  }
}
```

### 5.3 Runtime Data Schema

#### 5.3.1 standings.json

```json
{
  "league_id": "league_2025_even_odd",
  "version": 3,
  "last_updated": "2025-12-31T10:30:00Z",
  "rounds_completed": 1,
  "standings": [
    {
      "rank": 1,
      "player_id": "P02",
      "display_name": "Agent Beta",
      "played": 2,
      "wins": 2,
      "draws": 0,
      "losses": 0,
      "points": 6
    },
    {
      "rank": 2,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "played": 2,
      "wins": 1,
      "draws": 0,
      "losses": 1,
      "points": 3
    }
  ]
}
```

#### 5.3.2 match_R1M1.json (Match Audit Trail)

```json
{
  "match_id": "R1M1",
  "round_id": "R1",
  "league_id": "league_2025_even_odd",
  "game_type": "even_odd",
  "referee_id": "REF01",
  "players": {
    "PLAYER_A": "P01",
    "PLAYER_B": "P02"
  },
  "lifecycle": [
    {
      "state": "CREATED",
      "timestamp": "2025-12-31T10:00:00Z"
    },
    {
      "state": "WAITING_FOR_PLAYERS",
      "timestamp": "2025-12-31T10:00:05Z"
    },
    {
      "state": "COLLECTING_CHOICES",
      "timestamp": "2025-12-31T10:00:10Z"
    },
    {
      "state": "DRAWING_NUMBER",
      "timestamp": "2025-12-31T10:00:35Z"
    },
    {
      "state": "FINISHED",
      "timestamp": "2025-12-31T10:00:40Z"
    }
  ],
  "transcript": [
    {
      "seq": 1,
      "timestamp": "2025-12-31T10:00:05Z",
      "from": "referee:REF01",
      "to": "player:P01",
      "message_type": "GAME_INVITATION"
    },
    {
      "seq": 2,
      "timestamp": "2025-12-31T10:00:05Z",
      "from": "referee:REF01",
      "to": "player:P02",
      "message_type": "GAME_INVITATION"
    }
  ],
  "result": {
    "status": "WIN",
    "winner_player_id": "P02",
    "drawn_number": 7,
    "number_parity": "odd",
    "choices": {
      "P01": "even",
      "P02": "odd"
    },
    "score": {
      "P01": 0,
      "P02": 3
    },
    "reason": "P02 chose 'odd', number 7 is odd"
  }
}
```

---

## 6. State Management

### 6.1 Agent State Machine

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Lifecycle States                 │
└─────────────────────────────────────────────────────────┘

    INIT
      │
      │ (agent starts)
      ▼
  REGISTERING
      │
      │ (receives registration response)
      ▼
  REGISTERED
      │
      │ (league starts)
      ▼
    ACTIVE
      │
      │ (participating in matches)
      │
      ├───► (error condition) ──► SUSPENDED
      │                               │
      │                               │ (recovery)
      │◄──────────────────────────────┘
      │
      │ (league ends)
      ▼
  SHUTDOWN
```

### 6.2 Match State Machine

```
┌─────────────────────────────────────────────────────────┐
│                  Match Lifecycle States                 │
└─────────────────────────────────────────────────────────┘

     CREATED
        │
        │ (send GAME_INVITATION)
        ▼
 WAITING_FOR_PLAYERS
        │
        ├───► (timeout/reject) ──► CANCELLED
        │
        │ (both GAME_JOIN_ACK received)
        ▼
 COLLECTING_CHOICES
        │
        ├───► (timeout) ──► TIMEOUT_ERROR ──► (retry) ──┐
        │                        │                       │
        │                        │ (max retries)         │
        │                        ▼                       │
        │                  TECHNICAL_LOSS                │
        │                                                │
        │◄───────────────────────────────────────────────┘
        │
        │ (both CHOOSE_PARITY_RESPONSE received)
        ▼
  DRAWING_NUMBER
        │
        │ (draw random number, calculate winner)
        ▼
    FINISHED
        │
        │ (send GAME_OVER, MATCH_RESULT_REPORT)
        ▼
    REPORTED
```

### 6.3 League State Machine

```
┌─────────────────────────────────────────────────────────┐
│                  League Lifecycle States                │
└─────────────────────────────────────────────────────────┘

  INITIALIZED
      │
      │ (referee registrations)
      ▼
ACCEPTING_REFEREES
      │
      │ (player registrations)
      ▼
ACCEPTING_PLAYERS
      │
      │ (minimum players reached, schedule created)
      ▼
  SCHEDULED
      │
      │ (send ROUND_ANNOUNCEMENT)
      ▼
 IN_PROGRESS
      │
      │ (matches executing, results arriving)
      │
      ├───► (all matches in round complete) ──► ROUND_COMPLETE
      │                                              │
      │◄─────────────────────────────────────────────┘
      │                                         (more rounds)
      │
      │ (all rounds complete)
      ▼
   FINISHED
      │
      │ (send LEAGUE_COMPLETED)
      ▼
    CLOSED
```

---

## 7. Error Handling Strategy

### 7.1 Error Types and Handling

| Error Type | Code | Handling Strategy |
|------------|------|-------------------|
| AUTH_TOKEN_INVALID | E012 | Send LEAGUE_ERROR, reject request |
| PLAYER_NOT_REGISTERED | E013 | Send LEAGUE_ERROR, log incident |
| LEAGUE_NOT_FOUND | E014 | Send LEAGUE_ERROR, check config |
| TIMEOUT_ERROR | E001 | Retry up to 3 times, then technical loss |
| INVALID_CHOICE | E002 | Send GAME_ERROR, request new choice |
| DISCONNECTED | E003 | Circuit breaker, mark match as cancelled |

### 7.2 Retry Logic with Exponential Backoff

```python
def retry_with_backoff(func, max_retries=3, base_delay=1):
    """
    Retry function with exponential backoff

    Delays: 1s, 2s, 4s
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, propagate error

            delay = base_delay * (2 ** attempt)
            logger.warning("RETRY_ATTEMPT",
                          attempt=attempt+1,
                          max_retries=max_retries,
                          delay=delay,
                          error=str(e))
            time.sleep(delay)
```

### 7.3 Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────┐
│              Circuit Breaker State Machine              │
└─────────────────────────────────────────────────────────┘

      CLOSED
      (normal)
         │
         │ (too many failures)
         ▼
       OPEN
    (reject all)
         │
         │ (timeout expires)
         ▼
    HALF_OPEN
   (test recovery)
         │
         ├───► (success) ──────► CLOSED
         │
         └───► (failure) ──────► OPEN
```

**Parameters**:
- Failure threshold: 5 failures
- Open timeout: 30 seconds
- Half-open max calls: 1

### 7.4 Timeout Enforcement

```python
async def enforce_timeout(coro, timeout_sec, error_message):
    """
    Enforce timeout on async operation
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        logger.error("TIMEOUT",
                    timeout=timeout_sec,
                    error=error_message)
        raise TimeoutError(error_message)
```

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
Player                    League Manager
  │                             │
  │  LEAGUE_REGISTER_REQUEST    │
  │  (no auth_token)            │
  ├────────────────────────────►│
  │                             │
  │                             │ (generate token)
  │                             │
  │  LEAGUE_REGISTER_RESPONSE   │
  │  (includes auth_token)      │
  │◄────────────────────────────┤
  │                             │
  │  GAME_INVITATION            │
  │  (includes auth_token)      │
  │◄────────────────────────────┤
  │                             │
  │  GAME_JOIN_ACK              │
  │  (includes auth_token)      │
  ├────────────────────────────►│
  │                             │
  │                             │ (validate token)
  │                             │
```

### 8.2 Token Generation

```python
import hashlib
import secrets
from datetime import datetime

def generate_auth_token(agent_id: str, league_id: str) -> str:
    """
    Generate authentication token

    Format: tok_<hash>
    """
    nonce = secrets.token_hex(16)
    payload = f"{agent_id}:{league_id}:{nonce}:{datetime.utcnow().isoformat()}"
    hash_value = hashlib.sha256(payload.encode()).hexdigest()[:32]
    return f"tok_{hash_value}"
```

### 8.3 Input Validation

**All inputs validated using Pydantic models:**
- Message type must be one of 16 valid types
- Sender format must match `<type>:<id>` pattern
- Timestamp must be valid ISO-8601 UTC
- Parity choice must be "even" or "odd"
- Match IDs must match pattern `R\d+M\d+`

---

## 9. Deployment Architecture

### 9.1 Single-Machine Deployment

```
┌────────────────────────────────────────────────────────┐
│                    localhost                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Process 1: League Manager                            │
│  └─ uvicorn agents.league_manager.main:app            │
│     --host 0.0.0.0 --port 8000                        │
│                                                        │
│  Process 2: Referee REF01                             │
│  └─ uvicorn agents.referee.main:app                   │
│     --host 0.0.0.0 --port 8001                        │
│                                                        │
│  Process 3: Referee REF02                             │
│  └─ uvicorn agents.referee.main:app                   │
│     --host 0.0.0.0 --port 8002                        │
│                                                        │
│  Process 4: Player P01                                │
│  └─ uvicorn agents.player.main:app                    │
│     --host 0.0.0.0 --port 8101                        │
│                                                        │
│  Process 5: Player P02                                │
│  └─ uvicorn agents.player.main:app                    │
│     --host 0.0.0.0 --port 8102                        │
│                                                        │
│  Process 6: Player P03                                │
│  └─ uvicorn agents.player.main:app                    │
│     --host 0.0.0.0 --port 8103                        │
│                                                        │
│  Process 7: Player P04                                │
│  └─ uvicorn agents.player.main:app                    │
│     --host 0.0.0.0 --port 8104                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 9.2 Startup Sequence

**Critical Order** (MUST be followed):

1. **League Manager** (Terminal 1)
   ```bash
   python -m agents.league_manager.main
   ```
   Wait for: "League Manager listening on :8000"

2. **Referees** (Terminals 2-3, parallel OK)
   ```bash
   REFEREE_ID=REF01 PORT=8001 python -m agents.referee.main
   REFEREE_ID=REF02 PORT=8002 python -m agents.referee.main
   ```
   Wait for: "Referee REF01 registered successfully"

3. **Players** (Terminals 4-7, parallel OK)
   ```bash
   PLAYER_ID=P01 PORT=8101 python -m agents.player.main
   PLAYER_ID=P02 PORT=8102 python -m agents.player.main
   PLAYER_ID=P03 PORT=8103 python -m agents.player.main
   PLAYER_ID=P04 PORT=8104 python -m agents.player.main
   ```
   Wait for: "Player P01 registered successfully"

4. **Start League** (via League Manager API or auto-start)
   ```bash
   curl -X POST http://localhost:8000/admin/start_league
   ```

---

## 10. API Specifications

### 10.1 League Manager API

**Base URL**: `http://localhost:8000`

#### POST /mcp
JSON-RPC endpoint for all protocol messages

**Methods**:
- `register_referee` - Handle REFEREE_REGISTER_REQUEST
- `register_player` - Handle LEAGUE_REGISTER_REQUEST
- `report_match_result` - Handle MATCH_RESULT_REPORT

#### POST /admin/start_league
Start the league (after registrations complete)

**Response**:
```json
{
  "status": "started",
  "league_id": "league_2025_even_odd",
  "total_players": 4,
  "total_rounds": 3,
  "total_matches": 6
}
```

#### GET /admin/standings
Get current standings

**Response**: standings.json content

### 10.2 Referee API

**Base URL**: `http://localhost:8001` (REF01), `http://localhost:8002` (REF02)

#### POST /mcp
JSON-RPC endpoint for all protocol messages

**Methods**:
- `receive_game_join_ack` - Handle GAME_JOIN_ACK
- `receive_parity_response` - Handle CHOOSE_PARITY_RESPONSE

### 10.3 Player API

**Base URL**: `http://localhost:8101` (P01), `http://localhost:8102` (P02), etc.

#### POST /mcp
JSON-RPC endpoint for all protocol messages

**Methods**:
- `receive_round_announcement` - Handle ROUND_ANNOUNCEMENT
- `receive_game_invitation` - Handle GAME_INVITATION
- `receive_parity_call` - Handle CHOOSE_PARITY_CALL
- `receive_game_over` - Handle GAME_OVER
- `receive_standings_update` - Handle LEAGUE_STANDINGS_UPDATE
- `receive_round_completed` - Handle ROUND_COMPLETED
- `receive_league_completed` - Handle LEAGUE_COMPLETED

---

## 11. Performance Considerations

### 11.1 Scalability Limits

- **Maximum Players**: 10 (configured in league config)
- **Maximum Concurrent Matches**: 10 (limited by referee count × max_concurrent_matches)
- **Maximum Referees**: 10 (port range 8001-8010)
- **Message Processing**: < 100ms per message
- **Match Duration**: ~60 seconds (includes timeouts)
- **Full League (4 players)**: ~10 minutes total

### 11.2 Optimization Strategies

1. **Parallel Match Execution**: Utilize multiple referees for concurrent matches
2. **Async I/O**: Use FastAPI's async capabilities for non-blocking I/O
3. **Connection Pooling**: Reuse HTTP connections via httpx.AsyncClient
4. **Lazy Loading**: Load configurations on-demand with caching
5. **JSONL Logging**: Efficient append-only writes, no JSON parsing required

---

## 12. Future Enhancements

### 12.1 Technical Improvements
- WebSocket support for real-time notifications
- Database backend (PostgreSQL) for better scalability
- Distributed deployment with service discovery
- Grafana dashboards for monitoring
- Prometheus metrics collection

### 12.2 Feature Additions
- Support for additional game types
- LLM-powered player strategies
- ELO rating system
- Tournament brackets (in addition to Round-Robin)
- Replay system for match analysis

---

**End of Design Document**
