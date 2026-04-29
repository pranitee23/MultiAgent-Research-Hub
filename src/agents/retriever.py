"""Retriever: searches arXiv + Semantic Scholar for each sub-question.

- All sub-questions are fetched in parallel (ThreadPoolExecutor).
- Papers are deduplicated across sub-questions by title.
- Results are cached to FAISS for instant repeat lookups.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.tools.arxiv_search import search_arxiv
from src.tools.semantic_scholar import search_semantic_scholar
from src.core.state import ResearchState


logger = logging.getLogger(__name__)


def _fetch_papers_for_question(sub_q: str) -> tuple[str, str]:
    """Fetch from both sources for a single sub-question. Runs in a thread."""
    papers_text = ""

    try:
        arxiv_results = search_arxiv.invoke({"query": sub_q})
        papers_text += f"**arXiv:**\n{arxiv_results}\n\n"
    except Exception as e:
        logger.warning(f"arXiv failed for '{sub_q}': {e}")
        papers_text += "**arXiv:** Search failed\n\n"

    try:
        s2_results = search_semantic_scholar.invoke({"query": sub_q, "max_results": 3})
        papers_text += f"**Semantic Scholar:**\n{s2_results}"
    except Exception as e:
        logger.warning(f"S2 failed for '{sub_q}': {e}")
        papers_text += "**Semantic Scholar:** Unavailable"

    return sub_q, papers_text


_TITLE_RE = re.compile(r"Title:\s*(.+)", re.IGNORECASE)


def _deduplicate_papers(all_papers: dict[str, str]) -> dict[str, str]:
    """Remove duplicate papers across sub-questions by title."""
    seen_titles: set[str] = set()
    deduped: dict[str, str] = {}

    for sub_q, text in all_papers.items():
        blocks = text.split("---")
        unique_blocks = []
        for block in blocks:
            match = _TITLE_RE.search(block)
            if match:
                title = match.group(1).strip().lower()
                if title in seen_titles:
                    continue
                seen_titles.add(title)
            unique_blocks.append(block)
        deduped[sub_q] = "---".join(unique_blocks)

    return deduped


def _cache_to_faiss(all_papers: dict[str, str]) -> None:
    """Cache paper texts to FAISS for repeat query lookups."""
    try:
        from src.tools.vector_store import cache_papers
        texts = [text[:2000] for text in all_papers.values() if text.strip()]
        if texts:
            cache_papers(texts)
    except Exception as e:
        logger.debug(f"FAISS cache write skipped: {e}")


def retriever_node(state: ResearchState) -> dict:
    sub_questions = state["sub_questions"]

    all_papers: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=len(sub_questions) * 2) as pool:
        futures = {
            pool.submit(_fetch_papers_for_question, q): q
            for q in sub_questions
        }
        for future in as_completed(futures):
            try:
                sub_q, papers_text = future.result()
                all_papers[sub_q] = papers_text
            except Exception as e:
                q = futures[future]
                logger.error(f"Retrieval failed entirely for '{q}': {e}")
                all_papers[q] = "Search failed for this sub-question."

    all_papers = _deduplicate_papers(all_papers)
    _cache_to_faiss(all_papers)

    return {"retrieved_papers": all_papers}