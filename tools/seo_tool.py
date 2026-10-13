from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from schema import SerpApiInput, GetKeywordIdeasInput, AnalyzeTopCompetitorsInput
from langchain_core.tools import tool
from bs4 import BeautifulSoup
import requests
from config import SERP_API_KEY


_NON_CONTENT_URL_MARKERS = (
    "/contact",
    "/about",
    "/cart",
    "/checkout",
    "/login",
    "/signin",
    "/sign-in",
    "/signup",
    "/sign-up",
    "/account",
    "/privacy",
    "/terms",
    "/faq",
    "/help",
    "/support",
    "/forum",
    "/forums",
    "/community",
    "/discussion",
    "/thread",
    "/topic",
    "/tag/",
    "/category/",
    "/author/",
    "/search",
    "/sitemap",
)

_NON_CONTENT_DOMAINS = (
    "reddit.com",
    "quora.com",
    "stackexchange.com",
    "stackoverflow.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
    "youtube.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
)

_BOILERPLATE_HEADING_MARKERS = (
    "contact us",
    "for sales",
    "sales help",
    "customer service",
    "customer support",
    "recent posts",
    "recent articles",
    "latest news",
    "latest posts",
    "browse our",
    "connect with us",
    "follow us",
    "subscribe",
    "newsletter",
    "related topics",
    "related posts",
    "related articles",
    "you may also like",
    "recommended for you",
    "shopping cart",
    "your cart",
    "sign in",
    "log in",
    "register",
    "privacy policy",
    "terms of",
    "cookie",
    "dpd",
    "shipping",
    "delivery",
    "returns",
    "refund",
    "faq",
    "help center",
    "about us",
    "about our",
    "our story",
    "our team",
    "careers",
    "press",
    "menu",
    "navigation",
    "search",
    "share",
    "tags",
    "categories",
)


def _is_content_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    if any(marker in lowered for marker in _NON_CONTENT_URL_MARKERS):
        return False
    if any(domain in lowered for domain in _NON_CONTENT_DOMAINS):
        return False
    path = urlparse(url).path.strip("/")
    if not path:
        return False
    return True


def _is_boilerplate_heading(text: str) -> bool:
    if not text:
        return True
    lowered = text.lower().strip()
    if len(lowered) < 4:
        return True
    if lowered.endswith(":") and len(lowered.split()) <= 4:
        return True
    return any(marker in lowered for marker in _BOILERPLATE_HEADING_MARKERS)


@tool("search_serpapi", args_schema=SerpApiInput)
def search_serpapi(
    engine: str,
    query: str,
    num_results: int = 10,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run a raw SerpApi search against a specific engine and return the JSON response.

    Use this tool when you need a custom SerpApi query that the higher-level tools
    (get_keyword_ideas, analyze_top_competitors) do not cover — for example news,
    images, scholar, or localized results. For SEO keyword and competitor workflows,
    prefer the dedicated tools instead.

    Returns the raw SerpApi JSON on success, or {'error': '<message>'} on failure.
    """
    base_url = "https://serpapi.com/search"
    params: Dict[str, Any] = {
        "engine": engine,
        "q": query,
        "api_key": SERP_API_KEY,
    }
    if engine == "google":
        params.setdefault("num", num_results)
    if extra_params:
        params.update(extra_params)

    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@tool("get_keyword_ideas", args_schema=GetKeywordIdeasInput)
def get_keyword_ideas(seed_keyword: str) -> Dict[str, List[str]]:
    """
    Phase 1: Discover keyword ideas for a seed keyword.

    Aggregates Google Autocomplete suggestions, People Also Ask (PAA) questions, and
    Related Searches from the top Google results for the seed keyword. Use this as the
    first step when building a keyword plan or content brief.

    Returns a dict with three lists:
      - 'autocomplete': Google autocomplete suggestions
      - 'related_questions': People Also Ask questions
      - 'related_searches': related search queries from the SERP
    """
    ac_results = search_serpapi.invoke(
        {"engine": "google_autocomplete", "query": seed_keyword}
    )
    autocomplete = [s["value"] for s in ac_results.get("suggestions", [])]

    search_results = search_serpapi.invoke(
        {"engine": "google", "query": seed_keyword}
    )
    related_questions = [
        q["question"] for q in search_results.get("related_questions", [])
    ]
    related_searches = [
        s["query"] for s in search_results.get("related_searches", [])
    ]
    return {
        "autocomplete": autocomplete,
        "related_questions": related_questions,
        "related_searches": related_searches,
    }


@tool("analyze_top_competitors", args_schema=AnalyzeTopCompetitorsInput)
def analyze_top_competitors(
    keyword: str, num_results: int = 7
) -> List[Dict[str, Any]]:
    """
    Phase 2: Analyze the top-ranking competitor pages for a keyword.

    Fetches the top organic Google results for the keyword and scrapes each page's
    H1/H2/H3 headings to reveal content structure and coverage. Non-content URLs
    (contact/about/cart/forums/social/homepages) and boilerplate headings (nav,
    footer, recent posts, etc.) are filtered out automatically so the returned
    headings reflect real article structure.

    Use this after get_keyword_ideas to understand what a winning page must cover.

    Returns a list of dicts, one per successfully scraped competitor:
      - 'title': page title from the search results
      - 'url': page URL
      - 'headings': up to 15 article headings (H1-H3), boilerplate removed
    """
    results = search_serpapi.invoke(
        {"engine": "google", "query": keyword, "num_results": num_results}
    )
    organic_results = results.get("organic_results", [])

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    competitor_analysis: List[Dict[str, Any]] = []

    for result in organic_results:
        if len(competitor_analysis) >= num_results:
            break

        url = result.get("link")
        title = result.get("title")

        if not _is_content_url(url):
            print(f"  Skipping non-content URL: {url}")
            continue

        try:
            page = requests.get(url, timeout=10, headers=headers)
            page.raise_for_status()
            soup = BeautifulSoup(page.content, "html.parser")

            raw_headings = [
                h.get_text().strip()
                for h in soup.find_all(["h1", "h2", "h3"])
            ]
            seen = set()
            headings: List[str] = []
            for text in raw_headings:
                if not text or text in seen:
                    continue
                seen.add(text)
                if _is_boilerplate_heading(text):
                    continue
                headings.append(text)

            competitor_analysis.append(
                {
                    "title": title,
                    "url": url,
                    "headings": headings[:15],
                }
            )
        except Exception as e:
            print(f"  Could not scrape {url}: {e}")

    return competitor_analysis


seo_toolkit = [search_serpapi, get_keyword_ideas, analyze_top_competitors]