#!/bin/bash
# Startup Commands for MCP Even/Odd League System
# Section 8.2 - System Startup Order

# Port Allocation:
# - 8000: League Manager
# - 8001: Referee REF01
# - 8002: Referee REF02
# - 8101-8104: Players P01-P04

# CRITICAL: Start in this exact order!
# 1. League Manager (must start first)
# 2. Referees (register to league manager)
# 3. Players (register to league manager)
# 4. League starts only after all registrations complete

echo "=== MCP League System Startup ==="
echo ""
echo "Open 7 terminals and run these commands in order:"
echo ""

echo "Terminal 1 - League Manager:"
echo "python league_manager.py  # Listening on :8000"
echo ""

echo "Terminal 2 - Referee Alpha:"
echo "python referee.py --port 8001"
echo ""

echo "Terminal 3 - Referee Beta:"
echo "python referee.py --port 8002"
echo ""

echo "Terminal 4 - Player P01:"
echo "python player.py --port 8101"
echo ""

echo "Terminal 5 - Player P02:"
echo "python player.py --port 8102"
echo ""

echo "Terminal 6 - Player P03:"
echo "python player.py --port 8103"
echo ""

echo "Terminal 7 - Player P04:"
echo "python player.py --port 8104"
echo ""

echo "=== Endpoints ==="
echo "League Manager: http://localhost:8000/mcp"
echo "Referee REF01:  http://localhost:8001/mcp"
echo "Referee REF02:  http://localhost:8002/mcp"
echo "Player P01:     http://localhost:8101/mcp"
echo "Player P02:     http://localhost:8102/mcp"
echo "Player P03:     http://localhost:8103/mcp"
echo "Player P04:     http://localhost:8104/mcp"
