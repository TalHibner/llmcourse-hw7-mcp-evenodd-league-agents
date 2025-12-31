# Performance Benchmarks

## Overview

The MCP Even/Odd League system includes a comprehensive performance benchmarking suite that measures the execution time and throughput of critical components.

## Running Benchmarks

### Basic Usage

```bash
# Run with default settings (1000 iterations)
python -m scripts.benchmark

# Run with custom iterations
python -m scripts.benchmark -i 5000

# Specify custom output file
python -m scripts.benchmark -o my_results.json
```

### Command-Line Options

- `-i, --iterations`: Number of iterations per benchmark (default: 1000)
- `-o, --output`: Output JSON file for results (default: benchmark_results.json)

## Benchmark Categories

### 1. JWT Authentication
Tests the performance of JWT token operations:
- **Token Generation**: Creating new JWT tokens for agents
- **Token Validation**: Verifying token signatures and claims
- **Access Verification**: Checking agent permissions

### 2. Message Processing
Measures Pydantic model serialization/deserialization:
- **Serialization**: Converting Pydantic models to JSON
- **Deserialization**: Parsing JSON to Pydantic models

### 3. Player Strategies
Benchmarks decision-making algorithms:
- **Random Strategy**: Random parity selection
- **Pattern Strategy**: Pattern-based opponent analysis

### 4. Game Logic
Tests core game simulation:
- **Game Simulation**: Full game round execution with winner determination

### 5. League Management
Measures league orchestration components:
- **Standings Calculation**: Updating player rankings after matches
- **Round-Robin Scheduler**: Generating match schedules

### 6. Data Persistence
Tests repository I/O operations:
- **Repository Write**: Saving data to disk
- **Repository Read**: Loading data from disk
- **Match Repository**: Creating match records

## Performance Results

### Summary (1000 iterations per benchmark)

| Component | Mean (ms) | Throughput (ops/s) |
|-----------|-----------|-------------------|
| **JWT Token Generation** | 0.033 | 30,755 |
| **JWT Token Validation** | 0.032 | 31,224 |
| **JWT Access Verification** | 0.028 | 35,549 |
| **Message Serialization** | 0.005 | 187,270 |
| **Message Deserialization** | 0.006 | 158,729 |
| **Random Strategy** | 0.001 | 1,187,963 |
| **Pattern Strategy** | 0.001 | 887,854 |
| **Game Simulation** | 0.007 | 136,610 |
| **Standings Calculation (10 players)** | 0.075 | 13,337 |
| **Round-Robin Scheduler (8 players)** | 0.125 | 7,973 |
| **Repository Write** | 0.632 | 1,583 |
| **Repository Read** | 0.044 | 22,701 |
| **Match Repository Create** | 0.417 | 2,401 |

### Key Insights

#### ✨ Excellent Performance
- **Strategy Execution**: Both random and pattern-based strategies execute in ~1 microsecond, enabling extremely fast decision-making
- **Message Processing**: Pydantic serialization/deserialization operates at 150K+ ops/sec, suitable for high-throughput scenarios
- **JWT Operations**: Token generation and validation at 30K+ ops/sec provides secure authentication without performance bottlenecks

#### ⚡ Good Performance
- **Game Simulation**: 136K games/sec throughput supports rapid match execution
- **Repository Read**: 22K reads/sec enables fast data retrieval
- **Standings Calculation**: 13K updates/sec handles frequent ranking updates efficiently

#### 🔧 I/O Bound Operations
- **Repository Write**: 1.6K writes/sec - typical for disk I/O operations
- **Match Repository Create**: 2.4K creates/sec - includes filesystem operations

### Performance Characteristics

#### CPU-Bound Operations (Low Latency)
- Strategy execution
- Game logic
- Message serialization
- JWT cryptographic operations

#### Memory-Bound Operations (Medium Latency)
- Standings calculation
- Scheduler generation

#### I/O-Bound Operations (Higher Latency)
- Repository writes
- Match record creation

## Scalability Analysis

### Concurrent Match Capacity

Based on benchmark results, the system can theoretically handle:

```
Game Simulation: 136,610 games/sec
Repository Write: 1,583 writes/sec (bottleneck)
```

**Bottleneck**: Repository writes limit maximum throughput to ~1,583 matches/sec with sequential I/O.

**Mitigation Strategies**:
1. Batch repository writes
2. Use async I/O
3. Implement write buffering
4. Cache frequently accessed data

### Multi-Player Tournament Performance

For a tournament with N players:
- **Match Count**: N × (N-1) / 2
- **Scheduler Time**: ~0.125ms for 8 players
- **Standings Updates**: ~0.075ms per match

**Example**: 8-player tournament (28 matches)
- Schedule generation: 0.125ms
- Match execution: 28 × 0.007ms = 0.196ms
- Standings updates: 28 × 0.075ms = 2.1ms
- Repository writes: 28 × 0.632ms = 17.7ms
- **Total estimated time**: ~20ms (excluding network latency)

## Continuous Performance Monitoring

### Regression Detection

Run benchmarks before and after changes:

```bash
# Before changes
python -m scripts.benchmark -o before.json

# After changes
python -m scripts.benchmark -o after.json

# Compare results
python scripts/compare_benchmarks.py before.json after.json
```

### Performance Targets

Maintain the following targets for optimal system performance:

| Component | Target | Status |
|-----------|--------|--------|
| JWT Operations | < 0.1ms | ✅ PASS (0.03ms) |
| Message Processing | < 0.01ms | ✅ PASS (0.005ms) |
| Strategy Execution | < 0.01ms | ✅ PASS (0.001ms) |
| Game Simulation | < 0.05ms | ✅ PASS (0.007ms) |
| Standings Update | < 0.2ms | ✅ PASS (0.075ms) |
| Repository Read | < 0.1ms | ✅ PASS (0.044ms) |
| Repository Write | < 2ms | ✅ PASS (0.632ms) |

## Optimization Recommendations

### High-Priority
1. **Batch Repository Writes**: Reduce I/O overhead by batching multiple writes
2. **Connection Pooling**: Reuse connections for MCP client calls
3. **Caching Layer**: Cache frequently accessed standings and match data

### Medium-Priority
1. **Async I/O**: Use async file operations for repository writes
2. **Lazy Loading**: Defer loading of non-critical data
3. **Compression**: Compress log files and archived match data

### Low-Priority
1. **Database Migration**: Consider moving from JSON files to SQLite for large tournaments
2. **Distributed Architecture**: Implement referee load balancing for massive scale
3. **Profiling**: Use cProfile to identify micro-optimizations

## Environment Details

Benchmarks were conducted on:
- **Platform**: Linux 6.6.87.2-microsoft-standard-WSL2
- **Python**: 3.12.3
- **Date**: December 31, 2025

## Interpreting Results

### Mean vs Median
- **Mean**: Average execution time (affected by outliers)
- **Median**: Middle value (more representative of typical performance)

### Standard Deviation
- **Low StdDev** (< 0.01ms): Consistent performance
- **High StdDev** (> 0.1ms): Variable performance, may indicate GC pauses or I/O contention

### Throughput
- **ops/sec**: Operations per second (1 / mean_time)
- Higher values indicate better performance

## Future Enhancements

1. **Load Testing**: Add benchmarks for concurrent multi-agent scenarios
2. **Memory Profiling**: Track memory usage during benchmarks
3. **Network Simulation**: Add latency to MCP client benchmarks
4. **Stress Testing**: Test behavior under resource constraints
5. **Comparison Tool**: Automated performance regression detection

---

*For questions or issues with benchmarking, please refer to the main README.md or open an issue.*
