"""
Integration test for the complete league system.

Tests the full lifecycle: registration, rounds, matches, and completion.
"""

import asyncio
import httpx
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_full_league_lifecycle():
    """
    Test complete league lifecycle.

    This test assumes all agents are running:
    - League Manager on port 8000
    - Referees on ports 8001-8002
    - Players on ports 8101-8104
    """

    # Base URLs
    league_manager_url = "http://localhost:8000"

    # Wait for all services to be ready
    await asyncio.sleep(2)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check league manager health
        response = await client.get(f"{league_manager_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Check initial standings (should be empty before league starts)
        response = await client.get(f"{league_manager_url}/admin/standings")
        assert response.status_code == 200

        # Start the league
        response = await client.post(f"{league_manager_url}/admin/start_league")
        assert response.status_code == 200
        result = response.json()

        assert result["status"] == "started"
        assert result["total_players"] >= 2
        assert result["total_rounds"] > 0

        print(f"League started with {result['total_players']} players")
        print(f"Total rounds: {result['total_rounds']}")
        print(f"Total matches: {result['total_matches']}")

        # Wait for league to complete (approximate)
        # Each round takes ~40 seconds (5s join + 30s move + delays)
        estimated_duration = result['total_rounds'] * 45
        print(f"Waiting ~{estimated_duration}s for league to complete...")

        await asyncio.sleep(estimated_duration)

        # Check final standings
        response = await client.get(f"{league_manager_url}/admin/standings")
        assert response.status_code == 200

        standings_data = response.json()
        standings = standings_data.get("standings", [])

        assert len(standings) > 0, "Standings should not be empty"

        # Verify standings are sorted by rank
        for i in range(len(standings) - 1):
            assert standings[i]["rank"] <= standings[i + 1]["rank"]

        # Print final standings
        print("\nFinal Standings:")
        print("-" * 60)
        for standing in standings:
            print(
                f"Rank {standing['rank']}: {standing['display_name']} - "
                f"{standing['points']} points "
                f"({standing['wins']}W / {standing['draws']}D / {standing['losses']}L)"
            )

        # Verify champion
        champion = standings[0]
        assert champion["rank"] == 1
        print(f"\nChampion: {champion['display_name']} with {champion['points']} points!")


@pytest.mark.asyncio
async def test_player_stats():
    """Test player statistics endpoints"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check a few players
        for port in [8101, 8102, 8103, 8104]:
            response = await client.get(f"http://localhost:{port}/admin/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"\nPlayer stats (port {port}):")
                print(f"  Matches: {stats.get('total_matches', 0)}")
                print(f"  Wins: {stats.get('wins', 0)}")
                print(f"  Points: {stats.get('total_points', 0)}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_full_league_lifecycle())
