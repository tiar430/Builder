# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication required for local setup. For production, implement API key authentication.

---

## Health & Status Endpoints

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ollama_available": true,
  "ollama_model": "mistral",
  "mistral_available": true,
  "database_connected": true,
  "mcp_enabled": true
}
```

### GET /health/models

List available LLM models.

**Response:**

```json
[
  {
    "name": "mistral",
    "type": "local",
    "provider": "ollama",
    "available": true
  },
  {
    "name": "mistral-small",
    "type": "cloud",
    "provider": "mistral",
    "available": true
  }
]
```

### GET /agent/mcp-status

Get MCP clients status.

**Response:**

```json
{
  "enabled": true,
  "clients": {
    "supabase": true,
    "neon": false,
    "linear": true,
    "notion": true
  }
}
```

---

## Agent Endpoints

### POST /agent/debug

Debug code and identify issues.

**Request Body:**

```json
{
  "code": "def add(a, b)\n  return a + b",
  "language": "python",
  "error_message": "SyntaxError: invalid syntax",
  "context": "Optional additional context"
}
```

**Query Parameters:**

- `session_id` (optional): Session identifier for history

**Response:**

```json
{
  "success": true,
  "agent_type": "debugger",
  "result": "The issue is a missing colon after function definition...",
  "error": null,
  "metadata": {
    "language": "python",
    "syntax_errors": [
      {
        "type": "bracket_mismatch",
        "message": "Mismatched brackets"
      }
    ],
    "provider": "OllamaProvider"
  },
  "execution_time_ms": 3421,
  "tokens_used": 245
}
```

---

### POST /agent/analyze

Analyze code for quality, security, or performance.

**Request Body:**

```json
{
  "code": "SELECT * FROM users WHERE id = 1",
  "language": "sql",
  "analysis_type": "security",
  "context": "Optional context"
}
```

**Analysis Types:**

- `security`: Vulnerability detection, data handling, API security
- `performance`: Bottlenecks, complexity, optimization
- `quality`: Structure, readability, best practices
- `comprehensive`: All of the above (default)

**Response:**

```json
{
  "success": true,
  "agent_type": "analyzer",
  "result": "Security Analysis:\n1. SQL Injection Risk...",
  "error": null,
  "metadata": {
    "language": "sql",
    "analysis_type": "security",
    "quality_metrics": {
      "total_lines": 1,
      "non_empty_lines": 1,
      "comment_lines": 0,
      "average_line_length": 35.0,
      "functions": 0,
      "long_lines": 0
    },
    "provider": "MistralProvider"
  },
  "execution_time_ms": 2156,
  "tokens_used": 312
}
```

---

### POST /agent/generate-docs

Generate documentation for code.

**Request Body:**

```json
{
  "code": "def factorial(n):\n  if n <= 1:\n    return 1\n  return n * factorial(n-1)",
  "language": "python",
  "doc_type": "function",
  "style": "google"
}
```

**Doc Types:**

- `function`: Function documentation
- `class`: Class documentation
- `module`: Module documentation
- `api`: API endpoint documentation

**Styles:**

- `google`: Google-style docstrings
- `numpy`: NumPy-style docstrings
- `sphinx`: Sphinx/RST style

**Response:**

```json
{
  "success": true,
  "agent_type": "docs_generator",
  "result": "def factorial(n):\n  \"\"\"Calculate factorial of n.\n  ...\n  \"\"\"",
  "error": null,
  "metadata": {
    "language": "python",
    "doc_type": "function",
    "style": "google",
    "provider": "OllamaProvider"
  },
  "execution_time_ms": 4123,
  "tokens_used": 456
}
```

---

### POST /agent/orchestrate

Execute multiple tasks in sequence or parallel.

**Request Body:**

```json
{
  "session_id": "user-123",
  "tasks": [
    {
      "task_id": "debug-task",
      "task_type": "debugger",
      "input_data": {
        "code": "...",
        "language": "python"
      },
      "depends_on": [],
      "priority": 10
    },
    {
      "task_id": "analyze-task",
      "task_type": "analyzer",
      "input_data": {
        "code": "...",
        "language": "python",
        "analysis_type": "security"
      },
      "depends_on": [],
      "priority": 5
    }
  ],
  "parallel_execution": true,
  "context": "Optional overall context"
}
```

**Task Types:**

- `debugger`: Debug code
- `analyzer`: Analyze code
- `docs_generator`: Generate documentation

**Response:**

```json
{
  "success": true,
  "agent_type": "orchestrator",
  "result": "### Task 1: debug-task\nStatus: completed\n...",
  "error": null,
  "metadata": {
    "total_tasks": 2,
    "completed_tasks": 2,
    "failed_tasks": 0,
    "task_results": [
      {
        "task_id": "debug-task",
        "status": "completed",
        "execution_time_ms": 3421
      },
      {
        "task_id": "analyze-task",
        "status": "completed",
        "execution_time_ms": 2156
      }
    ]
  },
  "execution_time_ms": 5800,
  "tokens_used": 758
}
```

---

## History Endpoints

### GET /agent/history/{session_id}

Get conversation history for a session.

**Query Parameters:**

- `limit`: Maximum number of entries (default: 50)

**Response:**

```json
[
  {
    "id": 1,
    "session_id": "user-123",
    "user_message": "Debug this Python code",
    "agent_response": "The issue is...",
    "agent_type": "debugger",
    "created_at": "2024-01-15T10:30:00",
    "metadata_json": {
      "language": "python",
      "provider": "OllamaProvider"
    }
  }
]
```

---

### DELETE /agent/history/{session_id}

Clear conversation history for a session.

**Response:**

```json
{
  "status": "cleared"
}
```

---

### GET /agent/execution-stats/{session_id}

Get execution statistics.

**Query Parameters:**

- `days`: Number of days to analyze (default: 7)

**Response:**

```json
{
  "total_executions": 45,
  "successful": 43,
  "failed": 2,
  "average_time_ms": 3250,
  "total_tokens": 12450
}
```

---

## WebSocket Endpoint

### WS /agent/ws/agent

Real-time agent interaction via WebSocket.

**Connection:**

```javascript
const ws = new WebSocket("ws://localhost:8000/agent/ws/agent");
```

**Send Message:**

```json
{
  "agent_type": "debugger",
  "session_id": "user-123",
  "context": {
    "code": "...",
    "language": "python",
    "error_message": "..."
  }
}
```

**Receive Response:**

```json
{
  "success": true,
  "agent_type": "debugger",
  "result": "...",
  "error": null,
  "execution_time_ms": 3421
}
```

**Example (JavaScript):**

```javascript
const ws = new WebSocket("ws://localhost:8000/agent/ws/agent");

ws.onopen = () => {
  ws.send(
    JSON.stringify({
      agent_type: "debugger",
      session_id: "user-123",
      context: {
        code: "def foo():\n  return bar()",
        language: "python",
      },
    }),
  );
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log("Agent response:", response);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service (Ollama/API) unavailable

**Error Response Format:**

```json
{
  "success": false,
  "agent_type": "debugger",
  "result": null,
  "error": "Descriptive error message",
  "metadata": {},
  "execution_time_ms": 0,
  "tokens_used": null
}
```

---

## Rate Limiting

- No rate limiting in development
- Production should implement:
  - Per-IP rate limiting: 100 requests/minute
  - Per-session rate limiting: 20 requests/minute
  - Token usage limiting: 10,000 tokens/hour

---

## Examples

### Python Client

```python
import httpx

BASE_URL = "http://localhost:8000"

async def debug_code(code: str, language: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/agent/debug",
            json={
                "code": code,
                "language": language
            }
        )
        return response.json()
```

### JavaScript Fetch

```javascript
const debugCode = async (code, language) => {
  const response = await fetch("http://localhost:8000/agent/debug", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
  });
  return response.json();
};
```

### cURL

```bash
curl -X POST http://localhost:8000/agent/debug \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(hello)",
    "language": "python"
  }'
```

---

## API Docs

Interactive API documentation available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Rate Limits (Future)

Planned rate limiting configuration:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=200
```
