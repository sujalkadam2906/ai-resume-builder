"""Provider registry package exports."""

from typing import Dict, Type
from .base import BaseAIProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .cohere_provider import CohereProvider
from .openrouter_provider import OpenRouterProvider
from .cloudflare_provider import CloudflareProvider
from .offline_provider import OfflineProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseAIProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "cohere": CohereProvider,
    "openrouter": OpenRouterProvider,
    "cloudflare": CloudflareProvider,
    "offline": OfflineProvider,
}

__all__ = [
    "BaseAIProvider",
    "GeminiProvider",
    "GroqProvider",
    "CohereProvider",
    "OpenRouterProvider",
    "CloudflareProvider",
    "OfflineProvider",
    "PROVIDER_REGISTRY",
]
