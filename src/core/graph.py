"""LangGraph pipeline: Planner → Retriever → Synthesizer ⇄ Critic → Answer"""
from langgraph.graph import StateGraph, START, END
from src.core.state import ResearchState
from src.agents.planner import planner_node
from src.agents.retriever import retriever_node
from src.agents.synthesizer import synthesizer_node
from src.agents.critic import critic_node
from src.config.settings import settings


def should_continue(state: ResearchState) -> str:
    """Conditional edge: loop back or finish?"""
    if state.get("critique_passed", False):
        return "format_answer"
    if state.get("revision_count", 0) >= settings.max_critic_revisions:
        return "format_answer"
    return "synthesizer"


def format_answer_node(state: ResearchState) -> dict:
    """Package final answer for the user."""
    quality = "✅ Verified" if state.get("critique_passed") else "⚠️ Best effort"
    final = f"## Research Summary\n\n{state.get('synthesis', '')}\n\n---\n*Quality: {quality} | Revisions: {state.get('revision_count', 0)}*"
    if not state.get("critique_passed") and state.get("critique"):
        final += f"\n*Critic notes: {state['critique']}*"
    return {"final_answer": final}


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("critic", critic_node)
    graph.add_node("format_answer", format_answer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "synthesizer")
    graph.add_edge("synthesizer", "critic")
    graph.add_conditional_edges("critic", should_continue, {"synthesizer": "synthesizer", "format_answer": "format_answer"})
    graph.add_edge("format_answer", END)

    return graph.compile()


research_agent = build_graph()