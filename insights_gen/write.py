"""
Article generation.

Claude turns the gathered source material into a publishable Insights post in the
ARIS voice, returned as a strict JSON object the renderer can drop into the site
template. The system prompt is deliberately conservative about claims — this
content represents ARIS to carriers and reinsurers, so it
must never fabricate facts or imply relationships that don't exist.
"""

import datetime
import json
import re

import anthropic

from . import config

# How many times to regenerate when the sourcing gate rejects a draft before
# failing closed. Each retry feeds the exact rejection back to the model.
MAX_TRIES = 3

SYSTEM_PROMPT = """\
You are the analyst who writes an "Insights" note for ARIS Risk Inc., a company \
that builds physics-based, parcel-resolved wildfire catastrophe models for \
insurers and reinsurers. The model simulates fire across fuel, terrain and \
weather over ten thousand seasons, estimates the probability each structure is \
reached and lost, and writes exceedance-probability output in open insurer \
standards. The 2026 California forecast was sealed before the season. The \
grading method is sealed with it. The grade is published whatever it says.

AUDIENCE: insurance executives, actuaries, reinsurance and ILS professionals. \
VOICE: sharp, technical, confident, plainspoken. No hype, no buzzwords, no \
exclamation marks, no "in today's fast-paced world" filler. Make a real argument. \
Match the style of a senior analyst writing for peers who can smell BS.

HARD RULES — these protect the company and are non-negotiable:
- SOURCING IS MANDATORY. Every specific, checkable claim — any statistic, dollar \
figure, percentage, date, named event, named place, named organization, or direct \
quotation — MUST come from the SOURCE MATERIAL and MUST carry an inline citation: \
wrap the claim in <a href="EXACT-URL-FROM-SOURCE-MATERIAL">…</a> pointing to the \
source it came from. Use ONLY URLs that appear verbatim in the SOURCE MATERIAL — \
never invent, guess, or modify a URL.
- If a specific claim is not supported by the SOURCE MATERIAL, DO NOT make it — \
argue qualitatively instead. When in doubt, leave it out.
- If the SOURCE MATERIAL is empty or thin, write an evergreen analytical essay \
with NO specific statistics, dates, named events, or quotations, and return an \
empty "sources" array. A sourced qualitative piece is always better than an \
unsourced specific one.
- Do NOT claim ARIS has any customers, signed pilots, platform deals, \
procurement, bids, or named counterparties. Do NOT name any company as an ARIS \
partner or customer. Never mention a vendor or competitor by name, including \
"Verisk".
- Do NOT write a legacy-versus-ARIS comparison, a smackdown table, or peer \
superiority framing. Describe what ARIS does. Do not grade other models.
- Do NOT claim the site publishes a new analysis every week, or any other \
cadence. Notes are occasional.
- Do NOT invent results. Do NOT state an October 15 grade, a December 31 \
supplementary run, an accuracy figure, a policy count, a price, or a per-policy \
figure. Do NOT mention hail as a built model, First Nations, renewables, \
listing dates, or "Stage 2".
- California mitigation, if you discuss it: twelve measures that can bear on \
rates. Directional language only. It is not a mandate to buy a model.
- The ONLY ARIS capabilities you may assert are these: a physics-based, \
parcel-resolved wildfire catastrophe model; a ten-thousand-season catalogue; \
the probability each structure is reached and lost; exceedance-probability \
output in open insurer standards (do not name a format vendor); portfolio and \
accumulation views; pricing-grade parcel scores; mitigation targeting, \
planning, and rescoring on the same engine; response intelligence only as a \
concept demonstration available in 2027; the Prairie engine only as a 2027 \
build in progress, delivered with unnamed Saskatchewan field partners; the \
company based in Saskatchewan; model data stored in Canada; dedicated compute \
in Canada and no other hardware specification. Architecture in public is only \
"physics-based, two-stage, sealed and graded."
- Reproducibility may be stated as "100% reproducible bit-for-bit." Do NOT say \
the model was audited for data leakage, blind-tested, or certified against \
leakage.
- The forecast is sealed before the season, the grading method is sealed, and \
the grade is published whatever it says. You may say the 2026 California \
forecast was sealed before the season. You may not invent the grade.
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
Include at least two <h2> headings and one <blockquote>. Every specific claim \
must carry an inline <a href="..."> citation as described in the HARD RULES. Do \
NOT include <h1>, <script>, <style>, <img>, inline styles, or class attributes. \
Any external link (https://...) you use MUST be a URL from the SOURCE MATERIAL. \
End by connecting the argument to the way ARIS approaches the problem.
  "card_summary": a 1-2 sentence teaser for the article card, plain text, \
<= 200 characters.
  "sources": an array of {"title": "...", "url": "..."} objects, one for EVERY \
source you cited inline. Each "url" MUST appear verbatim in the SOURCE MATERIAL. \
Include only sources you actually cited; if you made no specific sourced claims, \
return an empty array [].
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

    base_message = (
        f"Today is {today.strftime('%A, %B %-d, %Y')}.\n\n"
        f"RECENT POST TITLES (do not repeat these angles):\n{recent}\n\n"
        f"SOURCE MATERIAL:\n{sources}\n\n"
        "Write one new ARIS Insights post as the JSON object specified."
    )

    required = {"kicker", "title", "slug", "description", "lede",
                "body_html", "card_summary", "sources"}

    # Generate, then enforce sourcing. If a citation isn't traceable to the
    # gathered material, feed the exact problem back and let the model repair it
    # rather than discarding a good post. Still fails closed after MAX_TRIES, so
    # nothing unsourced can ever ship.
    feedback = ""
    last_error: Exception | None = None
    for attempt in range(1, MAX_TRIES + 1):
        with client.messages.stream(
            model=config.WRITER_MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": base_message + feedback}],
        ) as stream:
            message = stream.get_final_message()

        text = "".join(b.text for b in message.content if b.type == "text")
        try:
            article = _coerce_json(text)
            missing = required - article.keys()
            if missing:
                raise ValueError(f"Model output missing keys: {sorted(missing)}")
            # Defense-in-depth: never let a stray script tag through.
            article["body_html"] = re.sub(
                r"<script.*?</script>", "", article["body_html"], flags=re.S | re.I
            )
            _enforce_sourcing(article, raw_source_text)
        except ValueError as e:
            last_error = e
            print(f"Attempt {attempt}/{MAX_TRIES} rejected: {e}")
            feedback = (
                f"\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED: {e}\n"
                "Rewrite the entire post and return the full JSON again. Use ONLY "
                "URLs that appear verbatim in the SOURCE MATERIAL above — for every "
                "inline <a href> citation AND every entry in the sources array. If a "
                "claim depended on a URL that is not in the SOURCE MATERIAL, either "
                "re-source it to one that is, or remove that claim entirely. Do not "
                "invent, guess, or lightly edit URLs."
            )
            continue

        n = len(article["sources"])
        print(f"Write complete on attempt {attempt}: \"{article['title']}\" "
              f"({len(article['body_html'].split())} words, {n} source(s) cited).")
        return article

    # Exhausted retries — fail closed (an unsourced post must never ship).
    raise ValueError(
        f"Could not produce a fully-sourced post after {MAX_TRIES} attempts. "
        f"Last error: {last_error}"
    )


def _norm_url(u: str) -> str:
    """Normalize a URL for set membership: drop scheme, fragment, trailing slash."""
    u = (u or "").strip().strip("<>\"'").split("#")[0]
    u = re.sub(r"^https?://", "", u)
    return u.rstrip("/").lower()


# Links to our own site are always allowed (internal navigation / CTAs).
_SELF_HOSTS = ("arisriskinc.com",)


def _enforce_sourcing(article: dict, raw_source_text: str) -> None:
    """Hard gate: every cited source and every external link in the body must
    correspond to a URL that actually appeared in the gathered SOURCE MATERIAL.
    Fabricated or uncited links fail the build so nothing unsourced ships."""
    gathered = {_norm_url(u) for u in re.findall(r"URL:\s*(\S+)", raw_source_text)}

    if not isinstance(article.get("sources"), list):
        raise ValueError("`sources` must be an array.")

    def _allowed(url: str) -> bool:
        n = _norm_url(url)
        if any(n == h or n.startswith(h + "/") for h in _SELF_HOSTS):
            return True
        return any(n == g or n.startswith(g) or g.startswith(n) for g in gathered)

    # 1) Every declared source must trace back to the gathered material.
    bad_sources = [s.get("url") for s in article["sources"]
                   if not isinstance(s, dict) or not _allowed(s.get("url", ""))]
    if bad_sources:
        raise ValueError(f"Uncited/fabricated source URL(s) not in SOURCE MATERIAL: {bad_sources}")

    # 2) Every external link embedded in the body must also be a gathered source.
    body_links = re.findall(r'href="(https?://[^"]+)"', article["body_html"])
    bad_links = [u for u in body_links if not _allowed(u)]
    if bad_links:
        raise ValueError(f"Body links not backed by SOURCE MATERIAL: {bad_links}")
