def estimate_token_count(text: str) -> int:
    """
    Estimates the number of tokens in a string using a standard approximation
    (approx 4 characters per token).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def calculate_llm_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculates cost based on token pricing for supported models.
    Defaulting to Llama-3.3-70b pricing:
    Input: $0.59 / Million tokens
    Output: $0.79 / Million tokens
    """
    input_rate = 0.59 / 1_000_000
    output_rate = 0.79 / 1_000_000

    # Adjust rates if model varies
    if "70b" in model_name.lower():
        input_rate = 0.59 / 1_000_000
        output_rate = 0.79 / 1_000_000
    elif "8b" in model_name.lower():
        input_rate = 0.05 / 1_000_000
        output_rate = 0.08 / 1_000_000

    return (prompt_tokens * input_rate) + (completion_tokens * output_rate)
