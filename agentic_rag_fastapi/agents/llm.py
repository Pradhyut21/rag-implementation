import os
import logging
from typing import Optional
from groq import Groq, RateLimitError, APIStatusError
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

load_dotenv()

logger = logging.getLogger("agentic_rag.llm")

# ---------------------------------------------------------------------------
# Lazy singleton — key validated on first actual API call, NOT at import time.
# This allows tests (conftest.py) to set GROQ_API_KEY before it is consumed.
# ---------------------------------------------------------------------------
_client: Optional[Groq] = None


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


# ---------------------------------------------------------------------------
# Retry decorator: retries up to 5 times on rate-limit (429) errors.
# Exponential back-off: 2s -> 4s -> 8s -> 16s -> 32s between attempts.
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception_type((RateLimitError, APIStatusError)),
    wait=wait_exponential(multiplier=2, min=2, max=32),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def safe_generate(prompt: str, temperature: float = 0) -> str:
    """
    Calls the Groq LLM with automatic exponential-backoff retry on
    rate-limit (HTTP 429) and transient API errors.

    Args:
        prompt: The full prompt string to send to the model.
        temperature: Sampling temperature (default 0 for deterministic output).

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
    )
    return response.choices[0].message.content.strip()
