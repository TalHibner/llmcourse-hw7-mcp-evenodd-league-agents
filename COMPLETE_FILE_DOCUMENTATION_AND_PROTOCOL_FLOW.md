# 📚 Complete MCP Even/Odd League - File Documentation & Protocol Flow

**Total Files Extracted: 51**
- 16 Protocol Message Examples (Core messages for Even/Odd league)
- 22 Python Implementation Examples
- 9 Configuration Examples
- 4 Runtime Data Examples
- 2 Log Examples
- 1 Bash Script
- 1 README

**Note:** The PDF describes 20 total message types. This documentation focuses on the 16 core messages required for Even/Odd implementation. See Appendix for 4 additional optional/framework messages.

---

## 🔄 Protocol Flow Overview

### **Complete League Lifecycle**

```
┌─────────────────────────────────────────────────────────────┐
│                    LEAGUE LIFECYCLE                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Phase 1: SYSTEM STARTUP                                      │
├──────────────────────────────────────────────────────────────┤
│ 1. League Manager starts (port 8000)                         │
│ 2. Referees start (ports 8001, 8002) and register            │
│ 3. Players start (ports 8101-8104) and register              │
│ 4. League Manager creates match schedule (Round-Robin)       │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 2: REFEREE REGISTRATION                                 │
├──────────────────────────────────────────────────────────────┤
│ Referee → League Manager: REFEREE_REGISTER_REQUEST           │
│     {display_name, game_types, endpoint, max_matches}        │
│                                                               │
│ League Manager → Referee: REFEREE_REGISTER_RESPONSE          │
│     {status: ACCEPTED, referee_id, auth_token}               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3: PLAYER REGISTRATION                                  │
├──────────────────────────────────────────────────────────────┤
│ Player → League Manager: LEAGUE_REGISTER_REQUEST             │
│     {display_name, game_types, endpoint}                     │
│                                                               │
│ League Manager → Player: LEAGUE_REGISTER_RESPONSE            │
│     {status: ACCEPTED, player_id, auth_token}                │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 4: ROUND ANNOUNCEMENT                                   │
├──────────────────────────────────────────────────────────────┤
│ League Manager → All Players: ROUND_ANNOUNCEMENT             │
│     {round_id, matches: [                                    │
│         {match_id, player_A, player_B, referee_endpoint}     │
│     ]}                                                        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 5: MATCH EXECUTION (per match)                         │
├──────────────────────────────────────────────────────────────┤
│ Step 5.1: Invitation                                          │
│   Referee → Player A: GAME_INVITATION                        │
│       {match_id, role: PLAYER_A, opponent_id}                │
│   Referee → Player B: GAME_INVITATION                        │
│       {match_id, role: PLAYER_B, opponent_id}                │
│                                                               │
│ Step 5.2: Join Acknowledgment                                │
│   Player A → Referee: GAME_JOIN_ACK                          │
│       {accept: true, arrival_timestamp}                      │
│   Player B → Referee: GAME_JOIN_ACK                          │
│       {accept: true, arrival_timestamp}                      │
│   [Timeout: 5 seconds]                                       │
│                                                               │
│ Step 5.3: Collect Choices                                    │
│   Referee → Player A: CHOOSE_PARITY_CALL                     │
│       {match_id, deadline, context}                          │
│   Referee → Player B: CHOOSE_PARITY_CALL                     │
│       {match_id, deadline, context}                          │
│                                                               │
│   Player A → Referee: CHOOSE_PARITY_RESPONSE                 │
│       {parity_choice: "even"}                                │
│   Player B → Referee: CHOOSE_PARITY_RESPONSE                 │
│       {parity_choice: "odd"}                                 │
│   [Timeout: 30 seconds]                                      │
│                                                               │
│ Step 5.4: Draw Number & Determine Winner                     │
│   Referee: draws random number (0-100)                       │
│   Referee: calculates winner based on parity                 │
│                                                               │
│ Step 5.5: Announce Result                                    │
│   Referee → Both Players: GAME_OVER                          │
│       {status: WIN/DRAW, winner_player_id,                   │
│        drawn_number, choices, reason}                        │
│                                                               │
│ Step 5.6: Report to League                                   │
│   Referee → League Manager: MATCH_RESULT_REPORT              │
│       {winner, score: {P01: 3, P02: 0}, details}            │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 6: ROUND COMPLETION                                     │
├──────────────────────────────────────────────────────────────┤
│ League Manager:                                               │
│   1. Receives all MATCH_RESULT_REPORT for round              │
│   2. Updates standings (calculates points)                   │
│   3. Sends standings update to all players                   │
│                                                               │
│ League Manager → All Players: LEAGUE_STANDINGS_UPDATE        │
│     {standings: [{rank, player_id, wins, losses, points}]}  │
│                                                               │
│ League Manager → All Players: ROUND_COMPLETED                │
│     {round_id, completed_matches}                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    More Rounds? ────YES──┐
                            │             │
                           NO             │
                            │             │
                            ▼             │
┌──────────────────────────────────────────────────────────────┐
│ Phase 7: LEAGUE COMPLETION                                    │
├──────────────────────────────────────────────────────────────┤
│ League Manager → All Players: LEAGUE_COMPLETED               │
│     {champion: {player_id, points},                          │
│      final_standings, total_rounds, total_matches}           │
└──────────────────────────────────────────────────────────────┘
```

### **State Transitions for a Match**

```
CREATED
   │
   ▼
WAITING_FOR_PLAYERS (send GAME_INVITATION)
   │
   ├── timeout or rejection → CANCELLED
   │
   ▼
COLLECTING_CHOICES (send CHOOSE_PARITY_CALL)
   │
   ├── timeout → TIMEOUT_ERROR → retry or technical loss
   │
   ▼
DRAWING_NUMBER (referee draws random number)
   │
   ▼
FINISHED (send GAME_OVER, then MATCH_RESULT_REPORT)
```

### **Error Handling Flow**

```
ERROR DETECTED
   │
   ├─→ Authentication Error
   │       └→ LEAGUE_ERROR (E012: AUTH_TOKEN_INVALID)
   │
   ├─→ Timeout Error
   │       └→ GAME_ERROR (E001: TIMEOUT_ERROR)
   │           └→ Retry with exponential backoff (max 3 retries)
   │               └→ Technical loss if all retries fail
   │
   └─→ Network Error
           └→ Circuit Breaker Pattern
               ├─→ CLOSED: Normal operation
               ├─→ OPEN: Too many failures, stop requests
               └─→ HALF_OPEN: Test if service recovered
```

---

## 📋 Complete File Inventory

### **1. Protocol Message Examples (16 files)**

Located in: `message_examples/`

**Note:** These are the 16 core messages required for Even/Odd league implementation. The PDF also describes 4 additional optional/framework messages (GAME_MOVE_CALL/RESPONSE, LEAGUE_QUERY/RESPONSE) documented in the Appendix section below.

#### **1.1 Registration Messages**

##### `referee_register_request.json`
**Purpose:** Referee registers itself to the League Manager
**Direction:** Referee → League Manager
**Protocol Phase:** Phase 2 (Registration)
**Key Fields:**
- `message_type`: "REFEREE_REGISTER_REQUEST"
- `referee_meta`: display_name, version, game_types, contact_endpoint, max_concurrent_matches
**Response:** REFEREE_REGISTER_RESPONSE

##### `referee_register_response.json`
**Purpose:** League Manager accepts/rejects referee registration
**Direction:** League Manager → Referee
**Protocol Phase:** Phase 2 (Registration)
**Key Fields:**
- `status`: "ACCEPTED" or "REJECTED"
- `referee_id`: Assigned unique ID (e.g., "REF01")
- `auth_token`: Authentication token for future requests
- `league_id`: Which league this referee is in
**Next Step:** Wait for league to start

##### `league_register_request.json`
**Purpose:** Player registers itself to the League Manager
**Direction:** Player → League Manager
**Protocol Phase:** Phase 3 (Registration)
**Key Fields:**
- `message_type`: "LEAGUE_REGISTER_REQUEST"
- `player_meta`: display_name, version, game_types, contact_endpoint
**Response:** LEAGUE_REGISTER_RESPONSE

##### `league_register_response.json`
**Purpose:** League Manager accepts/rejects player registration
**Direction:** League Manager → Player
**Protocol Phase:** Phase 3 (Registration)
**Key Fields:**
- `status`: "ACCEPTED" or "REJECTED"
- `player_id`: Assigned unique ID (e.g., "P01")
- `auth_token`: Authentication token for future requests
- `league_id`: Which league this player is in
**Next Step:** Wait for ROUND_ANNOUNCEMENT

---

#### **1.2 Round Management Messages**

##### `round_announcement.json`
**Purpose:** League Manager announces a new round with match pairings
**Direction:** League Manager → All Players
**Protocol Phase:** Phase 4 (Round Start)
**Key Fields:**
- `round_id`: Which round (1, 2, 3...)
- `matches`: Array of match assignments
  - Each match: match_id, game_type, player_A_id, player_B_id, referee_endpoint
**Next Step:** Referees send GAME_INVITATION to assigned players

##### `round_completed.json`
**Purpose:** League Manager announces round completion
**Direction:** League Manager → All Players
**Protocol Phase:** Phase 6 (Round End)
**Key Fields:**
- `round_id`: Which round just completed
- `completed_matches`: Array of match IDs that finished
- `next_round_id`: Next round number (or null if league done)
**Next Step:** Either next ROUND_ANNOUNCEMENT or LEAGUE_COMPLETED

---

#### **1.3 Game Execution Messages**

##### `game_invitation.json`
**Purpose:** Referee invites players to join a match
**Direction:** Referee → Player (sent to both players)
**Protocol Phase:** Phase 5.1 (Match Start)
**Key Fields:**
- `match_id`: Unique match identifier (e.g., "R1M1")
- `role_in_match`: "PLAYER_A" or "PLAYER_B"
- `opponent_id`: Who they're playing against
- `game_type`: "even_odd"
**Response:** GAME_JOIN_ACK (within 5 seconds)

##### `game_join_ack.json`
**Purpose:** Player confirms arrival for the match
**Direction:** Player → Referee
**Protocol Phase:** Phase 5.2 (Join Confirmation)
**Key Fields:**
- `accept`: true/false
- `arrival_timestamp`: When player received invitation
- `match_id`: Confirming which match
**Timeout:** 5 seconds
**Next Step:** Referee waits for both players, then sends CHOOSE_PARITY_CALL

##### `choose_parity_call.json`
**Purpose:** Referee asks player to choose "even" or "odd"
**Direction:** Referee → Player (sent to both players)
**Protocol Phase:** Phase 5.3 (Choice Collection)
**Key Fields:**
- `match_id`: Which match
- `game_type`: "even_odd"
- `deadline`: UTC timestamp for response
- `context`: Current standings, opponent info (optional)
**Response:** CHOOSE_PARITY_RESPONSE (within 30 seconds)

##### `choose_parity_response.json`
**Purpose:** Player submits their parity choice
**Direction:** Player → Referee
**Protocol Phase:** Phase 5.3 (Choice Submission)
**Key Fields:**
- `parity_choice`: "even" or "odd"
- `match_id`: Which match this is for
**Timeout:** 30 seconds
**Next Step:** Referee draws number and determines winner

##### `game_over.json`
**Purpose:** Referee announces match result to players
**Direction:** Referee → Both Players
**Protocol Phase:** Phase 5.5 (Result Announcement)
**Key Fields:**
- `game_result`:
  - `status`: "WIN" or "DRAW"
  - `winner_player_id`: Who won (or null for draw)
  - `drawn_number`: Random number that was drawn
  - `number_parity`: "even" or "odd"
  - `choices`: {P01: "even", P02: "odd"}
  - `reason`: Explanation of result
**Next Step:** Referee sends MATCH_RESULT_REPORT to League Manager

---

#### **1.4 League Management Messages**

##### `match_result_report.json`
**Purpose:** Referee reports match outcome to League Manager
**Direction:** Referee → League Manager
**Protocol Phase:** Phase 5.6 (Result Reporting)
**Key Fields:**
- `match_id`: Which match finished
- `round_id`: Which round this was in
- `result`:
  - `winner`: player_id of winner
  - `score`: {P01: 3, P02: 0} (points awarded)
  - `details`: drawn_number, choices
**Next Step:** League Manager updates standings

##### `league_standings_update.json`
**Purpose:** League Manager broadcasts updated standings
**Direction:** League Manager → All Players
**Protocol Phase:** Phase 6 (After each match/round)
**Key Fields:**
- `standings`: Array of player rankings
  - Each: rank, player_id, display_name, played, wins, draws, losses, points
- `round_id`: Current round
**Next Step:** Continue with next match or round

##### `league_completed.json`
**Purpose:** League Manager announces league has finished
**Direction:** League Manager → All Players
**Protocol Phase:** Phase 7 (League End)
**Key Fields:**
- `champion`: {player_id, display_name, points}
- `final_standings`: Complete ranking of all players
- `total_rounds`: How many rounds were played
- `total_matches`: How many matches were played
**Next Step:** League ends, agents can shut down

---

#### **1.5 Error Messages**

##### `league_error.json`
**Purpose:** League Manager reports an error (e.g., auth failure)
**Direction:** League Manager → Player/Referee
**Protocol Phase:** Any phase
**Key Fields:**
- `error_code`: "E012" (see error code table)
- `error_description`: "AUTH_TOKEN_INVALID"
- `context`: Additional info about the error
**Common Errors:**
- E012: AUTH_TOKEN_INVALID
- E013: PLAYER_NOT_REGISTERED
- E014: LEAGUE_NOT_FOUND

##### `game_error.json`
**Purpose:** Referee reports a game error (e.g., timeout)
**Direction:** Referee → Players
**Protocol Phase:** Phase 5 (during match)
**Key Fields:**
- `error_code`: "E001" (see error code table)
- `error_description`: "TIMEOUT_ERROR"
- `affected_player`: Which player caused the error
- `action_required`: What was expected
- `retry_count`: How many retries attempted
- `max_retries`: Maximum retries allowed (3)
- `consequence`: "Technical loss if no response after retries"
**Common Errors:**
- E001: TIMEOUT_ERROR
- E002: INVALID_CHOICE
- E003: DISCONNECTED

---

### **2. Python Implementation Examples (22 files)**

Located in: `python_examples/`

#### **2.1 Core Server & Agent Implementation**

##### `basic_mcp_server.py`
**Purpose:** Basic FastAPI server template for MCP agents
**Section:** 5.1
**Key Components:**
- FastAPI app with `/mcp` endpoint
- MCPRequest and MCPResponse Pydantic models
- JSON-RPC 2.0 request handling
- Example tool registration
**Usage:** Template for building any MCP server (referee, player, league manager)
**Dependencies:** FastAPI, Pydantic
**Example:**
```python
app = FastAPI()

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    # Handle JSON-RPC request
    return MCPResponse(...)
```

##### `simple_player_agent.py`
**Purpose:** Complete player agent implementation with random strategy
**Section:** 5.2
**Key Components:**
- Handles GAME_INVITATION
- Sends GAME_JOIN_ACK
- Receives CHOOSE_PARITY_CALL
- Makes random choice ("even" or "odd")
- Handles GAME_OVER
- Updates internal state
**Strategy:** Random selection
**Usage:** Starting point for building smarter player agents
**Example Flow:**
1. Receive invitation → Accept immediately
2. Receive parity call → Choose randomly
3. Receive game over → Update win/loss record

---

#### **2.2 League Manager Components**

##### `league_manager.py`
**Purpose:** Core LeagueManager class for orchestrating the league
**Section:** 5.3
**Key Components:**
- LeagueManager class
- Referee registration handling
- Player ID assignment
- Token generation
- Agent registry management
**Responsibilities:**
- Register referees and players
- Maintain source of truth for standings
- Coordinate match schedule
- Send round announcements
**Usage:** Core orchestrator for the entire league

##### `round_robin_scheduler.py`
**Purpose:** Create Round-Robin match schedule
**Section:** 5.4
**Key Components:**
- Uses `itertools.combinations` for pairings
- Generates match IDs (e.g., "R1M1", "R2M1")
- Assigns players to matches
**Algorithm:** Round-Robin ensures every player plays every other player
**Example:**
```python
# 4 players: P01, P02, P03, P04
# Round 1: P01 vs P02, P03 vs P04
# Round 2: P01 vs P03, P02 vs P04
# Round 3: P01 vs P04, P02 vs P03
```

---

#### **2.3 Referee Components**

##### `referee_registration.py`
**Purpose:** Referee registers itself to League Manager
**Section:** 5.5
**Key Components:**
- Constructs REFEREE_REGISTER_REQUEST
- Sends to League Manager endpoint
- Receives and stores auth_token
**Usage:** Called on referee startup
**Example:**
```python
def register_to_league():
    payload = {
        "jsonrpc": "2.0",
        "method": "register_referee",
        "params": {...}
    }
    response = requests.post(LEAGUE_MANAGER_URL, json=payload)
```

##### `winner_determination.py`
**Purpose:** Even/Odd game logic - determine match winner
**Section:** 5.6
**Key Components:**
- Draws random number (0-100)
- Determines if number is even or odd
- Compares against player choices
- Returns winner: "PLAYER_A", "PLAYER_B", or "DRAW"
**Logic:**
```python
if number % 2 == 0:  # Even
    if player_A_choice == "even": winner = "PLAYER_A"
    elif player_B_choice == "even": winner = "PLAYER_B"
    else: result = "DRAW"
```

---

#### **2.4 Communication & State Management**

##### `mcp_tool_caller.py`
**Purpose:** Helper function for making JSON-RPC calls
**Section:** 5.7
**Key Components:**
- Standard JSON-RPC 2.0 request format
- Error handling
- Response parsing
**Usage:** Simplifies MCP communication between agents
**Example:**
```python
def call_mcp_tool(endpoint, method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": generate_id()
    }
    return requests.post(endpoint, json=payload)
```

##### `player_state.py`
**Purpose:** PlayerState class for tracking player statistics
**Section:** 5.8
**Key Components:**
- PlayerState dataclass
- Tracks: wins, losses, draws, total_matches
- Maintains match history
- Methods: add_win(), add_loss(), add_draw()
**Usage:** Each player maintains their own state
**Example:**
```python
state = PlayerState(player_id="P01")
state.add_win()  # wins=1, total_matches=1
state.add_loss()  # losses=1, total_matches=2
```

---

#### **2.5 Resilience & Error Handling**

##### `timeout_handling.py`
**Purpose:** Request with timeout and exception handling
**Section:** 5.9
**Key Components:**
- Timeout decorator (30 seconds for moves)
- Exception handling for network errors
- Graceful degradation
**Usage:** Wrap network calls to prevent hanging
**Example:**
```python
try:
    response = requests.post(url, json=data, timeout=30)
except requests.Timeout:
    # Handle timeout
except requests.ConnectionError:
    # Handle network error
```

##### `retry_with_backoff.py`
**Purpose:** Exponential backoff retry logic
**Section:** 5.10
**Key Components:**
- Max retries: 3
- Exponential backoff: 1s, 2s, 4s
- Handles transient failures
**Usage:** Retry failed requests before giving up
**Example:**
```python
for attempt in range(max_retries):
    try:
        return make_request()
    except Exception:
        wait_time = 2 ** attempt
        time.sleep(wait_time)
```

##### `circuit_breaker.py`
**Purpose:** Circuit breaker pattern to prevent cascading failures
**Section:** 5.11
**Key Components:**
- States: CLOSED, OPEN, HALF_OPEN
- Failure threshold tracking
- Automatic recovery testing
**States:**
- CLOSED: Normal operation
- OPEN: Too many failures, reject requests immediately
- HALF_OPEN: Test if service recovered
**Usage:** Protect against repeated calls to failing service

---

#### **2.6 Logging & Observability**

##### `structured_logger.py`
**Purpose:** JSON-based structured logging
**Section:** 5.12
**Key Components:**
- StructuredLogger class
- Levels: DEBUG, INFO, WARN, ERROR
- Protocol-compliant log format
- Includes: timestamp, component, event_type, details
**Usage:** Consistent logging across all agents
**Example:**
```python
logger = StructuredLogger("player:P01")
logger.info("CHOICE_MADE", choice="even", match_id="R1M1")
```

##### `logger_usage_example.py`
**Purpose:** Example usage of StructuredLogger
**Section:** 5.12
**Shows:** How to log various events in proper format
**Example Output:**
```json
{
  "timestamp": "2025-01-15T10:15:00Z",
  "component": "player:P01",
  "event_type": "CHOICE_MADE",
  "level": "INFO",
  "details": {"choice": "even"}
}
```

##### `jsonl_logger.py`
**Purpose:** JSON Lines (.jsonl) logger for efficient append-only logging
**Section:** 10.6
**Key Components:**
- JsonLogger class
- JSONL format (one JSON per line)
- Convenience methods: debug(), info(), warning(), error()
- log_message_sent() helper
**Benefits:**
- Efficient append-only writes
- Each line is independent JSON
- Real-time streaming support
**Usage:** Production-quality logging for all agents

---

#### **2.7 Configuration Management (Section 10)**

##### `config_models_system.py`
**Purpose:** System configuration dataclasses
**Section:** 10.3.2
**Key Components:**
- NetworkConfig: ports, hosts
- SecurityConfig: auth tokens, TTL
- TimeoutsConfig: all timeout values
- SystemConfig: complete system config
**Usage:** Type-safe configuration models
**Example:**
```python
@dataclass
class TimeoutsConfig:
    move_timeout_sec: int = 30
    game_join_ack_timeout_sec: int = 5
```

##### `config_models_agents.py`
**Purpose:** Agent configuration dataclasses
**Section:** 10.3.3
**Key Components:**
- RefereeConfig: referee metadata
- PlayerConfig: player metadata
**Usage:** Type-safe agent configuration
**Fields:**
- referee_id, display_name, endpoint, version
- game_types, max_concurrent_matches, active status

##### `config_models_league.py`
**Purpose:** League configuration dataclasses
**Section:** 10.3.4
**Key Components:**
- ScoringConfig: points for win/draw/loss
- LeagueConfig: league-specific settings
**Usage:** Type-safe league configuration
**Example:**
```python
@dataclass
class ScoringConfig:
    win_points: int = 3
    draw_points: int = 1
    loss_points: int = 0
```

##### `dataclass_network_config.py`
**Purpose:** Standalone NetworkConfig example
**Section:** 10.3.1
**Key Components:**
- NetworkConfig dataclass
- base_host, ports ranges
**Usage:** Example of simple dataclass usage

##### `config_loader.py`
**Purpose:** Configuration loader with lazy loading and caching
**Section:** 10.4
**Key Components:**
- ConfigLoader class
- Lazy loading pattern
- Caching for performance
- Helper methods: get_referee_by_id(), get_player_by_id()
**Methods:**
- load_system() → SystemConfig
- load_agents() → AgentsConfig
- load_league(id) → LeagueConfig
- load_games_registry() → GamesRegistry
**Usage:** Core configuration management for all agents
**Pattern:** Load once, cache, reuse

---

#### **2.8 Data Repositories (Section 10)**

##### `repository_standings.py`
**Purpose:** Repository for managing league standings data
**Section:** 10.5.2
**Key Components:**
- StandingsRepository class
- load() - read from JSON
- save() - write to JSON with timestamp
- update_player() - update specific player stats
**Pattern:** Repository pattern for data persistence
**Usage:** League Manager uses this to persist standings
**Location:** `SHARED/data/leagues/<league_id>/standings.json`

---

#### **2.9 Usage Examples (Section 10)**

##### `usage_league_manager.py`
**Purpose:** Example of League Manager using ConfigLoader
**Section:** 10.7.1
**Key Components:**
- Loads system, agents, and league configs
- Initializes logger
- Builds lookup maps for fast access
**Shows:** How to properly initialize a complex agent
**Example:**
```python
loader = ConfigLoader()
self.system_cfg = loader.load_system()
self.agents_cfg = loader.load_agents()
self.league_cfg = loader.load_league(league_id)
self.logger = JsonLogger("league_manager", league_id)
```

##### `usage_referee_agent.py`
**Purpose:** Example of Referee using ConfigLoader
**Section:** 10.7.2
**Key Components:**
- Loads configs specific to this referee
- Uses get_referee_by_id() for self-configuration
- Shows registration implementation
**Shows:** How referee reads its own config and registers
**Example:**
```python
loader = ConfigLoader()
self.self_cfg = loader.get_referee_by_id(referee_id)
self.league_cfg = loader.load_league(league_id)
```

---

### **3. Configuration Examples (9 files)**

Located in: `config_examples/`

#### **3.1 Global System Configuration**

##### `system.json`
**Purpose:** Global system configuration for all agents
**Section:** 9.3.1
**Location:** `SHARED/config/system.json`
**Used By:** All agents
**Key Settings:**
- `protocol_version`: "league.v2"
- `timeouts`:
  - move_timeout_sec: 30
  - generic_response_timeout_sec: 10
- `retry_policy`:
  - max_retries: 3
  - backoff_strategy: "exponential"
**Purpose:** Single source of truth for system-wide parameters

---

#### **3.2 Agent Registry**

##### `agents_config.json`
**Purpose:** Central registry of all agents (the "citizen registry")
**Section:** 9.3.2
**Location:** `SHARED/config/agents/agents_config.json`
**Used By:** League Manager, Deployment tools
**Contents:**
- `league_manager`: {manager_id, display_name, endpoint}
- `referees`: Array of referee configs
  - referee_id, display_name, endpoint, version, game_types, max_concurrent_matches
- `players`: Array of player configs
  - player_id, display_name, endpoint, version, game_types
**Purpose:** Central directory of who exists in the system
**Scalability:** Can contain thousands of agents

---

#### **3.3 League Configuration**

##### `league_2025_even_odd.json`
**Purpose:** Configuration for a specific league
**Section:** 9.3.3
**Location:** `SHARED/config/leagues/league_2025_even_odd.json`
**Used By:** League Manager, Referees
**Key Settings:**
- `league_id`: "league_2025_even_odd"
- `game_type`: "even_odd"
- `scoring`:
  - win_points: 3
  - draw_points: 1
  - loss_points: 0
- `participants`:
  - min_players: 2
  - max_players: 10000
**Purpose:** Each league is a separate "country" with its own rules

---

#### **3.4 Game Types Registry**

##### `games_registry.json`
**Purpose:** Registry of all supported game types
**Section:** 9.3.4
**Location:** `SHARED/config/games/games_registry.json`
**Used By:** Referees (for loading rules modules), League Manager
**Contents:**
- Array of game definitions
- Each game: game_type, display_name, rules_module, max_round_time_sec, min/max_players
**Example:**
```json
{
  "game_type": "even_odd",
  "display_name": "Even or Odd",
  "rules_module": "even_odd_rules",
  "max_round_time_sec": 30
}
```
**Purpose:** Extensible system - add new games without code changes

---

#### **3.5 Default Settings**

##### `defaults/referee.json`
**Purpose:** Default settings for new referees
**Section:** 9.3.5
**Location:** `SHARED/config/defaults/referee.json`
**Used By:** New referee agents during initialization
**Contents:**
- version: "1.0.0"
- game_types: ["even_odd"]
- max_concurrent_matches: 2
- timeout_settings: {game_join_ack: 5s, move: 30s}
- retry_policy: {max_retries: 3, backoff: exponential}
**Purpose:** Reasonable defaults so referees can start quickly

##### `defaults/player.json`
**Purpose:** Default settings for new players
**Section:** 9.3.5
**Location:** `SHARED/config/defaults/player.json`
**Used By:** New player agents during initialization
**Contents:**
- version: "1.0.0"
- game_types: ["even_odd"]
- strategy: "random"
- memory: {keep_match_history: true, max_history_size: 1000}
**Purpose:** Reasonable defaults so players can start quickly

---

### **4. Runtime Data Examples (4 files)**

Located in: `data_examples/`

#### **4.1 League Data**

##### `standings.json`
**Purpose:** Current league standings (source of truth)
**Section:** 9.4.1
**Location:** `SHARED/data/leagues/<league_id>/standings.json`
**Updated By:** League Manager (after each MATCH_RESULT_REPORT)
**Read By:** Everyone (for current rankings)
**Contents:**
- version: increments with each update
- rounds_completed: how many rounds finished
- standings: array of player rankings
  - rank, player_id, display_name, played, wins, draws, losses, points
**Example:**
```json
{
  "rank": 1,
  "player_id": "P01",
  "display_name": "Agent Alpha",
  "wins": 4,
  "draws": 1,
  "losses": 1,
  "points": 13
}
```

##### `rounds.json`
**Purpose:** Complete history of all rounds
**Section:** 9.4.2
**Location:** `SHARED/data/leagues/<league_id>/rounds.json`
**Updated By:** League Manager (after ROUND_COMPLETED)
**Used For:** Analytics, debugging, historical analysis
**Contents:**
- Array of round objects
- Each round: round_id, status, start_time, end_time, matches[]
- Each match: match_id, player_A, player_B, referee_id, result, winner
**Purpose:** Historical record of the entire league

---

#### **4.2 Match Data**

##### `match_R1M1.json`
**Purpose:** Complete audit trail of a single match (the "ID card")
**Section:** 9.4.3
**Location:** `SHARED/data/matches/<league_id>/<match_id>.json`
**Updated By:** Referee managing the match
**Used For:** Debugging, auditing, analytics
**Contents:**
- `lifecycle`: State transitions with timestamps
  - CREATED → WAITING_FOR_PLAYERS → COLLECTING_CHOICES → DRAWING_NUMBER → FINISHED
- `transcript`: Full message history
  - Every message exchanged: type, from, to, timestamp, seq
- `result`: Final outcome
  - winner_player_id, drawn_number, choices, score
**Purpose:** Complete forensic record of what happened
**Example Timeline:**
```
10:10:00 CREATED
10:15:00 WAITING_FOR_PLAYERS (invitations sent)
10:15:05 COLLECTING_CHOICES (both players joined)
10:15:15 DRAWING_NUMBER (choices received)
10:15:30 FINISHED (result announced)
```

---

#### **4.3 Player Data**

##### `player_P01_history.json`
**Purpose:** Player's personal "memory" for strategy improvement
**Section:** 9.4.4
**Location:** `SHARED/data/players/<player_id>/history.json`
**Updated By:** Player agent itself
**Used For:** Learning opponent patterns, improving strategy
**Contents:**
- `stats`: total_matches, wins, losses, draws, win_rate
- `matches`: Array of match histories
  - match_id, opponent_id, result, my_choice, opponent_choice, drawn_number, points_earned
- `opponent_patterns`: Statistics per opponent
  - matches_played, wins_against, common_choice, choice_frequency
**Purpose:** Enable smart players to learn and adapt
**Example Strategy Use:**
```
If opponent P02 chooses "odd" 80% of the time,
and I've played them 5 times,
I should choose "even" to counter their pattern.
```

---

### **5. Log Examples (2 files)**

Located in: `log_examples/`

##### `league.log.jsonl`
**Purpose:** Central league event log (JSONL format)
**Section:** 9.5.1
**Location:** `SHARED/logs/league/<league_id>/league.log.jsonl`
**Written By:** League Manager
**Used By:** DevOps, Technical support, System monitoring
**Format:** JSON Lines (one JSON object per line)
**Contents:** System-wide events
- SYSTEM_STARTUP
- REFEREE_REGISTERED
- PLAYER_REGISTERED
- SCHEDULE_CREATED
- ROUND_ANNOUNCEMENT_SENT
- MATCH_RESULT_RECEIVED
- STANDINGS_UPDATED
- ROUND_COMPLETED
- LEAGUE_COMPLETED
**Example Line:**
```json
{"timestamp": "2025-01-15T10:00:00Z", "component": "league_manager", "event_type": "SYSTEM_STARTUP", "level": "INFO", "details": {"version": "1.0.0"}}
```
**Benefits:**
- Each line is independent (can process in parallel)
- Append-only (efficient writes)
- Standard tools can parse
- Real-time streaming support

##### `agent_P01.log.jsonl`
**Purpose:** Per-agent debug log (JSONL format)
**Section:** 9.5.2
**Location:** `SHARED/logs/agents/<agent_id>.log.jsonl`
**Written By:** Individual agent (P01 in this example)
**Used By:** Agent developers for debugging
**Format:** JSON Lines
**Contents:** Agent-specific events
- AGENT_STARTUP
- MESSAGE_SENT (with message_type, recipient)
- MESSAGE_RECEIVED (with message_type)
- CHOICE_MADE (with choice, strategy)
- MATCH_RESULT (with result, points)
- HISTORY_UPDATED
**Purpose:** End-to-end trace of agent's actions
**Example Use:**
"Player P01 received GAME_INVITATION at 10:15:01, sent GAME_JOIN_ACK at 10:15:02, made choice 'even' at 10:15:10"

---

### **6. Bash Examples (1 file)**

Located in: `bash_examples/`

##### `startup_commands.sh`
**Purpose:** Complete system startup sequence
**Section:** 8.2
**Contents:**
- Startup order documentation
- Terminal commands for all 7 agents
- Port allocation map
- Endpoint URLs
**Usage:** Follow this exact sequence to start the system
**Critical Order:**
1. Terminal 1: League Manager (port 8000) - MUST start first
2. Terminal 2-3: Referees (ports 8001-8002) - Register to league
3. Terminal 4-7: Players (ports 8101-8104) - Register to league
**Port Map:**
- 8000: League Manager
- 8001: Referee REF01
- 8002: Referee REF02
- 8101-8104: Players P01-P04
**Example:**
```bash
# Terminal 1 - League Manager
python league_manager.py  # Listening on :8000

# Terminal 2 - Referee Alpha
python referee.py --port 8001

# Terminal 4 - Player P01
python player.py --port 8101
```

---

## 📊 File Organization Summary

```
extracted_code/
├── message_examples/              # 16 JSON - Protocol messages
│   ├── Registration (4)
│   │   ├── referee_register_request.json
│   │   ├── referee_register_response.json
│   │   ├── league_register_request.json
│   │   └── league_register_response.json
│   ├── Round Management (2)
│   │   ├── round_announcement.json
│   │   └── round_completed.json
│   ├── Game Execution (5)
│   │   ├── game_invitation.json
│   │   ├── game_join_ack.json
│   │   ├── choose_parity_call.json
│   │   ├── choose_parity_response.json
│   │   └── game_over.json
│   ├── League Management (3)
│   │   ├── match_result_report.json
│   │   ├── league_standings_update.json
│   │   └── league_completed.json
│   └── Error Handling (2)
│       ├── league_error.json
│       └── game_error.json
│
├── python_examples/               # 22 Python - Implementation
│   ├── Core (2)
│   │   ├── basic_mcp_server.py
│   │   └── simple_player_agent.py
│   ├── League Manager (2)
│   │   ├── league_manager.py
│   │   └── round_robin_scheduler.py
│   ├── Referee (2)
│   │   ├── referee_registration.py
│   │   └── winner_determination.py
│   ├── Communication (2)
│   │   ├── mcp_tool_caller.py
│   │   └── player_state.py
│   ├── Resilience (3)
│   │   ├── timeout_handling.py
│   │   ├── retry_with_backoff.py
│   │   └── circuit_breaker.py
│   ├── Logging (3)
│   │   ├── structured_logger.py
│   │   ├── logger_usage_example.py
│   │   └── jsonl_logger.py
│   ├── Configuration (5)
│   │   ├── config_models_system.py
│   │   ├── config_models_agents.py
│   │   ├── config_models_league.py
│   │   ├── dataclass_network_config.py
│   │   └── config_loader.py
│   ├── Repository (1)
│   │   └── repository_standings.py
│   └── Usage Examples (2)
│       ├── usage_league_manager.py
│       └── usage_referee_agent.py
│
├── config_examples/               # 9 JSON - Configuration
│   ├── system.json                # Global system config
│   ├── agents_config.json         # All agents registry
│   ├── league_2025_even_odd.json  # League-specific config
│   ├── games_registry.json        # Game types registry
│   └── defaults/
│       ├── referee.json           # Referee defaults
│       └── player.json            # Player defaults
│
├── data_examples/                 # 4 JSON - Runtime data
│   ├── standings.json             # Current standings
│   ├── rounds.json                # Round history
│   ├── match_R1M1.json            # Match audit trail
│   └── player_P01_history.json    # Player memory
│
├── log_examples/                  # 2 JSONL - Logs
│   ├── league.log.jsonl           # Central league log
│   └── agent_P01.log.jsonl        # Per-agent log
│
└── bash_examples/                 # 1 Shell script
    └── startup_commands.sh        # System startup sequence
```

---

## 🎯 Quick Reference Tables

### **Message Flow by Phase**

| Phase | Messages | Direction | Purpose |
|-------|----------|-----------|---------|
| 2: Registration | REFEREE_REGISTER_REQUEST/RESPONSE | Ref ↔ LM | Register referees |
| 3: Registration | LEAGUE_REGISTER_REQUEST/RESPONSE | Player ↔ LM | Register players |
| 4: Round Start | ROUND_ANNOUNCEMENT | LM → All Players | Start new round |
| 5.1: Match Start | GAME_INVITATION | Ref → Players | Invite to match |
| 5.2: Join | GAME_JOIN_ACK | Players → Ref | Confirm arrival |
| 5.3: Choice | CHOOSE_PARITY_CALL/RESPONSE | Ref ↔ Players | Collect choices |
| 5.5: Result | GAME_OVER | Ref → Players | Announce winner |
| 5.6: Report | MATCH_RESULT_REPORT | Ref → LM | Report outcome |
| 6: Round End | LEAGUE_STANDINGS_UPDATE | LM → All Players | Update standings |
| 6: Round End | ROUND_COMPLETED | LM → All Players | Round finished |
| 7: League End | LEAGUE_COMPLETED | LM → All Players | League finished |
| Any: Error | LEAGUE_ERROR / GAME_ERROR | LM/Ref → Agent | Report error |

### **Timeout Values**

| Action | Timeout | Retries | Consequence |
|--------|---------|---------|-------------|
| GAME_JOIN_ACK | 5 sec | 0 | Match cancelled |
| CHOOSE_PARITY_RESPONSE | 30 sec | 3 | Technical loss |
| Generic response | 10 sec | 3 | Error reported |
| Network request | Varies | 3 | Circuit breaker |

### **Scoring System**

| Result | Winner Points | Loser Points |
|--------|---------------|--------------|
| WIN | 3 | 0 |
| DRAW | 1 | 1 |
| Technical Loss | 3 | 0 |

### **Port Allocation**

| Agent | Port | Endpoint |
|-------|------|----------|
| League Manager | 8000 | http://localhost:8000/mcp |
| Referee REF01 | 8001 | http://localhost:8001/mcp |
| Referee REF02 | 8002 | http://localhost:8002/mcp |
| Player P01 | 8101 | http://localhost:8101/mcp |
| Player P02 | 8102 | http://localhost:8102/mcp |
| Player P03 | 8103 | http://localhost:8103/mcp |
| Player P04 | 8104 | http://localhost:8104/mcp |

### **File Locations in SHARED Directory**

| Type | Path | Updated By | Purpose |
|------|------|------------|---------|
| System Config | `config/system.json` | Manual | Global settings |
| Agents Registry | `config/agents/agents_config.json` | Deployment | Agent directory |
| League Config | `config/leagues/<league_id>.json` | Manual | League rules |
| Games Registry | `config/games/games_registry.json` | Manual | Game types |
| Standings | `data/leagues/<league_id>/standings.json` | League Manager | Current rankings |
| Rounds History | `data/leagues/<league_id>/rounds.json` | League Manager | Round records |
| Match Details | `data/matches/<league_id>/<match_id>.json` | Referee | Match audit |
| Player History | `data/players/<player_id>/history.json` | Player | Personal memory |
| League Log | `logs/league/<league_id>/league.log.jsonl` | League Manager | System events |
| Agent Log | `logs/agents/<agent_id>.log.jsonl` | Agent | Agent events |

---

## 📋 Appendix: Additional Protocol Messages (Optional)

### **Complete Message Type List**

The PDF describes **20 total message types**. This documentation focuses on the **16 core messages** required for Even/Odd league implementation. For completeness, here are the 4 additional messages that provide framework extensibility and optional features:

#### **Generic Game Framework (2 messages) - Section 3.8**

**17. GAME_MOVE_CALL** - Generic framework for game moves
- **Purpose:** Abstract framework message (Section 3.8.2)
- **Specific Implementation:** CHOOSE_PARITY_CALL (for even_odd game)
- **When to Use:** When building a multi-game league system
- **Status:** Framework message - not needed for even_odd implementation

**18. GAME_MOVE_RESPONSE** - Generic framework for game responses
- **Purpose:** Abstract framework message (Section 3.8.3)
- **Specific Implementation:** CHOOSE_PARITY_RESPONSE (for even_odd game)
- **When to Use:** When building a multi-game league system
- **Status:** Framework message - not needed for even_odd implementation

**Relationship:**
```
Generic Framework:  GAME_MOVE_CALL ↔ GAME_MOVE_RESPONSE
                              ↓
Even/Odd Specific:  CHOOSE_PARITY_CALL ↔ CHOOSE_PARITY_RESPONSE
```

#### **Optional Query Messages (2 messages) - Section 4.9 & 8.11**

**19. LEAGUE_QUERY** - Player queries for current standings
- **Purpose:** On-demand standings query (Section 4.9.1)
- **Direction:** Player → League Manager
- **When to Use:** For on-demand queries between automatic updates
- **Status:** Optional - League Manager sends LEAGUE_STANDINGS_UPDATE automatically

**20. LEAGUE_QUERY_RESPONSE** - Response with standings
- **Purpose:** Returns standings data (Section 4.9.2)
- **Direction:** League Manager → Player
- **Format:** Same as LEAGUE_STANDINGS_UPDATE
- **Status:** Optional - not required for basic implementation

### **Implementation Guidance**

**For the Even/Odd League Assignment:**
- ✅ Use the **16 core messages** documented above
- ❌ You do NOT need GAME_MOVE_CALL/RESPONSE (use CHOOSE_PARITY instead)
- ❌ You do NOT need LEAGUE_QUERY/RESPONSE (automatic updates are sufficient)

**For Advanced/Generic Implementation:**
- If building a **multi-game league system**, implement the generic GAME_MOVE framework
- If adding **on-demand queries**, implement LEAGUE_QUERY/RESPONSE
- See Section 3.8 (Generic Framework) and Section 8.11 (Additional Tools) in PDF

**Summary:** The 16 messages documented in this guide are complete and sufficient for implementing the assignment. The 4 additional messages provide extensibility for future enhancements.

---

## 🚀 How to Use This Documentation

### **1. Building a New Agent**
Start with these files:
1. `basic_mcp_server.py` - Server template
2. `config_loader.py` - Load configuration
3. `jsonl_logger.py` - Add logging
4. `player_state.py` - Track state
5. Relevant message examples - Protocol messages

### **2. Understanding the Protocol**
Follow this path:
1. Read Protocol Flow diagram (above)
2. Examine message examples in order:
   - Registration messages
   - Round management messages
   - Game execution messages
3. Study match state transitions
4. Review error handling flow

### **3. Implementing Features**
**For League Manager:**
- `league_manager.py` - Core logic
- `round_robin_scheduler.py` - Match scheduling
- `repository_standings.py` - Data persistence

**For Referee:**
- `referee_registration.py` - Registration
- `winner_determination.py` - Game rules
- Message examples (game_invitation, choose_parity_call, game_over)

**For Player:**
- `simple_player_agent.py` - Basic agent
- `player_state.py` - State tracking
- `player_P01_history.json` - Memory format

### **4. Setting Up Configuration**
1. Copy `config_examples/*` to `SHARED/config/`
2. Modify `agents_config.json` with your agents
3. Adjust `system.json` for your needs
4. Create league config from `league_2025_even_odd.json`

### **5. Running the System**
1. Follow `startup_commands.sh` exactly
2. Monitor `league.log.jsonl` for system events
3. Check individual agent logs for debugging
4. Verify `standings.json` updates correctly

---

## ✨ Complete Coverage

**All sections extracted:**
- ✅ **Section 4:** Protocol messages (16 core + 4 optional in appendix)
- ✅ **Section 5:** Implementation patterns (13 files)
- ✅ **Section 8:** Startup procedures (1 file)
- ✅ **Section 9:** Data architecture (10 files)
- ✅ **Section 10:** league_sdk library (9 files)

**Total: 52 files** covering every aspect of the MCP Even/Odd League assignment.

---

**Everything you need to build a production-quality, scalable, multi-agent system!** 🎯
