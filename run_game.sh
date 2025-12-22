#!/bin/bash
# KeepyUppy Launcher Script
# Run this script to start the game

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  _  __                       _   _                   _ "
echo " | |/ /                      | | | |                 | |"
echo " | ' / ___  ___ _ __  _   _  | | | |_ __  _ __  _   _| |"
echo " |  < / _ \/ _ \ '_ \| | | | | | | | '_ \| '_ \| | | | |"
echo " | . \  __/  __/ |_) | |_| | | |_| | |_) | |_) | |_| |_|"
echo " |_|\_\___|\___| .__/ \__, |  \___/| .__/| .__/ \__, (_)"
echo "               | |     __/ |       | |   | |     __/ |  "
echo "               |_|    |___/        |_|   |_|    |___/   "
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
echo -e "${BLUE}Starting KeepyUppy...${NC}"
echo -e "${YELLOW}Tip: Press SPACE to start, ESC to pause/quit${NC}"
echo ""

# Run the game
python3 main.py "$@"

# Deactivate virtual environment when done
deactivate
