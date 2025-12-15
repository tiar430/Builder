import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.services.llm_service import LLMService
from backend.services.code_parser import CodeParser
from backend.services.history_service import HistoryService
from backend.models.request_models import AgentResponse

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    agent_type: str = "base"
    
    def __init__(self, llm_service: LLMService, db: Session):
        self.llm_service = llm_service
        self.db = db
        self.code_parser = CodeParser()
        self.history_service = HistoryService(db)
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Execute the agent with given context.
        
        Args:
            context: Dictionary containing input data
            
        Returns:
            AgentResponse with results
        """
        pass
    
    async def call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        **kwargs,
    ) -> tuple[str, str]:
        """Call LLM with prompt and return response and provider name.
        
        Returns:
            Tuple of (response_text, provider_name)
        """
        try:
            response, provider = await self.llm_service.generate(
                prompt=prompt,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response, provider
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "", "error"
    
    def build_system_prompt(self, agent_role: str, instructions: str) -> str:
        """Build system prompt for the agent."""
        return f"""You are a {agent_role} assistant. Your task is to help developers with code-related work.

{instructions}

Always be precise, clear, and actionable in your responses. Use code blocks for code examples.
Format your response in markdown when appropriate."""
    
    def build_debug_prompt(self, code: str, language: str, error: Optional[str] = None) -> str:
        """Build a prompt for debugging code."""
        prompt = f"""Analyze the following {language} code and identify issues:


{code}
```

"""
        if error:
            prompt += f"Error message: {error}\n\n"
        
        prompt += """Provide:
1. Issue identification (what's wrong)
2. Root cause (why it's happening)
3. Solution (how to fix it)
4. Prevention (how to avoid it in future)"""
        
        return prompt
    
    def build_analysis_prompt(self, code: str, language: str, analysis_type: str) -> str:
        """Build a prompt for code analysis."""
        prompt = f"""Analyze the following {language} code for {analysis_type}:

```{language}
{code}
```

Provide:
"""
        
        if analysis_type == "security":
            prompt += """1. Security vulnerabilities
2. Risk assessment
3. Mitigation strategies
4. Best practices"""
        elif analysis_type == "performance":
            prompt += """1. Performance bottlenecks
2. Optimization opportunities
3. Complexity analysis
4. Recommended improvements"""
        elif analysis_type == "quality":
            prompt += """1. Code quality issues
2. Readability concerns
3. Best practice violations
4. Refactoring suggestions"""
        else:  # comprehensive
            prompt += """1. Code structure and organization
2. Potential bugs or issues
3. Performance considerations
4. Security implications
5. Best practice alignment"""
        
        return prompt
    
    def save_to_history(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        metadata: Dict[str, Any] = None,
    ):
        """Save interaction to conversation history."""
        try:
            self.history_service.save_conversation(
                session_id=session_id,
                user_message=user_message,
                agent_response=agent_response,
                agent_type=self.agent_type,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error saving to history: {e}")
    
    def log_execution(
        self,
        session_id: str,
        task_description: str,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0,
        tokens_used: int = 0,
        model_used: str = None,
    ):
        """Log execution to execution history."""
        try:
            self.history_service.save_execution(
                session_id=session_id,
                agent_type=self.agent_type,
                task_description=task_description,
                status=status,
                result=result,
                error_message=error,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                model_used=model_used,
            )
        except Exception as e:
            logger.error(f"Error logging execution: {e}")
    
    async def create_response(
        self,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        execution_time_ms: float = 0,
        tokens_used: Optional[int] = None,
    ) -> AgentResponse:
        """Create standardized agent response."""
        return AgentResponse(
            success=success,
            agent_type=self.agent_type,
            result=result,
            error=error,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms,
            tokens_used=tokens_used,
        )
