import pytest

def test_full_pipeline():
    from src.core.graph import research_agent
    result = research_agent.invoke({
        "query": "What is retrieval augmented generation?",
        "sub_questions": [], "retrieved_papers": {}, "synthesis": "",
        "critique": "", "critique_passed": False, "revision_count": 0,
        "messages": [], "final_answer": "",
    })
    assert result["final_answer"] != ""
    assert len(result["sub_questions"]) >= 2
    assert result["revision_count"] >= 1