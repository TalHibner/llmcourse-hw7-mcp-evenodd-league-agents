# Product Requirements Document (PRD)
## MCP Even/Odd League Multi-Agent System

**Version:** 1.0
**Date:** December 31, 2025
**Author:** MCP Development Team
**Course:** Large Language Models - Homework 7
**Instructor:** Dr. Yoram Segal

---

## 1. Project Overview

### 1.1 Executive Summary
The MCP Even/Odd League is a multi-agent AI system designed to demonstrate distributed protocol communication, autonomous agent behavior, and tournament management. The system orchestrates games between competing AI player agents, managed by referee agents, and coordinated by a central league manager.

### 1.2 Project Objectives
- Implement a fully functional multi-agent communication system using the MCP (Model Context Protocol) league.v2 specification
- Demonstrate understanding of JSON-RPC 2.0 over HTTP for inter-agent communication
- Create autonomous agents capable of registration, gameplay, and strategy execution
- Implement a complete tournament lifecycle including Round-Robin scheduling, match execution, and standings management
- Provide comprehensive logging, error handling, and resilience patterns

### 1.3 Educational Goals
- Master protocol-based communication between distributed systems
- Understand multi-agent architectures and state management
- Implement timeout handling, retry logic, and circuit breaker patterns
- Practice modular software design with separation of concerns
- Apply best practices for configuration management and data persistence

---

## 2. Problem Statement

### 2.1 Challenge
Traditional tournament systems require manual coordination and centralized game management. This project explores how autonomous agents can self-organize into a competitive league with minimal manual intervention, using only protocol-based messages.

### 2.2 Use Cases
1. **Academic Research**: Study multi-agent coordination and emergent strategies
2. **AI Competition**: Provide a framework for AI strategy competitions
3. **Protocol Testing**: Validate MCP protocol compliance and interoperability
4. **Educational Platform**: Teach distributed systems and agent communication

---

## 3. Target Audience

### 3.1 Primary Users
- **University Students**: Learning multi-agent systems and protocol design
- **Course Instructor**: Dr. Yoram Segal, for assessment and evaluation
- **AI Researchers**: Studying agent strategies and coordination

### 3.2 Secondary Users
- **Software Developers**: Learning FastAPI and async Python
- **System Architects**: Studying distributed system patterns

---

## 4. Success Criteria and KPIs

### 4.1 Functional Success Criteria
- [ ] All 16 core message types implemented correctly
- [ ] Complete league lifecycle from registration to completion
- [ ] Round-Robin scheduling generating correct pairings
- [ ] Matches execute with proper timeout handling
- [ ] Standings calculated correctly (Win=3, Draw=1, Loss=0)
- [ ] All agents start successfully and register automatically
- [ ] Error handling prevents system crashes

### 4.2 Quality Metrics
- **Code Coverage**: Minimum 70% test coverage
- **Protocol Compliance**: 100% adherence to league.v2 specification
- **Uptime**: System runs complete 4-player league without crashes
- **Response Time**: All messages processed within specified timeouts
- **Logging Completeness**: All critical events logged in JSONL format

### 4.3 Performance Metrics
- **Match Execution**: Complete match in < 60 seconds
- **Round Completion**: Complete round in < 5 minutes
- **Concurrent Matches**: Support 2+ simultaneous matches
- **Scalability**: Support 4-10 players per league

---

## 5. Functional Requirements

### 5.1 Agent Types

#### 5.1.1 League Manager (LM)
**ID**: LEAGUE_MANAGER_01
**Port**: 8000
**Responsibilities**:
- Accept referee registrations (REFEREE_REGISTER_REQUEST/RESPONSE)
- Accept player registrations (LEAGUE_REGISTER_REQUEST/RESPONSE)
- Generate Round-Robin match schedule
- Send ROUND_ANNOUNCEMENT to all players
- Receive MATCH_RESULT_REPORT from referees
- Calculate and update standings
- Broadcast LEAGUE_STANDINGS_UPDATE
- Send ROUND_COMPLETED notifications
- Send LEAGUE_COMPLETED when tournament ends
- Handle LEAGUE_ERROR conditions

**Must Have**:
- Token generation and validation
- Persistent standings storage
- Match assignment to available referees
- Real-time standings calculation

#### 5.1.2 Referee Agents (REF)
**IDs**: REF01, REF02
**Ports**: 8001-8010
**Responsibilities**:
- Register with League Manager
- Receive match assignments from ROUND_ANNOUNCEMENT
- Send GAME_INVITATION to both players
- Receive GAME_JOIN_ACK (5-second timeout)
- Send CHOOSE_PARITY_CALL to both players
- Receive CHOOSE_PARITY_RESPONSE (30-second timeout)
- Draw random number (1-10)
- Determine winner based on Even/Odd rules
- Send GAME_OVER to both players
- Send MATCH_RESULT_REPORT to League Manager
- Handle GAME_ERROR conditions
- Maintain match audit trail

**Must Have**:
- Even/Odd game logic
- Timeout enforcement
- Retry logic (max 3 attempts)
- Match state machine (CREATED → WAITING → COLLECTING → DRAWING → FINISHED)
- Technical loss handling for timeouts

#### 5.1.3 Player Agents (P)
**IDs**: P01, P02, P03, P04
**Ports**: 8101-8104+
**Responsibilities**:
- Register with League Manager
- Receive ROUND_ANNOUNCEMENT
- Receive GAME_INVITATION from referee
- Send GAME_JOIN_ACK (accept match)
- Receive CHOOSE_PARITY_CALL
- Send CHOOSE_PARITY_RESPONSE ("even" or "odd")
- Receive GAME_OVER (match result)
- Update personal statistics
- Maintain match history for strategy learning

**Must Have**:
- Choice strategy (random, pattern-based, or LLM-driven)
- Response within timeout windows
- State tracking (wins, losses, draws)
- History persistence for learning

### 5.2 Protocol Messages

#### 5.2.1 Registration Phase
1. **REFEREE_REGISTER_REQUEST** (Referee → LM)
   - Fields: referee_meta (display_name, version, game_types, contact_endpoint, max_concurrent_matches)
2. **REFEREE_REGISTER_RESPONSE** (LM → Referee)
   - Fields: status (ACCEPTED/REJECTED), referee_id, auth_token, league_id
3. **LEAGUE_REGISTER_REQUEST** (Player → LM)
   - Fields: player_meta (display_name, version, game_types, contact_endpoint)
4. **LEAGUE_REGISTER_RESPONSE** (LM → Player)
   - Fields: status (ACCEPTED/REJECTED), player_id, auth_token, league_id

#### 5.2.2 Round Management
5. **ROUND_ANNOUNCEMENT** (LM → All Players)
   - Fields: round_id, matches[] (match_id, player_A_id, player_B_id, referee_endpoint)
6. **ROUND_COMPLETED** (LM → All Players)
   - Fields: round_id, completed_matches[], next_round_id

#### 5.2.3 Match Execution
7. **GAME_INVITATION** (Referee → Player)
   - Fields: match_id, role_in_match (PLAYER_A/PLAYER_B), opponent_id, game_type
8. **GAME_JOIN_ACK** (Player → Referee)
   - Fields: accept (true/false), arrival_timestamp, match_id
   - Timeout: 5 seconds
9. **CHOOSE_PARITY_CALL** (Referee → Player)
   - Fields: match_id, game_type, deadline, context
10. **CHOOSE_PARITY_RESPONSE** (Player → Referee)
    - Fields: parity_choice ("even"/"odd"), match_id
    - Timeout: 30 seconds
11. **GAME_OVER** (Referee → Both Players)
    - Fields: game_result (status, winner_player_id, drawn_number, number_parity, choices, reason)

#### 5.2.4 Reporting & Standings
12. **MATCH_RESULT_REPORT** (Referee → LM)
    - Fields: match_id, round_id, result (winner, score, details)
13. **LEAGUE_STANDINGS_UPDATE** (LM → All Players)
    - Fields: standings[] (rank, player_id, display_name, played, wins, draws, losses, points)
14. **LEAGUE_COMPLETED** (LM → All Players)
    - Fields: champion, final_standings, total_rounds, total_matches

#### 5.2.5 Error Handling
15. **LEAGUE_ERROR** (LM → Player/Referee)
    - Fields: error_code, error_description, context
    - Common codes: E012 (AUTH_TOKEN_INVALID), E013 (PLAYER_NOT_REGISTERED), E014 (LEAGUE_NOT_FOUND)
16. **GAME_ERROR** (Referee → Players)
    - Fields: error_code, error_description, affected_player, action_required, retry_count, max_retries, consequence
    - Common codes: E001 (TIMEOUT_ERROR), E002 (INVALID_CHOICE), E003 (DISCONNECTED)

### 5.3 Game Rules: Even/Odd

#### 5.3.1 Game Mechanics
1. Two players choose "even" or "odd" simultaneously (choices hidden from opponent)
2. Referee draws a random number between 1-10
3. Referee determines if number is even or odd
4. Winner determination:
   - If number is even → player who chose "even" wins
   - If number is odd → player who chose "odd" wins
   - If both chose the same parity and it's wrong → DRAW
   - If both chose the same parity and it's right → both win (DRAW)

#### 5.3.2 Scoring
- **Win**: 3 points
- **Draw**: 1 point each player
- **Loss**: 0 points
- **Technical Loss** (timeout/disconnect): Opponent gets 3 points, offender gets 0

### 5.4 Scheduling

#### 5.4.1 Round-Robin Algorithm
- All players play all other players exactly once
- Formula: Total matches = n × (n-1) / 2 where n = number of players
- Example (4 players):
  - Round 1: P01 vs P02, P03 vs P04
  - Round 2: P01 vs P03, P02 vs P04
  - Round 3: P01 vs P04, P02 vs P03
- Total: 6 matches across 3 rounds

#### 5.4.2 Match Assignment
- League Manager assigns matches to available referees
- Referees can handle max_concurrent_matches simultaneously
- Load balancing distributes matches evenly

### 5.5 Data Persistence

#### 5.5.1 Required Data Files
- **Standings**: `SHARED/data/leagues/<league_id>/standings.json`
- **Rounds History**: `SHARED/data/leagues/<league_id>/rounds.json`
- **Match Details**: `SHARED/data/matches/<league_id>/<match_id>.json`
- **Player History**: `SHARED/data/players/<player_id>/history.json`

#### 5.5.2 Logging
- **League Log**: `SHARED/logs/league/<league_id>/league.log.jsonl`
- **Agent Logs**: `SHARED/logs/agents/<agent_id>.log.jsonl`
- Format: JSON Lines (JSONL) for streaming and parallel processing

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **Message Processing**: < 100ms per message
- **Match Execution**: < 60 seconds per match
- **Timeout Enforcement**: Accurate to ±1 second
- **Concurrent Matches**: Support 2+ matches simultaneously

### 6.2 Reliability
- **Uptime**: System completes full league without crashes
- **Error Recovery**: Retry logic with exponential backoff (1s, 2s, 4s)
- **Circuit Breaker**: Prevent cascading failures
- **Data Persistence**: All critical data saved before acknowledgment

### 6.3 Security
- **Authentication**: Token-based auth for all post-registration messages
- **Validation**: All inputs validated before processing
- **Authorization**: Only registered agents receive messages
- **Token Expiry**: Tokens valid for league duration

### 6.4 Scalability
- **Player Count**: Support 4-10 players
- **Referee Count**: Support 2-5 referees
- **Match Concurrency**: 2-10 simultaneous matches
- **League Count**: Support multiple independent leagues

### 6.5 Maintainability
- **Code Modularity**: Files < 150 lines where possible
- **Type Hints**: Full Python type annotations
- **Documentation**: Docstrings for all classes and functions
- **Configuration**: All settings externalized to JSON files
- **Logging**: Comprehensive JSONL logging

### 6.6 Usability
- **Startup**: Single command per agent
- **Configuration**: JSON-based, human-readable
- **Monitoring**: Real-time logs via JSONL streaming
- **Debugging**: Complete match audit trails

---

## 7. Constraints and Dependencies

### 7.1 Technical Constraints
- **Language**: Python 3.10+
- **Framework**: FastAPI for HTTP servers
- **Protocol**: JSON-RPC 2.0 over HTTP
- **Message Format**: league.v2 specification
- **Timestamp Format**: ISO-8601 with UTC (Z suffix)

### 7.2 Dependencies
**Core**:
- fastapi
- uvicorn[standard]
- pydantic >=2.0
- httpx (or requests)

**Development**:
- pytest
- pytest-asyncio
- pytest-cov

**Optional**:
- python-dotenv (environment variables)
- rich (terminal output formatting)

### 7.3 System Requirements
- **OS**: Linux, macOS, Windows (WSL)
- **RAM**: 512MB minimum
- **Disk**: 100MB for code + logs
- **Network**: localhost communication (no external network required)

---

## 8. Timeline and Milestones

### Phase 1: Documentation (Day 1)
- [x] PRD.md
- [ ] DESIGN.md
- [ ] TASKS.md
- [ ] README.md

### Phase 2: Foundation (Day 1-2)
- [ ] Project structure
- [ ] Shared SDK (models, config_loader, logger)
- [ ] Configuration files

### Phase 3: Core Implementation (Day 2-3)
- [ ] League Manager
- [ ] Referee agent
- [ ] Player agent

### Phase 4: Testing & Integration (Day 3-4)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Full league simulation

### Phase 5: Finalization (Day 4)
- [ ] Documentation review
- [ ] Code cleanup
- [ ] Git commit and push

---

## 9. Out of Scope

### 9.1 Explicitly Excluded
- Web UI dashboard (future enhancement)
- Database backend (using JSON files only)
- Multi-game support beyond Even/Odd (future)
- LLM integration for players (optional, not required)
- Network security beyond basic token auth
- Distributed deployment (single machine only)
- Real-time WebSocket communication (HTTP polling sufficient)

### 9.2 Future Enhancements
- Support for additional game types (Rock-Paper-Scissors, Tic-Tac-Toe)
- Web dashboard for live standings
- Advanced player strategies using LLMs
- Multi-league tournaments
- ELO rating system
- Replay system for matches

---

## 10. Risks and Mitigation

### 10.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Timeout handling complexity | High | Medium | Use proven timeout decorators, comprehensive testing |
| Race conditions in concurrent matches | High | Medium | Proper async/await usage, state locking |
| Message delivery failures | Medium | Low | Retry logic with exponential backoff |
| Configuration errors | Medium | Medium | Validation on startup, clear error messages |
| Log file growth | Low | High | JSONL rotation, cleanup scripts |

### 10.2 Schedule Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Underestimated complexity | High | Modular design, use provided examples |
| Integration issues | Medium | Early integration testing, continuous validation |
| Testing gaps | Medium | Test-driven development, 70% coverage target |

---

## 11. Acceptance Criteria

### 11.1 Functional Acceptance
- [ ] 4 players successfully register
- [ ] 2 referees successfully register
- [ ] Round-Robin schedule generates 6 matches (4 players)
- [ ] All 6 matches execute successfully
- [ ] Standings update correctly after each match
- [ ] Champion declared at league end
- [ ] All 16 message types used correctly
- [ ] System handles timeouts gracefully
- [ ] Error messages sent for invalid scenarios

### 11.2 Code Quality Acceptance
- [ ] All files have docstrings
- [ ] Type hints throughout
- [ ] Test coverage ≥ 70%
- [ ] No hardcoded values (use config files)
- [ ] Proper error handling (no unhandled exceptions)
- [ ] Follows PEP 8 style guidelines
- [ ] README includes installation and usage instructions

### 11.3 Deliverables
- [ ] Complete source code
- [ ] Configuration files
- [ ] Test suite
- [ ] Documentation (PRD, DESIGN, TASKS, README)
- [ ] Git repository with proper .gitignore
- [ ] No PDF files in repository

---

## 12. Stakeholder Sign-off

**Student**: _________________
**Instructor**: Dr. Yoram Segal
**Date**: December 31, 2025

---

## Appendix A: Glossary

- **Agent**: An autonomous software component (League Manager, Referee, or Player)
- **MCP**: Model Context Protocol - communication protocol for agents
- **JSON-RPC 2.0**: Remote procedure call protocol using JSON
- **Round-Robin**: Tournament format where everyone plays everyone
- **JSONL**: JSON Lines format (one JSON object per line)
- **Circuit Breaker**: Pattern to prevent cascading failures
- **Exponential Backoff**: Retry strategy with increasing delays
- **Technical Loss**: Loss due to timeout or rule violation

## Appendix B: References

- MCP League Protocol v2 Specification
- JSON-RPC 2.0 Specification (https://www.jsonrpc.org/specification)
- FastAPI Documentation (https://fastapi.tiangolo.com/)
- Pydantic Documentation (https://docs.pydantic.dev/)
- Python asyncio Documentation

---

**End of PRD**
