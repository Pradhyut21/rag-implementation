import logging
import os

from dotenv import load_dotenv
from groq import APIStatusError, AuthenticationError, Groq, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()

logger = logging.getLogger("agentic_rag.llm")

# ---------------------------------------------------------------------------
# Lazy singleton — key validated on first actual API call, NOT at import time.
# This allows tests (conftest.py) to set GROQ_API_KEY before it is consumed.
# ---------------------------------------------------------------------------
_client: Groq | None = None


def _get_client() -> Groq:
    """Return (or create) the Groq singleton client."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Add it to your .env file or export it before starting the server."
            )
        _client = Groq(api_key=api_key)
    return _client


def _is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, AuthenticationError):
        return False
    if isinstance(exc, APIStatusError):
        return getattr(exc, "status_code", None) not in (401, 403, 400, 404, 422)
    return False


# ---------------------------------------------------------------------------
# Retry decorator: retries up to 5 times on rate-limit (429) / transient errors.
# Fail fast immediately on 401 AuthenticationError / 400 Bad Request.
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception(_is_transient_error),
    wait=wait_exponential(multiplier=2, min=2, max=32),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def safe_generate(prompt: str, temperature: float = 0, max_tokens: int = 512) -> str:
    """
    Calls the Groq LLM with automatic exponential-backoff retry on
    rate-limit (HTTP 429) and transient API errors.

    Args:
        prompt: The full prompt string to send to the model.
        temperature: Sampling temperature (default 0 for deterministic output).
        max_tokens: Maximum tokens to generate (default 512 for speed).

    Returns:
        The stripped text content from the model's first choice.

    Raises:
        RateLimitError / APIStatusError: Re-raised after 5 failed attempts.
    """
    response = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def fast_generate(prompt: str, temperature: float = 0, max_tokens: int = 256) -> str:
    """
    Lightweight LLM call using llama-3.1-8b-instant.
    Use for simple classification/JSON tasks where speed matters over depth.
    ~3x faster than llama-3.3-70b-versatile at trivial structured output.
    """
    response = _get_client().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
