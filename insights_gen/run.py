"""
Orchestrator for the ARIS Insights generator.

    python -m insights_gen.run

Steps: gather sources -> write one article -> render it into the site files ->
record it in history.json. The GitHub Actions workflow then opens a pull request
with the resulting file changes (draft-for-review by default).

Exit codes: 0 = an article was generated and written; 3 = skipped (e.g. no
ANTHROPIC_API_KEY). Any unexpected error propagates as a non-zero exit so the
workflow surfaces it instead of opening an empty PR.
"""

import datetime
import json
import os
import sys

from . import config, gather, render, write


def _load_history() -> list[dict]:
    if not os.path.exists(config.HISTORY_FILE):
        return []
    try:
        with open(config.HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history: list[dict]) -> None:
    with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _emit_outputs(slug: str, title: str) -> None:
    """Expose slug/title to the workflow via $GITHUB_OUTPUT when running in CI."""
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"slug={slug}\n")
        f.write(f"title={title}\n")
        f.write("generated=true\n")


def main() -> int:
    if not config.ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set — skipping insight generation.")
        return 3

    today = datetime.date.today()
    history = _load_history()
    recent_titles = [h["title"] for h in history[-config.RECENT_TITLES_WINDOW:]]

    raw = gather.gather(today)
    article = write.write_article(raw, recent_titles, today)
    slug = render.write_to_disk(article, today)

    history.append({
        "slug": slug,
        "title": article["title"],
        "kicker": article["kicker"],
        "date": today.isoformat(),
    })
    _save_history(history)
    _emit_outputs(slug, article["title"])

    print(f"\nDone. New draft post: insights/{slug}.html — \"{article['title']}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
