"""
Referee FastAPI application.

Manages matches and enforces game rules.
"""

import asyncio
import os
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from SHARED.league_sdk.models import (
    RefereeRegisterRequest, RefereeMeta,
    GameJoinAck, ChooseParityResponse,
    MessageType
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.config_loader import get_config_loader
from SHARED.league_sdk.repositories import MatchRepository
from SHARED.league_sdk.mcp_client import MCPClient
from .handlers import RefereeHandlers
from .match_manager import MatchManager
from .game_logic import EvenOddGame


# Get configuration
referee_id = os.getenv("REFEREE_ID", "REF01")
port = int(os.getenv("PORT", 8001))

config_loader = get_config_loader()
system_config = config_loader.load_system()

# Initialize app
app = FastAPI(title=f"Referee {referee_id}")
logger = JsonLogger(f"referee:{referee_id}")
handlers = RefereeHandlers(logger)

# League ID
league_id = "league_2025_even_odd"
league_config = config_loader.load_league(league_id)

# Match repository
match_repo = MatchRepository(league_id)

# Game logic
game_logic = EvenOddGame(
    number_range_min=league_config.rules.number_range_min,
    number_range_max=league_config.rules.number_range_max,
    draw_on_both_wrong=league_config.rules.draw_on_both_wrong
)

# Registration state
registered = False
auth_token = ""


@app.on_event("startup")
async def startup_event():
    """Register with league manager on startup"""
    global registered, auth_token

    logger.info("REFEREE_STARTING", referee_id=referee_id, port=port)

    # Get league manager endpoint
    agents_config = config_loader.load_agents()
    league_manager_endpoint = agents_config.league_manager.endpoint

    # Create registration request
    my_endpoint = f"http://{system_config.network.base_host}:{port}/mcp"

    registration_request = RefereeRegisterRequest(
        sender=f"referee:{referee_id}",
        timestamp=datetime.now(timezone.utc),
        conversation_id=f"register_{referee_id}",
        referee_meta=RefereeMeta(
            display_name=f"Referee {referee_id}",
            version="1.0.0",
            game_types=["even_odd"],
            contact_endpoint=my_endpoint,
            max_concurrent_matches=2
        )
    )

    # Send registration
    try:
        async with MCPClient(logger=logger) as client:
            response = await client.call_tool(
                endpoint=league_manager_endpoint,
                method="register_referee",
                params=registration_request.model_dump()
            )

            auth_token = response.get("response", {}).get("auth_token", "")
            registered = True

            logger.info(
                "REGISTRATION_SUCCESS",
                referee_id=referee_id,
                league_id=league_id
            )
    except Exception as e:
        logger.error("REGISTRATION_FAILED", error=str(e))


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint for JSON-RPC communication.

    Handles:
    - GAME_JOIN_ACK
    - CHOOSE_PARITY_RESPONSE
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})

        logger.debug("MCP_REQUEST_RECEIVED", method=method)

        # Route based on message type
        message_type = params.get("message_type")

        if message_type == MessageType.GAME_JOIN_ACK:
            ack = GameJoinAck(**params)
            result = handlers.handle_game_join_ack(ack)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.CHOOSE_PARITY_RESPONSE:
            response = ChooseParityResponse(**params)
            result = handlers.handle_parity_response(response)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
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


@app.post("/admin/run_match")
async def run_match(
    match_id: str,
    round_id: str,
    player_a_id: str,
    player_b_id: str,
    player_a_endpoint: str,
    player_b_endpoint: str
):
    """
    Run a match (called by league manager or admin).

    Args:
        match_id: Match identifier
        round_id: Round identifier
        player_a_id: Player A's ID
        player_b_id: Player B's ID
        player_a_endpoint: Player A's endpoint
        player_b_endpoint: Player B's endpoint
    """
    logger.info(
        "MATCH_STARTING",
        match_id=match_id,
        player_a=player_a_id,
        player_b=player_b_id
    )

    # Get league manager endpoint
    agents_config = config_loader.load_agents()
    league_manager_endpoint = agents_config.league_manager.endpoint

    # Create match manager
    match_manager = MatchManager(
        match_id=match_id,
        round_id=round_id,
        league_id=league_id,
        referee_id=referee_id,
        player_a_id=player_a_id,
        player_b_id=player_b_id,
        player_a_endpoint=player_a_endpoint,
        player_b_endpoint=player_b_endpoint,
        league_manager_endpoint=league_manager_endpoint,
        logger=logger,
        match_repo=match_repo,
        game_logic=game_logic,
        join_timeout_sec=system_config.timeouts.game_join_ack_timeout_sec,
        move_timeout_sec=system_config.timeouts.move_timeout_sec
    )

    # Register match
    handlers.register_match(match_id, match_manager)

    # Run match in background
    asyncio.create_task(_run_match_task(match_id, match_manager))

    return {"status": "started", "match_id": match_id}


async def _run_match_task(match_id: str, match_manager: MatchManager):
    """Background task to run match"""
    try:
        await match_manager.run_match()
    finally:
        handlers.unregister_match(match_id)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "referee_id": referee_id,
        "registered": registered
    }


if __name__ == "__main__":
    logger.info("REFEREE_STARTING", referee_id=referee_id, port=port)
    uvicorn.run(app, host="0.0.0.0", port=port)
