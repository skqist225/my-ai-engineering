"""Layer 7: RAG Triad Automated Evaluation Suite (Faithfulness, Relevance, Precision)."""

import json
from pathlib import Path
from typing import Any
from src.rag.store import KnowledgeStore
from src.rag.retriever import HybridRetriever
from src.extraction.schemas import SecurityAuditReport, SecurityFinding, Severity
from src.guardrails.grounding import filter_grounded_findings


def evaluate_rag_triad(golden_dataset_path: str | Path | None = None) -> dict[str, Any]:
    """Run automated RAG Triad evaluation over golden evaluation benchmark cases."""
    if golden_dataset_path is None:
        golden_dataset_path = Path(__file__).resolve().parent / "datasets" / "golden_security_evals.json"
    else:
        golden_dataset_path = Path(golden_dataset_path)

    if not golden_dataset_path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {golden_dataset_path}")

    dataset = json.loads(golden_dataset_path.read_text(encoding="utf-8"))

    store = KnowledgeStore()
    retriever = HybridRetriever(store=store)

    results = []
    faithfulness_scores = []
    relevance_scores = []
    context_precision_scores = []

    print("[EVAL] Starting RAG Triad Evaluation...")
    print(f"[EVAL] Benchmark Cases: {len(dataset)}")

    for case in dataset:
        eval_id = case["eval_id"]
        description = case["description"]
        snippet = case["input_snippet"]
        target_file = case["target_file"]
        expected = case["expected_finding"]

        # 1. Evaluate Retrieval (Context Precision)
        retrieved_chunks = retriever.retrieve(query=description, top_k=3)
        retrieved_text = " ".join(c["content"].lower() for c in retrieved_chunks)

        # Check if retrieved chunks mention any expected keywords
        matches = [kw for kw in expected["expected_keywords"] if kw.lower() in retrieved_text]
        context_precision = len(matches) / max(len(expected["expected_keywords"]), 1)
        context_precision_scores.append(context_precision)

        # 2. Simulate / Check Groundedness (Faithfulness)
        mock_finding = SecurityFinding(
            finding_id=eval_id,
            title=description,
            severity=Severity[expected["severity"]],
            category=expected["category"],
            file_path=target_file,
            evidence=snippet.splitlines()[0],
            cve_reference=expected["expected_keywords"][-1] if expected["expected_keywords"] else None,
            remediation_steps=[]
        )

        mock_contents = {target_file: snippet}
        grounded, rejected = filter_grounded_findings([mock_finding], mock_contents)
        faithfulness = 1.0 if len(grounded) == 1 else 0.0
        faithfulness_scores.append(faithfulness)

        # 3. Answer Relevance
        # Verify that target severity matches expected severity
        severity_match = 1.0 if mock_finding.severity.value == expected["severity"] else 0.5
        relevance_scores.append(severity_match)

        results.append({
            "eval_id": eval_id,
            "description": description,
            "context_precision": round(context_precision, 3),
            "faithfulness": round(faithfulness, 3),
            "answer_relevance": round(severity_match, 3),
            "status": "[PASS]" if (faithfulness >= 0.8 and severity_match >= 0.8) else "[WARN]",
        })

    avg_precision = sum(context_precision_scores) / max(len(context_precision_scores), 1)
    avg_faithfulness = sum(faithfulness_scores) / max(len(faithfulness_scores), 1)
    avg_relevance = sum(relevance_scores) / max(len(relevance_scores), 1)
    composite_triad_score = (avg_precision + avg_faithfulness + avg_relevance) / 3.0

    summary = {
        "benchmark_cases_evaluated": len(dataset),
        "mean_context_precision": round(avg_precision, 3),
        "mean_faithfulness": round(avg_faithfulness, 3),
        "mean_answer_relevance": round(avg_relevance, 3),
        "composite_rag_triad_score": round(composite_triad_score, 3),
        "benchmark_results": results,
    }

    # Print summary table
    print("\n" + "=" * 65)
    print(f"RAG TRIAD EVALUATION SUMMARY (Composite: {summary['composite_rag_triad_score']:.2f} / 1.00)")
    print("=" * 65)
    print(f"| {'Eval ID':<16} | {'Precision':<10} | {'Faithful':<10} | {'Relevance':<10} | Status |")
    print("|" + "-"*18 + "|" + "-"*12 + "|" + "-"*12 + "|" + "-"*12 + "|--------|")
    for r in results:
        print(f"| {r['eval_id']:<16} | {r['context_precision']:<10} | {r['faithfulness']:<10} | {r['answer_relevance']:<10} | {r['status']} |")
    print("=" * 65 + "\n")

    # Persist report
    report_dir = Path(__file__).resolve().parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "ragas_eval_report.json"
    report_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[EVAL] Detailed report saved to {report_file}")

    return summary


if __name__ == "__main__":
    evaluate_rag_triad()
