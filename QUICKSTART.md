# MCP Even/Odd League - Quick Start Guide

## Overview

This is a complete implementation of a multi-agent league system using the MCP (Model Context Protocol) league.v2 protocol. Players compete in Even/Odd number games, managed by referees and coordinated by a central league manager.

## System Architecture

```
League Manager (Port 8000)
    ├── Referee REF01 (Port 8001)
    ├── Referee REF02 (Port 8002)
    └── Players
        ├── P01 (Port 8101) - Random strategy
        ├── P02 (Port 8102) - Pattern-based strategy
        ├── P03 (Port 8103) - Random strategy
        └── P04 (Port 8104) - Random strategy
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import fastapi, uvicorn, pydantic, httpx; print('All dependencies installed!')"
```

## Running the League

### Option 1: Automated Startup (Recommended)

Use the automated startup script that manages all agents:

```bash
python scripts/start_league.py
```

This will:
1. Start the League Manager
2. Start all Referees
3. Start all Players
4. Trigger league start
5. Monitor progress and display standings
6. Press Ctrl+C to stop all services

### Option 2: Manual Startup

Start each component in a separate terminal:

**Terminal 1 - League Manager:**
```bash
python -m agents.league_manager.main
```

**Terminal 2 - Referee REF01:**
```bash
REFEREE_ID=REF01 PORT=8001 python -m agents.referee.main
```

**Terminal 3 - Referee REF02:**
```bash
REFEREE_ID=REF02 PORT=8002 python -m agents.referee.main
```

**Terminal 4 - Player P01:**
```bash
PLAYER_ID=P01 PORT=8101 STRATEGY=random python -m agents.player.main
```

**Terminal 5 - Player P02:**
```bash
PLAYER_ID=P02 PORT=8102 STRATEGY=pattern_based python -m agents.player.main
```

**Terminal 6 - Player P03:**
```bash
PLAYER_ID=P03 PORT=8103 STRATEGY=random python -m agents.player.main
```

**Terminal 7 - Player P04:**
```bash
PLAYER_ID=P04 PORT=8104 STRATEGY=random python -m agents.player.main
```

**Terminal 8 - Start League:**
```bash
# Wait 5 seconds for all registrations, then:
curl -X POST http://localhost:8000/admin/start_league
```

## Monitoring the League

### Check Standings

```bash
curl http://localhost:8000/admin/standings
```

### Check Player Stats

```bash
curl http://localhost:8101/admin/stats
```

### Check Service Health

```bash
# League Manager
curl http://localhost:8000/health

# Referee
curl http://localhost:8001/health

# Player
curl http://localhost:8101/health
```

## Running Tests

### Integration Test

```bash
# Make sure all services are running first
pytest tests/test_integration.py -v
```

## Project Structure

```
.
├── SHARED/
│   ├── config/                  # Configuration files
│   │   ├── system.json
│   │   ├── agents/
│   │   │   └── agents_config.json
│   │   ├── leagues/
│   │   │   └── league_2025_even_odd.json
│   │   ├── games/
│   │   │   └── games_registry.json
│   │   └── defaults/
│   ├── data/                    # Runtime data (created automatically)
│   │   ├── leagues/
│   │   ├── matches/
│   │   └── players/
│   ├── logs/                    # JSONL logs (created automatically)
│   └── league_sdk/              # Shared SDK
│       ├── models.py            # Pydantic models (16 message types)
│       ├── logger.py            # JSONL logger
│       ├── config_loader.py     # Configuration loader
│       ├── mcp_client.py        # HTTP JSON-RPC client
│       └── repositories.py      # Data persistence
│
├── agents/
│   ├── league_manager/          # Central orchestrator
│   │   ├── main.py
│   │   ├── handlers.py          # Registration & results
│   │   ├── scheduler.py         # Round-Robin scheduling
│   │   └── standings.py         # Rankings calculation
│   │
│   ├── referee/                 # Match management
│   │   ├── main.py
│   │   ├── handlers.py
│   │   ├── match_manager.py     # State machine
│   │   └── game_logic.py        # Even/Odd rules
│   │
│   └── player/                  # Player agents
│       ├── main.py
│       ├── handlers.py
│       ├── strategy.py          # Random & pattern-based
│       ├── state.py             # Stats tracking
│       └── history.py           # Match history
│
├── scripts/
│   └── start_league.py          # Automated startup
│
└── tests/
    └── test_integration.py      # Integration test
```

## Game Rules

### Even/Odd Game

1. Two players simultaneously choose "even" or "odd"
2. A random number (1-10) is drawn
3. Winner is determined by:
   - If both chose the same parity:
     - Both correct → DRAW (1 point each)
     - Both wrong → DRAW (1 point each)
   - If different parities:
     - Correct choice → WIN (3 points)
     - Wrong choice → LOSS (0 points)

### League Format

- **Round-Robin**: Each player faces every other player exactly once
- **Scoring**: Win=3, Draw=1, Loss=0
- **Rankings**: By points, then wins, then alphabetically

## Configuration

### System Settings (SHARED/config/system.json)

- Network ports and hosts
- Timeout values (join: 5s, move: 30s)
- Retry policy (max 3 retries, exponential backoff)
- Circuit breaker settings

### Agent Settings (SHARED/config/agents/agents_config.json)

- League Manager endpoint
- Referee configurations (endpoints, capacity)
- Player configurations (endpoints, strategies)

### League Settings (SHARED/config/leagues/league_2025_even_odd.json)

- Scoring rules
- Game parameters (number range: 1-10)
- Participant limits (2-10 players)

## Logs

All logs are written in JSONL format to `SHARED/logs/`:

- `league/league_2025_even_odd/league.log.jsonl` - League manager logs
- `agents/P01.log.jsonl` - Player P01 logs
- `agents/REF01.log.jsonl` - Referee REF01 logs

View logs:
```bash
tail -f SHARED/logs/league/league_2025_even_odd/league.log.jsonl
```

## Data Files

Match results and history are saved to `SHARED/data/`:

- `leagues/league_2025_even_odd/standings.json` - Current standings
- `leagues/league_2025_even_odd/rounds.json` - Round history
- `matches/league_2025_even_odd/match_R1M1.json` - Match audit trails
- `players/P01/history.json` - Player P01 match history

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Services Not Starting

Check logs in `SHARED/logs/` for error messages.

### Registration Failures

Ensure League Manager is running before starting referees and players.

### Matches Not Starting

Check that:
1. At least 2 players are registered
2. At least 1 referee is registered
3. League has been started via `/admin/start_league`

## Advanced Usage

### Custom Strategies

Edit player strategy in config or environment:
```bash
PLAYER_ID=P01 PORT=8101 STRATEGY=pattern_based python -m agents.player.main
```

### More Players

Add players to `SHARED/config/agents/agents_config.json` and start with unique IDs and ports.

### Custom Game Rules

Edit `SHARED/config/leagues/league_2025_even_odd.json`:
- Change number range
- Modify scoring rules
- Adjust timeouts

## Support

For issues or questions, refer to:
- `DESIGN.md` - Complete architecture documentation
- `PRD.md` - Product requirements
- `TASKS.md` - Implementation checklist
