"""
Nexus — Shared agent state.

The state schema is provider-independent — it doesn't care
whether the LLM is Groq, Gemini, or Ollama.
"""

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ResearchState(TypedDict):
    """State shared across all agents."""

    # User input
    query: str

    # Planner output
    sub_questions: list[str]

    # Retriever output
    retrieved_papers: dict[str, str]

    # Synthesizer output
    synthesis: str

    # Critic output
    critique: str
    critique_passed: bool
    revision_count: int

    # Final output
    final_answer: str

    # Conversation history (multi-turn)
    messages: Annotated[list[BaseMessage], add_messages]