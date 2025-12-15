from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from backend.database import Base


class ConversationHistory(Base):
    """Model for storing conversation history between user and agent."""
    
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    agent_type = Column(String, nullable=False)  # debugger, analyzer, orchestrator, docs_generator
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, session_id={self.session_id}, agent_type={self.agent_type})>"


class AgentExecutionHistory(Base):
    """Model for tracking agent execution metrics and results."""
    
    __tablename__ = "agent_execution_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    agent_type = Column(String, nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    result = Column(Text)
    error_message = Column(Text)
    execution_time_ms = Column(Float)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentExecutionHistory(id={self.id}, agent_type={self.agent_type}, status={self.status})>"


class CacheEntry(Base):
    """Model for caching LLM responses and analysis results."""
    
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    cache_type = Column(String, nullable=False)  # analysis, debug, docs, embedding
    value = Column(Text, nullable=False)
    embedding = Column(JSON)  # For vector similarity search
    ttl_hours = Column(Integer, default=24)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    
    def __repr__(self):
        return f"<CacheEntry(id={self.id}, cache_type={self.cache_type}, hits={self.hit_count})>"
