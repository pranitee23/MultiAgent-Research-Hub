"""Semantic Scholar search — free, no API key, 100 req/sec."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from semanticscholar import SemanticScholar
from langchain_core.tools import tool
from src.config.settings import settings

_S2_TIMEOUT = 10


def _s2_search(query: str, max_results: int):
    sch = SemanticScholar(timeout=5)
    return sch.search_paper(query, limit=max_results,
        fields=["title", "abstract", "year", "citationCount", "url", "authors"])


@tool
def search_semantic_scholar(query: str, max_results: int = 0) -> str:
    """Search Semantic Scholar for papers with citation counts."""
    if max_results == 0:
        max_results = settings.scholar_max_results

    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(_s2_search, query, max_results)
    try:
        results = future.result(timeout=_S2_TIMEOUT)
    except FuturesTimeout:
        pool.shutdown(wait=False, cancel_futures=True)
        # #region agent log
        import json as _json, time as _time; open("debug-4a2b3a.log","a").write(_json.dumps({"sessionId":"4a2b3a","hypothesisId":"S2-timeout","location":"semantic_scholar.py","message":"S2 hard timeout hit","data":{"query":query[:60],"timeout":_S2_TIMEOUT},"timestamp":int(_time.time()*1000)})+"\n")
        # #endregion
        return "Semantic Scholar timed out."
    except Exception:
        pool.shutdown(wait=False, cancel_futures=True)
        return "Semantic Scholar temporarily unavailable."
    pool.shutdown(wait=False)

    if not results:
        return "No papers found."

    output = []
    for p in results[:max_results]:
        authors = ", ".join(str(a.name) if hasattr(a, "name") else str(a) for a in (p.authors or [])[:3])
        output.append(
            f"Title: {p.title}\n"
            f"Authors: {authors}\n"
            f"Year: {p.year} | Citations: {p.citationCount}\n"
            f"Abstract: {(p.abstract or 'N/A')[:200]}\n"
            f"URL: {p.url}"
        )
    return "\n\n---\n\n".join(output)