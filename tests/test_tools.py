"""Test search tools work with real APIs."""
import pytest

def test_arxiv_returns_results():
    from src.tools.arxiv_search import search_arxiv
    result = search_arxiv.invoke({"query": "transformer attention mechanism", "max_results": 2})
    assert "Title:" in result
    assert len(result) > 100

def test_arxiv_no_results():
    from src.tools.arxiv_search import search_arxiv
    result = search_arxiv.invoke({"query": "xyznonexistentquery12345", "max_results": 1})
    assert "No papers" in result or "Title:" in result

def test_semantic_scholar_returns_results():
    from src.tools.semantic_scholar import search_semantic_scholar
    result = search_semantic_scholar.invoke({"query": "large language models", "max_results": 2})
    assert "Title:" in result

def test_vector_store_create_and_search():
    from src.tools.vector_store import cache_papers, search_cached
    cache_papers(["Test paper about transformers and attention mechanisms"])
    results = search_cached("attention", k=1)
    assert len(results) >= 1