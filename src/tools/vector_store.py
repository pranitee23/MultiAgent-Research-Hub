"""Cache retrieved papers locally for instant repeat lookups."""
import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from src.config.settings import settings

STORE_PATH = "data/paper_cache"
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    return _embeddings


def get_or_create_store():
    emb = _get_embeddings()
    if os.path.exists(f"{STORE_PATH}/index.faiss"):
        return FAISS.load_local(STORE_PATH, emb, allow_dangerous_deserialization=True)
    store = FAISS.from_texts(["initialization placeholder"], emb)
    store.save_local(STORE_PATH)
    return store


def cache_papers(texts: list[str]):
    store = get_or_create_store()
    if texts:
        store.add_texts(texts)
        store.save_local(STORE_PATH)


def search_cached(query: str, k: int = 3) -> list:
    store = get_or_create_store()
    return store.similarity_search(query, k=k)