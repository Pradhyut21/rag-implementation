from agents.llm import safe_generate
from utils.json_utils import extract_json_object

def planner_agent(query: str):
    prompt = f"""
You are a Planner Agent in an Agentic RAG system.

Break the user's query into 2 to 5 focused sub-questions that would help retrieve the required information.
Return ONLY a valid JSON array of strings.
Do not add any explanation.

User Query:
{query}
"""

    response = safe_generate(prompt)

    try:
        sub_queries = extract_json_object(response)
        if isinstance(sub_queries, list):
            return [str(x) for x in sub_queries]
    except Exception:
        pass

    return [query]
