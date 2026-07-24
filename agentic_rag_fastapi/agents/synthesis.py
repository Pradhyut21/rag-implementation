from agents.llm import safe_generate


def synthesis_agent(query: str, context: str):
    prompt = f"""
You are the Synthesis Agent in an Agentic RAG system.

Use ONLY the provided context to answer the user's question.
Do not invent missing facts.
If the context does not contain something, explicitly say so.

USER QUERY:
{query}

CONTEXT:
{context}

Now write a clear, grounded answer.
"""
    return safe_generate(prompt)
