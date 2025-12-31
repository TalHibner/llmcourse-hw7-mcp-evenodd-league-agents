# Message Flow Sequence Diagrams

## 1. Complete Registration Flow

### 1.1 Referee Registration

```
Referee                    League Manager
REF01
  │
  │  REFEREE_REGISTER_REQUEST
  │  {display_name, game_types,
  │   endpoint, max_matches}
  ├──────────────────────────────>
  │
  │  (League Manager validates)
  │  - Check game_types supported
  │  - Verify endpoint format
  │  - Assign referee_id
  │  - Generate auth_token
  │
  │  REFEREE_REGISTER_RESPONSE
  │  {status: ACCEPTED,
  │   referee_id: REF01,
  │   auth_token, league_id}
  │<──────────────────────────────
  │
  │  (Referee stores auth_token)
  │  Status: REGISTERED
  │
```

### 1.2 Player Registration

```
Player                     League Manager
 P01
  │
  │  LEAGUE_REGISTER_REQUEST
  │  {display_name, game_types,
  │   endpoint}
  ├──────────────────────────────>
  │
  │  (League Manager validates)
  │  - Check game_types supported
  │  - Verify endpoint format
  │  - Check max_players not exceeded
  │  - Assign player_id
  │  - Generate auth_token
  │
  │  LEAGUE_REGISTER_RESPONSE
  │  {status: ACCEPTED,
  │   player_id: P01,
  │   auth_token, league_id}
  │<──────────────────────────────
  │
  │  (Player stores auth_token)
  │  Status: REGISTERED
  │  Wait for ROUND_ANNOUNCEMENT
  │
```

## 2. Match Execution Flow (Complete)

```
League Mgr    Referee        Player A        Player B
    │           REF01           P01             P02
    │             │              │               │
    │ ROUND_      │              │               │
    │ ANNOUNCEMENT│              │               │
    ├────────────>│              │               │
    │ {round_id,  │              │               │
    │  matches:[  │              │               │
    │   {P01 vs   │              │               │
    │    P02}]}   │              │               │
    │             │              │               │
    │             │ GAME_        │               │
    │             │ INVITATION   │               │
    │             ├─────────────>│               │
    │             │ {role:       │               │
    │             │  PLAYER_A}   │               │
    │             │              │               │
    │             │ GAME_        │               │
    │             │ INVITATION   │               │
    │             ├──────────────────────────────>│
    │             │              │ {role:        │
    │             │              │  PLAYER_B}    │
    │             │              │               │
    │             │ GAME_JOIN_ACK│               │
    │             │<─────────────┤               │
    │             │ {accept:     │               │
    │             │  true}       │               │
    │             │              │               │
    │             │              │ GAME_JOIN_ACK │
    │             │<──────────────────────────────┤
    │             │              │ {accept: true}│
    │             │              │               │
    │   [Timeout: 5 seconds - if no ACK, cancel match]
    │             │              │               │
    │             │ CHOOSE_      │               │
    │             │ PARITY_CALL  │               │
    │             ├─────────────>│               │
    │             │ {deadline}   │               │
    │             │              │               │
    │             │              │ CHOOSE_PARITY │
    │             │              │     _CALL     │
    │             ├──────────────────────────────>│
    │             │              │  {deadline}   │
    │             │              │               │
    │             │ CHOOSE_PARITY│               │
    │             │   _RESPONSE  │               │
    │             │<─────────────┤               │
    │             │ {choice:     │               │
    │             │  "even"}     │               │
    │             │              │               │
    │             │              │ CHOOSE_PARITY │
    │             │              │   _RESPONSE   │
    │             │<──────────────────────────────┤
    │             │              │ {choice: "odd"}│
    │             │              │               │
    │   [Timeout: 30 seconds - retry 3x, then technical loss]
    │             │              │               │
    │  [Referee draws random number: 42 (even)]  │
    │  [Winner determination: P01 chose "even"]  │
    │             │              │               │
    │             │ GAME_OVER    │               │
    │             ├─────────────>│               │
    │             │ {winner:P01, │               │
    │             │  number:42}  │               │
    │             │              │               │
    │             │              │  GAME_OVER    │
    │             ├──────────────────────────────>│
    │             │              │ {winner:P01,  │
    │             │              │  number:42}   │
    │             │              │               │
    │  MATCH_     │              │               │
    │  RESULT_    │              │               │
    │  REPORT     │              │               │
    │<────────────┤              │               │
    │ {winner:P01,│              │               │
    │  score:     │              │               │
    │  {P01:3,    │              │               │
    │   P02:0}}   │              │               │
    │             │              │               │
```

## 3. Round Lifecycle Flow

```
League Manager         All Players
       │                    │
       │                    │
       │  ROUND_ANNOUNCEMENT│
       │  {round_id: 1,     │
       │   matches: [       │
       │     {P01 vs P02,   │
       │      P03 vs P04}]} │
       ├───────────────────>│
       │                    │
       │  (Matches execute  │
       │   via referees)    │
       │  ─ ─ ─ ─ ─ ─ ─ ─ ─>│
       │                    │
       │  [Referee sends    │
       │   MATCH_RESULT_    │
       │   REPORT for each  │
       │   completed match] │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─  │
       │                    │
       │  (League Manager   │
       │   updates          │
       │   standings.json)  │
       │                    │
       │  LEAGUE_STANDINGS_ │
       │  UPDATE            │
       │  {standings: [     │
       │    {rank:1,P01,    │
       │     wins:1,pts:3}, │
       │    {rank:2,P02,    │
       │     ...}]}         │
       ├───────────────────>│
       │                    │
       │  ROUND_COMPLETED   │
       │  {round_id: 1,     │
       │   completed_matches│
       │   next_round_id:2} │
       ├───────────────────>│
       │                    │
       │  (If more rounds)  │
       │  ROUND_ANNOUNCEMENT│
       │  {round_id: 2,...} │
       ├───────────────────>│
       │                    │
       │  (If league done)  │
       │  LEAGUE_COMPLETED  │
       │  {champion: P01,   │
       │   final_standings} │
       ├───────────────────>│
       │                    │
```

## 4. Error Handling with Retries

### 4.1 Timeout Error with Exponential Backoff

```
Referee                Player
REF01                   P02
  │                      │
  │ CHOOSE_PARITY_CALL   │
  ├─────────────────────>│
  │ {deadline: T+30s}    │
  │                      │
  │  [Wait 30 seconds]   │
  │                      │
  │  (No response)       │
  │                      │
  │ GAME_ERROR           │
  │ {error: E001,        │
  │  retry_count: 1,     │
  │  max_retries: 3}     │
  ├─────────────────────>│
  │                      │
  │  [Wait 1 second]     │
  │  (Exponential        │
  │   backoff: 2^0)      │
  │                      │
  │ CHOOSE_PARITY_CALL   │
  │ (Retry #1)           │
  ├─────────────────────>│
  │                      │
  │  [Wait 30 seconds]   │
  │                      │
  │  (No response)       │
  │                      │
  │ GAME_ERROR           │
  │ {retry_count: 2}     │
  ├─────────────────────>│
  │                      │
  │  [Wait 2 seconds]    │
  │  (Exponential        │
  │   backoff: 2^1)      │
  │                      │
  │ CHOOSE_PARITY_CALL   │
  │ (Retry #2)           │
  ├─────────────────────>│
  │                      │
  │  [Wait 30 seconds]   │
  │                      │
  │  (No response)       │
  │                      │
  │ GAME_ERROR           │
  │ {retry_count: 3}     │
  ├─────────────────────>│
  │                      │
  │  [Wait 4 seconds]    │
  │  (Exponential        │
  │   backoff: 2^2)      │
  │                      │
  │ CHOOSE_PARITY_CALL   │
  │ (Retry #3 - FINAL)   │
  ├─────────────────────>│
  │                      │
  │  [Wait 30 seconds]   │
  │                      │
  │  (No response)       │
  │  Max retries reached │
  │                      │
  │ GAME_OVER            │
  │ {status: WIN,        │
  │  winner: P01,        │
  │  reason: "Technical  │
  │   loss - timeout"}   │
  ├─────────────────────>│
  │                      │
  │  Report technical    │
  │  loss to League Mgr  │
  │                      │
```

### 4.2 Authentication Error (Non-Retryable)

```
Player               League Manager
 P01
  │
  │  ROUND_ANNOUNCEMENT
  │  {auth_token:
  │   "tok_invalid"}
  ├────────────────────────>
  │
  │  (Validation fails)
  │
  │  LEAGUE_ERROR
  │  {error_code: E012,
  │   error_description:
  │    "AUTH_TOKEN_INVALID",
  │   context: {
  │     message: "Please
  │      re-register"}}
  │<────────────────────────
  │
  │  (Player must re-register)
  │  No retry allowed
  │
```

### 4.3 Circuit Breaker Pattern

```
Agent                Remote Endpoint
  │                         │
  │  [Circuit: CLOSED]      │
  │  Request #1             │
  ├────────────────────────>│
  │<─ ─ ─ ─ ─ (timeout)     │
  │  Failure count: 1       │
  │                         │
  │  Request #2             │
  ├────────────────────────>│
  │<─ ─ ─ ─ ─ (timeout)     │
  │  Failure count: 2       │
  │                         │
  │  Request #3             │
  ├────────────────────────>│
  │<─ ─ ─ ─ ─ (timeout)     │
  │  Failure count: 3       │
  │                         │
  │  Request #4             │
  ├────────────────────────>│
  │<─ ─ ─ ─ ─ (timeout)     │
  │  Failure count: 4       │
  │                         │
  │  Request #5             │
  ├────────────────────────>│
  │<─ ─ ─ ─ ─ (timeout)     │
  │  Failure count: 5       │
  │                         │
  │  [Circuit: OPEN]        │
  │  Threshold reached!     │
  │                         │
  │  Request #6             │
  │  (Rejected immediately) │
  │  Error: Circuit open    │
  │                         │
  │  [Wait 30 seconds]      │
  │                         │
  │  [Circuit: HALF_OPEN]   │
  │  Test request           │
  ├────────────────────────>│
  │<────────────────────────┤
  │  Success!               │
  │                         │
  │  [Circuit: CLOSED]      │
  │  Reset failure count    │
  │  Normal operation       │
  │                         │
```

## 5. Parallel Match Execution

```
League        Referee 1      Referee 2      Players
Manager       (REF01)        (REF02)        (P01-P04)
   │             │              │               │
   │ ROUND_      │              │               │
   │ ANNOUNCEMENT│              │               │
   ├────────────>│              │               │
   │ {matches:[  │              │               │
   │   R1M1:     │              │               │
   │   P01vsP02, │              │               │
   │   R1M2:     │              │               │
   │   P03vsP04]}│              │               │
   │             │              │               │
   │             │ [Match R1M1] │ [Match R1M2]  │
   │             │ (P01 vs P02) │ (P03 vs P04)  │
   │             ├─────────────────────────────>│
   │             │              ├──────────────>│
   │             │              │               │
   │             │ (Both matches run in parallel)│
   │             │              │               │
   │             │ GAME_OVER    │  GAME_OVER    │
   │             ├─────────────────────────────>│
   │             │              ├──────────────>│
   │             │              │               │
   │  MATCH_     │              │               │
   │  RESULT     │              │               │
   │<────────────┤              │               │
   │             │  MATCH_      │               │
   │             │  RESULT      │               │
   │             │<─────────────┤               │
   │<────────────┼──────────────┘               │
   │             │                               │
   │  (Update standings.json)                   │
   │                                             │
   │  LEAGUE_STANDINGS_UPDATE                   │
   ├────────────────────────────────────────────>│
   │                                             │
```

## Message Flow Summary

### Key Timing Requirements

1. **GAME_JOIN_ACK**: Must respond within 5 seconds
2. **CHOOSE_PARITY_RESPONSE**: Must respond within 30 seconds
3. **Generic API calls**: 10 second timeout
4. **Retry delays**: 1s, 2s, 4s (exponential backoff)
5. **Circuit breaker**: Opens after 5 failures, tests recovery after 30s

### Message Ordering Guarantees

1. Registration must complete before any other operations
2. ROUND_ANNOUNCEMENT must precede match executions
3. Both GAME_JOIN_ACK required before CHOOSE_PARITY_CALL
4. Both CHOOSE_PARITY_RESPONSE required before GAME_OVER
5. GAME_OVER must precede MATCH_RESULT_REPORT
6. MATCH_RESULT_REPORT must precede LEAGUE_STANDINGS_UPDATE
