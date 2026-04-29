def test_planner_output():
    from src.agents.planner import planner_node
    result = planner_node({"query": "What are the latest approaches to LLM alignment?"})
    assert 2 <= len(result["sub_questions"]) <= 5

def test_critic_output_format():
    from src.agents.critic import critic_node
    state = {
        "synthesis": "RAG improves LLM accuracy by grounding responses.",
        "retrieved_papers": {"q1": "Paper about RAG showing improvements."},
        "revision_count": 0,
    }
    result = critic_node(state)
    assert "critique" in result
    assert isinstance(result["critique_passed"], bool)
    assert result["revision_count"] == 1