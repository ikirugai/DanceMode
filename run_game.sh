#!/bin/bash
# DanceMode Launcher Script
# Run this script to start the game

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}"
echo "  ____                        __  __           _      _ "
echo " |  _ \  __ _ _ __   ___ ___|  \/  | ___   __| | ___| |"
echo " | | | |/ _\` | '_ \ / __/ _ \ |\/| |/ _ \ / _\` |/ _ \ |"
echo " | |_| | (_| | | | | (_|  __/ |  | | (_) | (_| |  __/_|"
echo " |____/ \__,_|_| |_|\___\___|_|  |_|\___/ \__,_|\___(_)"
echo -e "${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo -e "${GREEN}Python 3 found: $(python3 --version)${NC}"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies${NC}"
    echo "Try running: pip install pygame opencv-python mediapipe numpy"
    exit 1
fi

echo -e "${GREEN}All dependencies installed!${NC}"
echo ""
echo -e "${MAGENTA}Starting DanceMode...${NC}"
echo -e "${YELLOW}Tip: SPACE to start, LEFT/RIGHT to select dance, ESC to quit${NC}"
echo ""

# Run the game
python3 main.py "$@"

# Deactivate virtual environment when done
deactivate
