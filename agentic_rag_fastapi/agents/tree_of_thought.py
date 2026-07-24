import time
import logging
import uuid
from typing import List, Dict, Any, Tuple
from agents.llm import safe_generate
from utils.json_utils import extract_json_object
from agents.rewriter import query_rewriter
from rag.retrieval import retrieve

logger = logging.getLogger("agentic_rag.tree_of_thought")


def generate_reasoning_tree(query: str) -> List[Dict[str, Any]]:
    """
    Generates multiple candidate reasoning branches for the query.
    Typically creates:
    - Branch A: General architecture / system overview
    - Branch B: Component-specific / granular logic
    - Branch C: Evidence-oriented / numerical metrics search
    """
    logger.info(f"Generating reasoning tree branches for query: '{query}'")

    prompt = f"""
You are a Tree of Thought (ToT) Planner Agent.
For the user's query, generate exactly 3 candidate retrieval/reasoning branches, each taking a different strategy:
1. Branch A: General architecture retrieval (focusing on high-level system overview, design, and broad concepts).
2. Branch B: Component-specific retrieval (focusing on individual modules, micro-logic, code structure, or specific step processes).
3. Branch C: Evidence-oriented retrieval (focusing on specific numerical metrics, latency values, benchmark performance, explicit results).

For each branch, provide:
- branch_name: A short clear name.
- sub_queries: A list of 1 to 3 distinct queries to search.
- expected_evidence: Description of what facts or details this branch expects to find.

Return ONLY a valid JSON list of 3 objects matching this structure:
[
  {{
    "branch_name": "Branch A: ...",
    "sub_queries": ["...", "..."],
    "expected_evidence": "..."
  }},
  ...
]

Do not add any commentary or markdown formatting other than the JSON itself.

User Query:
{query}
"""
    response = safe_generate(prompt)
    try:
        branches = extract_json_object(response)
        if isinstance(branches, list) and len(branches) > 0:
            # Add uuid for tracking
            for b in branches:
                b["branch_id"] = str(uuid.uuid4())
            return branches
    except Exception as e:
        logger.warning(f"Failed to parse reasoning tree branches from LLM: {e}")

    # Fallback to defaults
    return [
        {
            "branch_id": str(uuid.uuid4()),
            "branch_name": "Branch A (General architecture retrieval)",
            "sub_queries": [query],
            "expected_evidence": "High-level architectural context and concepts.",
        },
        {
            "branch_id": str(uuid.uuid4()),
            "branch_name": "Branch B (Component-specific retrieval)",
            "sub_queries": [f"detailed components of {query}"],
            "expected_evidence": "Technical details of specific sub-components.",
        },
        {
            "branch_id": str(uuid.uuid4()),
            "branch_name": "Branch C (Evidence-oriented retrieval)",
            "sub_queries": [f"metrics measurements and metrics values for {query}"],
            "expected_evidence": "Direct facts, benchmarks, and experimental measurements.",
        },
    ]


def evaluate_branch(
    branch: Dict[str, Any], query: str, embedding_model, vector_store, top_k: int = 3
) -> Dict[str, Any]:
    """
    Executes actual retrieval for a branch's sub-queries, aggregates the results,
    and calls the LLM to evaluate the retrieved content on multiple dimensions.
    """
    logger.info(f"Evaluating branch: {branch['branch_name']}")

    # 1. Retrieve data
    retrieved_results = []
    rewritten_queries = []
    total_similarity_score = 0.0
    chunk_count = 0

    for sq in branch.get("sub_queries", []):
        rewritten = query_rewriter(sq)
        rewritten_queries.append(rewritten)
        results = retrieve(rewritten, embedding_model, vector_store, top_k=top_k)

        for r in results:
            retrieved_results.append(r)
            total_similarity_score += r.get("score", 0.0)
            chunk_count += 1

    # Calculate average retrieval similarity (default to 0 if none)
    avg_similarity = total_similarity_score / chunk_count if chunk_count > 0 else 0.0

    # Unique chunks for evaluation context
    seen_chunks = set()
    aggregated_context_list = []
    for r in retrieved_results:
        chunk = r["chunk"]
        if chunk not in seen_chunks:
            seen_chunks.add(chunk)
            aggregated_context_list.append(chunk)
    aggregated_context = "\n\n".join(aggregated_context_list)

    # 2. Evaluate with LLM
    eval_prompt = f"""
You are a Tree of Thought evaluator.
Analyze the retrieved context and determine how effective it is for answering the user's query based on the strategy of the branch.

User Query:
{query}

Branch Strategy:
{branch.get("branch_name")}
Expected Evidence:
{branch.get("expected_evidence")}

Retrieved Context:
{aggregated_context[:6000]}

Score the retrieved context on these 4 metrics (between 0.0 and 1.0):
1. coverage: How well the context covers the user's overall query.
2. completeness: How complete is the information to draft a response.
3. evidence_quality: Does it contain specific facts, metrics, or details matching the strategy, or is it vague/speculative.
4. confidence: Overall confidence that this context will generate a high-quality answer.

Return ONLY a valid JSON object matching this structure:
{{
  "coverage": 0.8,
  "completeness": 0.7,
  "evidence_quality": 0.9,
  "confidence": 0.8,
  "evaluation_details": "Detailed summary explanation of the strengths/weaknesses of this retrieved context."
}}

Do not include markdown code fences or explain your rating process outside the JSON.
"""
    response = safe_generate(eval_prompt)
    try:
        eval_res = extract_json_object(response)
        coverage = float(eval_res.get("coverage", 0.5))
        completeness = float(eval_res.get("completeness", 0.5))
        evidence_quality = float(eval_res.get("evidence_quality", 0.5))
        confidence = float(eval_res.get("confidence", 0.5))
        details = str(eval_res.get("evaluation_details", "No details provided."))
    except Exception as e:
        logger.warning(f"Failed to parse branch evaluation scores: {e}")
        # Default scores if evaluation LLM fails
        coverage = 0.5
        completeness = 0.5
        evidence_quality = 0.5
        confidence = 0.5
        details = "Fallback evaluation due to parser error."

    # Scale FAISS distance score to a similarity score (typically lower distance is better, e.g. 1 - distance)
    # Let's map FAISS similarity score (higher is better in cosine, or lower in L2)
    # Assuming lower L2 distances indicate higher similarity, let's clamp it
    # We can cap distance at 2.0, similarity = max(0, 1 - avg_similarity / 2.0)
    retrieval_similarity = (
        max(0.0, min(1.0, 1.0 - (avg_similarity / 2.0))) if avg_similarity > 0 else 0.0
    )

    # Save fields back to branch
    branch["retrieved"] = retrieved_results
    branch["rewritten_queries"] = rewritten_queries
    branch["retrieval_similarity"] = retrieval_similarity

    # Calculate final score
    scores = score_branch(
        retrieval_similarity=retrieval_similarity,
        coverage=coverage,
        completeness=completeness,
        evidence_quality=evidence_quality,
        confidence=confidence,
    )
    branch["scores"] = scores
    branch["final_score"] = scores["final_score"]
    branch["evaluation_details"] = details

    return branch


def score_branch(
    retrieval_similarity: float,
    coverage: float,
    completeness: float,
    evidence_quality: float,
    confidence: float,
) -> Dict[str, float]:
    """
    Computes a weighted final score for a branch using its dimensional ratings.
    Weights:
    - retrieval_similarity: 15%
    - coverage: 25%
    - completeness: 20%
    - evidence_quality: 20%
    - confidence: 20%
    """
    final_score = (
        (retrieval_similarity * 0.15)
        + (coverage * 0.25)
        + (completeness * 0.20)
        + (evidence_quality * 0.20)
        + (confidence * 0.20)
    )

    return {
        "retrieval_similarity": round(retrieval_similarity, 3),
        "coverage": round(coverage, 3),
        "completeness": round(completeness, 3),
        "evidence_quality": round(evidence_quality, 3),
        "confidence": round(confidence, 3),
        "final_score": round(final_score, 3),
    }


def select_best_branch(
    branches: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Ranks branches and selects the highest scoring branch.
    Returns:
    - best_branch: Dict
    - ranked_branches: List (sorted descending by score)
    """
    ranked = sorted(branches, key=lambda b: b.get("final_score", 0.0), reverse=True)
    return ranked[0], ranked


def merge_branches(
    branches: List[Dict[str, Any]], score_threshold: float = 0.6, margin: float = 0.15
) -> Tuple[List[str], bool]:
    """
    Optionally merges the top branches if they are both above the threshold and close in score.
    Returns:
    - sub_queries: List of merged sub queries
    - merged: bool (True if a merge was performed)
    """
    if len(branches) < 2:
        return branches[0].get("sub_queries", []), False

    ranked = sorted(branches, key=lambda b: b.get("final_score", 0.0), reverse=True)
    top_branch = ranked[0]
    second_branch = ranked[1]

    top_score = top_branch.get("final_score", 0.0)
    second_score = second_branch.get("final_score", 0.0)

    # Merge if top score is reasonably good, and second score is very close to top score
    if top_score >= score_threshold and (top_score - second_score) <= margin:
        logger.info(
            f"Merging Branch A ({top_branch['branch_name']}) and Branch B ({second_branch['branch_name']})"
        )
        # Combine sub-queries without duplicates
        merged_queries = list(top_branch.get("sub_queries", []))
        for q in second_branch.get("sub_queries", []):
            if q not in merged_queries:
                merged_queries.append(q)
        return merged_queries, True

    return top_branch.get("sub_queries", []), False
