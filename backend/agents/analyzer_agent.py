import logging
import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import LLMService
from backend.models.request_models import AgentResponse

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """Agent for analyzing code quality, security, and performance."""
    
    agent_type = "analyzer"
    
    def __init__(self, llm_service: LLMService, db: Session):
        super().__init__(llm_service, db)
    
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze code for quality, security, or performance.
        
        Context should contain:
            - code: source code to analyze
            - language: programming language
            - analysis_type: 'security', 'performance', 'quality', or 'comprehensive'
            - session_id: (optional) session identifier
        """
        start_time = time.time()
        
        try:
            code = context.get("code")
            language = context.get("language")
            analysis_type = context.get("analysis_type", "comprehensive")
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
            
            # Get code quality metrics
            quality_metrics = self.code_parser.analyze_code_quality(code, language)
            
            # Extract code elements
            functions = self.code_parser.extract_functions(code, language)
            imports = self.code_parser.extract_imports(code, language)
            
            # Build analysis context
            analysis_context = {
                "code": code,
                "language": language,
                "analysis_type": analysis_type,
                "quality_metrics": quality_metrics,
                "functions_count": len(functions),
                "imports_count": len(imports),
            }
            
            # Build prompt
            system_prompt = self.build_system_prompt(
                "Code Analysis Expert",
                f"You are an expert code reviewer and analyst. "
                f"Perform {analysis_type} analysis with actionable insights."
            )
            
            user_prompt = self._build_analysis_prompt(
                code,
                language,
                analysis_type,
                quality_metrics,
                functions,
            )
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call LLM
            response, provider = await self.call_llm(
                prompt=full_prompt,
                temperature=0.5,
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
                user_message=f"Analyze {language} code ({analysis_type})",
                agent_response=response,
                metadata={
                    "language": language,
                    "analysis_type": analysis_type,
                    "quality_metrics": quality_metrics,
                    "provider": provider,
                },
            )
            
            # Log execution
            execution_time_ms = (time.time() - start_time) * 1000
            self.log_execution(
                session_id=session_id,
                task_description=f"Analyze {language} code ({analysis_type})",
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
                    "analysis_type": analysis_type,
                    "quality_metrics": quality_metrics,
                    "provider": provider,
                },
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
            )
        
        except Exception as e:
            logger.error(f"Analyzer agent error: {e}", exc_info=True)
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.log_execution(
                session_id=context.get("session_id", "default"),
                task_description="Analyze code",
                status="failed",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            
            return await self.create_response(
                success=False,
                error=f"Analyzer error: {str(e)}",
                execution_time_ms=execution_time_ms,
            )
    
    def _build_analysis_prompt(
        self,
        code: str,
        language: str,
        analysis_type: str,
        quality_metrics: Dict,
        functions: list,
    ) -> str:
        """Build comprehensive analysis prompt."""
        prompt = f"""Analyze this {language} code:


{code}


Code Metrics:
- Total lines: {quality_metrics.get('total_lines')}
- Non-empty lines: {quality_metrics.get('non_empty_lines')}
- Functions/Methods: {len(functions)}
- Long lines (>100 chars): {quality_metrics.get('long_lines')}
- Average line length: {quality_metrics.get('average_line_length', 0):.1f}

"""
        
        if analysis_type == "security":
            prompt += """Perform a security analysis focusing on:
1. **Vulnerability Detection**: Identify potential security vulnerabilities
2. **Data Handling**: Check for proper data validation and sanitization
3. **API Security**: Assess API endpoints and authentication
4. **Risk Assessment**: Rate severity of each issue
5. **Mitigation Strategies**: Provide specific fixes for each vulnerability
6. **Security Best Practices**: Recommend industry-standard practices"""
        
        elif analysis_type == "performance":
            prompt += """Perform a performance analysis focusing on:
1. **Bottleneck Identification**: Find performance-critical sections
2. **Complexity Analysis**: Evaluate algorithm complexity
3. **Resource Usage**: Check for memory leaks or inefficient resource usage
4. **Optimization Opportunities**: Suggest concrete improvements
5. **Benchmarking Tips**: Recommend tools for measuring improvements
6. **Scalability**: Assess how code handles increased load"""
        
        elif analysis_type == "quality":
            prompt += """Perform a quality analysis focusing on:
1. **Code Structure**: Evaluate organization and modularity
2. **Readability**: Check naming conventions and documentation
3. **Best Practices**: Identify violations of language conventions
4. **Test Coverage**: Assess testability of the code
5. **Refactoring Suggestions**: Provide specific refactoring opportunities
6. **Maintainability**: Rate how easy it is to maintain and extend"""
        
        else:  # comprehensive
            prompt += """Perform a comprehensive analysis covering:
1. **Code Structure & Organization**: How well is the code organized?
2. **Readability & Maintainability**: Is it easy to understand and modify?
3. **Security Concerns**: Are there potential security issues?
4. **Performance Implications**: Are there optimization opportunities?
5. **Best Practices Alignment**: Does it follow language conventions?
6. **Bug Potential**: Are there patterns that could lead to bugs?
7. **Testing & Documentation**: Is the code testable and documented?
8. **Overall Quality Score**: Rate on scale 1-10 with justification"""
        
        prompt += "\n\nProvide detailed, actionable feedback with specific examples and code snippets where applicable."
        
        return prompt
