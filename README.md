# AI Agent Multi-Tasking System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Chainlit](https://img.shields.io/badge/chainlit-1.0+-blue.svg)](https://chainlit.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An intelligent, open-source AI system for multi-language code debugging, analysis, and documentation generation. Powered by local LLMs (Ollama, LlamaIndex) with cloud API fallback (Mistral AI), featuring MCP integration for extended capabilities.

## Features

✨ **Core Capabilities**

- 🐛 **Multi-Language Debugging** - Debug code in 10+ programming languages
- 🔍 **Code Analysis** - Security, performance, and quality analysis
- 📚 **Auto Documentation** - Generate docs in multiple styles (Google, NumPy, Sphinx)
- ⚡ **Task Orchestration** - Execute multiple tasks in sequence or parallel
- 💾 **Conversation History** - Track all interactions and metrics
- 📱 **PWA Support** - Install as app on mobile/desktop

🚀 **Technical Excellence**

- 🎯 **Offline Support** - Service worker with offline caching
- 🔌 **MCP Integration** - Connect to Supabase, Neon, Linear, Notion, Sentry
- 🧠 **Local AI First** - Ollama for privacy-focused local processing
- ☁️ **Cloud Fallback** - Mistral AI API for enhanced capabilities
- 🗄️ **SQLite Database** - Lightweight persistence
- 📊 **Execution Metrics** - Track performance and token usage

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser / PWA Client                       │
│  (Service Worker, Offline Cache, Web Components)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ WebSocket / HTTP
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Chainlit Frontend (Port 8501)                   │
│  • Chat Interface                                            │
│  • File Upload                                               │
│  • Agent Selection                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API / WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (Port 8000)                        │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Agent Routers   │  │  Health Check    │                 │
│  │  /agent/debug    │  │  /health         │                 │
│  │  /agent/analyze  │  │  /models         │                 │
│  │  /agent/docs     │  │  /mcp-status     │                 │
│  │  /agent/ws       │  │                  │                 │
│  └──────────────────┘  └──────────────────┘                 │
└──────────────┬────────────────────────────────┬──────────────┘
               │                                │
      ┌────────▼─────────┐        ┌────────────▼────────┐
      │ Agents Layer     │        │ LLM Service         │
      │ ┌─────────────┐  │        │ ┌────────────────┐  │
      │ │ Debugger    │  │        │ │ Ollama Provider│  │
      │ │ Analyzer    │  │        │ │ (Local LLM)    │  │
      │ │ DocGenerator│  │        │ │                │  │
      │ │ Orchestrator│  │        │ │ Mistral AI API │  │
      │ └─────────────┘  │        │ │ (Cloud)        │  │
      └──────────────────┘        └────────────────┘  │
                                   └─────────────────┘
               │                        │
      ┌────────▼──────────┐  ┌─────────▼─────────┐
      │ Services Layer    │  │ MCP Integration   │
      │ ┌──────────────┐  │  │ ┌───────────────┐ │
      │ │CodeParser    │  │  │ │ Supabase      │ │
      │ │HistoryService│  │  │ │ Neon Postgres │ │
      │ └──────────────┘  │  │ │ Linear        │ │
      │                   │  │ │ Notion        │ │
      └───────────────────┘  │ └───────────────┘ │
                             └───────────────────┘
               │
      ┌────────▼──────────┐
      │ SQLite Database   │
      │ ConversationHist. │
      │ ExecutionHistory  │
      │ Cache             │
      └───────────────────┘
```

## Supported Languages

Python • JavaScript • TypeScript • Java • Go • Rust • C/C++ • Ruby • PHP • Swift • Kotlin • And more!

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip and venv
- [Ollama](https://ollama.ai) (for local AI) - recommended
- Optional: Mistral API key for cloud fallback

### Installation

1. **Clone and setup**

```bash
git clone <repository>
cd ai-agent-system
chmod +x scripts/setup.sh
./scripts/setup.sh
```

2. **Download LLM models (Ollama)**

```bash
ollama pull mistral
# Or use other models:
# ollama pull llama2
# ollama pull neural-chat
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings:
# - MISTRAL_API_KEY (optional)
# - MCP credentials (optional)
```

4. **Start services**

Terminal 1 - Backend:

```bash
source venv/bin/activate
python -m backend.main
# Server runs on http://localhost:8000
```

Terminal 2 - Frontend:

```bash
source venv/bin/activate
chainlit run frontend/app.py
# Open http://localhost:8501
```

## Docker Deployment

### Using Docker Compose

**Development setup (minimal):**

```bash
docker-compose --profile dev up
```

**Full setup (with Ollama + PostgreSQL):**

```bash
docker-compose up -d
```

**Specific services:**

```bash
# Backend + Ollama only
docker-compose --profile ollama up

# With all services
docker-compose up

# Remove all containers and volumes
docker-compose down -v
```

**Access:**

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Ollama: localhost:11434

## API Documentation

### Debug Endpoint

```bash
curl -X POST http://localhost:8000/agent/debug \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b)\n  return a + b",
    "language": "python",
    "error_message": "SyntaxError: invalid syntax"
  }'
```

### Analyze Endpoint

```bash
curl -X POST http://localhost:8000/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "SELECT * FROM users",
    "language": "sql",
    "analysis_type": "security"
  }'
```

### Generate Docs Endpoint

```bash
curl -X POST http://localhost:8000/agent/generate-docs \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def factorial(n):\n  return n * factorial(n-1)",
    "language": "python",
    "doc_type": "function",
    "style": "google"
  }'
```

### WebSocket Real-time

```javascript
const ws = new WebSocket("ws://localhost:8000/agent/ws/agent");
ws.send(
  JSON.stringify({
    agent_type: "debugger",
    session_id: "user-123",
    context: {
      code: "...",
      language: "python",
    },
  }),
);
```

## Configuration

### Environment Variables

See `.env.example` for all available options:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Mistral API (Cloud Fallback)
MISTRAL_API_KEY=your-api-key
MISTRAL_MODEL=mistral-small

# MCP Integration
MCP_ENABLED=true
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
NEON_DATABASE_URL=your-connection-string
```

### Supported Models

**Ollama Models:**

- `mistral` (7B) - Recommended for balance
- `llama2` (7B/13B) - Good for coding
- `neural-chat` (7B) - Optimized for chat
- `codellama` (7B/13B/34B) - Code-focused

**Cloud APIs:**

- Mistral: `mistral-small`, `mistral-medium`, `mistral-large`

## MCP Integration

Connect to external services for enhanced capabilities:

### Supabase

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxx...
```

### Neon Database

```env
NEON_DATABASE_URL=postgresql://user:password@region.neon.tech/dbname
```

### Linear (Issue Tracking)

```env
LINEAR_API_KEY=your-api-key
```

### Notion (Documentation)

```env
NOTION_API_KEY=your-api-key
```

## Usage Examples

### Debug Python Code

1. Paste Python code with an error
2. System analyzes syntax and logic errors
3. Provides fixes with explanations

### Security Analysis

1. Submit code for security review
2. Identifies vulnerabilities
3. Provides mitigation strategies

### Generate API Documentation

1. Paste API endpoint code
2. Select "API" doc type
3. Get formatted documentation

### Multi-Task Orchestration

1. Submit code once
2. System runs debug + analysis + docs
3. Get comprehensive results

## Performance Metrics

- **Response Time**: 2-10s (local Ollama) / 1-5s (Mistral API)
- **Token Usage**: ~1-3 tokens per character
- **Max Code Size**: 50KB (single request)
- **Concurrent Users**: Limited by available RAM/GPU

### Optimization Tips

1. **Use local Ollama for privacy**
   - Faster response (with GPU)
   - No API costs
   - Works offline

2. **Use Mistral API for accuracy**
   - Better reasoning
   - More token allowance
   - Premium model access

3. **Cache analysis results**
   - SQLite caches previous analyses
   - Reduces redundant LLM calls
   - Improves response time

## Troubleshooting

### Ollama Connection Failed

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Database Locked

```bash
# Reset SQLite database
rm agent_db.sqlite
# Restart backend to reinitialize
```

### Memory Issues

```bash
# For smaller models, use quantized versions
ollama pull mistral:7b-text-q4_0

# Monitor memory usage
watch -n 1 'ps aux | grep ollama'
```

### WebSocket Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/health

# Check firewall allows port 8000
netstat -tuln | grep 8000
```

## Development

### Project Structure

```
ai-agent-system/
├── backend/              # FastAPI application
│   ├── agents/          # AI agent implementations
│   ├── services/        # Core services
│   ├── models/          # Database & request models
│   ├── routers/         # API endpoints
│   └── mcp/             # MCP integrations
├── frontend/            # Chainlit application
├── public/              # Static assets & PWA files
├── scripts/             # Setup and deployment
├── docs/                # Documentation
└── docker-compose.yml   # Container orchestration
```

### Running Tests

```bash
source venv/bin/activate
pytest backend/
pytest backend/agents/
```

### Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/name`
4. Submit pull request

## Performance Benchmarks

| Task       | Ollama (GPU) | Ollama (CPU) | Mistral API |
| ---------- | ------------ | ------------ | ----------- |
| Debug      | 3-5s         | 10-15s       | 1-3s        |
| Analyze    | 5-8s         | 15-25s       | 2-5s        |
| Docs       | 4-6s         | 12-18s       | 1-4s        |
| Tokens/sec | 20-30        | 5-10         | 50-100      |

## Roadmap

- [ ] Support for more programming languages
- [ ] Real-time code analysis while typing
- [ ] Code refactoring suggestions
- [ ] Performance profiling
- [ ] Team collaboration features
- [ ] Cloud deployment templates
- [ ] Mobile app (React Native)
- [ ] IDE integrations (VS Code, IntelliJ)

## License

MIT License - see LICENSE file for details

## Support

- 📖 **Documentation**: See `docs/` directory
- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 📧 **Email**: support@example.com

## Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [Chainlit](https://chainlit.io/) - Chat UI
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Mistral AI](https://mistral.ai/) - Cloud LLM API

---

**Built with ❤️ for developers by developers**
