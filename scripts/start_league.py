"""
Automated startup script for the MCP Even/Odd League.

Starts all agents in the correct order and manages the league lifecycle.
"""

import asyncio
import subprocess
import time
import sys
import httpx
from pathlib import Path


class LeagueStarter:
    """Manages league startup and lifecycle"""

    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent.parent

    async def check_service(self, url: str, service_name: str, max_retries: int = 30) -> bool:
        """
        Check if a service is ready.

        Args:
            url: Service health endpoint URL
            service_name: Service name for logging
            max_retries: Maximum retry attempts

        Returns:
            True if service is ready, False otherwise
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            for i in range(max_retries):
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        print(f"✓ {service_name} is ready")
                        return True
                except Exception:
                    pass

                if i < max_retries - 1:
                    await asyncio.sleep(1)

        print(f"✗ {service_name} failed to start")
        return False

    def start_process(self, command: list, service_name: str, env: dict = None) -> subprocess.Popen:
        """
        Start a process.

        Args:
            command: Command to run
            service_name: Service name for logging
            env: Environment variables

        Returns:
            Process handle
        """
        print(f"Starting {service_name}...")

        import os
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        process = subprocess.Popen(
            command,
            cwd=self.base_dir,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.processes.append((service_name, process))
        return process

    async def start_league_manager(self) -> bool:
        """Start League Manager"""
        self.start_process(
            ["python", "-m", "agents.league_manager.main"],
            "League Manager",
            {"PORT": "8000"}
        )

        # Wait for it to be ready
        return await self.check_service(
            "http://localhost:8000/health",
            "League Manager"
        )

    async def start_referees(self) -> bool:
        """Start all referees"""
        referees = [
            ("REF01", 8001),
            ("REF02", 8002)
        ]

        for ref_id, port in referees:
            self.start_process(
                ["python", "-m", "agents.referee.main"],
                f"Referee {ref_id}",
                {"REFEREE_ID": ref_id, "PORT": str(port)}
            )

        # Wait for all referees to be ready
        await asyncio.sleep(2)  # Give them time to start

        for ref_id, port in referees:
            ready = await self.check_service(
                f"http://localhost:{port}/health",
                f"Referee {ref_id}"
            )
            if not ready:
                return False

        return True

    async def start_players(self) -> bool:
        """Start all players"""
        players = [
            ("P01", 8101, "random"),
            ("P02", 8102, "pattern_based"),
            ("P03", 8103, "random"),
            ("P04", 8104, "random")
        ]

        for player_id, port, strategy in players:
            self.start_process(
                ["python", "-m", "agents.player.main"],
                f"Player {player_id}",
                {
                    "PLAYER_ID": player_id,
                    "PORT": str(port),
                    "STRATEGY": strategy
                }
            )

        # Wait for all players to be ready
        await asyncio.sleep(2)  # Give them time to start

        for player_id, port, _ in players:
            ready = await self.check_service(
                f"http://localhost:{port}/health",
                f"Player {player_id}"
            )
            if not ready:
                return False

        return True

    async def start_league(self) -> bool:
        """Trigger league start"""
        print("\nWaiting for registrations to complete...")
        await asyncio.sleep(3)

        print("Starting the league...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post("http://localhost:8000/admin/start_league")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ League started successfully!")
                    print(f"  Players: {result['total_players']}")
                    print(f"  Rounds: {result['total_rounds']}")
                    print(f"  Matches: {result['total_matches']}")
                    return True
                else:
                    print(f"✗ Failed to start league: {response.text}")
                    return False
            except Exception as e:
                print(f"✗ Failed to start league: {e}")
                return False

    async def monitor_league(self):
        """Monitor league progress"""
        print("\nMonitoring league progress...")
        print("Press Ctrl+C to stop monitoring and shut down all services\n")

        async with httpx.AsyncClient(timeout=10.0) as client:
            last_standings = None

            while True:
                try:
                    # Get current standings
                    response = await client.get("http://localhost:8000/admin/standings")
                    if response.status_code == 200:
                        standings_data = response.json()
                        standings = standings_data.get("standings", [])

                        # Only print if standings changed
                        if standings != last_standings:
                            print("\nCurrent Standings:")
                            print("-" * 60)
                            for s in standings:
                                print(
                                    f"  {s['rank']}. {s['display_name']:20} - "
                                    f"{s['points']:2} pts  "
                                    f"({s['wins']}W/{s['draws']}D/{s['losses']}L)"
                                )
                            last_standings = standings

                    await asyncio.sleep(5)

                except KeyboardInterrupt:
                    print("\nShutting down...")
                    break
                except Exception as e:
                    # Service might be down
                    await asyncio.sleep(5)

    def cleanup(self):
        """Stop all processes"""
        print("\nStopping all services...")
        for service_name, process in reversed(self.processes):
            print(f"  Stopping {service_name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("✓ All services stopped")

    async def run(self):
        """Run the complete startup sequence"""
        try:
            print("=" * 60)
            print("MCP EVEN/ODD LEAGUE - AUTOMATED STARTUP")
            print("=" * 60)
            print()

            # Start in order
            if not await self.start_league_manager():
                print("Failed to start League Manager")
                return False

            if not await self.start_referees():
                print("Failed to start Referees")
                return False

            if not await self.start_players():
                print("Failed to start Players")
                return False

            if not await self.start_league():
                print("Failed to start league")
                return False

            # Monitor progress
            await self.monitor_league()

            return True

        except KeyboardInterrupt:
            print("\nInterrupted by user")
            return True

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.cleanup()


async def main():
    """Main entry point"""
    starter = LeagueStarter()
    success = await starter.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
