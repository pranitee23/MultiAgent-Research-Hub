"""arXiv search tool — free, no API key."""
import arxiv
from langchain_core.tools import tool
from src.config.settings import settings


@tool
def search_arxiv(query: str, max_results: int = 0) -> str:
    """Search arXiv for academic papers. Returns titles, abstracts, URLs."""
    if max_results == 0:
        max_results = settings.arxiv_max_results

    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)

    results = []
    for paper in client.results(search):
        results.append(
            f"Title: {paper.title}\n"
            f"Authors: {', '.join(a.name for a in paper.authors[:3])}\n"
            f"Date: {paper.published.strftime('%Y-%m-%d')}\n"
            f"Abstract: {paper.summary[:200]}\n"
            f"URL: {paper.entry_id}"
        )
    return "\n\n---\n\n".join(results) if results else "No papers found."