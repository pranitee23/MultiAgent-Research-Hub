"""Critic: fact-checks synthesis against source papers."""
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.state import ResearchState
from src.config.prompts import CRITIC_SYSTEM

prompt = ChatPromptTemplate.from_messages([
    ("system", CRITIC_SYSTEM),
    ("human", "Synthesis to verify:\n{synthesis}\n\nSource papers:\n{papers}\n\nYour verdict:")
])


def critic_node(state: ResearchState) -> dict:
    llm = get_llm(temperature=0.2).bind(max_tokens=500)

    papers_text = "\n".join(state["retrieved_papers"].values())

    chain = prompt | llm
    response = chain.invoke({"synthesis": state["synthesis"], "papers": papers_text[:6000]})

    content = response.content
    passed = "VERDICT: PASS" in content.upper() or "VERDICT:PASS" in content.upper()

    return {
        "critique": content,
        "critique_passed": passed,
        "revision_count": state.get("revision_count", 0) + 1,
    }