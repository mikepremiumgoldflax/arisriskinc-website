"""
Rendering: turn a generated article dict into site files.

- Writes `insights/<slug>.html` from the shared article template (the same
  head/nav/footer the hand-built articles use).
- Inserts a card at the top of the hub grid (`insights/index.html`) and the
  homepage grid (`index.html`), using the INSIGHTS:CARDS markers. The homepage
  grid is trimmed to the newest N cards; the hub keeps everything.

All insertion is marker- and regex-based so it's deterministic and never depends
on a particular existing card being present.
"""

import datetime
import html
import re
import unicodedata

from . import config

# Article page template. @@TOKENS@@ are substituted (str.replace, so the braces
# in the footer <style> block are left untouched).
ARTICLE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-JT9DW5SMTN"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JT9DW5SMTN');
  </script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>@@TITLE@@ — ARIS Risk Inc.</title>
  <meta name="description" content="@@DESCRIPTION@@" />
  <link rel="canonical" href="https://www.arisriskinc.com/insights/@@SLUG@@.html" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://www.arisriskinc.com/insights/@@SLUG@@.html" />
  <meta property="og:title" content="@@TITLE@@" />
  <meta property="og:description" content="@@DESCRIPTION@@" />
  <meta property="og:image" content="https://www.arisriskinc.com/assets/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/png" sizes="64x64" href="/favicon-64.png" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <meta name="theme-color" content="#0a1424" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700;800;900&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <header class="nav scrolled" id="nav">
    <div class="container">
      <a class="brand" href="/" aria-label="ARIS Risk Inc. home">
        <img class="mark" src="/assets/aris-emblem.png" alt="ARIS Risk Inc." />
        <span class="name">ARIS RISK INC.</span>
      </a>
      <nav class="nav-links" aria-label="Primary">
        <a href="/#problem">The Problem</a>
        <a href="/#difference">See the Difference</a>
        <a href="/#how">How It Works</a>
        <a href="/#proof">Proof</a>
        <a href="/insights/">Insights</a>
      </nav>
      <div class="nav-cta">
        <a class="btn btn-primary" href="mailto:partnerships@arisriskinc.com?subject=Request%20the%20Sealed%202026%20Forecast%20Brief">Get the Brief</a>
      </div>
    </div>
  </header>
  <article class="article">
    <a class="back-link" href="/insights/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>All insights</a>
    <div class="meta"><span class="post__kicker">@@KICKER@@</span><span class="post__date">@@DATE_HUMAN@@</span></div>
    <h1>@@TITLE_TEXT@@</h1>
    <p class="lede">@@LEDE@@</p>
@@BODY@@
    <div class="article-cta">
      <h3>See the standard for yourself</h3>
      <p>Get the Sealed 2026 Forecast Brief, or book a 15-minute technical walkthrough with the team that built the model.</p>
      <a class="btn btn-primary" href="mailto:partnerships@arisriskinc.com?subject=Request%20the%20Sealed%202026%20Forecast%20Brief">
        Get the Sealed 2026 Forecast Brief
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      </a>
    </div>
  </article>

  <footer class="aris-footer">
    <div class="aris-footer__inner">
      <p class="aris-footer__brand">ARIS Risk Inc.</p>
      <p class="aris-footer__tagline">Prediction, graded by reality.</p>
      <p class="aris-footer__contact"><a href="mailto:partnerships@arisriskinc.com">partnerships@arisriskinc.com</a></p>
      <p class="aris-footer__copy">&copy; 2026 ARIS Risk Inc. All Rights Reserved.</p>
    </div>
  </footer>
  <style>
    .aris-footer { border-top: 1px solid rgba(255,255,255,0.08); background: #0e1b30; padding: 2.5rem 1.5rem; }
    .aris-footer__inner { max-width: 760px; margin: 0 auto; text-align: center; }
    .aris-footer__brand { font-family: "Outfit", sans-serif; font-weight: 700; color: #fff; letter-spacing: .02em; margin-bottom:.35rem; }
    .aris-footer__tagline { font-family: "Outfit", sans-serif; font-weight: 600; color: #ff6a1a; font-size:.95rem; margin-bottom:.75rem; }
    .aris-footer__contact a { color: #ff6a1a; }
    .aris-footer__copy { margin-top:.75rem; font-size:.8rem; color:#94a3b8; }
  </style>
</body>
</html>
"""

# A card matches from its opening anchor to its closing tag. Cards contain no
# nested <a>, so a non-greedy match to the first </a> is exact.
CARD_RE = re.compile(r'        <a class="card post.*?</a>', re.S)


def slugify(value: str, max_len: int = 60) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:max_len].strip("-") or "insight"


def _esc_attr(s: str) -> str:
    return html.escape(s, quote=True)


def _esc_text(s: str) -> str:
    return html.escape(s, quote=False)


def _sources_html(article: dict) -> str:
    """Render a visible Sources list from the cited sources (empty if none)."""
    sources = article.get("sources") or []
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="{_esc_attr(s["url"])}" rel="nofollow noopener" '
        f'target="_blank">{_esc_text(s.get("title") or s["url"])}</a></li>'
        for s in sources if isinstance(s, dict) and s.get("url")
    )
    return f"<h2>Sources</h2>\n<ul>{items}</ul>" if items else ""


def render_article_html(article: dict, today: datetime.date) -> str:
    body = article["body_html"].strip()
    sources = _sources_html(article)
    if sources:
        body = f"{body}\n{sources}"
    # Indent body lines by 4 spaces to sit inside <article>.
    body = "\n".join(("    " + ln) if ln.strip() else ln for ln in body.splitlines())
    replacements = {
        "@@TITLE@@": _esc_attr(article["title"]),
        "@@TITLE_TEXT@@": _esc_text(article["title"]),
        "@@DESCRIPTION@@": _esc_attr(article["description"]),
        "@@SLUG@@": article["slug"],
        "@@KICKER@@": _esc_text(article["kicker"]),
        "@@DATE_HUMAN@@": today.strftime("%B %Y"),
        "@@LEDE@@": _esc_text(article["lede"]),
        "@@BODY@@": body,
    }
    out = ARTICLE_TEMPLATE
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def build_card(article: dict, today: datetime.date, reveal: bool) -> str:
    cls = "card post reveal" if reveal else "card post"
    arrow = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M5 12h14M13 6l6 6-6 6"/></svg>')
    return (
        f'        <a class="{cls}" href="/insights/{article["slug"]}.html">\n'
        f'          <div class="post__top">\n'
        f'            <span class="post__kicker">{_esc_text(article["kicker"])}</span>'
        f'<span class="post__date">{today.strftime("%b %Y")}</span>\n'
        f'            <h3>{_esc_text(article["title"])}</h3>\n'
        f'          </div>\n'
        f'          <p>{_esc_text(article["card_summary"])}</p>\n'
        f'          <span class="post__more">Read the analysis {arrow}</span>\n'
        f'        </a>'
    )


def _insert_card(page_html: str, card_html: str, keep: int | None) -> str:
    m = re.search(r"<!-- INSIGHTS:CARDS:START.*?-->", page_html)
    end_marker = "<!-- INSIGHTS:CARDS:END -->"
    if not m or end_marker not in page_html:
        raise ValueError("INSIGHTS:CARDS markers not found in page.")
    si = m.end()
    ei = page_html.index(end_marker)
    inner = page_html[si:ei]

    cards = [card_html] + CARD_RE.findall(inner)
    if keep is not None:
        cards = cards[:keep]
    new_inner = "\n" + "\n".join(cards) + "\n        "
    return page_html[:si] + new_inner + page_html[ei:]


def write_to_disk(article: dict, today: datetime.date | None = None) -> str:
    """Render the article and splice cards into the hub + homepage. Returns slug."""
    import os

    today = today or datetime.date.today()

    # Ensure a unique slug / filename.
    slug = slugify(article.get("slug") or article["title"])
    path = os.path.join(config.INSIGHTS_DIR, f"{slug}.html")
    n = 2
    while os.path.exists(path):
        slug = f"{slugify(article.get('slug') or article['title'])}-{n}"
        path = os.path.join(config.INSIGHTS_DIR, f"{slug}.html")
        n += 1
    article["slug"] = slug

    with open(path, "w", encoding="utf-8") as f:
        f.write(render_article_html(article, today))

    with open(config.INSIGHTS_INDEX, encoding="utf-8") as f:
        hub = f.read()
    hub = _insert_card(hub, build_card(article, today, reveal=False), keep=None)
    with open(config.INSIGHTS_INDEX, "w", encoding="utf-8") as f:
        f.write(hub)

    with open(config.HOMEPAGE, encoding="utf-8") as f:
        home = f.read()
    home = _insert_card(home, build_card(article, today, reveal=True),
                        keep=config.HOMEPAGE_MAX_CARDS)
    with open(config.HOMEPAGE, "w", encoding="utf-8") as f:
        f.write(home)

    print(f"Rendered insights/{slug}.html and updated hub + homepage.")
    return slug
