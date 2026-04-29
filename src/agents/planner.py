"""Planner: decomposes complex queries into sub-questions."""
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.state import ResearchState
from src.config.prompts import PLANNER_SYSTEM

prompt = ChatPromptTemplate.from_messages([
    ("system", PLANNER_SYSTEM),
    ("human", "Query: {query}")
])


def planner_node(state: ResearchState) -> dict:
    llm = get_llm(temperature=0.3, tier="light").bind(max_tokens=200)
    chain = prompt | llm
    response = chain.invoke({"query": state["query"]})

    # Parse numbered list
    sub_questions = []
    for line in response.content.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            q = line.split(".", 1)[-1].strip()
            if q:
                sub_questions.append(q)

    return {"sub_questions": sub_questions[:5]}