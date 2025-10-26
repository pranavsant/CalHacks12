#!/bin/bash
# Script to run the Parametric Curve Drawing System server

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from .env.example..."
    if [ -f backend/.env.example ]; then
        cp backend/.env.example .env
        echo "✅ Created .env file. Please edit it with your API keys."
        echo ""
    fi
fi

# Check if ANTHROPIC_API_KEY is set
source .env 2>/dev/null
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY is not set in .env file"
    echo "Please add your Anthropic API key to the .env file"
    exit 1
fi

echo "🚀 Starting Parametric Curve Drawing System..."
echo "📍 Server will be available at http://localhost:8000"
echo "📚 API documentation at http://localhost:8000/docs"
echo ""

# Run the server from repo root
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
