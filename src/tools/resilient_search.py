"""Retry decorator with exponential backoff for search tools."""
import logging, time
from functools import wraps

logger = logging.getLogger(__name__)


def with_retry(max_retries=2, timeout_seconds=30, fallback="Search temporarily unavailable."):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    start = time.time()
                    result = func(*args, **kwargs)
                    logger.info(f"{func.__name__} OK in {time.time()-start:.1f}s (attempt {attempt+1})")
                    return result
                except Exception as e:
                    logger.warning(f"{func.__name__} attempt {attempt+1} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                    else:
                        return fallback
        return wrapper
    return decorator

# Usage: wrap your existing @tool functions
# @with_retry(max_retries=2)
# @tool
# def search_arxiv(...): ...