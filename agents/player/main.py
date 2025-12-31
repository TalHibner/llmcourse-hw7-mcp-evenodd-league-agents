"""
Player FastAPI application.

Implements a player agent that participates in matches.
"""

import os
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from SHARED.league_sdk.models import (
    LeagueRegisterRequest, PlayerMeta,
    RoundAnnouncement, GameInvitation, ChooseParityCall,
    GameOver, LeagueStandingsUpdate, RoundCompleted,
    LeagueCompleted, MessageType
)
from SHARED.league_sdk.logger import JsonLogger
from SHARED.league_sdk.config_loader import get_config_loader
from SHARED.league_sdk.mcp_client import MCPClient
from .handlers import PlayerHandlers


# Get configuration
player_id = os.getenv("PLAYER_ID", "P01")
port = int(os.getenv("PORT", 8101))
strategy = os.getenv("STRATEGY", "random")

config_loader = get_config_loader()
system_config = config_loader.load_system()

# Initialize app
app = FastAPI(title=f"Player {player_id}")
logger = JsonLogger(f"player:{player_id}")

# Get player config
player_config = config_loader.get_player_by_id(player_id)
if player_config:
    display_name = player_config.display_name
    strategy = player_config.strategy
else:
    display_name = f"Player {player_id}"

# Handlers
handlers = PlayerHandlers(player_id, display_name, strategy, logger)

# Registration state
registered = False
auth_token = ""
league_id = "league_2025_even_odd"


@app.on_event("startup")
async def startup_event():
    """Register with league manager on startup"""
    global registered, auth_token

    logger.info("PLAYER_STARTING", player_id=player_id, port=port, strategy=strategy)

    # Get league manager endpoint
    agents_config = config_loader.load_agents()
    league_manager_endpoint = agents_config.league_manager.endpoint

    # Create registration request
    my_endpoint = f"http://{system_config.network.base_host}:{port}/mcp"

    registration_request = LeagueRegisterRequest(
        sender=f"player:{player_id}",
        timestamp=datetime.now(timezone.utc),
        conversation_id=f"register_{player_id}",
        player_meta=PlayerMeta(
            display_name=display_name,
            version="1.0.0",
            game_types=["even_odd"],
            contact_endpoint=my_endpoint
        )
    )

    # Send registration
    try:
        async with MCPClient(logger=logger) as client:
            response = await client.call_tool(
                endpoint=league_manager_endpoint,
                method="register_player",
                params=registration_request.model_dump()
            )

            auth_token = response.get("response", {}).get("auth_token", "")
            registered = True

            logger.info(
                "REGISTRATION_SUCCESS",
                player_id=player_id,
                league_id=league_id
            )
    except Exception as e:
        logger.error("REGISTRATION_FAILED", error=str(e))


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint for JSON-RPC communication.

    Handles all player messages.
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})

        logger.debug("MCP_REQUEST_RECEIVED", method=method)

        # Route based on message type
        message_type = params.get("message_type")

        if message_type == MessageType.ROUND_ANNOUNCEMENT:
            announcement = RoundAnnouncement(**params)
            result = handlers.handle_round_announcement(announcement)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.GAME_INVITATION:
            invitation = GameInvitation(**params)
            result = await handlers.handle_game_invitation(invitation)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.CHOOSE_PARITY_CALL:
            call = ChooseParityCall(**params)
            result = await handlers.handle_parity_call(call)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.GAME_OVER:
            game_over = GameOver(**params)
            result = handlers.handle_game_over(game_over)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.LEAGUE_STANDINGS_UPDATE:
            update = LeagueStandingsUpdate(**params)
            result = handlers.handle_standings_update(update)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.ROUND_COMPLETED:
            completed = RoundCompleted(**params)
            result = handlers.handle_round_completed(completed)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": body.get("id", 1)
            })

        elif message_type == MessageType.LEAGUE_COMPLETED:
            completed = LeagueCompleted(**params)
            result = handlers.handle_league_completed(completed)
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


@app.get("/admin/stats")
async def get_stats():
    """Get player statistics"""
    return handlers.get_stats()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "player_id": player_id,
        "registered": registered,
        "strategy": strategy
    }


if __name__ == "__main__":
    logger.info("PLAYER_STARTING", player_id=player_id, port=port)
    uvicorn.run(app, host="0.0.0.0", port=port)
