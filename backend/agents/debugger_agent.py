import logging
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMService
from backend.models.request_models import AgentResponse

logger = logging.getLogger(__name__)


class DebuggerAgent(BaseAgent):
    """Agent for debugging code in multiple programming languages."""
    
    agent_type = "debugger"
    
    def __init__(self, llm_service: LLMService, db: Session):
        super().__init__(llm_service, db)
    
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Debug code and provide fixes.
        
        Context should contain:
            - code: source code to debug
            - language: programming language
            - error_message: (optional) error message
            - session_id: (optional) session identifier
        """
        start_time = time.time()
        
        try:
            code = context.get("code")
            language = context.get("language")
            error_message = context.get("error_message")
            session_id = context.get("session_id", "default")
            
            if not code:
                return await self.create_response(
                    success=False,
                    error="No code provided",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Detect language if not provided
            if not language:
                language = self.code_parser.detect_language(code)
            
            # Analyze code for syntax errors
            syntax_errors = self.code_parser.find_syntax_errors(code, language)
            
            # Prepare debugging context
            debug_context = {
                "code": code,
                "language": language,
                "error_message": error_message,
                "syntax_errors": syntax_errors,
            }
            
            # Build prompt for LLM
            system_prompt = self.build_system_prompt(
                "Professional Code Debugger",
                "You are an expert debugger proficient in multiple programming languages. "
                "Analyze code, identify bugs, and provide clear, actionable solutions."
            )
            
            user_prompt = self._build_debug_prompt(code, language, error_message, syntax_errors)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call LLM
            response, provider = await self.call_llm(
                prompt=full_prompt,
                temperature=0.3,  # Lower temperature for precise debugging
                max_tokens=2048,
            )
            
            if not response:
                return await self.create_response(
                    success=False,
                    error="Failed to get response from LLM",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Estimate tokens
            tokens_used = len(full_prompt) // 4 + len(response) // 4
            
            # Save to history
            self.save_to_history(
                session_id=session_id,
                user_message=f"Debug {language} code",
                agent_response=response,
                metadata={
                    "language": language,
                    "error_message": error_message,
                    "syntax_errors_found": len(syntax_errors),
                    "provider": provider,
                },
            )
            
            # Log execution
            execution_time_ms = (time.time() - start_time) * 1000
            self.log_execution(
                session_id=session_id,
                task_description=f"Debug {language} code",
                status="completed",
                result=response[:500],  # Store first 500 chars
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                model_used=provider,
            )
            
            return await self.create_response(
                success=True,
                result=response,
                metadata={
                    "language": language,
                    "syntax_errors": syntax_errors,
                    "provider": provider,
                },
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
            )
        
        except Exception as e:
            logger.error(f"Debugger agent error: {e}", exc_info=True)
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.log_execution(
                session_id=context.get("session_id", "default"),
                task_description="Debug code",
                status="failed",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            
            return await self.create_response(
                success=False,
                error=f"Debugger error: {str(e)}",
                execution_time_ms=execution_time_ms,
            )
    
    def _build_debug_prompt(
        self,
        code: str,
        language: str,
        error_message: Optional[str],
        syntax_errors: list,
    ) -> str:
        """Build comprehensive debugging prompt."""
        prompt = f"""I need help debugging this {language} code:


{code}
```

"""
        
        if error_message:
            prompt += f"Error message: {error_message}\n\n"
        
        if syntax_errors:
            prompt += "Found potential issues:\n"
            for error in syntax_errors:
                prompt += f"- {error['message']}"
                if 'line' in error:
                    prompt += f" (line {error['line']})"
                prompt += "\n"
            prompt += "\n"
        
        prompt += """Please provide:
1. **Issue Identification**: What specific issues exist in the code?
2. **Root Cause Analysis**: Why do these issues occur?
3. **Detailed Solution**: How to fix each issue (provide corrected code)
4. **Prevention Tips**: How to avoid similar issues in the future
5. **Testing Suggestions**: How to verify the fixes work

Format your response with clear sections and code blocks."""
        
        return prompt
