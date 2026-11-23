"""Multi-provider AI package exports."""

from .gemini_client import GeminiResumeClient, generate_offline_content
from .provider_manager import ProviderManager
from .providers import (
    BaseAIProvider,
    GeminiProvider,
    GroqProvider,
    CohereProvider,
    OpenRouterProvider,
    CloudflareProvider,
    OfflineProvider,
    PROVIDER_REGISTRY,
)
from .structured_schemas import TailoredProject, TailoredResumeContent
from .fallback import GeminiAPIError, InvalidAPIKeyError

__all__ = [
    "ProviderManager",
    "BaseAIProvider",
    "GeminiProvider",
    "GroqProvider",
    "CohereProvider",
    "OpenRouterProvider",
    "CloudflareProvider",
    "OfflineProvider",
    "PROVIDER_REGISTRY",
    "GeminiResumeClient",
    "generate_offline_content",
    "TailoredProject",
    "TailoredResumeContent",
    "GeminiAPIError",
    "InvalidAPIKeyError",
]
