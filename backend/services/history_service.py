import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.database_models import ConversationHistory, AgentExecutionHistory
from backend.models.request_models import ConversationHistoryEntry

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing conversation and execution history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_conversation(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        agent_type: str,
        metadata: Dict[str, Any] = None,
    ) -> ConversationHistory:
        """Save conversation entry to database."""
        try:
            entry = ConversationHistory(
                session_id=session_id,
                user_message=user_message,
                agent_response=agent_response,
                agent_type=agent_type,
                metadata_json=metadata or {},
            )
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            self.db.rollback()
            raise
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[ConversationHistoryEntry]:
        """Get conversation history for a session."""
        try:
            entries = self.db.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id
            ).order_by(
                desc(ConversationHistory.created_at)
            ).limit(limit).all()
            
            return [
                ConversationHistoryEntry(
                    id=entry.id,
                    session_id=entry.session_id,
                    user_message=entry.user_message,
                    agent_response=entry.agent_response,
                    agent_type=entry.agent_type,
                    created_at=entry.created_at,
                    metadata_json=entry.metadata_json,
                )
                for entry in entries
            ]
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session."""
        try:
            self.db.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id
            ).delete()
            self.db.commit()
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            self.db.rollback()
            raise
    
    def save_execution(
        self,
        session_id: str,
        agent_type: str,
        task_description: str,
        status: str,
        result: str = None,
        error_message: str = None,
        execution_time_ms: float = 0,
        tokens_used: int = 0,
        model_used: str = None,
    ) -> AgentExecutionHistory:
        """Save agent execution history."""
        try:
            execution = AgentExecutionHistory(
                session_id=session_id,
                agent_type=agent_type,
                task_description=task_description,
                status=status,
                result=result,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                model_used=model_used,
            )
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)
            return execution
        except Exception as e:
            logger.error(f"Error saving execution history: {e}")
            self.db.rollback()
            raise
    
    def get_execution_history(
        self,
        session_id: str = None,
        agent_type: str = None,
        status: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get execution history with optional filters."""
        try:
            query = self.db.query(AgentExecutionHistory)
            
            if session_id:
                query = query.filter(AgentExecutionHistory.session_id == session_id)
            if agent_type:
                query = query.filter(AgentExecutionHistory.agent_type == agent_type)
            if status:
                query = query.filter(AgentExecutionHistory.status == status)
            
            executions = query.order_by(
                desc(AgentExecutionHistory.created_at)
            ).limit(limit).all()
            
            return [
                {
                    "id": ex.id,
                    "session_id": ex.session_id,
                    "agent_type": ex.agent_type,
                    "task_description": ex.task_description,
                    "status": ex.status,
                    "execution_time_ms": ex.execution_time_ms,
                    "tokens_used": ex.tokens_used,
                    "model_used": ex.model_used,
                    "created_at": ex.created_at.isoformat(),
                }
                for ex in executions
            ]
        except Exception as e:
            logger.error(f"Error retrieving execution history: {e}")
            return []
    
    def get_execution_stats(self, session_id: str = None, days: int = 7) -> Dict[str, Any]:
        """Get execution statistics."""
        try:
            query = self.db.query(AgentExecutionHistory)
            
            if session_id:
                query = query.filter(AgentExecutionHistory.session_id == session_id)
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(AgentExecutionHistory.created_at >= cutoff_date)
            
            executions = query.all()
            
            if not executions:
                return {
                    "total_executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "average_time_ms": 0,
                    "total_tokens": 0,
                }
            
            successful = len([e for e in executions if e.status == "completed"])
            failed = len([e for e in executions if e.status == "failed"])
            avg_time = sum(e.execution_time_ms for e in executions) / len(executions)
            total_tokens = sum(e.tokens_used for e in executions)
            
            return {
                "total_executions": len(executions),
                "successful": successful,
                "failed": failed,
                "average_time_ms": avg_time,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            logger.error(f"Error retrieving execution stats: {e}")
            return {}
