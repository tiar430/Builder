import logging
import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMService
from backend.models.request_models import AgentResponse

logger = logging.getLogger(__name__)


class DocsGeneratorAgent(BaseAgent):
    """Agent for generating documentation from code."""
    
    agent_type = "docs_generator"
    
    def __init__(self, llm_service: LLMService, db: Session):
        super().__init__(llm_service, db)
    
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Generate documentation for code.
        
        Context should contain:
            - code: source code to document
            - language: programming language
            - doc_type: 'function', 'class', 'module', or 'api'
            - style: 'google', 'numpy', or 'sphinx'
            - session_id: (optional) session identifier
        """
        start_time = time.time()
        
        try:
            code = context.get("code")
            language = context.get("language")
            doc_type = context.get("doc_type", "function")
            style = context.get("style", "google")
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
            
            # Extract code elements
            functions = self.code_parser.extract_functions(code, language)
            imports = self.code_parser.extract_imports(code, language)
            
            # Build documentation context
            doc_context = {
                "code": code,
                "language": language,
                "doc_type": doc_type,
                "style": style,
                "functions_count": len(functions),
                "imports_count": len(imports),
            }
            
            # Build prompt
            system_prompt = self.build_system_prompt(
                "Technical Documentation Expert",
                f"You are an expert at writing clear, comprehensive {style}-style documentation. "
                f"Generate {doc_type} documentation that is easy to understand and follow."
            )
            
            user_prompt = self._build_docs_prompt(
                code,
                language,
                doc_type,
                style,
                functions,
            )
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call LLM
            response, provider = await self.call_llm(
                prompt=full_prompt,
                temperature=0.4,
                max_tokens=3000,
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
                user_message=f"Generate {doc_type} documentation ({style} style)",
                agent_response=response,
                metadata={
                    "language": language,
                    "doc_type": doc_type,
                    "style": style,
                    "provider": provider,
                },
            )
            
            # Log execution
            execution_time_ms = (time.time() - start_time) * 1000
            self.log_execution(
                session_id=session_id,
                task_description=f"Generate {doc_type} documentation ({style} style)",
                status="completed",
                result=response[:500],
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                model_used=provider,
            )
            
            return await self.create_response(
                success=True,
                result=response,
                metadata={
                    "language": language,
                    "doc_type": doc_type,
                    "style": style,
                    "provider": provider,
                },
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
            )
        
        except Exception as e:
            logger.error(f"Docs generator error: {e}", exc_info=True)
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.log_execution(
                session_id=context.get("session_id", "default"),
                task_description="Generate documentation",
                status="failed",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            
            return await self.create_response(
                success=False,
                error=f"Docs generator error: {str(e)}",
                execution_time_ms=execution_time_ms,
            )
    
    def _build_docs_prompt(
        self,
        code: str,
        language: str,
        doc_type: str,
        style: str,
        functions: list,
    ) -> str:
        """Build documentation generation prompt."""
        prompt = f"""Generate {style}-style {doc_type} documentation for this {language} code:


{code}


"""
        
        if doc_type == "function":
            prompt += """Create documentation for the main function including:
1. **Summary**: One-line description
2. **Detailed Description**: What the function does and why
3. **Parameters**: List all parameters with types and descriptions
4. **Returns**: Describe return value and type
5. **Raises**: List any exceptions that can be raised
6. **Examples**: Provide usage examples
7. **Notes**: Additional important information"""
        
        elif doc_type == "class":
            prompt += """Create documentation for the main class including:
1. **Class Summary**: Purpose and usage
2. **Attributes**: List all class attributes with types and descriptions
3. **Methods**: Document key methods
4. **Properties**: Document any properties
5. **Usage Examples**: Show how to use the class
6. **Design Patterns**: Mention any patterns used
7. **Notes**: Special considerations or warnings"""
        
        elif doc_type == "module":
            prompt += """Create module documentation including:
1. **Module Overview**: Purpose and scope
2. **Main Components**: List classes, functions, and their purposes
3. **Dependencies**: External dependencies and imports
4. **Usage Guide**: How to use the module
5. **Examples**: Code examples showing typical usage
6. **Configuration**: Any required configuration
7. **Performance Notes**: Performance considerations if any"""
        
        elif doc_type == "api":
            prompt += """Create API documentation including:
1. **Endpoints**: List all API endpoints
2. **Methods**: GET, POST, PUT, DELETE, etc.
3. **Parameters**: Request parameters and types
4. **Responses**: Response format and status codes
5. **Error Handling**: Error responses and codes
6. **Authentication**: Required authentication methods
7. **Rate Limiting**: Rate limiting information if any
8. **Examples**: Example requests and responses"""
        
        prompt += f"""

Format the documentation using {style} style:"""
        
        if style == "google":
            prompt += """
- Use Google-style docstrings
- Format: Summary, Extended description, Args, Returns, Raises, Examples"""
        elif style == "numpy":
            prompt += """
- Use NumPy-style docstrings
- Format: Summary, Extended description, Parameters, Returns, Raises, Examples, Notes"""
        elif style == "sphinx":
            prompt += """
- Use Sphinx/RST style
- Format: :param:, :type:, :returns:, :rtype:, :raises:"""
        
        return prompt
