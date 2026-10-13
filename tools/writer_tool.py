import httpx
import requests
from langchain_core.tools import tool
from config import UNSPLASH_ACCESS_KEY
from config import TAVILY_API_KEY
from schema import Source
from langchain_tavily import TavilySearch



def _is_url_live(url: str, timeout: float = 5.0) -> bool:
    """Return True if the URL responds with a 2xx/3xx status."""
    if not url:
        return False
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        ) as client:
            resp = client.head(url)
            # Some servers reject HEAD; retry with GET
            if resp.status_code in (403, 405):
                resp = client.get(url)
            return 200 <= resp.status_code < 400
    except Exception:
        return False


@tool
def tavily_tool(content: str) -> list[Source] | str:
    """
    Search the live web for reliable, citable sources on a topic.
    Use it to find authoritative sources (.gov/.edu, reports, docs), verify
    statistics or factual claims, and gather 2-4 external citations when the
    brief has no reference URLs. Not for breaking news, paywalled content, or
    opinions. Input is a focused, specific query (e.g., "B2B SaaS content
    marketing ROI benchmarks 2025"). Returns up to 5 live sources with title,
    url, date, and summary, or a fallback string if none are reachable.
    Always review sources before citing; never fabricate citations.
    """
    try:
        tavily_search_tool = TavilySearch(max_results=5, api_key=TAVILY_API_KEY)
        result = tavily_search_tool.invoke({"query": content})

        candidates = [
            Source(
                title=item.get("title", ""),
                url=item.get("url", ""),
                date=item.get("date", ""),
                summary=item.get("content", ""),
            )
            for item in result.get("results", [])
        ]

        live_sources = [s for s in candidates if _is_url_live(s.url)]

        dropped = len(candidates) - len(live_sources)
        if dropped:
            print(f"tavily_tool: dropped {dropped} dead URL(s)")
        return live_sources or "No live sources found."
    except Exception as e:
        return f"Tavily search failed: {e}"



writer_toolkit = [tavily_tool]