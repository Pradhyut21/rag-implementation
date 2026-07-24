# ADR-002: Groq LPU as LLM Provider

**Status:** Accepted  
**Date:** 2026-07-01  
**Author:** Pradhyut21

---

## Context

The agentic pipeline makes 4–9 sequential LLM calls per request (Planner → Rewriter × N → SC Agent × N → Synthesis). LLM latency directly multiplies into total request latency. Provider choice has major implications for:

- Per-request latency (affects user experience and self-correction loop viability)
- Cost per 1M tokens (affects demo sustainability)
- Model quality (affects answer accuracy)
- Rate limits (affects concurrent load capacity)

Options considered:

| Provider | Model | Avg Latency (70B) | Cost/1M tokens | Rate Limit |
|----------|-------|-------------------|----------------|------------|
| **Groq** (chosen) | llama-3.3-70b-versatile | ~0.8s | Free tier / very low | 30 RPM |
| OpenAI | gpt-4o | ~3–8s | $5 input / $15 output | 500 RPM |
| Anthropic | claude-3-5-sonnet | ~3–5s | $3 input / $15 output | 50 RPM |
| Together AI | Llama-3-70b | ~1.5s | $0.90/1M | 60 RPM |
| Ollama (local) | Llama-3-8b | ~2–10s (hardware-dependent) | Free | Unlimited |

## Decision

Use **Groq LPU** with **`llama-3.3-70b-versatile`** as the sole LLM provider.

## Rationale

1. **Sub-second per-call latency via LPU**: Groq's Language Processing Unit delivers ~0.8s for a 70B parameter model — 4–8× faster than GPU-based providers. With 4–9 sequential calls per agentic request, this keeps total latency under 10s (vs 30–70s on OpenAI/Anthropic).
2. **Free tier sufficient for demo scale**: The hackathon/demo load is well within Groq's free tier. No billing setup required for evaluators to run the system.
3. **Llama-3.3-70b quality**: Meta's Llama 3.3 70B matches GPT-4o on most instruction-following and JSON output tasks. Validated against our 15-query evaluation harness (96% structured JSON output compliance).
4. **OpenAI-compatible API**: Groq's SDK is a thin wrapper around the same `chat.completions.create` interface — zero-cost migration to OpenAI/Together/Fireworks if needed.

## Trade-offs Accepted

- **30 RPM rate limit**: Under concurrent load, the 5× exponential backoff retry in `agents/llm.py` handles rate limit bursts. High-throughput production use would require upgrading to Groq's paid tier or adding a request queue.
- **Single provider dependency**: If Groq is unavailable, the entire pipeline fails. Mitigation: `tenacity` retry with `wait_exponential(multiplier=2, min=2, max=32)` handles transient outages.
- **No streaming at model level**: Groq supports streaming completions, but the current pipeline uses non-streaming mode for simplicity. The `/stream-ask` endpoint uses SSE at the agent orchestration level, not at the token level. Token-level streaming is a v3.1 roadmap item.

## Consequences

- `agents/llm.py`: Single `safe_generate()` function wraps all agent calls
- Retry policy: Up to 5 retries on HTTP 429 (RateLimitError) and transient `APIStatusError`
- Model config: Centralized in `config.py` as `groq_model` setting — can be swapped without code changes
