import logging
from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.llm_service import get_llm_service, LLMService
from backend.agents.debugger_agent import DebuggerAgent
from backend.agents.analyzer_agent import AnalyzerAgent
from backend.agents.docs_generator import DocsGeneratorAgent
from backend.agents.orchestrator import TaskOrchestrator
from backend.services.history_service import HistoryService
from backend.models.request_models import (
    DebugRequest,
    AnalyzeRequest,
    DocsGenerationRequest,
    OrchestrationRequest,
    AgentResponse,
    ConversationHistoryEntry,
)
from backend.mcp import get_mcp_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/debug", response_model=AgentResponse)
async def debug_code(
    request: DebugRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Debug code and provide fixes."""
    agent = DebuggerAgent(llm_service, db)
    
    context = {
        "code": request.code,
        "language": request.language,
        "error_message": request.error_message,
        "context": request.context,
        "session_id": "default",
    }
    
    return await agent.execute(context)


@router.post("/analyze", response_model=AgentResponse)
async def analyze_code(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Analyze code for quality, security, or performance."""
    agent = AnalyzerAgent(llm_service, db)
    
    context = {
        "code": request.code,
        "language": request.language,
        "analysis_type": request.analysis_type,
        "context": request.context,
        "session_id": "default",
    }
    
    return await agent.execute(context)


@router.post("/generate-docs", response_model=AgentResponse)
async def generate_docs(
    request: DocsGenerationRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate documentation for code."""
    agent = DocsGeneratorAgent(llm_service, db)
    
    context = {
        "code": request.code,
        "language": request.language,
        "doc_type": request.doc_type,
        "style": request.style,
        "session_id": "default",
    }
    
    return await agent.execute(context)


@router.post("/orchestrate", response_model=AgentResponse)
async def orchestrate_tasks(
    request: OrchestrationRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Execute multiple tasks in sequence or parallel."""
    orchestrator = TaskOrchestrator(llm_service, db)
    
    context = {
        "tasks": request.tasks,
        "parallel_execution": request.parallel_execution,
        "session_id": request.session_id,
        "context": request.context,
    }
    
    return await orchestrator.execute(context)


@router.get("/history/{session_id}", response_model=List[ConversationHistoryEntry])
async def get_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get conversation history for a session."""
    history_service = HistoryService(db)
    return history_service.get_conversation_history(session_id, limit)


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Clear conversation history for a session."""
    history_service = HistoryService(db)
    history_service.clear_conversation_history(session_id)
    return {"status": "cleared"}


@router.get("/execution-stats/{session_id}")
async def get_execution_stats(
    session_id: str = None,
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Get execution statistics."""
    history_service = HistoryService(db)
    stats = history_service.get_execution_stats(session_id, days)
    return stats


@router.get("/mcp-status")
async def get_mcp_status(mcp_manager = Depends(get_mcp_manager)):
    """Get MCP clients status."""
    status = await mcp_manager.get_available_clients()
    return {
        "enabled": True,
        "clients": status,
    }


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/agent")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """WebSocket endpoint for real-time agent interaction."""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            agent_type = data.get("agent_type")
            context = data.get("context", {})
            session_id = data.get("session_id", "default")
            
            context["session_id"] = session_id
            
            # Route to appropriate agent
            agent = None
            if agent_type == "debugger":
                agent = DebuggerAgent(llm_service, db)
            elif agent_type == "analyzer":
                agent = AnalyzerAgent(llm_service, db)
            elif agent_type == "docs_generator":
                agent = DocsGeneratorAgent(llm_service, db)
            elif agent_type == "orchestrator":
                agent = TaskOrchestrator(llm_service, db)
            
            if not agent:
                await websocket.send_json({
                    "error": f"Unknown agent type: {agent_type}",
                })
                continue
            
            # Execute agent
            try:
                result = await agent.execute(context)
                await websocket.send_json({
                    "success": result.success,
                    "agent_type": result.agent_type,
                    "result": result.result,
                    "error": result.error,
                    "execution_time_ms": result.execution_time_ms,
                })
            except Exception as e:
                logger.error(f"WebSocket agent execution error: {e}")
                await websocket.send_json({
                    "error": str(e),
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
