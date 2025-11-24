#!/bin/bash

# Start the FastAPI backend server
# Usage: ./start_backend.sh

echo "Starting Canvalo Multi-Agent Chat Backend..."
echo "=============================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found"
    echo "Please create .env file with required configuration"
    echo "See .env.example for reference"
    echo ""
fi

# Start the server
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

uv run python -m backend.main
