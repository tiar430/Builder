import logging
import time
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.agents.base_agent import BaseAgent
from backend.agents.debugger_agent import DebuggerAgent
from backend.agents.analyzer_agent import AnalyzerAgent
from backend.agents.docs_generator import DocsGeneratorAgent
from backend.services.llm_service import LLMService
from backend.models.request_models import AgentResponse, Task, TaskResult

logger = logging.getLogger(__name__)


class TaskOrchestrator(BaseAgent):
    """Orchestrator for managing multiple agent tasks."""
    
    agent_type = "orchestrator"
    
    def __init__(self, llm_service: LLMService, db: Session):
        super().__init__(llm_service, db)
        # Initialize all available agents
        self.agents = {
            "debugger": DebuggerAgent(llm_service, db),
            "analyzer": AnalyzerAgent(llm_service, db),
            "docs_generator": DocsGeneratorAgent(llm_service, db),
        }
    
    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Execute multiple tasks in sequence or parallel.
        
        Context should contain:
            - tasks: List of Task objects
            - parallel_execution: Whether to execute tasks in parallel
            - session_id: Session identifier
        """
        start_time = time.time()
        session_id = context.get("session_id", "default")
        
        try:
            tasks = context.get("tasks", [])
            parallel_execution = context.get("parallel_execution", False)
            
            if not tasks:
                return await self.create_response(
                    success=False,
                    error="No tasks provided",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Resolve dependencies
            task_order = self._resolve_dependencies(tasks)
            
            # Execute tasks
            results = []
            if parallel_execution and not self._has_dependencies(tasks):
                # Execute independent tasks in parallel
                results = await self._execute_parallel(task_order, session_id)
            else:
                # Execute tasks sequentially
                results = await self._execute_sequential(task_order, session_id)
            
            # Aggregate results
            overall_success = all(r.status == "completed" for r in results)
            completed_count = sum(1 for r in results if r.status == "completed")
            failed_count = sum(1 for r in results if r.status == "failed")
            
            # Build response
            result_summary = "\n\n".join([
                f"### Task {i+1}: {r.task_id}\n"
                f"Status: {r.status}\n"
                f"Time: {r.execution_time_ms:.2f}ms\n"
                f"Result:\n{r.result or r.error}"
                for i, r in enumerate(results)
            ])
            
            # Save to history
            self.save_to_history(
                session_id=session_id,
                user_message=f"Execute {len(tasks)} tasks",
                agent_response=result_summary,
                metadata={
                    "total_tasks": len(tasks),
                    "completed": completed_count,
                    "failed": failed_count,
                    "parallel": parallel_execution,
                },
            )
            
            # Log execution
            execution_time_ms = (time.time() - start_time) * 1000
            self.log_execution(
                session_id=session_id,
                task_description=f"Execute {len(tasks)} tasks orchestration",
                status="completed" if overall_success else "partial",
                result=result_summary[:500],
                execution_time_ms=execution_time_ms,
                tokens_used=sum(r.execution_time_ms // 10 for r in results),  # Rough estimate
            )
            
            return await self.create_response(
                success=overall_success,
                result=result_summary,
                metadata={
                    "total_tasks": len(tasks),
                    "completed_tasks": completed_count,
                    "failed_tasks": failed_count,
                    "task_results": [
                        {
                            "task_id": r.task_id,
                            "status": r.status,
                            "execution_time_ms": r.execution_time_ms,
                        }
                        for r in results
                    ],
                },
                execution_time_ms=execution_time_ms,
            )
        
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.log_execution(
                session_id=session_id,
                task_description="Task orchestration",
                status="failed",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            
            return await self.create_response(
                success=False,
                error=f"Orchestrator error: {str(e)}",
                execution_time_ms=execution_time_ms,
            )
    
    def _resolve_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Resolve task dependencies and return ordered list."""
        # Create dependency graph
        completed = set()
        ordered = []
        
        while len(ordered) < len(tasks):
            for task in tasks:
                if task.task_id in completed:
                    continue
                
                # Check if all dependencies are completed
                if all(dep in completed for dep in task.depends_on):
                    ordered.append(task)
                    completed.add(task.task_id)
                    break
            else:
                # If we get here, there's a circular dependency
                logger.warning("Circular dependency detected, adding remaining tasks")
                for task in tasks:
                    if task.task_id not in completed:
                        ordered.append(task)
                break
        
        # Sort by priority (higher priority first)
        return sorted(ordered, key=lambda t: -t.priority)
    
    def _has_dependencies(self, tasks: List[Task]) -> bool:
        """Check if any tasks have dependencies."""
        return any(task.depends_on for task in tasks)
    
    async def _execute_parallel(
        self,
        tasks: List[Task],
        session_id: str,
    ) -> List[TaskResult]:
        """Execute independent tasks in parallel."""
        coroutines = [
            self._execute_single_task(task, session_id)
            for task in tasks
        ]
        return await asyncio.gather(*coroutines, return_exceptions=True)
    
    async def _execute_sequential(
        self,
        tasks: List[Task],
        session_id: str,
    ) -> List[TaskResult]:
        """Execute tasks sequentially."""
        results = []
        task_outputs = {}  # Store outputs for dependent tasks
        
        for task in tasks:
            result = await self._execute_single_task(task, session_id)
            results.append(result)
            
            # Store output for dependent tasks
            if result.status == "completed":
                task_outputs[task.task_id] = result.result
        
        return results
    
    async def _execute_single_task(
        self,
        task: Task,
        session_id: str,
    ) -> TaskResult:
        """Execute a single task."""
        task_start = time.time()
        
        try:
            task_type = task.task_type
            
            if task_type not in self.agents:
                return TaskResult(
                    task_id=task.task_id,
                    task_type=task_type,
                    status="failed",
                    error=f"Unknown task type: {task_type}",
                    execution_time_ms=(time.time() - task_start) * 1000,
                )
            
            agent = self.agents[task_type]
            
            # Prepare context for agent
            agent_context = {
                **task.input_data,
                "session_id": session_id,
            }
            
            # Execute agent
            agent_response = await agent.execute(agent_context)
            
            execution_time_ms = (time.time() - task_start) * 1000
            
            return TaskResult(
                task_id=task.task_id,
                task_type=task_type,
                status="completed" if agent_response.success else "failed",
                result=agent_response.result,
                error=agent_response.error,
                execution_time_ms=execution_time_ms,
            )
        
        except Exception as e:
            logger.error(f"Task {task.task_id} execution error: {e}")
            execution_time_ms = (time.time() - task_start) * 1000
            
            return TaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                status="failed",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
