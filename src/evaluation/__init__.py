"""Nexus evaluation framework — multi-dimensional LLM-as-judge."""

from src.evaluation.benchmark import BENCHMARK_CASES, get_pass_cases, get_fail_cases

__all__ = [
    "BENCHMARK_CASES",
    "get_pass_cases",
    "get_fail_cases",
    "judge_synthesis",
    "JudgeResult",
    "run_evaluation",
]


def __getattr__(name: str):
    """Lazy-import judge and runner to avoid loading LangChain at import time."""
    if name in ("judge_synthesis", "JudgeResult"):
        from src.evaluation.judge import judge_synthesis, JudgeResult
        return {"judge_synthesis": judge_synthesis, "JudgeResult": JudgeResult}[name]
    if name == "run_evaluation":
        from src.evaluation.run_eval import run_evaluation
        return run_evaluation
    raise AttributeError(f"module 'src.evaluation' has no attribute {name!r}")
