"""
Source gathering for Insights posts.

Reuses the battle-tested Tavily search + BeautifulSoup scraper from the briefing
pipeline (`briefing.phase1_gather`) so there's a single implementation to
maintain. Only the search queries differ — these are tuned for the kind of
material that makes a good ARIS Insights essay: legacy-model failures, the
California regulatory shift, parcel-level / catastrophe-modeling science, and
the wider wildfire-insurance market.
"""

import datetime

from briefing.phase1_gather import scrape_article_text, search
from . import config


def target_search_queries(today: datetime.date) -> list[str]:
    """Insights-relevant queries, with the current month/year filled in."""
    month_year = today.strftime("%B %Y")
    year = today.strftime("%Y")
    return [
        f"wildfire catastrophe model accuracy criticism {year}",
        f"California wildfire insurance regulation FAIR Plan rate filing {month_year}",
        f"parcel-level property risk modeling wildfire {year}",
        f"P&C insurers exiting California wildfire losses {month_year}",
        f"climate catastrophe model reinsurance pricing {year}",
        f"ZestyAI CoreLogic Cape Analytics wildfire model {year}",
    ]


def gather(today: datetime.date | None = None) -> str:
    """Run the queries, collect article text, return one raw source blob."""
    today = today or datetime.date.today()
    seen_urls: set[str] = set()
    articles: list[str] = []

    for query in target_search_queries(today):
        for result in search(query):
            url = result["url"]
            if not url or url in seen_urls or len(articles) >= config.MAX_ARTICLES:
                continue
            seen_urls.add(url)

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

    print(f"Gather complete: {len(articles)} source article(s).")
    return "\n\n========================================\n\n".join(articles)
