import httpx
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from the model."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=300)  # 5 min timeout for large models
    
    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name") == self.model for m in models)
            return False
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Generate text using Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama generation failed: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return ""


class MistralProvider(LLMProvider):
    """Mistral AI cloud provider."""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.MISTRAL_API_KEY
        self.model = model or settings.MISTRAL_MODEL
        self.base_url = "https://api.mistral.ai/v1"
        self.client = httpx.AsyncClient(timeout=60)
    
    async def is_available(self) -> bool:
        """Check if Mistral API is available."""
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Generate text using Mistral AI."""
        if not self.api_key:
            logger.error("Mistral API key not configured")
            return ""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            else:
                logger.error(f"Mistral generation failed: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error calling Mistral: {e}")
            return ""


class LLMService:
    """Service for managing LLM providers with fallback logic."""
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.available_providers: List[LLMProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers."""
        # Try Ollama first (local, faster)
        self.providers.append(OllamaProvider())
        
        # Then Mistral (cloud fallback)
        self.providers.append(MistralProvider())
    
    async def initialize(self):
        """Check which providers are available."""
        self.available_providers = []
        for provider in self.providers:
            if await provider.is_available():
                self.available_providers.append(provider)
                logger.info(f"LLM Provider available: {provider.__class__.__name__}")
        
        if not self.available_providers:
            logger.warning("No LLM providers available!")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        **kwargs
    ) -> tuple[str, str]:
        """Generate text using available providers with fallback.
        
        Returns:
            Tuple of (generated_text, provider_name)
        """
        if not self.available_providers:
            await self.initialize()
        
        for provider in self.available_providers:
            try:
                result = await provider.generate(
                    prompt=prompt,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    **kwargs
                )
                if result:
                    return result, provider.__class__.__name__
            except Exception as e:
                logger.warning(f"Error with {provider.__class__.__name__}: {e}")
                continue
        
        return "", "none"
    
    async def count_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Dependency for getting LLM service."""
    if not llm_service.available_providers:
        await llm_service.initialize()
    return llm_service
