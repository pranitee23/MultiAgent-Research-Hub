"""Synthesizer: builds structured summary from retrieved papers.

Papers are reranked by cross-encoder relevance before synthesis
to filter noise and prioritize the most relevant results.
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.state import ResearchState
from src.config.prompts import SYNTHESIZER_SYSTEM
from src.tools.reranker import rerank_papers

logger = logging.getLogger(__name__)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYNTHESIZER_SYSTEM),
    ("human", "Original query: {query}\n\nRetrieved papers:\n{papers}\n\nCreate synthesis:")
])


def synthesizer_node(state: ResearchState) -> dict:
    llm = get_llm(temperature=0.4).bind(max_tokens=1500)
    query = state["query"]

    all_blocks: list[str] = []
    for papers_text in state["retrieved_papers"].values():
        blocks = [b.strip() for b in papers_text.split("---") if b.strip()]
        all_blocks.extend(blocks)

    reranked = rerank_papers(query, all_blocks, top_k=8)
    papers_text = "\n\n---\n\n".join(reranked)

    chain = prompt | llm
    response = chain.invoke({"query": query, "papers": papers_text[:8000]})
    return {"synthesis": response.content}