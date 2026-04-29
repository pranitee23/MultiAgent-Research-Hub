"""Integration tests with real queries."""

BENCHMARK_QUERIES = [
    "What is retrieval augmented generation?",
    "Compare transformer and mamba architectures",
    "Latest approaches to LLM hallucination",
]

def test_pipeline_completes_for_simple_query():
    from src.core.graph import research_agent
    result = research_agent.invoke({
        "query": BENCHMARK_QUERIES[0],
        "sub_questions": [], "retrieved_papers": {}, "synthesis": "",
        "critique": "", "critique_passed": False, "revision_count": 0,
        "messages": [], "final_answer": "",
    })
    assert result["final_answer"] != ""
    assert "Research Summary" in result["final_answer"]

def test_sub_questions_are_generated():
    from src.agents.planner import planner_node
    for q in BENCHMARK_QUERIES:
        result = planner_node({"query": q})
        assert len(result["sub_questions"]) >= 2, f"Failed for: {q}"