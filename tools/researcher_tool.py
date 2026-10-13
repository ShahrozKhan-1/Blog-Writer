from config import TAVILY_API_KEY, WEBZ_API_URL, WEBZ_API_TOKEN
from schema import NewsSearchInput, Source
from langchain_tavily import TavilySearch
from bs4 import BeautifulSoup
from langchain.tools import tool
from urllib.request import Request, urlopen
from bs4.element import Comment
import requests
import httpx




@tool
def tavily_tool(content: str) -> list[Source] | str:
    """
    Search the web for reliable and relevant information about a topic.
    Use this for general research, facts, articles, documentation, and reports.
    It is primarily used to discover useful sources related to the research topic.
    Use this when the information does not specifically require current news.
    The search query should be clear and focused on the required information.
    Review the returned sources before using their information.
    Returns source titles, URLs, and summaries from the search results.
    Only live, reachable URLs are returned.
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
def get_web_content(url: str) -> str:
    """
    Fetch and extract readable content from a specific webpage URL.
    Use this when detailed information from a previously discovered source is needed.
    The URL should normally come from a relevant search result.
    Use this tool to inspect, verify, or extract additional information from a source.
    It retrieves the visible text available on the webpage.
    Do not use it for discovering new sources; use a search tool for that.
    Returns the extracted text content of the webpage.
    """
    try:
        req = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/138.0.0.0 Safari/537.36"
                )
            },
        )
        html = urlopen(req).read()
        soup = BeautifulSoup(html, "html.parser")
        visible_text = " ".join(
            text.strip()
            for text in soup.find_all(string=True)
            if text.parent.name not in [
                "style", "script", "head", "title", "meta", "[document]"
            ]
            and not isinstance(text, Comment)
            and text.strip()
        )
        return visible_text
    except Exception as e:
        return f"Unable to fetch webpage content: {e}"


@tool(args_schema=NewsSearchInput)
def search_news(query: str):
    """
    Search for recent and current news related to a specific topic.
    Use this for breaking news, recent events, announcements, and developments.
    It is useful when the research requires information from the latest news.
    Use a focused query describing the topic or event that needs investigation.
    Review the returned articles and prefer relevant and credible sources.
    Do not use this as the primary tool for general, non-time-sensitive research.
    Returns relevant news articles with their title, URL, date, source, and content.
    Only live, reachable URLs are returned.
    """
    params = {
        "token": WEBZ_API_TOKEN,
        "q": query,
        "sort": "crawled",
        "format": "json",
        "size": 10,
        "webz_reporter": "true",
        "includeSyndicated": "false",
        "allowNewsHistory": "false",
    }

    try:
        response = requests.get(
            WEBZ_API_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()
        articles = []

        for article in data.get("posts", []):
            url = article.get("url")
            if not url or not _is_url_live(url):
                continue
            thread = article.get("thread", {})
            articles.append({
                "title": article.get("title"),
                "url": url,
                "published": article.get("published"),
                "source": thread.get("site_title"),
                "summary": article.get("summary"),
                "text": article.get("text"),
            })

        if not articles:
            return {
                "query": query,
                "articles": [],
                "note": "No live articles found. No recent developments confirmed.",
            }

        return {
            "query": query,
            "articles": articles
        }
    except requests.RequestException as e:
        return {
            "error": f"News search failed: {str(e)}"
        }



researcher_toolkit = [tavily_tool, get_web_content, search_news]
