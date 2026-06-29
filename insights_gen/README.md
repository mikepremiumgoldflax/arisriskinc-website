# ARIS Insights generator — weekly content velocity

Drafts one publishable **Insights** post a week and, by default, opens a pull
request for review. It's the content-velocity sibling of the `briefing/`
pipeline: same secrets, same Claude model, same env-driven design — but instead
of an audio briefing for the team, it produces a website article.

## What it does

1. **Gather** — runs ARIS-relevant search queries (legacy-model failure, the
   California regulatory shift, parcel-level science, the wildfire-insurance
   market) via Tavily and scrapes the results. Reuses `briefing.phase1_gather`.
2. **Write** — Claude (`claude-opus-4-8`) writes one article in the ARIS voice
   and returns it as strict JSON. The prompt has hard guardrails: no fabricated
   stats, no claimed customers/partners, never names "Verisk", and only asserts
   ARIS capabilities already established on the site.
   - **Mandatory sourcing.** Every specific claim (stat, date, named event,
     quotation) must carry an inline `<a href>` citation to a URL from the
     gathered material, and the post returns a `sources` array. `write.py` then
     **hard-fails the build** if any cited source — or any external link in the
     body — isn't a URL that actually appeared in the gathered sources, so
     nothing unsourced can ship. With no sources gathered, the post stays
     qualitative (no specifics) and lists no sources.
3. **Render** — writes `insights/<slug>.html` from the shared template and
   splices a card into the hub (`insights/index.html`, keeps all) and the
   homepage (`index.html`, keeps the newest 3) via the `INSIGHTS:CARDS` markers.
4. **Record** — appends the post to `history.json` so future runs pick a fresh
   angle and slugs stay unique.

The GitHub Actions workflow (`.github/workflows/weekly-insight.yml`) then opens a
PR with the diff. **Nothing goes live without a human merge** — a deliberate
choice, since this site is read by carriers, reinsurers, and analytics platforms.

## Run it locally

```bash
pip install -r insights_gen/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export TAVILY_API_KEY=tvly-...        # optional but recommended for fresh sources
python -m insights_gen.run
```

This writes the new files into your working tree. Review with `git diff`, then
commit or discard. Without `ANTHROPIC_API_KEY` the run exits cleanly (code 3)
and changes nothing.

## Schedule & secrets (GitHub Actions)

The workflow runs `0 14 * * 1` (Mon 7 AM Pacific) and can be triggered manually
from the **Actions** tab. It reuses the briefing pipeline's secrets —
`ANTHROPIC_API_KEY` (required) and `TAVILY_API_KEY` (recommended). No new
secrets needed.

> One repo setting is required for the PR step: **Settings → Actions → General →
> Workflow permissions → enable "Allow GitHub Actions to create and approve pull
> requests."**

### PR (default) vs. publish

- **PR mode** (default for scheduled runs, and the default dispatch choice):
  opens a pull request into `gh-pages` for review.
- **Publish mode**: from the **Actions → Run workflow** dialog, choose
  `mode = publish` to commit straight to the live site. Use sparingly.

## Configuration knobs (env vars)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ARIS_INSIGHTS_MODEL` | `claude-opus-4-8` | Claude model that writes the post |
| `ARIS_HOMEPAGE_MAX_CARDS` | `3` | Cards kept in the homepage Insights grid |
| `ARIS_RECENT_TITLES_WINDOW` | `12` | Recent titles fed back to avoid repeats |
| `ARIS_RESULTS_PER_QUERY` | `4` | Search results pulled per query |
| `ARIS_MAX_ARTICLES` | `10` | Cap on source articles fed to Claude |

## Adding a post by hand

Copy any file in `insights/`, edit the copy, then add a matching card inside the
`<!-- INSIGHTS:CARDS:START -->`…`<!-- INSIGHTS:CARDS:END -->` markers in both
`insights/index.html` and the homepage `#insights` grid.
