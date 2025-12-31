# Implementation Tasks
## MCP Even/Odd League Multi-Agent System

**Version:** 1.0
**Date:** December 31, 2025

---

## Task Status Legend

- [ ] Not Started
- [⧗] In Progress
- [✓] Completed
- [✗] Blocked

---

## Phase 1: Documentation (Day 1)

### Task 1.1: Product Requirements Document
- [✓] Create PRD.md
- [✓] Define functional requirements
- [✓] Define non-functional requirements
- [✓] List all 16 message types
- [✓] Define acceptance criteria

### Task 1.2: Architecture Design Document
- [✓] Create DESIGN.md
- [✓] Design three-layer architecture
- [✓] Create component diagrams
- [✓] Design communication flow
- [✓] Define data architecture
- [✓] Design state machines

### Task 1.3: Implementation Tasks Document
- [⧗] Create TASKS.md (this file)
- [ ] Break down all implementation tasks
- [ ] Define task dependencies
- [ ] Estimate task complexity

### Task 1.4: User Guide
- [ ] Create README.md
- [ ] Installation instructions
- [ ] Configuration guide
- [ ] Usage instructions
- [ ] Troubleshooting section

---

## Phase 2: Foundation Setup (Day 1-2)

### Task 2.1: Project Structure
**Estimated Time**: 30 minutes
**Dependencies**: None
**Files**: Directory structure, __init__.py files

- [ ] Create root directory structure
  - [ ] `SHARED/`
  - [ ] `SHARED/config/`
  - [ ] `SHARED/config/agents/`
  - [ ] `SHARED/config/leagues/`
  - [ ] `SHARED/config/games/`
  - [ ] `SHARED/config/defaults/`
  - [ ] `SHARED/data/`
  - [ ] `SHARED/data/leagues/`
  - [ ] `SHARED/data/matches/`
  - [ ] `SHARED/data/players/`
  - [ ] `SHARED/logs/`
  - [ ] `SHARED/logs/league/`
  - [ ] `SHARED/logs/agents/`
  - [ ] `SHARED/logs/system/`
  - [ ] `SHARED/league_sdk/`
  - [ ] `agents/`
  - [ ] `agents/league_manager/`
  - [ ] `agents/referee/`
  - [ ] `agents/player/`
  - [ ] `tests/`
  - [ ] `scripts/`

- [ ] Create `.gitkeep` files for empty directories
- [ ] Create `__init__.py` files for all Python packages

### Task 2.2: Dependency Management
**Estimated Time**: 20 minutes
**Dependencies**: Task 2.1
**Files**: requirements.txt, pyproject.toml

- [ ] Create `requirements.txt`
  - [ ] Add fastapi
  - [ ] Add uvicorn[standard]
  - [ ] Add pydantic>=2.0
  - [ ] Add httpx
  - [ ] Add pytest
  - [ ] Add pytest-asyncio
  - [ ] Add pytest-cov
  - [ ] Add python-dotenv (optional)

- [ ] Create `pyproject.toml` (optional)
  - [ ] Define project metadata
  - [ ] Define dependencies
  - [ ] Configure build system

### Task 2.3: Git Configuration
**Estimated Time**: 10 minutes
**Dependencies**: Task 2.1
**Files**: .gitignore

- [ ] Create `.gitignore`
  - [ ] Python artifacts (__pycache__, *.pyc, *.egg-info)
  - [ ] Virtual environments (venv/, .venv/, env/)
  - [ ] IDE files (.idea/, .vscode/, *.swp)
  - [ ] Environment files (.env, .env.local)
  - [ ] Runtime logs (SHARED/logs/**/*.jsonl)
  - [ ] Runtime data (SHARED/data/**/*.json, keep .gitkeep)
  - [ ] PDF files (*.pdf) - **CRITICAL**
  - [ ] OS files (.DS_Store, Thumbs.db)

---

## Phase 3: Shared SDK Implementation (Day 2)

### Task 3.1: Data Models
**Estimated Time**: 2 hours
**Dependencies**: Task 2.1
**Files**: SHARED/league_sdk/models.py

- [ ] Create Pydantic models for message envelope
  - [ ] `MessageEnvelope` base model
  - [ ] Validation for protocol version
  - [ ] Validation for timestamp format
  - [ ] Validation for sender format

- [ ] Create models for registration messages (4 types)
  - [ ] `RefereeRegisterRequest`
  - [ ] `RefereeRegisterResponse`
  - [ ] `LeagueRegisterRequest`
  - [ ] `LeagueRegisterResponse`

- [ ] Create models for round management (2 types)
  - [ ] `RoundAnnouncement`
  - [ ] `RoundCompleted`

- [ ] Create models for game execution (5 types)
  - [ ] `GameInvitation`
  - [ ] `GameJoinAck`
  - [ ] `ChooseParityCall`
  - [ ] `ChooseParityResponse`
  - [ ] `GameOver`

- [ ] Create models for league management (3 types)
  - [ ] `MatchResultReport`
  - [ ] `LeagueStandingsUpdate`
  - [ ] `LeagueCompleted`

- [ ] Create models for error handling (2 types)
  - [ ] `LeagueError`
  - [ ] `GameError`

- [ ] Create supporting data models
  - [ ] `PlayerMeta`
  - [ ] `RefereeMeta`
  - [ ] `MatchInfo`
  - [ ] `StandingEntry`
  - [ ] `GameResult`

### Task 3.2: Configuration Loader
**Estimated Time**: 1.5 hours
**Dependencies**: Task 2.1, Task 3.1
**Files**: SHARED/league_sdk/config_loader.py

- [ ] Implement `ConfigLoader` class
  - [ ] Lazy loading pattern
  - [ ] Caching mechanism
  - [ ] File path resolution

- [ ] Implement configuration loading methods
  - [ ] `load_system()` → SystemConfig
  - [ ] `load_agents()` → AgentsConfig
  - [ ] `load_league(league_id)` → LeagueConfig
  - [ ] `load_games_registry()` → GamesRegistry

- [ ] Implement helper methods
  - [ ] `get_referee_by_id(referee_id)`
  - [ ] `get_player_by_id(player_id)`
  - [ ] `get_game_by_type(game_type)`

- [ ] Add validation and error handling
  - [ ] File existence checks
  - [ ] JSON parsing errors
  - [ ] Schema validation

### Task 3.3: Structured Logger
**Estimated Time**: 1 hour
**Dependencies**: Task 2.1
**Files**: SHARED/league_sdk/logger.py

- [ ] Implement `JsonLogger` class
  - [ ] JSONL format output
  - [ ] Log levels: DEBUG, INFO, WARNING, ERROR
  - [ ] Timestamp in UTC ISO-8601
  - [ ] Component identification

- [ ] Implement logging methods
  - [ ] `debug(event, **details)`
  - [ ] `info(event, **details)`
  - [ ] `warning(event, **details)`
  - [ ] `error(event, **details)`

- [ ] Implement convenience methods
  - [ ] `log_message_sent(message_type, recipient)`
  - [ ] `log_message_received(message_type, sender)`
  - [ ] `log_state_change(old_state, new_state)`

- [ ] Add file handling
  - [ ] Auto-create log directories
  - [ ] Append-only writes
  - [ ] Flush on each write

### Task 3.4: MCP Client
**Estimated Time**: 2 hours
**Dependencies**: Task 2.1, Task 3.1, Task 3.3
**Files**: SHARED/league_sdk/mcp_client.py

- [ ] Implement `MCPClient` class
  - [ ] HTTP client using httpx.AsyncClient
  - [ ] JSON-RPC 2.0 request formatting
  - [ ] Response parsing and validation

- [ ] Implement core method
  - [ ] `call_tool(endpoint, method, params, timeout)`
  - [ ] Generate unique request IDs
  - [ ] Handle JSON-RPC errors

- [ ] Implement retry logic
  - [ ] Exponential backoff (1s, 2s, 4s)
  - [ ] Max retries: 3
  - [ ] Log retry attempts

- [ ] Implement circuit breaker
  - [ ] States: CLOSED, OPEN, HALF_OPEN
  - [ ] Failure threshold: 5
  - [ ] Open timeout: 30 seconds
  - [ ] Track failures per endpoint

- [ ] Add timeout handling
  - [ ] Configurable timeouts
  - [ ] Graceful timeout exceptions

### Task 3.5: Data Repositories
**Estimated Time**: 1.5 hours
**Dependencies**: Task 2.1, Task 3.1
**Files**: SHARED/league_sdk/repositories.py

- [ ] Implement `StandingsRepository`
  - [ ] `load(league_id)` - Read standings.json
  - [ ] `save(league_id, standings)` - Write standings.json
  - [ ] `update_player(league_id, player_id, stats)` - Update player entry
  - [ ] Version incrementing

- [ ] Implement `RoundsRepository`
  - [ ] `load(league_id)` - Read rounds.json
  - [ ] `save(league_id, rounds)` - Write rounds.json
  - [ ] `add_round(league_id, round_data)` - Append round

- [ ] Implement `MatchRepository`
  - [ ] `create(league_id, match_id, match_data)` - Create match file
  - [ ] `update(league_id, match_id, updates)` - Update match file
  - [ ] `load(league_id, match_id)` - Read match file
  - [ ] `add_to_transcript(match_id, message)` - Append message

- [ ] Implement `PlayerHistoryRepository`
  - [ ] `load(player_id)` - Read player history
  - [ ] `save(player_id, history)` - Write player history
  - [ ] `add_match(player_id, match_data)` - Append match
  - [ ] `get_opponent_stats(player_id, opponent_id)` - Analyze patterns

- [ ] Add file handling utilities
  - [ ] Auto-create directories
  - [ ] Atomic writes (write to temp, then rename)
  - [ ] JSON formatting with indentation

---

## Phase 4: Configuration Files (Day 2)

### Task 4.1: System Configuration
**Estimated Time**: 30 minutes
**Dependencies**: Task 2.1
**Files**: SHARED/config/system.json

- [ ] Create `system.json`
  - [ ] Protocol version: "league.v2"
  - [ ] Network configuration (ports)
  - [ ] Timeout values
  - [ ] Retry policy
  - [ ] Circuit breaker settings
  - [ ] Logging configuration

### Task 4.2: Agents Registry
**Estimated Time**: 30 minutes
**Dependencies**: Task 2.1
**Files**: SHARED/config/agents/agents_config.json

- [ ] Create `agents_config.json`
  - [ ] League Manager configuration
  - [ ] Referee configurations (REF01, REF02)
  - [ ] Player configurations (P01, P02, P03, P04)
  - [ ] Endpoint URLs
  - [ ] Game types support
  - [ ] Version numbers

### Task 4.3: League Configuration
**Estimated Time**: 20 minutes
**Dependencies**: Task 2.1
**Files**: SHARED/config/leagues/league_2025_even_odd.json

- [ ] Create `league_2025_even_odd.json`
  - [ ] League ID and display name
  - [ ] Game type: "even_odd"
  - [ ] Format: "round_robin"
  - [ ] Scoring rules (Win=3, Draw=1, Loss=0)
  - [ ] Participant limits
  - [ ] Schedule settings
  - [ ] Game-specific rules

### Task 4.4: Games Registry
**Estimated Time**: 15 minutes
**Dependencies**: Task 2.1
**Files**: SHARED/config/games/games_registry.json

- [ ] Create `games_registry.json`
  - [ ] Even/Odd game definition
  - [ ] Display name
  - [ ] Rules module reference
  - [ ] Time limits
  - [ ] Player count (min=2, max=2)

### Task 4.5: Default Settings
**Estimated Time**: 20 minutes
**Dependencies**: Task 2.1
**Files**: SHARED/config/defaults/*.json

- [ ] Create `referee.json`
  - [ ] Default version
  - [ ] Default game types
  - [ ] Default max_concurrent_matches
  - [ ] Default timeout settings
  - [ ] Default retry policy

- [ ] Create `player.json`
  - [ ] Default version
  - [ ] Default game types
  - [ ] Default strategy: "random"
  - [ ] Default memory settings

---

## Phase 5: League Manager Implementation (Day 2-3)

### Task 5.1: League Manager Core
**Estimated Time**: 2 hours
**Dependencies**: Tasks 3.x, 4.x
**Files**: agents/league_manager/main.py

- [ ] Create FastAPI application
  - [ ] Define app with metadata
  - [ ] Configure CORS if needed
  - [ ] Set up startup/shutdown handlers

- [ ] Implement `/mcp` endpoint
  - [ ] POST handler for JSON-RPC requests
  - [ ] Route to appropriate handlers based on method
  - [ ] Return JSON-RPC responses

- [ ] Initialize components
  - [ ] Load configurations
  - [ ] Initialize logger
  - [ ] Initialize repositories
  - [ ] Create agent registry

- [ ] Implement state management
  - [ ] League state tracking
  - [ ] Registered referees map
  - [ ] Registered players map
  - [ ] Current round tracking

### Task 5.2: Registration Handlers
**Estimated Time**: 1.5 hours
**Dependencies**: Task 5.1
**Files**: agents/league_manager/handlers.py

- [ ] Implement `handle_referee_register()`
  - [ ] Validate referee metadata
  - [ ] Assign referee ID
  - [ ] Generate auth token
  - [ ] Store in registry
  - [ ] Return REFEREE_REGISTER_RESPONSE

- [ ] Implement `handle_player_register()`
  - [ ] Validate player metadata
  - [ ] Assign player ID
  - [ ] Generate auth token
  - [ ] Store in registry
  - [ ] Return LEAGUE_REGISTER_RESPONSE

- [ ] Implement token validation
  - [ ] `validate_token(agent_id, token)`
  - [ ] Return LEAGUE_ERROR for invalid tokens

### Task 5.3: Round-Robin Scheduler
**Estimated Time**: 1.5 hours
**Dependencies**: Task 5.1
**Files**: agents/league_manager/scheduler.py

- [ ] Implement `RoundRobinScheduler` class
  - [ ] Generate all pairings using combinations
  - [ ] Organize into balanced rounds
  - [ ] Assign match IDs (R1M1, R1M2, etc.)

- [ ] Implement `generate_schedule(players)`
  - [ ] Calculate total rounds
  - [ ] Calculate matches per round
  - [ ] Return list of rounds with matches

- [ ] Implement referee assignment
  - [ ] Load balance across available referees
  - [ ] Respect max_concurrent_matches limit
  - [ ] Assign referee endpoints to matches

### Task 5.4: Match Result Handler
**Estimated Time**: 1 hour
**Dependencies**: Task 5.1, 5.2
**Files**: agents/league_manager/handlers.py

- [ ] Implement `handle_match_result_report()`
  - [ ] Validate auth token
  - [ ] Extract match result
  - [ ] Update standings repository
  - [ ] Calculate new rankings
  - [ ] Check if round complete
  - [ ] Broadcast LEAGUE_STANDINGS_UPDATE

### Task 5.5: Round Management
**Estimated Time**: 1 hour
**Dependencies**: Task 5.1, 5.3
**Files**: agents/league_manager/handlers.py

- [ ] Implement `announce_round(round_id)`
  - [ ] Get matches for round
  - [ ] Broadcast ROUND_ANNOUNCEMENT to all players
  - [ ] Log announcement

- [ ] Implement `complete_round(round_id)`
  - [ ] Verify all matches finished
  - [ ] Save round to repository
  - [ ] Broadcast ROUND_COMPLETED
  - [ ] Check if league finished

- [ ] Implement `complete_league()`
  - [ ] Calculate final standings
  - [ ] Determine champion
  - [ ] Broadcast LEAGUE_COMPLETED
  - [ ] Update league state

### Task 5.6: Standings Calculator
**Estimated Time**: 1 hour
**Dependencies**: Task 5.1
**Files**: agents/league_manager/standings.py

- [ ] Implement `StandingsCalculator` class
  - [ ] Calculate points (Win=3, Draw=1, Loss=0)
  - [ ] Sort by points (descending)
  - [ ] Handle ties (alphabetical by ID)
  - [ ] Assign ranks

- [ ] Implement `update_standings(match_result)`
  - [ ] Load current standings
  - [ ] Update both players' stats
  - [ ] Recalculate rankings
  - [ ] Save updated standings

---

## Phase 6: Referee Implementation (Day 3)

### Task 6.1: Referee Core
**Estimated Time**: 1.5 hours
**Dependencies**: Tasks 3.x, 4.x
**Files**: agents/referee/main.py

- [ ] Create FastAPI application
  - [ ] Load referee config from environment
  - [ ] Configure port from environment
  - [ ] Set up startup handler for registration

- [ ] Implement registration on startup
  - [ ] Send REFEREE_REGISTER_REQUEST to League Manager
  - [ ] Store auth token from response
  - [ ] Log successful registration

- [ ] Implement `/mcp` endpoint
  - [ ] Handle GAME_JOIN_ACK
  - [ ] Handle CHOOSE_PARITY_RESPONSE
  - [ ] Route to appropriate handlers

- [ ] Initialize match state tracking
  - [ ] Active matches dictionary
  - [ ] Match state machine per match

### Task 6.2: Match State Machine
**Estimated Time**: 2 hours
**Dependencies**: Task 6.1
**Files**: agents/referee/match_manager.py

- [ ] Implement `MatchStateMachine` class
  - [ ] States: CREATED, WAITING_FOR_PLAYERS, COLLECTING_CHOICES, DRAWING_NUMBER, FINISHED
  - [ ] State transition validation
  - [ ] Event handling per state

- [ ] Implement match creation
  - [ ] `create_match(match_id, player_A, player_B)`
  - [ ] Initialize match data
  - [ ] Create match record in repository

- [ ] Implement state transitions
  - [ ] `transition_to_waiting()` - Send invitations
  - [ ] `transition_to_collecting()` - Request choices
  - [ ] `transition_to_drawing()` - Draw number
  - [ ] `transition_to_finished()` - Announce result

- [ ] Implement transcript recording
  - [ ] Record every message sent/received
  - [ ] Add to match repository

### Task 6.3: Game Invitation Manager
**Estimated Time**: 1 hour
**Dependencies**: Task 6.2
**Files**: agents/referee/invitation_manager.py

- [ ] Implement `send_invitations(match)`
  - [ ] Send GAME_INVITATION to player A
  - [ ] Send GAME_INVITATION to player B
  - [ ] Start 5-second timeout timer
  - [ ] Log invitations sent

- [ ] Implement `handle_join_ack(player_id, accept)`
  - [ ] Validate player is in match
  - [ ] Record join acknowledgment
  - [ ] Check if both players joined
  - [ ] Transition to COLLECTING_CHOICES or cancel

- [ ] Implement timeout handling
  - [ ] Cancel match if timeout
  - [ ] Notify League Manager of cancellation

### Task 6.4: Choice Collector
**Estimated Time**: 1 hour
**Dependencies**: Task 6.2
**Files**: agents/referee/choice_collector.py

- [ ] Implement `request_choices(match)`
  - [ ] Send CHOOSE_PARITY_CALL to player A
  - [ ] Send CHOOSE_PARITY_CALL to player B
  - [ ] Start 30-second timeout timer
  - [ ] Calculate deadline timestamp

- [ ] Implement `handle_parity_response(player_id, choice)`
  - [ ] Validate choice is "even" or "odd"
  - [ ] Record choice
  - [ ] Check if both choices received
  - [ ] Transition to DRAWING_NUMBER or retry

- [ ] Implement retry logic
  - [ ] Retry up to 3 times
  - [ ] Exponential backoff
  - [ ] Technical loss if all retries fail

### Task 6.5: Even/Odd Game Logic
**Estimated Time**: 1 hour
**Dependencies**: Task 6.2
**Files**: agents/referee/game_logic.py

- [ ] Implement `EvenOddGameLogic` class
  - [ ] Draw random number (1-10)
  - [ ] Determine number parity
  - [ ] Compare with player choices
  - [ ] Determine winner

- [ ] Implement `determine_winner(choice_A, choice_B, number)`
  - [ ] Logic: if number even and player chose "even" → win
  - [ ] Logic: if number odd and player chose "odd" → win
  - [ ] Logic: if both chose same and wrong → draw
  - [ ] Return result with reason

- [ ] Implement `calculate_score(result)`
  - [ ] Win: 3 points to winner, 0 to loser
  - [ ] Draw: 1 point each
  - [ ] Return score dictionary

### Task 6.6: Result Reporter
**Estimated Time**: 45 minutes
**Dependencies**: Task 6.2, 6.5
**Files**: agents/referee/result_reporter.py

- [ ] Implement `announce_result(match, result)`
  - [ ] Send GAME_OVER to player A
  - [ ] Send GAME_OVER to player B
  - [ ] Log result announcement

- [ ] Implement `report_to_league(match, result)`
  - [ ] Format MATCH_RESULT_REPORT
  - [ ] Send to League Manager
  - [ ] Log report sent

- [ ] Implement match finalization
  - [ ] Update match state to FINISHED
  - [ ] Save final match record
  - [ ] Clean up match from active matches

---

## Phase 7: Player Implementation (Day 3)

### Task 7.1: Player Core
**Estimated Time**: 1 hour
**Dependencies**: Tasks 3.x, 4.x
**Files**: agents/player/main.py

- [ ] Create FastAPI application
  - [ ] Load player config from environment
  - [ ] Configure port from environment
  - [ ] Set up startup handler for registration

- [ ] Implement registration on startup
  - [ ] Send LEAGUE_REGISTER_REQUEST to League Manager
  - [ ] Store auth token from response
  - [ ] Log successful registration

- [ ] Implement `/mcp` endpoint
  - [ ] Handle ROUND_ANNOUNCEMENT
  - [ ] Handle GAME_INVITATION
  - [ ] Handle CHOOSE_PARITY_CALL
  - [ ] Handle GAME_OVER
  - [ ] Handle LEAGUE_STANDINGS_UPDATE
  - [ ] Handle ROUND_COMPLETED
  - [ ] Handle LEAGUE_COMPLETED

- [ ] Initialize player state
  - [ ] Load or create player history
  - [ ] Initialize statistics

### Task 7.2: Message Handlers
**Estimated Time**: 1.5 hours
**Dependencies**: Task 7.1
**Files**: agents/player/handlers.py

- [ ] Implement `handle_round_announcement(announcement)`
  - [ ] Store round info
  - [ ] Log matches assigned
  - [ ] Prepare for invitations

- [ ] Implement `handle_game_invitation(invitation)`
  - [ ] Store match info
  - [ ] Send GAME_JOIN_ACK immediately
  - [ ] Log invitation accepted

- [ ] Implement `handle_choose_parity_call(call)`
  - [ ] Invoke strategy engine
  - [ ] Get choice ("even" or "odd")
  - [ ] Send CHOOSE_PARITY_RESPONSE
  - [ ] Log choice made

- [ ] Implement `handle_game_over(game_over)`
  - [ ] Extract result
  - [ ] Update player statistics
  - [ ] Save to player history
  - [ ] Log result

- [ ] Implement `handle_standings_update(update)`
  - [ ] Log current standings
  - [ ] Update local standings view

- [ ] Implement `handle_league_completed(completion)`
  - [ ] Log final standings
  - [ ] Log champion
  - [ ] Prepare for shutdown

### Task 7.3: Strategy Engine
**Estimated Time**: 1.5 hours
**Dependencies**: Task 7.1
**Files**: agents/player/strategy.py

- [ ] Implement `StrategyEngine` base class
  - [ ] Abstract method: `make_choice(context)`
  - [ ] Context: opponent_id, match history, standings

- [ ] Implement `RandomStrategy`
  - [ ] Random choice between "even" and "odd"
  - [ ] 50/50 probability

- [ ] Implement `PatternBasedStrategy`
  - [ ] Analyze opponent's choice history
  - [ ] Calculate opponent's preference
  - [ ] Counter opponent's pattern
  - [ ] Fallback to random if insufficient data

- [ ] Implement `LLMStrategy` (optional)
  - [ ] Format context for LLM
  - [ ] Call LLM API
  - [ ] Parse LLM response
  - [ ] Validate and return choice

- [ ] Implement strategy selection
  - [ ] Load strategy from config
  - [ ] Instantiate appropriate strategy class

### Task 7.4: State Tracker
**Estimated Time**: 45 minutes
**Dependencies**: Task 7.1
**Files**: agents/player/state.py

- [ ] Implement `PlayerState` class
  - [ ] Attributes: wins, losses, draws, total_matches, points
  - [ ] Methods: add_win(), add_loss(), add_draw()
  - [ ] Method: get_win_rate()
  - [ ] Method: to_dict() for serialization

- [ ] Implement state persistence
  - [ ] Load from player history
  - [ ] Update after each match
  - [ ] Save to player history

### Task 7.5: History Manager
**Estimated Time**: 1 hour
**Dependencies**: Task 7.1, 7.4
**Files**: agents/player/history.py

- [ ] Implement `HistoryManager` class
  - [ ] Load player history from repository
  - [ ] Add match to history
  - [ ] Save updated history

- [ ] Implement match recording
  - [ ] Record: match_id, opponent_id, result, choices, number, points
  - [ ] Timestamp each match

- [ ] Implement opponent analysis
  - [ ] `get_opponent_stats(opponent_id)`
  - [ ] Calculate: matches_played, wins_against, common_choice
  - [ ] Calculate choice frequency ("even" %, "odd" %)

- [ ] Implement pattern detection
  - [ ] Detect streaks (e.g., always "even")
  - [ ] Detect alternating patterns
  - [ ] Return pattern confidence

---

## Phase 8: Testing (Day 3-4)

### Task 8.1: Unit Tests - Shared SDK
**Estimated Time**: 2 hours
**Dependencies**: Phase 3
**Files**: tests/test_sdk.py

- [ ] Test models.py
  - [ ] Test message envelope validation
  - [ ] Test all 16 message type models
  - [ ] Test validation errors

- [ ] Test config_loader.py
  - [ ] Test loading all config types
  - [ ] Test caching mechanism
  - [ ] Test helper methods
  - [ ] Test error handling

- [ ] Test logger.py
  - [ ] Test log formatting
  - [ ] Test log levels
  - [ ] Test file output

- [ ] Test mcp_client.py
  - [ ] Test JSON-RPC formatting
  - [ ] Test retry logic (mock failures)
  - [ ] Test circuit breaker (mock failures)
  - [ ] Test timeout handling

- [ ] Test repositories.py
  - [ ] Test CRUD operations
  - [ ] Test file creation
  - [ ] Test atomic writes

### Task 8.2: Unit Tests - League Manager
**Estimated Time**: 1.5 hours
**Dependencies**: Phase 5
**Files**: tests/test_league_manager.py

- [ ] Test registration handlers
  - [ ] Test referee registration
  - [ ] Test player registration
  - [ ] Test token generation
  - [ ] Test duplicate registrations

- [ ] Test scheduler
  - [ ] Test Round-Robin with 4 players (6 matches, 3 rounds)
  - [ ] Test Round-Robin with 5 players (10 matches, 5 rounds)
  - [ ] Test referee assignment

- [ ] Test standings calculator
  - [ ] Test point calculation
  - [ ] Test ranking
  - [ ] Test tie handling

- [ ] Test match result handling
  - [ ] Test standings update
  - [ ] Test round completion detection
  - [ ] Test league completion detection

### Task 8.3: Unit Tests - Referee
**Estimated Time**: 1.5 hours
**Dependencies**: Phase 6
**Files**: tests/test_referee.py

- [ ] Test match state machine
  - [ ] Test state transitions
  - [ ] Test invalid transitions
  - [ ] Test state persistence

- [ ] Test game logic
  - [ ] Test Even/Odd winner determination
  - [ ] Test all scenarios (even wins, odd wins, draw)
  - [ ] Test score calculation

- [ ] Test invitation manager
  - [ ] Test sending invitations
  - [ ] Test join acknowledgments
  - [ ] Test timeout handling

- [ ] Test choice collector
  - [ ] Test choice collection
  - [ ] Test timeout and retries
  - [ ] Test technical loss

### Task 8.4: Unit Tests - Player
**Estimated Time**: 1 hour
**Dependencies**: Phase 7
**Files**: tests/test_player.py

- [ ] Test strategy engines
  - [ ] Test RandomStrategy
  - [ ] Test PatternBasedStrategy
  - [ ] Test pattern detection

- [ ] Test state tracker
  - [ ] Test stat updates
  - [ ] Test win rate calculation

- [ ] Test history manager
  - [ ] Test match recording
  - [ ] Test opponent analysis
  - [ ] Test pattern detection

### Task 8.5: Integration Tests
**Estimated Time**: 2 hours
**Dependencies**: Phases 5, 6, 7
**Files**: tests/test_integration.py

- [ ] Test full registration flow
  - [ ] Start League Manager
  - [ ] Register 2 referees
  - [ ] Register 4 players
  - [ ] Verify all registered successfully

- [ ] Test single match flow
  - [ ] Start League Manager, 1 Referee, 2 Players
  - [ ] Execute one match
  - [ ] Verify GAME_INVITATION, GAME_JOIN_ACK, CHOOSE_PARITY_CALL/RESPONSE, GAME_OVER
  - [ ] Verify MATCH_RESULT_REPORT sent
  - [ ] Verify standings updated

- [ ] Test full league flow
  - [ ] Start all 7 agents
  - [ ] Execute complete 4-player league (6 matches)
  - [ ] Verify all rounds complete
  - [ ] Verify LEAGUE_COMPLETED sent
  - [ ] Verify champion declared

- [ ] Test error scenarios
  - [ ] Test timeout on GAME_JOIN_ACK
  - [ ] Test timeout on CHOOSE_PARITY_RESPONSE
  - [ ] Test invalid auth token
  - [ ] Test invalid parity choice

### Task 8.6: Test Coverage
**Estimated Time**: 30 minutes
**Dependencies**: Tasks 8.1-8.5

- [ ] Run pytest with coverage
  ```bash
  pytest --cov=SHARED/league_sdk --cov=agents --cov-report=html
  ```
- [ ] Verify ≥70% coverage
- [ ] Identify untested code paths
- [ ] Add tests for critical paths

---

## Phase 9: Scripts and Utilities (Day 4)

### Task 9.1: Startup Script
**Estimated Time**: 1 hour
**Dependencies**: Phases 5, 6, 7
**Files**: scripts/start_league.py

- [ ] Implement startup script
  - [ ] Start League Manager in subprocess
  - [ ] Wait for health check
  - [ ] Start Referees in subprocesses
  - [ ] Wait for referee registrations
  - [ ] Start Players in subprocesses
  - [ ] Wait for player registrations
  - [ ] Trigger league start

- [ ] Add monitoring
  - [ ] Monitor process health
  - [ ] Tail logs in real-time
  - [ ] Handle Ctrl+C gracefully

- [ ] Add cleanup
  - [ ] Kill all subprocesses on exit
  - [ ] Save final logs

### Task 9.2: Demo Script
**Estimated Time**: 30 minutes
**Dependencies**: Task 9.1
**Files**: scripts/run_demo.py

- [ ] Create demo script
  - [ ] Use start_league.py
  - [ ] Display standings after each round
  - [ ] Display final results
  - [ ] Highlight champion

### Task 9.3: Cleanup Utility
**Estimated Time**: 20 minutes
**Dependencies**: None
**Files**: scripts/cleanup.py

- [ ] Create cleanup script
  - [ ] Clear SHARED/data/ (except .gitkeep)
  - [ ] Clear SHARED/logs/ (except .gitkeep)
  - [ ] Confirm before deletion

---

## Phase 10: Documentation Finalization (Day 4)

### Task 10.1: README.md
**Estimated Time**: 1 hour
**Dependencies**: All previous phases

- [ ] Project overview
  - [ ] Description
  - [ ] Features
  - [ ] Screenshots/diagrams

- [ ] Installation
  - [ ] Prerequisites
  - [ ] Clone repository
  - [ ] Install dependencies
  - [ ] Verify installation

- [ ] Configuration
  - [ ] Explain config files
  - [ ] How to add players/referees
  - [ ] How to create new leagues

- [ ] Usage
  - [ ] Startup sequence
  - [ ] Manual startup (7 terminals)
  - [ ] Script-based startup
  - [ ] Monitoring logs

- [ ] Testing
  - [ ] Run unit tests
  - [ ] Run integration tests
  - [ ] Check coverage

- [ ] Project structure
  - [ ] Directory tree
  - [ ] File descriptions

- [ ] Troubleshooting
  - [ ] Common issues
  - [ ] Solutions

- [ ] Contributing
  - [ ] Code style
  - [ ] Testing requirements

- [ ] License
- [ ] Credits

### Task 10.2: Code Documentation
**Estimated Time**: 1 hour
**Dependencies**: Phases 3-7

- [ ] Review all files for docstrings
  - [ ] Module-level docstrings
  - [ ] Class docstrings
  - [ ] Function/method docstrings
  - [ ] Type hints

- [ ] Add missing documentation
  - [ ] Complex functions
  - [ ] Public APIs
  - [ ] Configuration formats

### Task 10.3: API Documentation
**Estimated Time**: 30 minutes
**Dependencies**: Phases 5-7

- [ ] Document all endpoints
  - [ ] League Manager `/mcp` methods
  - [ ] Referee `/mcp` methods
  - [ ] Player `/mcp` methods

- [ ] Create examples
  - [ ] Example requests
  - [ ] Example responses

---

## Phase 11: Git and Submission (Day 4)

### Task 11.1: Final Review
**Estimated Time**: 30 minutes
**Dependencies**: All previous phases

- [ ] Code review checklist
  - [ ] All TODOs resolved
  - [ ] No hardcoded values
  - [ ] All files < 150 lines (where possible)
  - [ ] Type hints present
  - [ ] Docstrings present
  - [ ] Tests passing
  - [ ] Coverage ≥70%

- [ ] Documentation review
  - [ ] README complete
  - [ ] PRD accurate
  - [ ] DESIGN accurate
  - [ ] TASKS complete

- [ ] Configuration review
  - [ ] All configs valid JSON
  - [ ] No sensitive data
  - [ ] Paths correct

### Task 11.2: Git Commit
**Estimated Time**: 15 minutes
**Dependencies**: Task 11.1

- [ ] Verify .gitignore
  - [ ] **No PDF files staged**
  - [ ] No runtime data
  - [ ] No logs
  - [ ] No virtual environments

- [ ] Stage all files
  ```bash
  git add .
  ```

- [ ] Verify no PDFs staged
  ```bash
  git status | grep -i pdf  # Should be empty
  ```

- [ ] Create commit
  ```bash
  git commit -m "feat: Complete MCP Even/Odd League implementation

  - Added PRD.md, DESIGN.md, TASKS.md, README.md documentation
  - Implemented League Manager (registration, scheduling, standings)
  - Implemented Referee (match management, Even/Odd game logic)
  - Implemented Player Agent (registration, strategy)
  - Added shared SDK (config loader, logger, models, MCP client)
  - Added configuration files
  - Added unit and integration tests
  - Full protocol v2 compliance with 16 message types
  - Test coverage: XX%"
  ```

### Task 11.3: Git Push
**Estimated Time**: 5 minutes
**Dependencies**: Task 11.2

- [ ] Push to remote
  ```bash
  git push origin main
  ```

- [ ] Verify on GitHub
  - [ ] All files present
  - [ ] **No PDF files**
  - [ ] README renders correctly

---

## Summary

**Total Estimated Time**: 35-40 hours across 4 days

**Critical Path**:
1. Documentation (PRD, DESIGN, TASKS, README) - 3 hours
2. Foundation (structure, dependencies) - 1 hour
3. Shared SDK (models, config, logger, client, repos) - 8 hours
4. Configuration files - 2 hours
5. League Manager - 7 hours
6. Referee - 7 hours
7. Player - 5.5 hours
8. Testing - 7.5 hours
9. Scripts - 1.5 hours
10. Documentation finalization - 2.5 hours
11. Git operations - 1 hour

**Key Milestones**:
- End of Day 1: Documentation + Foundation + SDK
- End of Day 2: Configuration + League Manager
- End of Day 3: Referee + Player + Tests
- End of Day 4: Integration + Documentation + Git

---

**CRITICAL REMINDER**:
- **NEVER commit PDF files**
- Verify .gitignore before every commit
- Run `git status | grep -i pdf` before pushing

---

**End of TASKS.md**
