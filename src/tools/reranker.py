"""Cross-encoder reranker for retrieved papers.

Scores each paper block against the original query and keeps only
the top-k most relevant, filtering noise before synthesis.

Uses sentence-transformers CrossEncoder (already a project dependency)
with a lightweight model that runs locally in ~100ms.
"""

import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("Cross-encoder reranker loaded")
    return _reranker


def rerank_papers(
    query: str,
    paper_blocks: list[str],
    top_k: int = 0,
) -> list[str]:
    """Rerank paper blocks by relevance to query, return top-k.

    Args:
        query: The original user query.
        paper_blocks: List of paper text blocks (title+abstract+metadata).
        top_k: Number of top results to keep. Defaults to arxiv_max_results.

    Returns:
        The top-k paper blocks sorted by relevance (most relevant first).
    """
    if not paper_blocks:
        return paper_blocks

    if top_k <= 0:
        top_k = settings.arxiv_max_results

    try:
        model = _get_reranker()
        pairs = [(query, block) for block in paper_blocks]
        scores = model.predict(pairs)

        scored = sorted(zip(scores, paper_blocks), key=lambda x: x[0], reverse=True)
        return [block for _, block in scored[:top_k]]
    except Exception as e:
        logger.warning(f"Reranking failed, returning original order: {e}")
        return paper_blocks[:top_k]
