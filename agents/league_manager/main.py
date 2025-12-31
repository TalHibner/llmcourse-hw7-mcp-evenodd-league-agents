"""
League Manager FastAPI application.

Central orchestrator for the league system.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx

from SHARED.league_sdk.models import (
    RefereeRegisterRequest, LeagueRegisterRequest,
    MatchResultReport, RoundAnnouncement, RoundCompleted,
    LeagueCompleted, MessageType
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.config_loader import get_config_loader
from SHARED.league_sdk.repositories import StandingsRepository, RoundsRepository
from SHARED.league_sdk.mcp_client import MCPClient
from .handlers import RegistrationHandler, ResultHandler
from .scheduler import RoundRobinScheduler
from .standings import StandingsCalculator


# Global state
app = FastAPI(title="League Manager")
league_id = "league_2025_even_odd"
logger = JsonLogger("league_manager", league_id)

# Handlers
registration_handler = RegistrationHandler(league_id, logger)
standings_calculator = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)
standings_repo = StandingsRepository(league_id)
rounds_repo = RoundsRepository(league_id)
result_handler = ResultHandler(
    league_id, logger, standings_calculator, standings_repo, rounds_repo
)

# League state
league_started = False
current_round_index = 0
match_schedule = []


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint for JSON-RPC communication.

    Handles:
    - REFEREE_REGISTER_REQUEST
    - LEAGUE_REGISTER_REQUEST
    - MATCH_RESULT_REPORT
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})

        logger.debug("MCP_REQUEST_RECEIVED", method=method)

        # Route based on message type
        message_type = params.get("message_type")

        if message_type == MessageType.REFEREE_REGISTER_REQUEST:
            req = RefereeRegisterRequest(**params)
            response = registration_handler.handle_referee_registration(req)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {"status": "success", "response": response.model_dump()},
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.LEAGUE_REGISTER_REQUEST:
            req = LeagueRegisterRequest(**params)
            response = registration_handler.handle_player_registration(req)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {"status": "success", "response": response.model_dump()},
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.MATCH_RESULT_REPORT:
            report = MatchResultReport(**params)

            # Get player endpoints
            player_endpoints = {
                pid: info["endpoint"]
                for pid, info in registration_handler.registered_players.items()
            }

            await result_handler.handle_match_result(report, player_endpoints)

            # Check if round is complete
            await check_round_completion()

            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {"status": "success"},
                "id": body.get("id", 1)
            })

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Unknown message type: {message_type}"},
                "id": body.get("id", 1)
            }, status_code=400)

    except Exception as e:
        logger.error("MCP_REQUEST_ERROR", error=str(e))
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": body.get("id", 1)
        }, status_code=500)


@app.post("/admin/start_league")
async def start_league():
    """Start the league (admin endpoint)"""
    global league_started, match_schedule

    if league_started:
        return {"error": "League already started"}

    logger.info("LEAGUE_STARTING")

    # Get registered players
    player_ids = list(registration_handler.registered_players.keys())
    player_names = {
        pid: info["display_name"]
        for pid, info in registration_handler.registered_players.items()
    }

    if len(player_ids) < 2:
        return {"error": "Not enough players registered"}

    # Initialize standings
    initial_standings = standings_calculator.initialize_standings(
        player_ids, player_names
    )
    standings_repo.update_standings(initial_standings)

    # Generate match schedule
    referee_ids = list(registration_handler.registered_referees.keys())
    scheduler = RoundRobinScheduler(player_ids, referee_ids)
    match_schedule = scheduler.generate_schedule()

    logger.info(
        "SCHEDULE_GENERATED",
        total_rounds=len(match_schedule),
        total_matches=sum(len(r) for r in match_schedule)
    )

    league_started = True

    # Start first round
    await announce_round(0)

    return {
        "status": "started",
        "league_id": league_id,
        "total_players": len(player_ids),
        "total_rounds": len(match_schedule),
        "total_matches": sum(len(r) for r in match_schedule)
    }


async def announce_round(round_index: int):
    """Announce a new round to all players"""
    global current_round_index

    if round_index >= len(match_schedule):
        await complete_league()
        return

    current_round_index = round_index
    round_matches = match_schedule[round_index]
    round_id = f"R{round_index + 1}"

    # Save round to repository
    rounds_repo.add_round(round_id, round_matches)

    # Create announcement
    announcement = RoundAnnouncement(
        sender="league_manager:LEAGUE_MANAGER_01",
        timestamp=datetime.now(timezone.utc),
        conversation_id=f"round_{round_id}",
        auth_token="",
        round_id=round_id,
        league_id=league_id,
        matches=round_matches
    )

    # Broadcast to all players
    player_endpoints = {
        pid: info["endpoint"]
        for pid, info in registration_handler.registered_players.items()
    }

    async with MCPClient(logger=logger) as client:
        tasks = []
        for player_id, endpoint in player_endpoints.items():
            task = client.call_tool(
                endpoint=endpoint,
                method="receive_round_announcement",
                params=announcement.model_dump()
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(
        "ROUND_ANNOUNCED",
        round_id=round_id,
        num_matches=len(round_matches)
    )

    # Start matches by calling referees
    await start_matches(round_id, round_matches)


async def start_matches(round_id: str, matches: List[MatchInfo]):
    """Start all matches in a round by calling referees"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        for match in matches:
            # Extract referee endpoint and ID from match
            referee_endpoint = match.referee_endpoint.replace("/mcp", "")

            # Get player endpoints
            player_a_endpoint = registration_handler.registered_players[match.player_A_id]["endpoint"]
            player_b_endpoint = registration_handler.registered_players[match.player_B_id]["endpoint"]

            # Call referee to start match
            try:
                response = await client.post(
                    f"{referee_endpoint}/admin/run_match",
                    params={
                        "match_id": match.match_id,
                        "round_id": round_id,
                        "player_a_id": match.player_A_id,
                        "player_b_id": match.player_B_id,
                        "player_a_endpoint": player_a_endpoint,
                        "player_b_endpoint": player_b_endpoint
                    }
                )
                response.raise_for_status()
                logger.info("MATCH_STARTED", match_id=match.match_id)
            except Exception as e:
                logger.error("MATCH_START_FAILED", match_id=match.match_id, error=str(e))


async def check_round_completion():
    """Check if current round is complete and start next round"""
    round_id = f"R{current_round_index + 1}"
    round_data = rounds_repo.get_round(round_id)

    if not round_data:
        return

    total_matches = len(round_data["matches"])
    completed_matches = len(round_data["completed_matches"])

    if completed_matches >= total_matches:
        # Round is complete
        rounds_repo.mark_round_completed(round_id)
        standings_repo.increment_rounds_completed()

        logger.info("ROUND_COMPLETED", round_id=round_id)

        # Notify all players
        player_endpoints = {
            pid: info["endpoint"]
            for pid, info in registration_handler.registered_players.items()
        }

        next_round_id = None
        if current_round_index + 1 < len(match_schedule):
            next_round_id = f"R{current_round_index + 2}"

        round_completed_msg = RoundCompleted(
            sender="league_manager:LEAGUE_MANAGER_01",
            timestamp=datetime.now(timezone.utc),
            conversation_id=f"round_complete_{round_id}",
            auth_token="",
            round_id=round_id,
            league_id=league_id,
            completed_matches=round_data["completed_matches"],
            next_round_id=next_round_id
        )

        async with MCPClient(logger=logger) as client:
            tasks = []
            for endpoint in player_endpoints.values():
                task = client.call_tool(
                    endpoint=endpoint,
                    method="receive_round_completed",
                    params=round_completed_msg.model_dump()
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        # Start next round
        await asyncio.sleep(2)  # Brief delay between rounds
        await announce_round(current_round_index + 1)


async def complete_league():
    """Complete the league and announce winner"""
    logger.info("LEAGUE_COMPLETING")

    standings = standings_repo.get_standings()
    champion = standings_calculator.get_champion(standings)

    total_matches = sum(len(r) for r in match_schedule)

    completion_msg = LeagueCompleted(
        sender="league_manager:LEAGUE_MANAGER_01",
        timestamp=datetime.now(timezone.utc),
        conversation_id="league_complete",
        auth_token="",
        league_id=league_id,
        champion=champion,
        final_standings=standings,
        total_rounds=len(match_schedule),
        total_matches=total_matches
    )

    # Broadcast to all players
    player_endpoints = {
        pid: info["endpoint"]
        for pid, info in registration_handler.registered_players.items()
    }

    async with MCPClient(logger=logger) as client:
        tasks = []
        for endpoint in player_endpoints.values():
            task = client.call_tool(
                endpoint=endpoint,
                method="receive_league_completed",
                params=completion_msg.model_dump()
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(
        "LEAGUE_COMPLETED",
        champion=champion.player_id,
        total_rounds=len(match_schedule),
        total_matches=total_matches
    )


@app.get("/admin/standings")
async def get_standings():
    """Get current standings"""
    standings = standings_repo.get_standings()
    return {"standings": [s.model_dump() for s in standings]}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "league_id": league_id}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info("LEAGUE_MANAGER_STARTING", port=port)
    uvicorn.run(app, host="0.0.0.0", port=port)
