"""
Article generation.

Claude turns the gathered source material into a publishable Insights post in the
ARIS voice, returned as a strict JSON object the renderer can drop into the site
template. The system prompt is deliberately conservative about claims — this
content represents ARIS to carriers, reinsurers, and analytics platforms, so it
must never fabricate facts or imply relationships that don't exist.
"""

import datetime
import json
import re

import anthropic

from . import config

SYSTEM_PROMPT = """\
You are the analyst who writes the weekly "Insights" essay for ARIS Risk Inc., a \
company that sells parcel-level, physics-grounded wildfire risk intelligence to \
P&C insurance. ARIS's signature is a 2026 California forecast that was sealed and \
cryptographically timestamped before fire season, so reality grades it — not a \
backtest.

AUDIENCE: insurance executives, actuaries, reinsurance and ILS professionals. \
VOICE: sharp, technical, confident, plainspoken. No hype, no buzzwords, no \
exclamation marks, no "in today's fast-paced world" filler. Make a real argument. \
Match the style of a senior analyst writing for peers who can smell BS.

HARD RULES — these protect the company and are non-negotiable:
- Do NOT fabricate statistics, dollar figures, dates, percentages, quotes, or \
study results. If you reference a real development, it must be supportable from \
the SOURCE MATERIAL provided. Otherwise argue qualitatively.
- Do NOT claim ARIS has any customers, signed partners, pilots, or specific \
deals. Do NOT name any specific company as an ARIS partner or customer. Never \
mention "Verisk" at all.
- The ONLY ARIS capabilities you may assert are these established ones: a sealed, \
cryptographically timestamped 2026 California forecast; parcel-level resolution; \
physics-grounded fire science (fuel, terrain, wind, defensible space); \
bit-for-bit reproducibility and auditing for data leakage; pure-play data with \
no channel conflict (ARIS does not write insurance).
- You may critique legacy/incumbent catastrophe models and ZIP/county-level \
approaches in general terms, and you may discuss named competitors' publicly \
known approaches factually and fairly — but do not assert private or unverifiable \
facts about them.
- Pick a fresh angle that is NOT a rehash of the recent titles you are given.

OUTPUT: a single strict JSON object and NOTHING else (no markdown, no code \
fences). Keys:
  "kicker": one or two words categorizing the post (e.g. "Methodology", \
"Regulation", "Resolution", "Market", "Science").
  "title": <= 70 characters, specific and compelling, no clickbait.
  "slug": lowercase, hyphen-separated, ASCII only, derived from the title, \
<= 60 characters.
  "description": a meta description, 120-160 characters, plain text.
  "lede": one strong opening paragraph, plain text, no HTML tags.
  "body_html": the article body as clean HTML, 550-850 words. Use ONLY these \
tags: <h2>, <p>, <ul>, <li>, <strong>, <blockquote>, and <a href="...">. \
Include at least two <h2> headings and one <blockquote>. Do NOT include <h1>, \
<script>, <style>, <img>, inline styles, or class attributes. End by connecting \
the argument to the way ARIS approaches the problem.
  "card_summary": a 1-2 sentence teaser for the article card, plain text, \
<= 200 characters.
"""


def _coerce_json(text: str) -> dict:
    """Extract and parse the JSON object from the model output."""
    text = text.strip()
    # Strip accidental code fences.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output.")
    return json.loads(text[start : end + 1])


def write_article(
    raw_source_text: str,
    recent_titles: list[str],
    today: datetime.date | None = None,
) -> dict:
    """Generate one Insights article as a structured dict."""
    today = today or datetime.date.today()
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)

    recent = "\n".join(f"- {t}" for t in recent_titles) or "(none yet)"
    sources = raw_source_text or "(No fresh sources were retrieved — write an " \
        "evergreen analytical essay grounded only in established, widely-known " \
        "industry dynamics, and do not invent specifics.)"

    user_message = (
        f"Today is {today.strftime('%A, %B %-d, %Y')}.\n\n"
        f"RECENT POST TITLES (do not repeat these angles):\n{recent}\n\n"
        f"SOURCE MATERIAL:\n{sources}\n\n"
        "Write one new ARIS Insights post as the JSON object specified."
    )

    with client.messages.stream(
        model=config.WRITER_MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        message = stream.get_final_message()

    text = "".join(b.text for b in message.content if b.type == "text")
    article = _coerce_json(text)

    required = {"kicker", "title", "slug", "description", "lede", "body_html", "card_summary"}
    missing = required - article.keys()
    if missing:
        raise ValueError(f"Model output missing keys: {sorted(missing)}")

    # Defense-in-depth: never let a stray script tag through.
    article["body_html"] = re.sub(
        r"<script.*?</script>", "", article["body_html"], flags=re.S | re.I
    )
    print(f"Write complete: \"{article['title']}\" ({len(article['body_html'].split())} words).")
    return article
