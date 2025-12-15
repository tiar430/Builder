import chainlit as cl
import httpx
import json
from typing import Optional, List, Dict, Any
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = 60

# Initialize HTTP client
client = httpx.AsyncClient(timeout=API_TIMEOUT)


def get_language_from_filename(filename: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
    }
    
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    
    return "unknown"


@cl.on_chat_start
async def start():
    """Initialize chat session."""
    cl.user_session.set("session_id", cl.user_session.get("id"))
    
    welcome_message = """# Welcome to AI Agent Multi-Tasking System 🤖

I'm your intelligent code assistant. I can help you with:

- **🐛 Debug Code**: Identify and fix bugs in your code
- **🔍 Analyze Code**: Check quality, security, and performance
- **📚 Generate Docs**: Create documentation automatically
- **⚡ Execute Tasks**: Run multiple analysis tasks at once

### How to use:
1. **Paste code directly** in the chat or **upload a file**
2. **Select what you need**: debugging, analysis, or documentation
3. I'll analyze and provide recommendations
4. View your **conversation history** and metrics anytime

### Supported Languages:
Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, PHP, Swift, Kotlin, and more!

---

**What can I help you with today?**"""
    
    await cl.Message(welcome_message).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming user messages."""
    user_input = message.content
    session_id = cl.user_session.get("session_id")
    
    # Check if there are file attachments
    file_content = None
    language = None
    
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                file_content = element.content.decode('utf-8', errors='ignore')
                language = get_language_from_filename(element.name)
                break
    
    # If no file, check if message contains code
    if not file_content:
        if "```" in user_input:
            # Extract code from markdown code block
            import re
            match = re.search(r'```(\w+)?\n(.*?)\n```', user_input, re.DOTALL)
            if match:
                language = match.group(1) or "unknown"
                file_content = match.group(2)
    
    # Determine action based on user input
    if any(word in user_input.lower() for word in ["debug", "fix", "error", "bug"]):
        await handle_debug(file_content, user_input, language, session_id)
    elif any(word in user_input.lower() for word in ["analyze", "review", "check", "security", "performance", "quality"]):
        await handle_analyze(file_content, user_input, language, session_id)
    elif any(word in user_input.lower() for word in ["document", "doc", "docs", "documentation"]):
        await handle_docs(file_content, user_input, language, session_id)
    elif any(word in user_input.lower() for word in ["task", "orchestrate", "execute", "multiple"]):
        await handle_orchestration(file_content, user_input, language, session_id)
    else:
        # Default: show options
        await show_action_menu(file_content, language, session_id)


async def handle_debug(code: Optional[str], user_input: str, language: Optional[str], session_id: str):
    """Handle code debugging request."""
    if not code:
        await cl.Message("Please paste or upload code to debug.").send()
        return
    
    # Extract error message if provided
    error_msg = None
    if "error:" in user_input.lower():
        error_msg = user_input.split("error:")[-1].strip()
    
    # Send thinking message
    response_msg = cl.Message(content="🔍 Analyzing code for bugs...")
    await response_msg.send()
    
    try:
        request_data = {
            "code": code,
            "language": language or "unknown",
            "error_message": error_msg,
        }
        
        api_response = await client.post(
            f"{BACKEND_URL}/agent/debug",
            json=request_data,
        )
        
        if api_response.status_code == 200:
            result = api_response.json()
            debug_result = result.get("result", "")
            execution_time = result.get("execution_time_ms", 0)
            tokens = result.get("tokens_used")
            
            # Format response with metadata
            response_text = f"""## 🐛 Debug Analysis

{debug_result}

---
**Execution Time**: {execution_time:.2f}ms
**Tokens Used**: {tokens or 'N/A'}
**Language**: {language or 'detected'}"""
            
            response_msg.content = response_text
            await response_msg.update()
        else:
            response_msg.content = f"❌ Error: {api_response.text}"
            await response_msg.update()
    
    except Exception as e:
        response_msg.content = f"❌ Connection error: {str(e)}"
        await response_msg.update()


async def handle_analyze(code: Optional[str], user_input: str, language: Optional[str], session_id: str):
    """Handle code analysis request."""
    if not code:
        await cl.Message("Please paste or upload code to analyze.").send()
        return
    
    # Determine analysis type
    analysis_type = "comprehensive"
    if "security" in user_input.lower():
        analysis_type = "security"
    elif "performance" in user_input.lower():
        analysis_type = "performance"
    elif "quality" in user_input.lower():
        analysis_type = "quality"
    
    response_msg = cl.Message(content=f"🔍 Running {analysis_type} analysis...")
    await response_msg.send()
    
    try:
        request_data = {
            "code": code,
            "language": language or "unknown",
            "analysis_type": analysis_type,
        }
        
        api_response = await client.post(
            f"{BACKEND_URL}/agent/analyze",
            json=request_data,
        )
        
        if api_response.status_code == 200:
            result = api_response.json()
            analysis_result = result.get("result", "")
            execution_time = result.get("execution_time_ms", 0)
            tokens = result.get("tokens_used")
            
            response_text = f"""## 📊 {analysis_type.capitalize()} Analysis

{analysis_result}

---
**Analysis Type**: {analysis_type}
**Execution Time**: {execution_time:.2f}ms
**Tokens Used**: {tokens or 'N/A'}"""
            
            response_msg.content = response_text
            await response_msg.update()
        else:
            response_msg.content = f"❌ Error: {api_response.text}"
            await response_msg.update()
    
    except Exception as e:
        response_msg.content = f"❌ Connection error: {str(e)}"
        await response_msg.update()


async def handle_docs(code: Optional[str], user_input: str, language: Optional[str], session_id: str):
    """Handle documentation generation request."""
    if not code:
        await cl.Message("Please paste or upload code to document.").send()
        return
    
    # Determine doc type and style
    doc_type = "function"
    if "class" in user_input.lower():
        doc_type = "class"
    elif "module" in user_input.lower():
        doc_type = "module"
    elif "api" in user_input.lower():
        doc_type = "api"
    
    style = "google"
    if "numpy" in user_input.lower():
        style = "numpy"
    elif "sphinx" in user_input.lower():
        style = "sphinx"
    
    response_msg = cl.Message(content=f"📚 Generating {style}-style {doc_type} documentation...")
    await response_msg.send()
    
    try:
        request_data = {
            "code": code,
            "language": language or "unknown",
            "doc_type": doc_type,
            "style": style,
        }
        
        api_response = await client.post(
            f"{BACKEND_URL}/agent/generate-docs",
            json=request_data,
        )
        
        if api_response.status_code == 200:
            result = api_response.json()
            docs_result = result.get("result", "")
            execution_time = result.get("execution_time_ms", 0)
            tokens = result.get("tokens_used")
            
            response_text = f"""## 📚 Generated Documentation

{docs_result}

---
**Doc Type**: {doc_type}
**Style**: {style}
**Execution Time**: {execution_time:.2f}ms
**Tokens Used**: {tokens or 'N/A'}"""
            
            response_msg.content = response_text
            await response_msg.update()
        else:
            response_msg.content = f"❌ Error: {api_response.text}"
            await response_msg.update()
    
    except Exception as e:
        response_msg.content = f"❌ Connection error: {str(e)}"
        await response_msg.update()


async def handle_orchestration(code: Optional[str], user_input: str, language: Optional[str], session_id: str):
    """Handle multi-task orchestration."""
    if not code:
        await cl.Message("Please paste or upload code for multi-task execution.").send()
        return
    
    response_msg = cl.Message(content="⚡ Executing multiple analysis tasks...")
    await response_msg.send()
    
    try:
        # Create tasks for analysis
        tasks = [
            {
                "task_id": "debug",
                "task_type": "debugger",
                "input_data": {
                    "code": code,
                    "language": language or "unknown",
                },
                "depends_on": [],
                "priority": 0,
            },
            {
                "task_id": "analyze",
                "task_type": "analyzer",
                "input_data": {
                    "code": code,
                    "language": language or "unknown",
                    "analysis_type": "comprehensive",
                },
                "depends_on": [],
                "priority": 0,
            },
            {
                "task_id": "docs",
                "task_type": "docs_generator",
                "input_data": {
                    "code": code,
                    "language": language or "unknown",
                    "doc_type": "function",
                    "style": "google",
                },
                "depends_on": [],
                "priority": 0,
            },
        ]
        
        request_data = {
            "session_id": session_id,
            "tasks": tasks,
            "parallel_execution": True,
        }
        
        api_response = await client.post(
            f"{BACKEND_URL}/agent/orchestrate",
            json=request_data,
        )
        
        if api_response.status_code == 200:
            result = api_response.json()
            orchestration_result = result.get("result", "")
            metadata = result.get("metadata", {})
            execution_time = result.get("execution_time_ms", 0)
            
            response_text = f"""## ⚡ Multi-Task Orchestration Results

{orchestration_result}

---
**Total Tasks**: {metadata.get('total_tasks', 0)}
**Completed**: {metadata.get('completed_tasks', 0)}
**Failed**: {metadata.get('failed_tasks', 0)}
**Total Execution Time**: {execution_time:.2f}ms"""
            
            response_msg.content = response_text
            await response_msg.update()
        else:
            response_msg.content = f"❌ Error: {api_response.text}"
            await response_msg.update()
    
    except Exception as e:
        response_msg.content = f"❌ Connection error: {str(e)}"
        await response_msg.update()


async def show_action_menu(code: Optional[str], language: Optional[str], session_id: str):
    """Show action menu for user to choose."""
    if code:
        message = f"""I found code ({language or 'unknown'} language). What would you like me to do?

Type one of:
- **Debug** - Find and fix bugs
- **Analyze** - Review code quality, security, or performance
- **Document** - Generate documentation
- **Multi-task** - Run all analyses

Or upload a different file."""
    else:
        message = """Please **paste code** or **upload a file** to get started!

I can help with:
- 🐛 **Debug** - Fix bugs and errors
- 🔍 **Analyze** - Check quality, security, performance
- 📚 **Document** - Generate documentation
- ⚡ **Execute** - Run multiple tasks"""
    
    await cl.Message(message).send()


@cl.on_file_upload
async def on_file_upload(files: List[cl.File]) -> str:
    """Handle file uploads."""
    if not files:
        return ""
    
    file = files[0]
    try:
        content = file.content.decode('utf-8', errors='ignore')
        language = get_language_from_filename(file.name)
        
        message = f"""✅ **File Uploaded**: {file.name}
**Language**: {language}
**Size**: {len(content)} characters

What would you like me to do with this code?"""
        
        await cl.Message(message).send()
        return content
    
    except Exception as e:
        await cl.Message(f"❌ Error reading file: {str(e)}").send()
        return ""
