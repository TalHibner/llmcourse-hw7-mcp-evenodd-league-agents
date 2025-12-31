# MCP Even/Odd League Multi-Agent System

A distributed multi-agent system implementing the Model Context Protocol (MCP) league.v2 specification for autonomous AI agents competing in Even/Odd games through a tournament league.

**Version**: 1.0
**Protocol**: league.v2
**Course**: Large Language Models - Homework 7
**Instructor**: Dr. Yoram Segal

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Documentation](#documentation)
4. [System Requirements](#system-requirements)
5. [Installation](#installation)
6. [Project Structure](#project-structure)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [Testing](#testing)
10. [Architecture](#architecture)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)
13. [License](#license)

---

## Overview

The MCP Even/Odd League is a sophisticated multi-agent system demonstrating:

- **Protocol-based Communication**: All agents communicate via JSON-RPC 2.0 over HTTP following the league.v2 specification
- **Autonomous Behavior**: Agents self-register, execute matches, and compete without manual intervention
- **Tournament Management**: Full Round-Robin scheduling with automatic standings tracking
- **Resilience Patterns**: Timeout handling, retry logic with exponential backoff, and circuit breakers
- **Comprehensive Logging**: Structured JSONL logs for all events and transactions

### Game Rules: Even/Odd

1. Two players simultaneously choose "even" or "odd" (hidden from opponent)
2. Referee draws a random number between 1-10
3. If the number is even, the player who chose "even" wins
4. If the number is odd, the player who chose "odd" wins
5. If both chose the same parity and it's wrong, the match is a draw

**Scoring**: Win = 3 points, Draw = 1 point, Loss = 0 points

---

## Features

### Core Functionality
- **Three-Layer Architecture**: League Manager, Referees, and Player agents
- **16 Core Message Types**: Complete protocol implementation
- **Round-Robin Scheduling**: Fair tournament format ensuring all players compete
- **Real-time Standings**: Automatic updates after each match
- **Match Audit Trails**: Complete transcript of every match
- **Player History**: Persistent memory for strategy learning

### Technical Features
- **FastAPI HTTP Servers**: High-performance async web framework
- **Pydantic Validation**: Type-safe message handling
- **Structured Logging**: JSONL format for easy parsing and analysis
- **Configuration-Driven**: All behavior controlled via JSON files
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascading failures
- **Test Coverage**: Comprehensive unit and integration tests

### Agent Types

1. **League Manager** (Port 8000)
   - Central orchestrator
   - Handles registrations
   - Generates Round-Robin schedule
   - Maintains standings
   - Declares champion

2. **Referees** (Ports 8001-8010)
   - Manage individual matches
   - Enforce Even/Odd game rules
   - Handle timeouts (5s join, 30s move)
   - Report results to League Manager

3. **Players** (Ports 8101-8200)
   - Register with league
   - Execute strategies (random, pattern-based, or LLM-driven)
   - Maintain match history
   - Adapt to opponents

---

## Documentation

Comprehensive documentation is available in the `doc/` directory:

### Protocol Specification
- **[doc/protocol-spec.md](doc/protocol-spec.md)** - Complete league.v2 protocol specification
  - Message envelope format and required fields
  - All 16 core message types with field descriptions
  - Error codes and handling guidelines
  - Timeout values and retry policies
  - Authentication and security
  - JSON-RPC 2.0 transport details

### Message Examples
Example JSON messages for all 16 protocol message types in `doc/message-examples/`:

- **Registration** (4 messages)
  - [referee_register_request.json](doc/message-examples/registration/referee_register_request.json)
  - [referee_register_response.json](doc/message-examples/registration/referee_register_response.json)
  - [league_register_request.json](doc/message-examples/registration/league_register_request.json)
  - [league_register_response.json](doc/message-examples/registration/league_register_response.json)

- **Round Management** (2 messages)
  - [round_announcement.json](doc/message-examples/round-management/round_announcement.json)
  - [round_completed.json](doc/message-examples/round-management/round_completed.json)

- **Game Flow** (5 messages)
  - [game_invitation.json](doc/message-examples/game-flow/game_invitation.json)
  - [game_join_ack.json](doc/message-examples/game-flow/game_join_ack.json)
  - [choose_parity_call.json](doc/message-examples/game-flow/choose_parity_call.json)
  - [choose_parity_response.json](doc/message-examples/game-flow/choose_parity_response.json)
  - [game_over.json](doc/message-examples/game-flow/game_over.json)

- **League Management** (3 messages)
  - [match_result_report.json](doc/message-examples/league-management/match_result_report.json)
  - [league_standings_update.json](doc/message-examples/league-management/league_standings_update.json)
  - [league_completed.json](doc/message-examples/league-management/league_completed.json)

- **Errors** (2 messages)
  - [league_error.json](doc/message-examples/errors/league_error.json)
  - [game_error.json](doc/message-examples/errors/game_error.json)

### Architecture Diagrams
Visual representations of system architecture in `doc/diagrams/`:

- **[architecture.md](doc/diagrams/architecture.md)** - Three-layer architecture, port allocation, SHARED directory structure
- **[message-flow.md](doc/diagrams/message-flow.md)** - Sequence diagrams for registration, match execution, round lifecycle, error handling
- **[state-machines.md](doc/diagrams/state-machines.md)** - Agent lifecycle, match states, circuit breaker states

### Additional Documentation
- **[PRD.md](PRD.md)** - Product Requirements Document
- **[DESIGN.md](DESIGN.md)** - Architecture Design Document
- **[TASKS.md](TASKS.md)** - Implementation Tasks
- **[QUICKSTART.md](QUICKSTART.md)** - Quick Start Guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation Summary

---

## System Requirements

### Required
- **Python**: 3.10 or higher
- **OS**: Linux, macOS, or Windows (with WSL)
- **RAM**: 512MB minimum
- **Disk**: 100MB for code and logs

### Dependencies
See `requirements.txt` for full list. Key dependencies:
- `fastapi` - Web framework for agent servers
- `uvicorn[standard]` - ASGI server
- `pydantic>=2.0` - Data validation
- `httpx` - Async HTTP client
- `pytest` - Testing framework

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/llmcourse-hw7-mcp-evenodd-league-agents.git
cd llmcourse-hw7-mcp-evenodd-league-agents
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import fastapi, pydantic, httpx; print('All dependencies installed!')"
```

### 5. Initialize Project Structure

The project structure will be created automatically when you run the agents. Alternatively, run:

```bash
python scripts/init_structure.py
```

---

## Project Structure

```
llmcourse-hw7-mcp-evenodd-league-agents/
├── README.md                    # This file
├── PRD.md                       # Product Requirements Document
├── DESIGN.md                    # Architecture Design Document
├── TASKS.md                     # Implementation Tasks
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
├── .gitignore                  # Git ignore rules
│
├── SHARED/                     # Shared resources (all agents)
│   ├── config/                 # Configuration files
│   │   ├── system.json         # Global system settings
│   │   ├── agents/
│   │   │   └── agents_config.json  # All agents registry
│   │   ├── leagues/
│   │   │   └── league_2025_even_odd.json  # League config
│   │   ├── games/
│   │   │   └── games_registry.json  # Game types
│   │   └── defaults/
│   │       ├── referee.json     # Default referee settings
│   │       └── player.json      # Default player settings
│   │
│   ├── data/                   # Runtime data (NOT in git)
│   │   ├── leagues/
│   │   │   └── league_2025_even_odd/
│   │   │       ├── standings.json   # Current standings
│   │   │       └── rounds.json      # Round history
│   │   ├── matches/
│   │   │   └── league_2025_even_odd/
│   │   │       └── match_*.json     # Match audit trails
│   │   └── players/
│   │       └── P*/
│   │           └── history.json     # Player match history
│   │
│   ├── logs/                   # JSONL logs (NOT in git)
│   │   ├── league/
│   │   │   └── league_2025_even_odd/
│   │   │       └── league.log.jsonl
│   │   ├── agents/
│   │   │   ├── P01.log.jsonl
│   │   │   ├── REF01.log.jsonl
│   │   │   └── ...
│   │   └── system/
│   │       └── startup.log.jsonl
│   │
│   └── league_sdk/             # Shared Python library
│       ├── __init__.py
│       ├── models.py           # Pydantic models for all messages
│       ├── config_loader.py    # Configuration management
│       ├── logger.py           # JSONL structured logger
│       ├── mcp_client.py       # JSON-RPC HTTP client
│       └── repositories.py     # Data persistence layer
│
├── agents/                     # Agent implementations
│   ├── league_manager/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI server
│   │   ├── handlers.py        # Message handlers
│   │   ├── scheduler.py       # Round-Robin scheduler
│   │   └── standings.py       # Standings calculator
│   │
│   ├── referee/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI server
│   │   ├── handlers.py        # Message handlers
│   │   ├── match_manager.py   # Match state machine
│   │   ├── game_logic.py      # Even/Odd rules
│   │   └── result_reporter.py # Result reporting
│   │
│   └── player/
│       ├── __init__.py
│       ├── main.py            # FastAPI server
│       ├── handlers.py        # Message handlers
│       ├── strategy.py        # Choice strategies
│       ├── state.py           # State tracking
│       └── history.py         # Match history
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_sdk.py            # SDK unit tests
│   ├── test_league_manager.py # League Manager tests
│   ├── test_referee.py        # Referee tests
│   ├── test_player.py         # Player tests
│   └── test_integration.py    # Integration tests
│
└── scripts/                    # Utility scripts
    ├── start_league.py        # Automated startup
    ├── run_demo.py            # Demo script
    └── cleanup.py             # Clean runtime data
```

---

## Configuration

### Global System Settings (`SHARED/config/system.json`)

Controls system-wide behavior:

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
    "generic_response_timeout_sec": 10
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential"
  }
}
```

### Agent Registry (`SHARED/config/agents/agents_config.json`)

Defines all agents in the system:

```json
{
  "league_manager": {
    "manager_id": "LEAGUE_MANAGER_01",
    "display_name": "Central League Manager",
    "endpoint": "http://localhost:8000/mcp"
  },
  "referees": [
    {
      "referee_id": "REF01",
      "display_name": "Referee Alpha",
      "endpoint": "http://localhost:8001/mcp",
      "game_types": ["even_odd"],
      "max_concurrent_matches": 2
    }
  ],
  "players": [
    {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "endpoint": "http://localhost:8101/mcp",
      "strategy": "random"
    }
  ]
}
```

### Adding New Agents

1. Edit `SHARED/config/agents/agents_config.json`
2. Add new player entry with unique ID and port
3. Start the new player agent with appropriate environment variables

---

## Usage

### Option 1: Automated Startup (Recommended)

Use the provided script to start all agents automatically:

```bash
python scripts/start_league.py
```

This will:
1. Start League Manager
2. Start all configured Referees
3. Start all configured Players
4. Monitor the league progress
5. Display final standings

### Option 2: Manual Startup (7 Terminals)

**CRITICAL**: Start agents in this exact order!

#### Terminal 1: League Manager

```bash
source venv/bin/activate
python -m agents.league_manager.main
```

Wait for: `INFO: League Manager listening on port 8000`

#### Terminals 2-3: Referees

```bash
# Terminal 2
source venv/bin/activate
REFEREE_ID=REF01 PORT=8001 python -m agents.referee.main

# Terminal 3
source venv/bin/activate
REFEREE_ID=REF02 PORT=8002 python -m agents.referee.main
```

Wait for: `INFO: Referee REF01 registered successfully`

#### Terminals 4-7: Players

```bash
# Terminal 4
source venv/bin/activate
PLAYER_ID=P01 PORT=8101 python -m agents.player.main

# Terminal 5
source venv/bin/activate
PLAYER_ID=P02 PORT=8102 python -m agents.player.main

# Terminal 6
source venv/bin/activate
PLAYER_ID=P03 PORT=8103 python -m agents.player.main

# Terminal 7
source venv/bin/activate
PLAYER_ID=P04 PORT=8104 python -m agents.player.main
```

Wait for: `INFO: Player P01 registered successfully`

#### Start the League

Once all agents are registered, trigger the league start:

```bash
curl -X POST http://localhost:8000/admin/start_league
```

### Monitoring

#### View Real-time Logs

```bash
# League Manager log
tail -f SHARED/logs/league/league_2025_even_odd/league.log.jsonl | jq

# Specific agent log
tail -f SHARED/logs/agents/P01.log.jsonl | jq
```

#### Check Current Standings

```bash
curl http://localhost:8000/admin/standings | jq
```

#### View Match Details

```bash
cat SHARED/data/matches/league_2025_even_odd/match_R1M1.json | jq
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/test_sdk.py
pytest tests/test_league_manager.py
pytest tests/test_referee.py
pytest tests/test_player.py
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Run with Coverage

```bash
pytest --cov=SHARED/league_sdk --cov=agents --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

### Test Specific Functionality

```bash
# Test registration flow
pytest tests/test_integration.py::test_registration_flow -v

# Test single match
pytest tests/test_integration.py::test_single_match -v

# Test full league
pytest tests/test_integration.py::test_full_league -v
```

---

## Architecture

### Three-Layer Design

1. **Orchestration Layer** (League Manager)
   - Central coordinator
   - Source of truth for standings
   - Tournament lifecycle management

2. **Judging Layer** (Referees)
   - Match execution
   - Game rule enforcement
   - Timeout management

3. **Gameplay Layer** (Players)
   - Strategy execution
   - Match participation
   - History tracking

### Communication Protocol

All communication uses **JSON-RPC 2.0 over HTTP** following the **league.v2** specification.

**Message Envelope** (required for all messages):

```json
{
  "protocol": "league.v2",
  "message_type": "GAME_INVITATION",
  "sender": "referee:REF01",
  "timestamp": "2025-12-31T10:30:00Z",
  "conversation_id": "conv-abc123",
  "auth_token": "tok_xyz789"
}
```

### 16 Core Message Types

| Phase | Message Type | Direction |
|-------|-------------|-----------|
| Registration | REFEREE_REGISTER_REQUEST/RESPONSE | Ref ↔ LM |
| Registration | LEAGUE_REGISTER_REQUEST/RESPONSE | Player ↔ LM |
| Round Mgmt | ROUND_ANNOUNCEMENT | LM → All Players |
| Round Mgmt | ROUND_COMPLETED | LM → All Players |
| Match Exec | GAME_INVITATION | Ref → Player |
| Match Exec | GAME_JOIN_ACK | Player → Ref |
| Match Exec | CHOOSE_PARITY_CALL | Ref → Player |
| Match Exec | CHOOSE_PARITY_RESPONSE | Player → Ref |
| Match Exec | GAME_OVER | Ref → Player |
| League Mgmt | MATCH_RESULT_REPORT | Ref → LM |
| League Mgmt | LEAGUE_STANDINGS_UPDATE | LM → All Players |
| League Mgmt | LEAGUE_COMPLETED | LM → All Players |
| Errors | LEAGUE_ERROR | LM → Agent |
| Errors | GAME_ERROR | Ref → Player |

### State Machines

#### Match States
```
CREATED → WAITING_FOR_PLAYERS → COLLECTING_CHOICES → DRAWING_NUMBER → FINISHED
```

#### Agent States
```
INIT → REGISTERING → REGISTERED → ACTIVE → SHUTDOWN
```

---

## Troubleshooting

### Common Issues

#### 1. "Connection refused" when starting agents

**Cause**: League Manager not running or not ready

**Solution**:
```bash
# Ensure League Manager started first
# Check it's listening
curl http://localhost:8000/health
```

#### 2. "AUTH_TOKEN_INVALID" errors

**Cause**: Agent not properly registered

**Solution**:
- Restart the agent
- Check logs for registration errors
- Verify `agents_config.json` has correct endpoint

#### 3. Timeout errors during matches

**Cause**: Player not responding within 30 seconds

**Solution**:
- Check player logs for errors
- Verify player process is running
- Check CPU usage (strategy computation time)

#### 4. "No matches scheduled"

**Cause**: Insufficient players registered

**Solution**:
- Need minimum 2 players
- Check all players registered successfully
- Verify League Manager received registrations

#### 5. Port already in use

**Cause**: Previous process still running

**Solution**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use the cleanup script
python scripts/cleanup.py --kill-processes
```

#### 6. Import errors

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Debugging Tips

1. **Check Logs**:
   ```bash
   # View all league events
   cat SHARED/logs/league/league_2025_even_odd/league.log.jsonl | jq

   # View specific agent
   cat SHARED/logs/agents/P01.log.jsonl | jq
   ```

2. **Verify Configuration**:
   ```bash
   # Validate JSON syntax
   python -m json.tool < SHARED/config/system.json
   ```

3. **Test Individual Components**:
   ```bash
   # Test just the SDK
   pytest tests/test_sdk.py -v

   # Test just one agent
   pytest tests/test_player.py -v
   ```

4. **Monitor Network**:
   ```bash
   # Check which ports are open
   netstat -tuln | grep -E '8000|8001|8002|8101|8102|8103|8104'
   ```

---

## Contributing

### Code Style

- Follow **PEP 8** style guidelines
- Use **type hints** throughout
- Add **docstrings** to all classes and functions
- Keep files **< 150 lines** where possible

### Testing Requirements

- Write tests for all new features
- Maintain **≥70% code coverage**
- Test edge cases and error conditions
- Run full test suite before committing

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is created for educational purposes as part of a university course on Large Language Models.

**Instructor**: Dr. Yoram Segal
**Course**: Large Language Models - Homework 7
**Academic Year**: 2025

---

## Credits

### Built With

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

### References

- MCP League Protocol v2 Specification
- JSON-RPC 2.0 Specification
- Round-Robin Tournament Algorithm

---

## Contact

**Author**: [Your Name]
**Email**: [Your Email]
**Course**: Large Language Models
**Instructor**: Dr. Yoram Segal

---

## Appendix

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLAYER_ID` | Player identifier (P01, P02, etc.) | Required |
| `REFEREE_ID` | Referee identifier (REF01, REF02, etc.) | Required |
| `PORT` | Agent listening port | Required |
| `LEAGUE_MANAGER_URL` | League Manager endpoint | http://localhost:8000/mcp |
| `LOG_LEVEL` | Logging level | INFO |

### Port Allocation

| Agent Type | Port Range | Default Ports |
|------------|------------|---------------|
| League Manager | 8000 | 8000 |
| Referees | 8001-8010 | 8001, 8002 |
| Players | 8101-8200 | 8101-8104 |

### File Sizes

- Configuration files: < 10 KB
- Match audit trails: ~5-10 KB per match
- Player history: ~10-50 KB per player
- Logs: ~1-5 MB per complete league

---

**Happy Coding!**
