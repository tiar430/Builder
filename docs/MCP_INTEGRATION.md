# MCP Integration Guide

## Overview

Model Context Protocol (MCP) allows the AI Agent system to connect to external services and databases, extending its capabilities beyond code analysis.

**Integrated MCP Servers:**
- Supabase (Database & Auth)
- Neon (PostgreSQL Database)
- Linear (Issue Tracking)
- Notion (Documentation)
- Sentry (Error Monitoring)
- Stripe (Payments)

## Architecture

```
┌─────────────────────────────────────┐
│   AI Agent System (Chainlit UI)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   MCP Client Manager                │
│  ┌─────────────────────────────┐    │
│  │ MCPClientManager            │    │
│  │ • connect_all()             │    │
│  │ • get_available_clients()   │    │
│  │ • get_client()              │    │
│  └─────────────────────────────┘    │
└──────┬──────────────────┬───────────┘
       │                  │
    ┌──▼──┐          ┌────▼────┐
    │ ... │          │ Neon    │
    └─────┘          └────┬────┘
                           │
                    PostgreSQL DB
```

## Configuration

### Enable MCP
```env
MCP_ENABLED=true
```

### Disable Specific Clients
Comment out environment variables for unused services:
```env
# SUPABASE_URL=  # Disabled
# SUPABASE_KEY=  # Disabled
NEON_DATABASE_URL=postgresql://...
```

---

## Service Setup

### 1. Supabase

**Purpose:** Database, authentication, real-time subscriptions

**Setup:**
1. Create account at https://supabase.com
2. Create new project
3. Get credentials from Settings > API

**Environment Variables:**
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Usage in Agents:**
```python
mcp_manager = MCPClientManager()
supabase = mcp_manager.get_client('supabase')
results = await supabase.query('users', filters={'id': 123})
```

**Capabilities:**
- User authentication integration
- Store conversation history
- Cache analysis results
- Store execution metrics

---

### 2. Neon Database

**Purpose:** Managed PostgreSQL database for production

**Setup:**
1. Create account at https://neon.tech
2. Create new project
3. Copy connection string

**Environment Variables:**
```env
NEON_DATABASE_URL=postgresql://user:password@ep-cool-name.us-east-1.neon.tech/dbname?sslmode=require
```

**Usage in Agents:**
```python
neon = mcp_manager.get_client('neon')
result = await neon.execute(
    "INSERT INTO logs (agent_type, result) VALUES ($1, $2)",
    ['debugger', 'analysis_result']
)
```

**Schema Setup:**
```sql
CREATE TABLE conversation_history (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255),
  user_message TEXT,
  agent_response TEXT,
  agent_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE execution_metrics (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255),
  agent_type VARCHAR(50),
  execution_time_ms FLOAT,
  tokens_used INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. Linear Integration

**Purpose:** Issue tracking, bug reports, feature requests

**Setup:**
1. Create account at https://linear.app
2. Create workspace and project
3. Generate API key from Settings > API Keys

**Environment Variables:**
```env
LINEAR_API_KEY=lin_api_...
```

**Usage in Agents:**
```python
linear = mcp_manager.get_client('linear')
issue = await linear.create_issue(
    team_id='ENG',
    title='Code quality issue found',
    description='...',
    priority='HIGH'
)
```

**Common Tasks:**
- Auto-create bugs from error reports
- Link analysis results to issues
- Track performance improvements

---

### 4. Notion Integration

**Purpose:** Documentation, knowledge base, notes

**Setup:**
1. Create Notion workspace
2. Create database for logs/reports
3. Create integration at https://www.notion.so/my-integrations
4. Share database with integration

**Environment Variables:**
```env
NOTION_API_KEY=secret_abc123xyz...
```

**Usage in Agents:**
```python
notion = mcp_manager.get_client('notion')
await notion.create_page(
    parent_id='database_id',
    title='Code Analysis Report',
    content='...'
)
```

**Common Tasks:**
- Store generated documentation
- Create analysis reports
- Team knowledge sharing

---

### 5. Sentry Integration (Future)

**Purpose:** Error monitoring and debugging

**Setup:**
1. Create account at https://sentry.io
2. Create project for your app
3. Get DSN from Settings

**Environment Variables:**
```env
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/123
```

**Capabilities:**
- Track agent errors
- Monitor performance
- Trigger alerts

---

### 6. Stripe Integration (Future)

**Purpose:** Payment processing, usage tracking

**Setup:**
1. Create account at https://stripe.com
2. Get API keys from Developers > API Keys

**Environment Variables:**
```env
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Capabilities:**
- Track API usage
- Implement usage-based billing
- Manage subscriptions

---

## Client Manager API

### Methods

```python
from backend.mcp import MCPClientManager

manager = MCPClientManager()

# Connect all available clients
await manager.connect_all()

# Get specific client
client = manager.get_client('supabase')

# Check available clients
available = await manager.get_available_clients()

# List all registered clients
clients = await manager.list_clients()

# Disconnect all clients
await manager.disconnect_all()
```

---

## Agent Integration Example

```python
# In agents/custom_agent.py
from backend.mcp import MCPClientManager

class CustomAgent(BaseAgent):
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        # Get MCP manager
        mcp_manager = MCPClientManager()
        
        # Get Neon client
        neon = mcp_manager.get_client('neon')
        
        # Store results in database
        if neon and await neon.is_available():
            await neon.execute(
                """INSERT INTO analysis_results 
                   (session_id, agent_type, result) 
                   VALUES ($1, $2, $3)""",
                [session_id, 'custom', result]
            )
        
        return await self.create_response(
            success=True,
            result='Analysis complete'
        )
```

---

## Error Handling

```python
try:
    # Connect to MCP service
    status = await manager.connect_all()
    
    if not status.get('neon'):
        logger.warning("Neon database not available")
        # Fall back to SQLite
except Exception as e:
    logger.error(f"MCP error: {e}")
    # Continue without MCP
```

---

## Testing MCP Connections

```bash
# Test each MCP service
curl http://localhost:8000/agent/mcp-status

# Response
{
  "enabled": true,
  "clients": {
    "supabase": true,
    "neon": true,
    "linear": false,
    "notion": false
  }
}
```

---

## Best Practices

1. **Error Handling**
   - Always check if client is available before use
   - Implement graceful fallbacks
   - Log errors for debugging

2. **Performance**
   - Cache results in SQLite
   - Use connection pooling
   - Batch database operations

3. **Security**
   - Store API keys in environment variables
   - Never commit .env files
   - Use least-privilege API keys
   - Rotate keys regularly

4. **Monitoring**
   - Track MCP connection status
   - Monitor API rate limits
   - Alert on failures
   - Log all integrations

---

## Troubleshooting

### MCP Client Not Connecting

```bash
# Check environment variables
grep MCP .env
grep SUPABASE .env
grep NEON .env

# Test connectivity
curl https://supabase-project.supabase.co/rest/v1/

# Check credentials
echo $SUPABASE_KEY
```

### Database Connection Errors

```bash
# Test Neon connection
psql "postgresql://user:pass@host/dbname"

# Check connection string format
# postgresql://user:password@host:port/dbname?sslmode=require
```

### API Rate Limiting

```env
# Add rate limiting config
RATE_LIMIT_MCP=100  # requests per minute
```

---

## Future MCP Services

Planned integrations:
- GitHub (code repository integration)
- Slack (notifications)
- Discord (team communication)
- AWS S3 (file storage)
- Google Cloud (additional services)
- HubSpot (CRM integration)

---

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Supabase Docs](https://supabase.com/docs)
- [Neon Docs](https://neon.tech/docs)
- [Linear API](https://linear.app/api-reference)
- [Notion API](https://developers.notion.com/)

---

## Support

For MCP integration issues:
1. Check `.env` configuration
2. Verify API credentials
3. Test service connectivity
4. Review error logs
5. Open GitHub issue with details
