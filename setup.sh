#!/bin/bash
# Setup script for MCP Even/Odd League system

echo "Setting up MCP Even/Odd League system..."
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

echo "Python version:"
python3 --version
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo
echo "Setup complete!"
echo
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo
echo "To start the league system:"
echo "  python scripts/start_league.py"
echo
echo "Or to run manually, start each component in separate terminals:"
echo "  python -m agents.league_manager.main"
echo "  REFEREE_ID=REF01 PORT=8001 python -m agents.referee.main"
echo "  PLAYER_ID=P01 PORT=8101 python -m agents.player.main"
echo
