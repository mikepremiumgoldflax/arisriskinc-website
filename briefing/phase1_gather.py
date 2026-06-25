"""
Phase 1: Intelligence Gathering (Search & Scraping).

The pipeline does not rely on a single static scraper. It runs targeted search
queries across news and industry databases, then extracts article text with
BeautifulSoup. Search is done through the Tavily API; the BeautifulSoup scraper
below is unchanged from the documented ARIS pipeline.
"""

import datetime
import re

import requests
from bs4 import BeautifulSoup

from . import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def target_search_queries(today: datetime.date) -> list[str]:
    """The ARIS-relevant search queries, with today's date/month/year filled in."""
    date_str = today.strftime("%B %-d, %Y")   # e.g. "June 25, 2026"
    month_year = today.strftime("%B %Y")        # e.g. "June 2026"
    year = today.strftime("%Y")                 # e.g. "2026"
    return [
        f"AI news today {date_str}",
        f"InsurTech AI funding acquisition {month_year}",
        f"ZestyAI CoreLogic Cape Analytics news {year}",
        f"California wildfire insurance FAIR Plan {month_year}",
        f"State Farm CDI California insurance enforcement {year}",
    ]


def search(query: str) -> list[dict]:
    """Run one query against the Tavily search API. Returns [{title,url,content}]."""
    if not config.TAVILY_API_KEY:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": config.RESULTS_PER_QUERY,
                "include_raw_content": True,
                "topic": "news",
            },
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": (r.get("raw_content") or r.get("content") or "").strip(),
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        return []


def scrape_article_text(url: str) -> str | None:
    """Scrape the main text content from a given URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        # Extract text from paragraphs
        paragraphs = soup.find_all("p")
        text_content = "\n\n".join(
            p.get_text().strip() for p in paragraphs if p.get_text().strip()
        )

        # Clean up extra whitespace
        text_content = re.sub(r"\n{3,}", "\n\n", text_content)
        return text_content
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def gather(today: datetime.date | None = None) -> str:
    """Run all queries, collect article text, and return one raw intelligence blob."""
    today = today or datetime.date.today()
    seen_urls: set[str] = set()
    articles: list[str] = []

    queries = target_search_queries(today)
    for query in queries:
        for result in search(query):
            url = result["url"]
            if not url or url in seen_urls or len(articles) >= config.MAX_ARTICLES:
                continue
            seen_urls.add(url)

            # Prefer Tavily's extracted content; deep-scrape if it's thin.
            body = result["content"]
            if len(body) < 400:
                scraped = scrape_article_text(url)
                if scraped:
                    body = scraped
            if len(body) < 200:
                continue

            articles.append(
                f"SOURCE: {result['title']}\nURL: {url}\nQUERY: {query}\n\n{body[:6000]}"
            )

    # Fallback: no Tavily key, scrape the fixed source list directly.
    if not articles and not config.TAVILY_API_KEY:
        print("No TAVILY_API_KEY set — scraping fallback source list.")
        for url in config.FALLBACK_SOURCE_URLS:
            if len(articles) >= config.MAX_ARTICLES:
                break
            scraped = scrape_article_text(url)
            if scraped and len(scraped) > 200:
                articles.append(f"SOURCE: {url}\nURL: {url}\n\n{scraped[:6000]}")

    print(f"Phase 1 complete: gathered {len(articles)} article(s).")
    return "\n\n========================================\n\n".join(articles)
