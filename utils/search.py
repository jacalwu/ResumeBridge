"""Web search utility — finds real learning resources for skill gaps.

Uses DuckDuckGo Instant Answer API (free, no key required).
Gracefully degrades if the library is not installed or search fails.
"""

from typing import Optional


def search_resources(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for learning resources related to a skill/topic.

    Returns a list of dicts: {title, url, snippet}.
    Returns empty list if search is unavailable or fails.
    """
    if not query or not query.strip():
        return []

    # Append learning intent to the query
    full_query = f"{query.strip()} course tutorial learning guide"

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return _fallback_suggestions(query)

    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(full_query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            return results
    except Exception:
        return _fallback_suggestions(query)


def _fallback_suggestions(query: str) -> list[dict]:
    """
    Return curated platform-specific search links when live search is unavailable.
    These are NOT hallucinated — they are URL templates that resolve to real search results.
    """
    q = query.strip().replace(" ", "+")
    return [
        {
            "title": f"Search Coursera for '{query}'",
            "url": f"https://www.coursera.org/search?query={q}",
            "snippet": "Browse top-rated courses from leading universities on Coursera.",
        },
        {
            "title": f"Search Udemy for '{query}'",
            "url": f"https://www.udemy.com/courses/search/?q={q}",
            "snippet": "Find practical, hands-on courses on Udemy.",
        },
        {
            "title": f"Search edX for '{query}'",
            "url": f"https://www.edx.org/search?q={q}",
            "snippet": "Explore free and paid courses from top institutions on edX.",
        },
        {
            "title": f"Search YouTube for '{query}'",
            "url": f"https://www.youtube.com/results?search_query={q}+tutorial",
            "snippet": "Watch free video tutorials and lectures on YouTube.",
        },
        {
            "title": f"Search Google for '{query}'",
            "url": f"https://www.google.com/search?q={q}+learning+resources",
            "snippet": "General web search for learning materials and documentation.",
        },
    ]


def is_search_available() -> bool:
    """Check if live DuckDuckGo search is available."""
    try:
        from duckduckgo_search import DDGS  # noqa: F401
        return True
    except ImportError:
        return False
