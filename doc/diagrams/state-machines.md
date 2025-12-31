# State Machine Diagrams

## 1. Agent Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LIFECYCLE STATES                      │
└─────────────────────────────────────────────────────────────────┘

                            ┌──────┐
                            │ INIT │
                            └───┬──┘
                                │
                                │ Agent starts
                                │ Load configuration
                                │
                                ▼
                        ┌───────────────┐
                        │  REGISTERING  │
                        └───┬───────┬───┘
                            │       │
          Send registration │       │ Registration rejected
          request           │       │
                            │       │
                            ▼       ▼
                      ┌──────────┐  ┌──────────┐
                      │REGISTERED│  │  FAILED  │
                      └────┬─────┘  └──────────┘
                           │              │
      Wait for league start│              │ Log error
      Receive auth_token   │              │ Shutdown
                           │              │
                           ▼              ▼
                      ┌────────┐    ┌──────────┐
                      │ ACTIVE │    │ SHUTDOWN │
                      └────┬───┘    └──────────┘
                           │
         Participate in    │
         matches/rounds    │
                           │
                           │ League complete
                           │ or error
                           │
                           ▼
                      ┌──────────┐
                      │ SHUTDOWN │
                      └──────────┘


STATE DESCRIPTIONS:

INIT
  - Initial state when agent process starts
  - Load configuration from SHARED/config/
  - Initialize internal data structures
  - Set up HTTP server and /mcp endpoint
  - Transition: Automatically → REGISTERING

REGISTERING
  - Send registration request to League Manager
  - Wait for registration response (timeout: 10s)
  - Transitions:
    * ACCEPTED → REGISTERED (store auth_token)
    * REJECTED → FAILED (log reason)
    * TIMEOUT → retry (max 3), then FAILED

REGISTERED
  - Successfully registered with League Manager
  - Stored auth_token for future communications
  - Waiting for league to start
  - For Players: Wait for ROUND_ANNOUNCEMENT
  - For Referees: Wait for match assignments
  - Transition: League starts → ACTIVE

ACTIVE
  - Fully operational, participating in league
  - Players: Accept invitations, make choices
  - Referees: Run matches, report results
  - League Manager: Coordinate rounds
  - Transitions:
    * LEAGUE_COMPLETED → SHUTDOWN
    * Fatal error → SHUTDOWN
    * Manual stop → SHUTDOWN

FAILED
  - Registration failed (rejected or timeout)
  - Log failure reason
  - Cannot participate in league
  - Transition: Automatically → SHUTDOWN

SHUTDOWN
  - Terminal state
  - Clean up resources
  - Close HTTP server
  - Save final state
  - Process exits
```

## 2. Match State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                       MATCH LIFECYCLE STATES                    │
└─────────────────────────────────────────────────────────────────┘

                          ┌─────────┐
                          │ CREATED │
                          └────┬────┘
                               │
        Referee receives match │
        assignment from League │
        Manager                │
                               │
                               ▼
                    ┌─────────────────────┐
                    │ WAITING_FOR_PLAYERS │
                    └──────┬──────┬───────┘
                           │      │
      Send GAME_INVITATION │      │ Timeout (5s)
      to both players      │      │ or rejection
                           │      │
                           │      ▼
                           │  ┌───────────┐
                           │  │ CANCELLED │
                           │  └─────┬─────┘
                           │        │
                           │        │ Report to
                           │        │ League Mgr
                           │        │
                           │        ▼
      Both players         │  ┌──────────┐
      sent GAME_JOIN_ACK   │  │ FINISHED │
                           │  └──────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │ COLLECTING_CHOICES  │
                  └──────┬──────┬───────┘
                         │      │
    Send CHOOSE_PARITY   │      │ Timeout (30s)
    _CALL to both        │      │ after 3 retries
                         │      │
                         │      ▼
                         │  ┌────────────────┐
                         │  │ TIMEOUT_ERROR  │
                         │  └───────┬────────┘
                         │          │
                         │          │ Technical loss
                         │          │ for non-responder
                         │          │
    Both players         │          ▼
    sent response        │      ┌──────────┐
                         │      │ FINISHED │
                         │      └──────────┘
                         │
                         ▼
                  ┌───────────────┐
                  │ DRAWING_NUMBER│
                  └───────┬───────┘
                          │
      Draw random number  │
      (0-100)             │
      Determine parity    │
      (even/odd)          │
      Calculate winner    │
                          │
                          ▼
                     ┌──────────┐
                     │ FINISHED │
                     └────┬─────┘
                          │
      Send GAME_OVER to   │
      both players        │
      Send MATCH_RESULT   │
      _REPORT to League   │
      Manager             │
                          │
                          ▼
                     [Terminal]


STATE DESCRIPTIONS:

CREATED
  - Match assigned to referee
  - match_id generated (e.g., "R1M1")
  - Players identified (player_A_id, player_B_id)
  - State persisted to SHARED/data/matches/
  - Transition: Automatically → WAITING_FOR_PLAYERS

WAITING_FOR_PLAYERS
  - Send GAME_INVITATION to both players
  - Wait for GAME_JOIN_ACK from both (timeout: 5s)
  - Track arrival timestamps
  - Transitions:
    * Both accept → COLLECTING_CHOICES
    * Any reject → CANCELLED
    * Timeout → CANCELLED

COLLECTING_CHOICES
  - Send CHOOSE_PARITY_CALL to both players
  - Wait for CHOOSE_PARITY_RESPONSE (timeout: 30s)
  - Validate choices ("even" or "odd")
  - Retry on timeout (max 3 attempts, exponential backoff)
  - Transitions:
    * Both respond → DRAWING_NUMBER
    * Timeout after retries → TIMEOUT_ERROR
    * Invalid choice → TIMEOUT_ERROR

DRAWING_NUMBER
  - Draw random number (0-100 inclusive)
  - Determine number parity (num % 2 == 0)
  - Compare against player choices
  - Calculate winner:
    * If number is even: player who chose "even" wins
    * If number is odd: player who chose "odd" wins
    * If both chose same: DRAW
  - Transition: Automatically → FINISHED

TIMEOUT_ERROR
  - Player failed to respond after max retries
  - Assign technical loss to non-responder
  - Award 3 points to opponent, 0 to offender
  - Log error with details
  - Transition: Automatically → FINISHED

CANCELLED
  - Match could not start
  - Reasons: player rejection, timeout, network error
  - Report cancellation to League Manager
  - No points awarded
  - Transition: Automatically → FINISHED

FINISHED
  - Terminal state
  - Send GAME_OVER to both players
  - Send MATCH_RESULT_REPORT to League Manager
  - Update match audit file with complete transcript
  - Match complete
```

## 3. Circuit Breaker State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                   CIRCUIT BREAKER STATES                        │
│               (Per-Endpoint Failure Protection)                 │
└─────────────────────────────────────────────────────────────────┘

                           ┌────────┐
                           │ CLOSED │
                           └───┬────┘
                               │
          Normal operation     │
          Requests allowed     │
          failure_count = 0    │
                               │
                               │ Request
                               │
                               ▼
                        ┌──────────────┐
                        │ Make Request │
                        └──┬─────────┬─┘
                           │         │
                     Success│         │Failure
                           │         │
                           ▼         ▼
                     ┌─────────┐  ┌──────────────┐
                     │ Reset   │  │ Increment    │
                     │ counter │  │ failure_count│
                     └────┬────┘  └──────┬───────┘
                          │              │
                          │              │ failure_count
                          │              │ < 5?
                          │              │
                          │         ┌────┴────┐
                          │    Yes  │    No   │
                          │         │         │
                          ▼         ▼         ▼
                      ┌────────┐  ┌──────────────┐
                      │ CLOSED │  │     OPEN     │
                      └────────┘  └──────┬───────┘
                                         │
              Circuit opened             │
              Reject all requests        │
              Start recovery timer       │
                                         │
                                         │ Wait 30
                                         │ seconds
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │  HALF_OPEN  │
                                  └──────┬──────┘
                                         │
                      Allow one test     │
                      request            │
                                         │
                                         │ Test
                                         │ request
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ Make Request │
                                  └──┬─────────┬─┘
                                     │         │
                               Success│         │Failure
                                     │         │
                                     ▼         ▼
                              ┌────────┐   ┌──────┐
                              │ CLOSED │   │ OPEN │
                              └────────┘   └──────┘
                                  │             │
              Service recovered   │             │ Service still
              Reset to normal     │             │ down
              failure_count = 0   │             │ Return to OPEN
                                  │             │
                                  ▼             ▼
                           [Normal Ops]   [Wait 30s again]


STATE DESCRIPTIONS:

CLOSED (Normal Operation)
  - Requests are allowed through
  - failure_count = 0
  - Track request outcomes
  - On success: Stay in CLOSED
  - On failure: Increment failure_count
  - Transition: failure_count >= 5 → OPEN

OPEN (Circuit Tripped)
  - Requests rejected immediately (fail-fast)
  - Error: "Circuit breaker is OPEN"
  - Protects failing service from overload
  - Start recovery timer (30 seconds)
  - No requests attempted during this time
  - Transition: After 30s → HALF_OPEN

HALF_OPEN (Testing Recovery)
  - Allow ONE test request through
  - Determine if service recovered
  - Transitions:
    * Test succeeds → CLOSED (service recovered)
    * Test fails → OPEN (service still down)
  - If returning to OPEN, restart 30s timer


CONFIGURATION:

failure_threshold: 5 consecutive failures
recovery_timeout: 30 seconds
per_endpoint: Each endpoint has independent circuit breaker


EXAMPLE FAILURE SEQUENCE:

Time    Event                   State      failure_count
----    -----                   -----      -------------
T+0s    Request 1 → timeout     CLOSED     1
T+1s    Request 2 → timeout     CLOSED     2
T+2s    Request 3 → timeout     CLOSED     3
T+3s    Request 4 → timeout     CLOSED     4
T+4s    Request 5 → timeout     OPEN       5
T+5s    Request 6 → rejected    OPEN       5
T+34s   (30s elapsed)           HALF_OPEN  5
T+34s   Test request → success  CLOSED     0
T+35s   Request 7 → success     CLOSED     0
```

## 4. Round State Machine (League Manager)

```
┌─────────────────────────────────────────────────────────────────┐
│                        ROUND LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────────┐
                        │ ROUND_INIT   │
                        └──────┬───────┘
                               │
        Create round schedule  │
        Assign matches to      │
        referees               │
                               │
                               ▼
                        ┌──────────────┐
                        │ ANNOUNCED    │
                        └──────┬───────┘
                               │
        Send ROUND_ANNOUNCEMENT│
        to all players         │
        Notify referees        │
                               │
                               ▼
                        ┌──────────────┐
                        │  IN_PROGRESS │
                        └──────┬───────┘
                               │
        Matches executing      │
        Receive MATCH_RESULT   │
        _REPORT from referees  │
        Track completion       │
                               │
                               │ All matches
                               │ complete?
                               │
                               ▼
                        ┌──────────────┐
                        │  COMPLETED   │
                        └──────┬───────┘
                               │
        Update standings.json  │
        Send LEAGUE_STANDINGS  │
        _UPDATE                │
        Send ROUND_COMPLETED   │
                               │
                               ▼
                        ┌──────────────┐
                        │ More rounds? │
                        └──┬────────┬──┘
                           │        │
                      Yes  │        │ No
                           │        │
                           ▼        ▼
                    ┌───────────┐  ┌────────────┐
                    │ROUND_INIT │  │LEAGUE_DONE │
                    │(next round│  └────────────┘
                    └───────────┘        │
                                         │
                                Send     │
                                LEAGUE   │
                                _COMPLETED│
                                         │
                                         ▼
                                   [Terminal]
```

## State Transition Triggers

### Agent Lifecycle Triggers
- **INIT → REGISTERING**: Process start, config loaded
- **REGISTERING → REGISTERED**: Registration accepted
- **REGISTERING → FAILED**: Registration rejected/timeout
- **REGISTERED → ACTIVE**: League starts
- **ACTIVE → SHUTDOWN**: League complete or error
- **FAILED → SHUTDOWN**: Cleanup after failure

### Match Triggers
- **CREATED → WAITING_FOR_PLAYERS**: Match assigned
- **WAITING_FOR_PLAYERS → COLLECTING_CHOICES**: Both join acks received
- **WAITING_FOR_PLAYERS → CANCELLED**: Timeout or rejection
- **COLLECTING_CHOICES → DRAWING_NUMBER**: Both choices received
- **COLLECTING_CHOICES → TIMEOUT_ERROR**: Max retries exceeded
- **DRAWING_NUMBER → FINISHED**: Winner determined
- **TIMEOUT_ERROR → FINISHED**: Technical loss assigned
- **CANCELLED → FINISHED**: Cancellation reported

### Circuit Breaker Triggers
- **CLOSED → OPEN**: 5 consecutive failures
- **OPEN → HALF_OPEN**: 30 second recovery timer
- **HALF_OPEN → CLOSED**: Test request succeeds
- **HALF_OPEN → OPEN**: Test request fails

### Round Triggers
- **ROUND_INIT → ANNOUNCED**: Schedule created
- **ANNOUNCED → IN_PROGRESS**: First match starts
- **IN_PROGRESS → COMPLETED**: All matches finished
- **COMPLETED → ROUND_INIT**: More rounds remain
- **COMPLETED → LEAGUE_DONE**: All rounds complete
