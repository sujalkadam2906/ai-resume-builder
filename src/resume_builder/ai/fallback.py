"""Gemini model discovery, priority ranking, and intelligent fallback handling."""

import logging
import time
from typing import Any, Callable, List, Optional, Tuple
from ..config import config

logger = logging.getLogger("resume_builder.ai")


class GeminiAPIError(Exception):
    """Base error for Gemini API failures."""
    pass


class InvalidAPIKeyError(GeminiAPIError):
    """Raised when API key is missing, unauthorized, or invalid."""
    pass


class ModelUnavailableError(GeminiAPIError):
    """Raised when a specific model is not found or not supported."""
    pass


class QuotaExhaustedError(GeminiAPIError):
    """Raised when quota/billing is exhausted (HTTP 429)."""
    pass


def classify_error(err: Exception) -> Tuple[str, str]:
    """Classify API exception into code and human-readable advice."""
    err_str = str(err)
    if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
        return "AUTH_ERROR", "Invalid or missing GEMINI_API_KEY. Please verify your key in .env."
    if "404" in err_str or "NOT_FOUND" in err_str:
        return "MODEL_NOT_FOUND", "The requested model was not found or is deprecated."
    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
        return "QUOTA_EXHAUSTED", "Rate limit reached or quota exhausted. Attempting fallback model."
    if any(code in err_str for code in ["500", "503", "504", "UNAVAILABLE"]):
        return "SERVER_ERROR", "Temporary Google service disruption. Retrying with exponential backoff."
    if "400" in err_str or "INVALID_ARGUMENT" in err_str:
        return "BAD_REQUEST", "Invalid request parameters or schema constraint mismatch."
    return "UNKNOWN", f"Unexpected error: {err_str}"


def discover_active_model(client: Any, candidate_models: List[str]) -> str:
    """
    Validate candidates against the API or probe model availability.
    Returns the highest-priority functional candidate model.
    """
    logger.info("Discovering usable Gemini models from candidate list...")
    # Attempt to list models if supported
    available_api_names = set()
    try:
        models_pager = client.models.list()
        for m in models_pager:
            name = getattr(m, "name", "")
            # e.g. 'models/gemini-2.5-flash' -> 'gemini-2.5-flash'
            short_name = name.split("/")[-1] if "/" in name else name
            available_api_names.add(short_name)
    except Exception as e:
        logger.debug(f"Could not list models directly: {e}. Will test candidates sequentially.")

    for model_name in candidate_models:
        if available_api_names and model_name not in available_api_names:
            logger.debug(f"Model {model_name} not listed in available API models, skipping.")
            continue
        return model_name

    # If none from candidate list matched listed models, default to candidate #1 or 3.8-flash
    for fallback in candidate_models:
        if "flash" in fallback:
            return fallback
    return candidate_models[0]


def execute_with_fallback(
    client: Any,
    candidate_models: List[str],
    call_fn: Callable[[str], Any],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
) -> Tuple[Any, str]:
    """
    Executes an API call with automatic retry, exponential backoff,
    and fallback across models in priority order.
    """
    last_error: Optional[Exception] = None

    for model_index, model_name in enumerate(candidate_models):
        logger.info(f"Attempting content generation with model: {model_name}")
        retries = 0

        while retries < max_retries:
            try:
                result = call_fn(model_name)
                logger.info(f"Successfully generated structured content with {model_name}")
                return result, model_name

            except Exception as e:
                err_type, advice = classify_error(e)
                last_error = e

                if err_type == "AUTH_ERROR":
                    logger.error(f"Authentication failed: {advice}")
                    raise InvalidAPIKeyError(advice) from e

                if err_type in ("MODEL_NOT_FOUND", "BAD_REQUEST"):
                    logger.warning(f"Model {model_name} failed ({err_type}). Skipping to next candidate.")
                    break  # Skip to next model

                if err_type in ("QUOTA_EXHAUSTED", "SERVER_ERROR"):
                    retries += 1
                    sleep_time = (backoff_factor ** retries)
                    logger.warning(
                        f"Transient failure on {model_name} (attempt {retries}/{max_retries}). "
                        f"Retrying in {sleep_time:.1f}s... Reason: {advice}"
                    )
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Encountered error with {model_name}: {e}. Retrying...")
                    retries += 1
                    time.sleep(1.0)

    raise GeminiAPIError(
        f"All candidate models exhausted. Last error: {last_error}"
    )
