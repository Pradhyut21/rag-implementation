import logging
from agents.llm import safe_generate
from utils.json_utils import extract_json_object

logger = logging.getLogger("agentic_rag.sufficient_context")

def sufficient_context_agent(query: str, context: str, intermediate_draft: str):
    prompt = f"""
You are the Sufficient Context Agent in an Agentic RAG system.

Your job is to determine whether the retrieved context is sufficient to answer the user's question fully, faithfully, and explicitly.

STRICT EVALUATION RULES:
1. If the user query asks for a fact-specific detail (examples: a latency metric, a benchmark score, a specific number, an exact date, an exact metric, or a reported outcome) and that specific fact is NOT explicitly present in the retrieved context, you MUST mark "is_context_sufficient" as false.
2. You must distinguish between:
   - "The context discusses the topic generally"
   - "The context explicitly contains the answer to the user's exact question"
   If the context discusses the topic generally but lacks the specific detail/number requested, you MUST mark "is_context_sufficient" as false.
3. Do NOT assume or guess any metrics. Do NOT extrapolate or use external knowledge.
4. Set "evidence_type" to:
   - "explicit" if the exact answer/metric is present in the context.
   - "partial" if the context covers the general topic but is missing the specific detail or number requested.
   - "missing" if the context does not discuss the requested topic at all.

Return exactly one JSON object.
Do not wrap the object in a list.
Do not include markdown fences.
Do not include commentary before or after the JSON.
The top-level response must be a JSON dictionary with these exact keys:
- is_context_sufficient
- missing_information
- feedback_log
- reasoning_summary
- evidence_type

Return ONLY a valid JSON object in exactly this format:

{{
  "is_context_sufficient": false,
  "missing_information": ["Specific fact missing from context"],
  "feedback_log": "What retrieval should search for next.",
  "reasoning_summary": "Why the context is insufficient or sufficient.",
  "evidence_type": "explicit"
}}

USER QUERY:
{query}

RETRIEVED CONTEXT:
{context}

INTERMEDIATE DRAFT:
{intermediate_draft}
"""

    response = safe_generate(prompt)
    logger.debug(f"Sufficient Context Agent LLM raw response: {response}")

    try:
        result = extract_json_object(response)

        # If the model wrapped the dictionary in a list, extract the first element
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                result = result[0]
            else:
                raise ValueError("Parsed JSON is a list but does not contain a valid dictionary object")

        if not isinstance(result, dict):
            raise ValueError("Parsed JSON is not a dictionary object")

        # Build clean output mapping safely
        is_sufficient = bool(result.get("is_context_sufficient", False))
        
        # Ensure evidence_type is valid
        evidence_val = result.get("evidence_type", "missing")
        evidence = str(evidence_val).lower() if evidence_val is not None else "missing"
        if evidence not in ["explicit", "partial", "missing"]:
            evidence = "missing"
            
        # Ensure missing_information is a list
        missing_info = result.get("missing_information", [])
        if not isinstance(missing_info, list):
            missing_info = [str(missing_info)] if missing_info else []
            
        return {
            "is_context_sufficient": is_sufficient,
            "missing_information": missing_info,
            "feedback_log": str(result.get("feedback_log", "")),
            "reasoning_summary": str(result.get("reasoning_summary", "No reasoning summary provided by model.")),
            "evidence_type": evidence
        }
    except Exception as e:
        logger.exception("Sufficient Context Agent failed to parse JSON. Triggering conservative fallback.")
        return {
            "is_context_sufficient": False,
            "missing_information": ["Unable to reliably verify whether the retrieved context fully answers the query."],
            "feedback_log": "Retry retrieval with more specific evidence-seeking queries.",
            "reasoning_summary": f"Failed to parse LLM response due to error: {str(e)}",
            "evidence_type": "missing"
        }
