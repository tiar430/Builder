from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.request_models import HealthResponse, ModelInfo
from backend.config import settings
import httpx
from typing import List

router = APIRouter(prefix="/health", tags=["health"])


async def check_ollama():
    """Check if Ollama is available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def check_mistral():
    """Check if Mistral API is available."""
    return bool(settings.MISTRAL_API_KEY)


@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    ollama_available = await check_ollama()
    mistral_available = await check_mistral()
    database_connected = True
    
    try:
        db.execute("SELECT 1")
    except Exception:
        database_connected = False
    
    return HealthResponse(
        status="healthy" if all([ollama_available or mistral_available, database_connected]) else "degraded",
        version=settings.APP_VERSION,
        ollama_available=ollama_available,
        ollama_model=settings.OLLAMA_MODEL,
        mistral_available=mistral_available,
        database_connected=database_connected,
        mcp_enabled=settings.MCP_ENABLED,
    )


@router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """Get list of available models."""
    models = []
    
    # Check Ollama models
    ollama_available = await check_ollama()
    if ollama_available:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("models", []):
                        models.append(
                            ModelInfo(
                                name=model.get("name", "unknown"),
                                type="local",
                                provider="ollama",
                                available=True,
                            )
                        )
        except Exception:
            pass
    
    # Mistral AI
    if await check_mistral():
        models.append(
            ModelInfo(
                name=settings.MISTRAL_MODEL,
                type="cloud",
                provider="mistral",
                available=True,
            )
        )
    
    return models
