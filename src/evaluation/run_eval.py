"""
Nexus — Evaluation runner.

Runs all benchmark cases through the judge, computes a confusion matrix,
and writes results to src/evaluation/results.json.

Usage:
    python -m src.evaluation.run_eval              # run all cases
    python -m src.evaluation.run_eval --verbose     # detailed per-case output
    python -m src.evaluation.run_eval --case rag_good  # run single case by id
"""

import json
import time
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from src.evaluation.benchmark import BENCHMARK_CASES
from src.evaluation.judge import judge_synthesis, JudgeResult
from src.core.llm import get_provider_info

logger = logging.getLogger(__name__)

RESULTS_PATH = Path(__file__).parent / "results.json"


# ── Single case evaluation ────────────────────────────────────────────────

def evaluate_case(case: dict) -> dict:
    """Run the judge on one benchmark case and classify the result."""
    start = time.time()

    result: JudgeResult = judge_synthesis(
        query=case["query"],
        source_papers=case["source_papers"],
        synthesis=case["synthesis"],
    )

    elapsed = time.time() - start
    predicted = "pass" if result.passed else "fail"
    expected = case["expected_verdict"]

    return {
        "id": case["id"],
        "query": case["query"][:80],
        "expected": expected,
        "predicted": predicted,
        "correct": predicted == expected,
        "failure_mode": case.get("failure_mode"),
        "scores": {
            "factual_accuracy": result.factual_accuracy,
            "relevance": result.relevance,
            "citation_grounding": result.citation_grounding,
            "completeness": result.completeness,
            "coherence": result.coherence,
        },
        "average_score": round(result.average_score, 2),
        "min_score": result.min_score,
        "justifications": result.justifications,
        "elapsed_seconds": round(elapsed, 1),
        # Confusion matrix classification
        "tp": predicted == "pass" and expected == "pass",
        "tn": predicted == "fail" and expected == "fail",
        "fp": predicted == "pass" and expected == "fail",
        "fn": predicted == "fail" and expected == "pass",
    }


# ── Confusion matrix ─────────────────────────────────────────────────────

def compute_metrics(results: list[dict]) -> dict:
    """Compute confusion matrix and derived metrics from evaluated results."""
    tp = sum(1 for r in results if r["tp"])
    tn = sum(1 for r in results if r["tn"])
    fp = sum(1 for r in results if r["fp"])
    fn = sum(1 for r in results if r["fn"])

    total = len(results)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    fp_cases = [r["id"] for r in results if r["fp"]]
    fn_cases = [r["id"] for r in results if r["fn"]]

    return {
        "total_cases": total,
        "correct": tp + tn,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_ids": fp_cases,
        "false_negative_ids": fn_cases,
        "zero_fp": fp == 0,
        "zero_fn": fn == 0,
    }


# ── Pretty printing ──────────────────────────────────────────────────────

def print_case_result(r: dict, verbose: bool = False) -> None:
    status = "CORRECT" if r["correct"] else "WRONG"
    icon = "  +" if r["correct"] else "  X"
    tag = ""
    if r["fp"]:
        tag = " [FALSE POSITIVE — reward hacking!]"
    elif r["fn"]:
        tag = " [FALSE NEGATIVE — reward denial!]"

    print(f"{icon} {r['id']:<35} expected={r['expected']:<4}  "
          f"predicted={r['predicted']:<4}  avg={r['average_score']:<5}  "
          f"min={r['min_score']}  {status}{tag}")

    if verbose:
        for dim, score in r["scores"].items():
            just = r["justifications"].get(dim.upper(), "")
            print(f"      {dim}: {score}/5  {just}")
        print()


def print_summary(metrics: dict) -> None:
    cm = metrics["confusion_matrix"]
    print("\n" + "=" * 60)
    print("  EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:  {metrics['total_cases']}")
    print(f"  Correct:      {metrics['correct']}/{metrics['total_cases']}")
    print()
    print("  Confusion Matrix:")
    print(f"                  Predicted PASS    Predicted FAIL")
    print(f"    Actual PASS       TP={cm['tp']:<6}        FN={cm['fn']}")
    print(f"    Actual FAIL       FP={cm['fp']:<6}        TN={cm['tn']}")
    print()
    print(f"  Accuracy:   {metrics['accuracy']:.2%}")
    print(f"  Precision:  {metrics['precision']:.2%}")
    print(f"  Recall:     {metrics['recall']:.2%}")
    print(f"  F1 Score:   {metrics['f1_score']:.2%}")
    print()

    if metrics["zero_fp"] and metrics["zero_fn"]:
        print("  RESULT: PERFECT — zero false positives, zero false negatives")
    else:
        if not metrics["zero_fp"]:
            print(f"  WARNING: {cm['fp']} false positive(s) (reward hacking)")
            print(f"           Cases: {metrics['false_positive_ids']}")
        if not metrics["zero_fn"]:
            print(f"  WARNING: {cm['fn']} false negative(s) (reward denial)")
            print(f"           Cases: {metrics['false_negative_ids']}")

    print("=" * 60)


# ── Main runner ───────────────────────────────────────────────────────────

def run_evaluation(
    cases: list[dict] | None = None,
    verbose: bool = False,
    save: bool = True,
) -> dict:
    """Run the full evaluation and return metrics."""
    if cases is None:
        cases = BENCHMARK_CASES

    provider_info = get_provider_info()
    print(f"\nRunning evaluation with {provider_info['provider']} "
          f"({provider_info.get('model', 'unknown')})")
    print(f"Evaluating {len(cases)} benchmark cases...\n")

    results = []
    total_start = time.time()

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] Evaluating {case['id']}...")
        try:
            r = evaluate_case(case)
            results.append(r)
            print_case_result(r, verbose=verbose)
        except Exception as e:
            logger.error("Failed on case %s: %s", case["id"], e)
            print(f"  ! ERROR on {case['id']}: {e}")
            results.append({
                "id": case["id"],
                "query": case["query"][:80],
                "expected": case["expected_verdict"],
                "predicted": "error",
                "correct": False,
                "error": str(e),
                "tp": False, "tn": False, "fp": False, "fn": False,
            })

    total_elapsed = time.time() - total_start

    metrics = compute_metrics(results)
    print_summary(metrics)
    print(f"\n  Completed in {total_elapsed:.1f}s")

    if save:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider_info,
            "metrics": metrics,
            "cases": results,
        }
        RESULTS_PATH.write_text(json.dumps(output, indent=2, default=str))
        print(f"  Results saved to {RESULTS_PATH}")

    return metrics


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Nexus evaluation runner")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-dimension scores and justifications")
    parser.add_argument("--case", type=str, default=None,
                        help="Run a single case by id (e.g. rag_good)")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save results to results.json")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    cases = None
    if args.case:
        cases = [c for c in BENCHMARK_CASES if c["id"] == args.case]
        if not cases:
            valid = [c["id"] for c in BENCHMARK_CASES]
            print(f"Unknown case '{args.case}'. Valid IDs: {valid}")
            sys.exit(1)

    metrics = run_evaluation(
        cases=cases,
        verbose=args.verbose,
        save=not args.no_save,
    )

    sys.exit(0 if (metrics["zero_fp"] and metrics["zero_fn"]) else 1)


if __name__ == "__main__":
    main()
