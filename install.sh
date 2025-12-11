#!/bin/bash
# Quorum installation script

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Quorum...${NC}"
echo

# Check Python version
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        echo -e "${GREEN}OK${NC} (Python $PY_VERSION)"
    else
        echo -e "${RED}FAIL${NC}"
        echo "Python 3.11 or higher required (found $PY_VERSION)"
        exit 1
    fi
else
    echo -e "${RED}FAIL${NC}"
    echo "Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo -e "${GREEN}OK${NC} (Node $NODE_VERSION)"
    else
        echo -e "${YELLOW}WARNING${NC} (Node $NODE_VERSION, recommend 18+)"
    fi
else
    echo -e "${RED}FAIL${NC}"
    echo "Node.js not found. Please install Node.js 18 or higher."
    exit 1
fi

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}OK${NC} (npm $NPM_VERSION)"
else
    echo -e "${RED}FAIL${NC}"
    echo "npm not found. Please install npm."
    exit 1
fi

echo

# Check/install uv
echo -n "Checking uv... "
if ! command -v uv &> /dev/null; then
    echo "not found, installing..."
    pip3 install uv --quiet 2>/dev/null || pip install uv --quiet
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}FAIL${NC}"
        echo "Failed to install uv. Please install manually: pip install uv"
        exit 1
    fi
fi
UV_VERSION=$(uv --version | awk '{print $2}')
echo -e "${GREEN}OK${NC} (uv $UV_VERSION)"

echo

# Remove incompatible venv if it exists (e.g., from different platform)
if [ -d .venv ] && [ ! -f .venv/bin/python ]; then
    echo "Removing incompatible virtual environment..."
    rm -rf .venv
fi

# Install Python dependencies with uv
echo "Installing Python dependencies..."
uv sync --quiet
echo -e "${GREEN}Done${NC}"

echo

# Install and build frontend
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
echo -e "${GREEN}Done${NC}"

echo "Building frontend..."
npm run build --silent
echo -e "${GREEN}Done${NC}"
cd ..

echo

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
else
    echo ".env already exists"
fi

echo
echo -e "${GREEN}Installation complete!${NC}"
echo
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./quorum"
echo
