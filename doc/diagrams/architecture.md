# System Architecture Diagram

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: ORCHESTRATION                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                      ┌─────────────────────┐                        │
│                      │  League Manager     │                        │
│                      │  Port: 8000         │                        │
│                      │  /mcp endpoint      │                        │
│                      └──────────┬──────────┘                        │
│                                 │                                   │
│  Responsibilities:              │                                   │
│  - Register referees & players  │                                   │
│  - Create match schedule        │                                   │
│  - Send round announcements     │                                   │
│  - Track standings              │                                   │
│  - Manage league lifecycle      │                                   │
│                                 │                                   │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
┌───────────────────▼───────────────────────────▼───────────────────┐
│                      LAYER 2: GAME EXECUTION                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────────────┐              ┌──────────────────┐          │
│   │  Referee REF01   │              │  Referee REF02   │          │
│   │  Port: 8001      │              │  Port: 8002      │          │
│   │  /mcp endpoint   │              │  /mcp endpoint   │          │
│   └────────┬─────────┘              └────────┬─────────┘          │
│            │                                 │                    │
│  Responsibilities:                           │                    │
│  - Run matches                               │                    │
│  - Send invitations                          │                    │
│  - Collect parity choices                    │                    │
│  - Draw random numbers                       │                    │
│  - Determine winners                         │                    │
│  - Report results to League Manager          │                    │
│            │                                 │                    │
└────────────┼─────────────────────────────────┼────────────────────┘
             │                                 │
        ┌────┴────┬────────┬────────┐    ┌────┴────┬────────┐
        │         │        │        │    │         │        │
┌───────▼─────────▼────────▼────────▼────▼─────────▼────────▼──────┐
│                     LAYER 3: GAME PLAYERS                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Player   │  │ Player   │  │ Player   │  │ Player   │  ...    │
│  │  P01     │  │  P02     │  │  P03     │  │  P04     │         │
│  │ Port:    │  │ Port:    │  │ Port:    │  │ Port:    │         │
│  │ 8101     │  │ 8102     │  │ 8103     │  │ 8104     │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│                                                                   │
│  Responsibilities:                                                │
│  - Register with League Manager                                  │
│  - Accept match invitations                                      │
│  - Make parity choices (even/odd)                                │
│  - Receive match results                                         │
│  - Track personal statistics                                     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Port Allocation

```
┌─────────────────────────────────────────────────────────┐
│                    PORT ALLOCATION MAP                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  League Manager:                                        │
│    8000          http://localhost:8000/mcp             │
│                                                         │
│  Referees (8001-8010):                                 │
│    8001          http://localhost:8001/mcp (REF01)     │
│    8002          http://localhost:8002/mcp (REF02)     │
│    8003-8010     Reserved for additional referees      │
│                                                         │
│  Players (8101-8200):                                  │
│    8101          http://localhost:8101/mcp (P01)       │
│    8102          http://localhost:8102/mcp (P02)       │
│    8103          http://localhost:8103/mcp (P03)       │
│    8104          http://localhost:8104/mcp (P04)       │
│    8105-8200     Reserved for additional players       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## SHARED Directory Structure

```
SHARED/
├── config/                           # Configuration files
│   ├── system.json                   # Global system settings
│   ├── agents/
│   │   └── agents_config.json        # Agent registry (citizen directory)
│   ├── leagues/
│   │   └── league_2025_even_odd.json # League-specific config
│   ├── games/
│   │   └── games_registry.json       # Game types registry
│   └── defaults/
│       ├── referee.json              # Default referee settings
│       └── player.json               # Default player settings
│
├── data/                             # Runtime data (dynamic)
│   ├── leagues/
│   │   └── <league_id>/
│   │       ├── standings.json        # Current standings (source of truth)
│   │       └── rounds.json           # Round history
│   ├── matches/
│   │   └── <league_id>/
│   │       └── <match_id>.json       # Match audit trail
│   └── players/
│       └── <player_id>/
│           └── history.json          # Player's memory/stats
│
└── logs/                             # Log files (JSONL format)
    ├── league/
    │   └── <league_id>/
    │       └── league.log.jsonl      # Central league event log
    └── agents/
        └── <agent_id>.log.jsonl      # Per-agent debug logs
```

## Communication Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                   COMMUNICATION FLOW PATTERNS                   │
└─────────────────────────────────────────────────────────────────┘

1. REGISTRATION PATTERN (Startup)

   Referee ──REFEREE_REGISTER_REQUEST──> League Manager
   Referee <─REFEREE_REGISTER_RESPONSE─── League Manager

   Player ──LEAGUE_REGISTER_REQUEST──> League Manager
   Player <─LEAGUE_REGISTER_RESPONSE─── League Manager


2. ROUND ANNOUNCEMENT PATTERN (Broadcast)

   League Manager ──ROUND_ANNOUNCEMENT──> All Players (broadcast)


3. MATCH EXECUTION PATTERN (Referee coordinates)

   Referee ──GAME_INVITATION──────────> Player A
   Referee ──GAME_INVITATION──────────> Player B

   Referee <─GAME_JOIN_ACK─────────────  Player A
   Referee <─GAME_JOIN_ACK─────────────  Player B

   Referee ──CHOOSE_PARITY_CALL───────> Player A
   Referee ──CHOOSE_PARITY_CALL───────> Player B

   Referee <─CHOOSE_PARITY_RESPONSE────  Player A
   Referee <─CHOOSE_PARITY_RESPONSE────  Player B

   Referee ──GAME_OVER─────────────────> Player A
   Referee ──GAME_OVER─────────────────> Player B

   Referee ──MATCH_RESULT_REPORT──────> League Manager


4. STANDINGS UPDATE PATTERN (Broadcast)

   League Manager ──LEAGUE_STANDINGS_UPDATE──> All Players


5. ERROR HANDLING PATTERN (Targeted)

   League Manager ──LEAGUE_ERROR──────> Specific Agent
   Referee ──────────GAME_ERROR───────> Specific Player


┌─────────────────────────────────────────────────────────────────┐
│                     PROTOCOL CHARACTERISTICS                    │
├─────────────────────────────────────────────────────────────────┤
│  Transport:      JSON-RPC 2.0 over HTTP POST                   │
│  Encoding:       UTF-8                                          │
│  Content-Type:   application/json                              │
│  Protocol:       league.v2                                      │
│  Authentication: Token-based (after registration)              │
│  Timeout:        5s (join), 30s (choice), 10s (generic)        │
│  Retry:          3 attempts with exponential backoff           │
└─────────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

```
┌────────────────────────────────────────────────────────────┐
│                    SCALING DIMENSIONS                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Horizontal Scaling:                                       │
│    - Single League Manager (1 instance)                    │
│    - Multiple Referees (2-10 instances)                    │
│    - Many Players (4-100+ instances)                       │
│                                                            │
│  Concurrent Matches:                                       │
│    - Each referee handles max 2 concurrent matches         │
│    - 2 referees = up to 4 simultaneous matches            │
│    - Round-robin ensures all pairings over time            │
│                                                            │
│  Data Architecture:                                        │
│    - SHARED directory = single source of truth             │
│    - JSON files for configuration & data                   │
│    - JSONL for append-only logs                            │
│    - No database required for basic implementation         │
│                                                            │
│  Network Resilience:                                       │
│    - Circuit breaker per endpoint                          │
│    - Exponential backoff retry (1s, 2s, 4s)               │
│    - Timeout enforcement at each layer                     │
│    - Technical loss for unresponsive players               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```
