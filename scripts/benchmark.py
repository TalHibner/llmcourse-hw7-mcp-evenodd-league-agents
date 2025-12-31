"""
Performance Benchmarking Script for MCP Even/Odd League System.

Measures performance of various components:
- JWT token generation and validation
- Message serialization/deserialization
- Strategy execution
- Repository operations
- Game simulation
- Standings calculation
"""

import time
import statistics
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Callable, Any
import json

# Import components to benchmark
from SHARED.league_sdk.auth import JWTAuthenticator
from SHARED.league_sdk.models import (
    GameInvitation, ChooseParityCall, GameResult, GameStatus,
    ParityChoice, StandingEntry, MatchResultReport
)
from SHARED.league_sdk.repositories import (
    StandingsRepository, RoundsRepository, MatchRepository
)
from SHARED.league_sdk.logger import JsonLogger
from agents.player.strategy import RandomStrategy, PatternBasedStrategy
from agents.referee.game_logic import EvenOddGame
from agents.league_manager.scheduler import RoundRobinScheduler
from agents.league_manager.standings import StandingsCalculator


class BenchmarkResult:
    """Store benchmark results"""

    def __init__(self, name: str, iterations: int):
        self.name = name
        self.iterations = iterations
        self.times: List[float] = []

    def add_time(self, elapsed: float):
        """Add a timing measurement"""
        self.times.append(elapsed)

    @property
    def mean(self) -> float:
        """Mean execution time"""
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def median(self) -> float:
        """Median execution time"""
        return statistics.median(self.times) if self.times else 0.0

    @property
    def stdev(self) -> float:
        """Standard deviation"""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def min_time(self) -> float:
        """Minimum execution time"""
        return min(self.times) if self.times else 0.0

    @property
    def max_time(self) -> float:
        """Maximum execution time"""
        return max(self.times) if self.times else 0.0

    @property
    def throughput(self) -> float:
        """Operations per second"""
        return 1.0 / self.mean if self.mean > 0 else 0.0

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": self.mean * 1000,
            "median_ms": self.median * 1000,
            "stdev_ms": self.stdev * 1000,
            "min_ms": self.min_time * 1000,
            "max_ms": self.max_time * 1000,
            "throughput_ops_per_sec": self.throughput
        }


class PerformanceBenchmark:
    """Performance benchmarking suite"""

    def __init__(self, iterations: int = 1000):
        """
        Initialize benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = None
    ) -> BenchmarkResult:
        """
        Run a benchmark test.

        Args:
            name: Name of the benchmark
            func: Function to benchmark (no arguments)
            iterations: Number of iterations (default: self.iterations)

        Returns:
            BenchmarkResult with timing statistics
        """
        iterations = iterations or self.iterations
        result = BenchmarkResult(name, iterations)

        print(f"Running benchmark: {name} ({iterations} iterations)...", end=" ", flush=True)

        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = time.perf_counter() - start
            result.add_time(elapsed)

        print(f"✓ (mean: {result.mean * 1000:.3f}ms)")

        self.results.append(result)
        return result

    def benchmark_jwt_generation(self):
        """Benchmark JWT token generation"""
        auth = JWTAuthenticator()

        def generate():
            auth.generate_token(
                agent_id="P01",
                league_id="LEAGUE01",
                agent_type="player"
            )

        self.run_benchmark("JWT Token Generation", generate)

    def benchmark_jwt_validation(self):
        """Benchmark JWT token validation"""
        auth = JWTAuthenticator()
        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        def validate():
            auth.validate_token(token)

        self.run_benchmark("JWT Token Validation", validate)

    def benchmark_jwt_access_verification(self):
        """Benchmark JWT access verification"""
        auth = JWTAuthenticator()
        token = auth.generate_token(
            agent_id="P01",
            league_id="LEAGUE01",
            agent_type="player"
        )

        def verify():
            auth.verify_agent_access(
                token=token,
                required_agent_id="P01",
                required_league_id="LEAGUE01"
            )

        self.run_benchmark("JWT Access Verification", verify)

    def benchmark_message_serialization(self):
        """Benchmark message serialization"""
        invitation = GameInvitation(
            sender="referee:REF01",
            timestamp=datetime.now(timezone.utc),
            conversation_id="CONV123",
            auth_token="token123",
            match_id="R01M01",
            opponent_id="P02",
            role_in_match="PLAYER_A"
        )

        def serialize():
            invitation.model_dump_json()

        self.run_benchmark("Message Serialization (Pydantic)", serialize)

    def benchmark_message_deserialization(self):
        """Benchmark message deserialization"""
        data = {
            "sender": "referee:REF01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation_id": "CONV123",
            "auth_token": "token123",
            "match_id": "R01M01",
            "opponent_id": "P02",
            "role_in_match": "PLAYER_A"
        }
        json_str = json.dumps(data)

        def deserialize():
            GameInvitation.model_validate_json(json_str)

        self.run_benchmark("Message Deserialization (Pydantic)", deserialize)

    def benchmark_random_strategy(self):
        """Benchmark random strategy execution"""
        strategy = RandomStrategy()

        def choose():
            strategy.choose("P02", [])

        self.run_benchmark("Random Strategy Choice", choose, iterations=10000)

    def benchmark_pattern_strategy(self):
        """Benchmark pattern-based strategy"""
        strategy = PatternBasedStrategy(threshold=0.6)
        history = [
            {"opponent_choice": "even", "result": "WIN"},
            {"opponent_choice": "odd", "result": "LOSS"},
            {"opponent_choice": "even", "result": "WIN"},
        ]

        def choose():
            strategy.choose("P02", history)

        self.run_benchmark("Pattern Strategy Choice", choose, iterations=10000)

    def benchmark_game_simulation(self):
        """Benchmark full game simulation"""
        game = EvenOddGame()

        def simulate():
            game.determine_winner(
                "P01", "P02",
                ParityChoice.EVEN,
                ParityChoice.ODD,
                drawn_number=4
            )

        self.run_benchmark("Game Simulation", simulate, iterations=10000)

    def benchmark_standings_calculation(self):
        """Benchmark standings calculation"""
        calculator = StandingsCalculator()
        current_standings = [
            StandingEntry(
                rank=i,
                player_id=f"P{i:02d}",
                display_name=f"Player {i}",
                played=10,
                wins=5,
                draws=3,
                losses=2,
                points=18
            )
            for i in range(1, 11)
        ]

        match_result = {
            "status": GameStatus.WIN,
            "score": {"P01": 3, "P02": 0}
        }

        def update():
            calculator.update_standings(current_standings, match_result)

        self.run_benchmark("Standings Calculation (10 players)", update, iterations=5000)

    def benchmark_scheduler(self):
        """Benchmark round-robin scheduler"""
        players = [f"P{i:02d}" for i in range(1, 9)]
        referees = ["REF01", "REF02"]

        def schedule():
            scheduler = RoundRobinScheduler(players, referees)
            scheduler.generate_schedule()

        self.run_benchmark("Round-Robin Scheduler (8 players)", schedule, iterations=1000)

    def benchmark_repository_operations(self):
        """Benchmark repository write operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = StandingsRepository(league_id="bench", data_dir=Path(tmpdir))
            standings = [
                StandingEntry(
                    rank=1,
                    player_id="P01",
                    display_name="Player 1",
                    played=0,
                    wins=0,
                    draws=0,
                    losses=0,
                    points=0
                )
            ]

            def save():
                repo.update_standings(standings)

            self.run_benchmark("Repository Write (Standings)", save, iterations=1000)

    def benchmark_repository_read(self):
        """Benchmark repository read operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = StandingsRepository(league_id="bench", data_dir=Path(tmpdir))
            standings = [
                StandingEntry(
                    rank=1,
                    player_id="P01",
                    display_name="Player 1",
                    played=0,
                    wins=0,
                    draws=0,
                    losses=0,
                    points=0
                )
            ]
            repo.update_standings(standings)

            def load():
                repo.get_standings()

            self.run_benchmark("Repository Read (Standings)", load, iterations=1000)

    def benchmark_match_repository(self):
        """Benchmark match repository operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = MatchRepository(league_id="bench", data_dir=Path(tmpdir))

            def create():
                repo.create_match(
                    match_id=f"M{time.time_ns()}",
                    round_id="R01",
                    league_id="bench",
                    referee_id="REF01",
                    player_a_id="P01",
                    player_b_id="P02"
                )

            self.run_benchmark("Match Repository Create", create, iterations=500)

    def run_all(self):
        """Run all benchmarks"""
        print("\n" + "=" * 70)
        print("MCP Even/Odd League - Performance Benchmark Suite")
        print("=" * 70 + "\n")

        # JWT Authentication Benchmarks
        print("Category: JWT Authentication")
        print("-" * 70)
        self.benchmark_jwt_generation()
        self.benchmark_jwt_validation()
        self.benchmark_jwt_access_verification()

        # Message Processing Benchmarks
        print("\nCategory: Message Processing")
        print("-" * 70)
        self.benchmark_message_serialization()
        self.benchmark_message_deserialization()

        # Strategy Benchmarks
        print("\nCategory: Player Strategies")
        print("-" * 70)
        self.benchmark_random_strategy()
        self.benchmark_pattern_strategy()

        # Game Logic Benchmarks
        print("\nCategory: Game Logic")
        print("-" * 70)
        self.benchmark_game_simulation()

        # League Management Benchmarks
        print("\nCategory: League Management")
        print("-" * 70)
        self.benchmark_standings_calculation()
        self.benchmark_scheduler()

        # Repository Benchmarks
        print("\nCategory: Data Persistence")
        print("-" * 70)
        self.benchmark_repository_operations()
        self.benchmark_repository_read()
        self.benchmark_match_repository()

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 70)
        print("Benchmark Summary")
        print("=" * 70 + "\n")

        # Print table header
        print(f"{'Benchmark':<40} {'Mean (ms)':<12} {'Throughput (ops/s)':<20}")
        print("-" * 70)

        # Print results
        for result in self.results:
            print(f"{result.name:<40} {result.mean * 1000:>10.3f}  {result.throughput:>18.1f}")

        print("\n" + "=" * 70)
        print("Detailed Statistics")
        print("=" * 70 + "\n")

        for result in self.results:
            summary = result.summary()
            print(f"\n{summary['name']}:")
            print(f"  Iterations:  {summary['iterations']}")
            print(f"  Mean:        {summary['mean_ms']:.3f} ms")
            print(f"  Median:      {summary['median_ms']:.3f} ms")
            print(f"  Std Dev:     {summary['stdev_ms']:.3f} ms")
            print(f"  Min:         {summary['min_ms']:.3f} ms")
            print(f"  Max:         {summary['max_ms']:.3f} ms")
            print(f"  Throughput:  {summary['throughput_ops_per_sec']:.1f} ops/sec")

    def export_results(self, filename: str = "benchmark_results.json"):
        """Export results to JSON file"""
        results_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iterations": self.iterations,
            "benchmarks": [result.summary() for result in self.results]
        }

        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\nResults exported to: {filename}")


def main():
    """Run benchmark suite"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP League Performance Benchmarks")
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=1000,
        help="Number of iterations per benchmark (default: 1000)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file for results (default: benchmark_results.json)"
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = PerformanceBenchmark(iterations=args.iterations)
    benchmark.run_all()
    benchmark.print_summary()
    benchmark.export_results(args.output)

    print("\n✓ Benchmark suite completed successfully!")


if __name__ == "__main__":
    main()
