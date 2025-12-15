#!/bin/bash

set -e

echo "================================================"
echo "AI Agent Multi-Tasking System - Setup Script"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✅ pip upgraded"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created - please edit with your configuration"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from backend.database import init_db; init_db(); print('✅ Database initialized')" || echo "⚠️ Database initialization skipped"

# Check for Ollama
echo ""
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama found"
    echo "   Available models:"
    ollama list 2>/dev/null || echo "   (No models pulled yet)"
else
    echo "⚠️ Ollama not found. Install from: https://ollama.ai"
    echo "   After installation, pull a model:"
    echo "   ollama pull mistral"
fi

# Summary
echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration:"
echo "   - OLLAMA_BASE_URL (if using local Ollama)"
echo "   - MISTRAL_API_KEY (if using Mistral AI)"
echo "   - MCP credentials (Supabase, Neon, etc.)"
echo ""
echo "2. Start the backend:"
echo "   source venv/bin/activate"
echo "   python -m backend.main"
echo ""
echo "3. In another terminal, start the frontend:"
echo "   source venv/bin/activate"
echo "   chainlit run frontend/app.py"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8501"
echo ""
echo "================================================"
