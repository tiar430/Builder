# Installation & Setup Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- Python 3.11+
- 4GB RAM
- 2GB free disk space
- Internet connection (for cloud APIs)

### Recommended Setup
- Python 3.11 or 3.12
- 8GB+ RAM (for local LLM)
- GPU (NVIDIA, AMD, or Apple Silicon) for faster inference
- 10GB+ free disk space (for Ollama models)
- Linux, macOS, or WSL2 on Windows

### GPU Support (Optional)
- **NVIDIA**: CUDA 11.8+ with cuDNN
- **AMD**: ROCm 5.5+
- **Apple**: Metal GPU support (automatic)
- **CPU**: Works but slower (10-30 tokens/sec vs 50-100 with GPU)

## Installation Methods

### Method 1: Automated Setup (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd ai-agent-system

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Follow the prompts to complete setup
```

The setup script will:
- Check Python version
- Create virtual environment
- Install dependencies
- Initialize database
- Create .env file

### Method 2: Manual Installation

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r backend/requirements.txt
```

### Method 3: Docker Installation

```bash
# Build and start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Configure Local AI (Ollama)

**Install Ollama:**
```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows
Download from: https://ollama.ai/download/windows

# Or use Docker
docker pull ollama/ollama
docker run -d -p 11434:11434 ollama/ollama
```

**Pull a model:**
```bash
ollama pull mistral

# Other options:
ollama pull llama2
ollama pull neural-chat
ollama pull codellama
```

**Configure in .env:**
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### Step 3: Configure Cloud API (Optional)

**Get Mistral API Key:**
1. Visit https://console.mistral.ai
2. Create account or sign in
3. Generate API key
4. Add to .env:

```env
MISTRAL_API_KEY=your_api_key_here
MISTRAL_MODEL=mistral-small
```

### Step 4: Configure Database (Optional)

**Default (SQLite):**
```env
DATABASE_URL=sqlite:///./agent_db.sqlite
```

**PostgreSQL (Production):**
```env
DATABASE_URL=postgresql://user:password@localhost/agent_db
```

### Step 5: Configure MCP Services (Optional)

**Supabase:**
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxx...
```

**Neon Database:**
```env
NEON_DATABASE_URL=postgresql://user:password@region.neon.tech/dbname
```

**Linear:**
```env
LINEAR_API_KEY=your_api_key
```

**Notion:**
```env
NOTION_API_KEY=your_api_key
```

## Verification

### Test Installation

```bash
# 1. Verify Python
python3 --version  # Should be 3.11+

# 2. Test virtual environment
source venv/bin/activate
which python  # Should show venv path

# 3. Test dependencies
python -c "import fastapi, chainlit; print('OK')"

# 4. Check Ollama
curl http://localhost:11434/api/tags

# 5. Test database
python -c "from backend.database import init_db; init_db(); print('Database OK')"
```

### Start Services

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python -m backend.main
# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Press CTRL+C to quit
```

**Terminal 2 - Frontend:**
```bash
source venv/bin/activate
chainlit run frontend/app.py
# Expected output:
# Welcome to Chainlit! 🚀
# Your app is available at http://localhost:8501
```

**Terminal 3 - Ollama (if not already running):**
```bash
ollama serve
```

### Access the Application

Open browser and navigate to:
- Frontend: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Test API

```bash
# Health check
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/health/models

# Test debug endpoint
curl -X POST http://localhost:8000/agent/debug \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def foo():\n    return bar()",
    "language": "python"
  }'
```

## Troubleshooting

### Python Issues

**"Python 3.11+ not found"**
```bash
# Install Python 3.11
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Then use explicitly
python3.11 -m venv venv
```

### Virtual Environment Issues

**"source: command not found"**
```bash
# You're on Windows, use:
venv\Scripts\activate
```

**"Permission denied"**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Ollama Issues

**"Connection refused to http://localhost:11434"**
```bash
# Start Ollama
ollama serve

# Or check if already running
ps aux | grep ollama
```

**"Failed to load model"**
```bash
# Check model is installed
ollama list

# Pull model if missing
ollama pull mistral

# Verify model works
ollama run mistral "Say hello"
```

### Database Issues

**"database is locked"**
```bash
# Remove old database and restart
rm agent_db.sqlite
python -m backend.main
```

**"psycopg2 import error"**
```bash
# Reinstall psycopg2
pip install --upgrade psycopg2-binary
```

### Dependency Issues

**"ModuleNotFoundError: No module named 'fastapi'"**
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Memory Issues

**"Out of memory with Ollama"**
```bash
# Use smaller model
ollama pull mistral:7b-text-q4_0
# Update .env
OLLAMA_MODEL=mistral:7b-text-q4_0

# Or use cloud API
MISTRAL_API_KEY=your_key
```

### Port Conflicts

**"Address already in use"**
```bash
# Change port in .env
PORT=8001  # Instead of 8000

# Or kill process on port
lsof -ti:8000 | xargs kill -9
```

## Performance Tuning

### CPU-Only Setup
- Use smaller models: `mistral:7b-text-q4_0`
- Reduce max_tokens: `LLM_MAX_TOKENS=1024`
- Expect: 10-15 tokens/second

### GPU Setup
- Use full precision models: `mistral`
- Increase max_tokens: `LLM_MAX_TOKENS=4096`
- Expect: 50-100 tokens/second

### Database Optimization
- Use PostgreSQL for production
- Add indexes for frequently queried fields
- Enable connection pooling

## Next Steps

1. **Read API Documentation**: See `docs/API.md`
2. **Configure MCP**: See `docs/MCP_INTEGRATION.md`
3. **Deploy to Production**: See `docs/DEPLOYMENT.md` (coming soon)
4. **Integrate with IDE**: VS Code extension (coming soon)

## Getting Help

- Check logs: `tail -f backend.log`
- View database: `sqlite3 agent_db.sqlite`
- Test endpoints: Open http://localhost:8000/docs
- Check Ollama status: `curl -s http://localhost:11434/api/tags | jq`
