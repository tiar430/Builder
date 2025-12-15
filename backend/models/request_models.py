from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DebugRequest(BaseModel):
    """Request model for code debugging."""
    code: str = Field(..., description="Code to debug")
    language: str = Field(..., description="Programming language")
    error_message: Optional[str] = Field(None, description="Error message if available")
    context: Optional[str] = Field(None, description="Additional context")


class AnalyzeRequest(BaseModel):
    """Request model for code analysis."""
    code: str = Field(..., description="Code to analyze")
    language: str = Field(..., description="Programming language")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis: comprehensive, security, performance, quality")
    context: Optional[str] = Field(None, description="Additional context")


class Task(BaseModel):
    """Model for individual task in orchestration."""
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type: debug, analyze, generate_docs")
    input_data: Dict[str, Any] = Field(..., description="Input data for the task")
    depends_on: List[str] = Field(default=[], description="Task IDs this task depends on")
    priority: int = Field(default=0, description="Priority level (higher = higher priority)")


class OrchestrationRequest(BaseModel):
    """Request model for multi-task orchestration."""
    session_id: str = Field(..., description="Session identifier")
    tasks: List[Task] = Field(..., description="List of tasks to execute")
    parallel_execution: bool = Field(default=False, description="Whether to execute independent tasks in parallel")
    context: Optional[str] = Field(None, description="Overall context for all tasks")


class DocsGenerationRequest(BaseModel):
    """Request model for documentation generation."""
    code: str = Field(..., description="Code to generate docs for")
    language: str = Field(..., description="Programming language")
    doc_type: str = Field(default="function", description="Type: function, class, module, api")
    style: str = Field(default="google", description="Documentation style: google, numpy, sphinx")


class AgentResponse(BaseModel):
    """Standard response from agent."""
    success: bool = Field(..., description="Whether the operation succeeded")
    agent_type: str = Field(..., description="Type of agent that processed the request")
    result: Optional[str] = Field(None, description="Result or analysis")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    execution_time_ms: float = Field(default=0, description="Execution time in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used by LLM")


class ConversationHistoryEntry(BaseModel):
    """Model for conversation history entry."""
    id: int
    session_id: str
    user_message: str
    agent_response: str
    agent_type: str
    created_at: datetime
    metadata_json: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    ollama_available: bool
    ollama_model: Optional[str]
    mistral_available: bool
    database_connected: bool
    mcp_enabled: bool


class ModelInfo(BaseModel):
    """Information about available models."""
    name: str
    type: str  # local, cloud
    provider: str  # ollama, mistral
    available: bool


class TaskResult(BaseModel):
    """Result of a single task execution."""
    task_id: str
    task_type: str
    status: str  # completed, failed, pending
    result: Optional[str]
    error: Optional[str]
    execution_time_ms: float


class OrchestrationResult(BaseModel):
    """Result of orchestration execution."""
    session_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    task_results: List[TaskResult]
    total_execution_time_ms: float
    overall_status: str  # success, partial, failed
