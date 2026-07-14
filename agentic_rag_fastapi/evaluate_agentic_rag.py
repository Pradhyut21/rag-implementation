import json
import time
import os
import requests
from docx import Document

def create_eval_document():
    filename = "eval_rag_doc.docx"
    doc = Document()
    doc.add_heading("Google's Agentic RAG Architecture Overview", level=0)
    
    doc.add_heading("1. Introduction", level=1)
    doc.add_paragraph(
        "Agentic Retrieval-Augmented Generation (Agentic RAG) is a design pattern that introduces "
        "multiple agents to orchestrate the retrieval, reasoning, and synthesis phases in RAG systems. "
        "Unlike vanilla RAG which simply retrieves documents and outputs answers in a single step, "
        "Agentic RAG utilizes a planner, query rewriter, sufficient context checker, and feedback loop "
        "to ensure high-fidelity answers."
    )
    
    doc.add_heading("2. Core Agents", level=1)
    doc.add_paragraph(
        "The Planner Agent is the entry point, breaking the user's complex request into a sequence of sub-questions. "
        "The Query Rewriter Agent transforms these sub-questions into technical, search-friendly retrieval queries. "
        "The Sufficient Context Agent evaluates whether the aggregated retrieved context is enough to faithfully "
        "answer the original query. Finally, the Synthesis Agent drafts the grounded answer."
    )
    
    doc.add_heading("3. The Feedback Loop", level=1)
    doc.add_paragraph(
        "When the Sufficient Context Agent flags that information is missing, it suggests feedback instructions. "
        "The system aggregates this feedback, generates rewritten queries targeting the missing pieces, "
        "and triggers a new round of retrieval. This iteratively patches the retrieved context."
    )
    
    doc.save(filename)
    print(f"Evaluation document '{filename}' created successfully (WITHOUT latency details).")
    return filename

def run_evaluation():
    base_url = "http://127.0.0.1:8002"
    doc_path = create_eval_document()
    
    print("\nStarting Agentic RAG Evaluation Suite with CoT and ToT support...")
    
    # 1. Upload the evaluation document
    print("\nStep 1: Uploading evaluation document to API...")
    try:
        with open(doc_path, "rb") as f:
            files = {"file": (doc_path, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            r = requests.post(f"{base_url}/upload-doc", files=files)
        
        if r.status_code != 200:
            print(f"Error: Upload failed with status {r.status_code}. Response: {r.text}")
            return
            
        upload_resp = r.json()
        doc_id = upload_resp["doc_id"]
        print(f"Document indexed successfully. Assigned doc_id: '{doc_id}'")
    except Exception as e:
        print("Upload failed:", e)
        return
        
    eval_queries = [
        {
            "query": "Explain Google's Agentic RAG architecture and the role of the Sufficient Context Agent.",
            "expected_sufficient": True
        },
        {
            "query": "What latency measurements did Google report for the Sufficient Context Agent?",
            "expected_sufficient": False
        }
    ]
    
    results = []
    
    # Track metrics
    standard_sufficiency_count = 0
    tot_sufficiency_count = 0
    
    cot_stages_count = []
    tot_branches_count = []
    tot_branch_scores = []
    tot_winning_branch_scores = []
    
    # 2. Run Standard Mode (Baseline)
    print("\n--- Running Standard RAG (Baseline) ---")
    for q_case in eval_queries:
        payload = {
            "query": q_case["query"],
            "doc_id": doc_id,
            "top_k": 3,
            "include_trace": True,
            "response_mode": "detailed",
            "reasoning_mode": "standard"
        }
        try:
            r = requests.post(f"{base_url}/ask-debug", json=payload)
            if r.status_code == 200:
                resp = r.json()
                is_sufficient = resp["context_sufficient"]
                if is_sufficient:
                    standard_sufficiency_count += 1
                print(f"Query: '{q_case['query']}' | Sufficient: {is_sufficient}")
                results.append({
                    "mode": "standard",
                    "query": q_case["query"],
                    "sufficient": is_sufficient
                })
        except Exception as e:
            print("Failed to run standard case:", e)

    # 3. Run Chain of Thought (CoT) Mode
    print("\n--- Running Chain of Thought (CoT) RAG ---")
    for q_case in eval_queries:
        payload = {
            "query": q_case["query"],
            "doc_id": doc_id,
            "top_k": 3,
            "include_trace": True,
            "response_mode": "detailed",
            "reasoning_mode": "cot"
        }
        try:
            r = requests.post(f"{base_url}/ask-debug", json=payload)
            if r.status_code == 200:
                resp = r.json()
                session_id = resp.get("session_id")
                is_sufficient = resp["context_sufficient"]
                
                # Fetch reasoning stages from API
                cot_r = requests.get(f"{base_url}/reasoning/cot/{session_id}")
                stages_data = cot_r.json()
                stages = stages_data.get("stages", [])
                cot_stages_count.append(len(stages))
                
                print(f"Query: '{q_case['query']}' | Sufficient: {is_sufficient} | CoT Stages: {len(stages)}")
                results.append({
                    "mode": "cot",
                    "query": q_case["query"],
                    "sufficient": is_sufficient,
                    "session_id": session_id,
                    "stages_count": len(stages)
                })
        except Exception as e:
            print("Failed to run CoT case:", e)

    # 4. Run Tree of Thought (ToT) Mode
    print("\n--- Running Tree of Thought (ToT) RAG ---")
    for q_case in eval_queries:
        payload = {
            "query": q_case["query"],
            "doc_id": doc_id,
            "top_k": 3,
            "include_trace": True,
            "response_mode": "detailed",
            "reasoning_mode": "tot"
        }
        try:
            r = requests.post(f"{base_url}/ask-debug", json=payload)
            if r.status_code == 200:
                resp = r.json()
                session_id = resp.get("session_id")
                is_sufficient = resp["context_sufficient"]
                if is_sufficient:
                    tot_sufficiency_count += 1
                
                # Fetch reasoning tree from API
                tot_r = requests.get(f"{base_url}/reasoning/tot/{session_id}")
                tree_data = tot_r.json()
                branches = tree_data.get("branches", [])
                tot_branches_count.append(len(branches))
                
                for b in branches:
                    if b.get("score") and "final_score" in b["score"]:
                        tot_branch_scores.append(b["score"]["final_score"])
                
                winning_score = tree_data.get("winning_branch", {}).get("score", 0.0)
                tot_winning_branch_scores.append(winning_score)
                
                print(f"Query: '{q_case['query']}' | Sufficient: {is_sufficient} | Branches: {len(branches)} | Winner Score: {winning_score}")
                results.append({
                    "mode": "tot",
                    "query": q_case["query"],
                    "sufficient": is_sufficient,
                    "session_id": session_id,
                    "branches_count": len(branches),
                    "winning_score": winning_score
                })
        except Exception as e:
            print("Failed to run ToT case:", e)

    # 5. Calculate Metrics
    num_queries = len(eval_queries)
    avg_stages = sum(cot_stages_count) / len(cot_stages_count) if cot_stages_count else 0
    avg_branches = sum(tot_branches_count) / len(tot_branches_count) if tot_branches_count else 0
    avg_branch_score = sum(tot_branch_scores) / len(tot_branch_scores) if tot_branch_scores else 0.0
    avg_winning_score = sum(tot_winning_branch_scores) / len(tot_winning_branch_scores) if tot_winning_branch_scores else 0.0
    
    sufficiency_before = standard_sufficiency_count / num_queries if num_queries else 0.0
    sufficiency_after = tot_sufficiency_count / num_queries if num_queries else 0.0
    improvement = sufficiency_after - sufficiency_before

    metrics = {
        "avg_reasoning_stages": round(avg_stages, 2),
        "avg_branches_generated": round(avg_branches, 2),
        "avg_branch_score": round(avg_branch_score, 3),
        "winning_branch_accuracy": round(avg_winning_score, 3),
        "context_sufficiency_before_tot": round(sufficiency_before, 2),
        "context_sufficiency_after_tot": round(sufficiency_after, 2),
        "retrieval_improvement": round(improvement, 2)
    }

    print("\n--- Evaluation Metrics Summary ---")
    print(f"Average Reasoning Stages (CoT): {metrics['avg_reasoning_stages']}")
    print(f"Average Branches Generated (ToT): {metrics['avg_branches_generated']}")
    print(f"Average Branch Score (ToT): {metrics['avg_branch_score']}")
    print(f"Winning Branch Average Score: {metrics['winning_branch_accuracy']}")
    print(f"Context Sufficiency Rate BEFORE ToT: {metrics['context_sufficiency_before_tot']}")
    print(f"Context Sufficiency Rate AFTER ToT: {metrics['context_sufficiency_after_tot']}")
    print(f"Retrieval Sufficiency Improvement: {metrics['retrieval_improvement']}")

    # 6. Save report
    report_file = "evaluation_report.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "doc_id": doc_id,
        "metrics": metrics,
        "results": results
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nEvaluation complete. Detailed metrics report saved to: {report_file}")
    
    # 7. Cleanup
    print("\nStep 4: Cleaning up indexed document...")
    try:
        r = requests.delete(f"{base_url}/documents/{doc_id}")
        print("DELETE response:", r.json())
    except Exception as e:
        print("Cleanup request failed:", e)
        
    if os.path.exists(doc_path):
        os.remove(doc_path)
        print("Removed temporary local document.")

if __name__ == "__main__":
    run_evaluation()
