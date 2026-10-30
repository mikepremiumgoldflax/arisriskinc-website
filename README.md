# ARIS Risk Inc. — Website

Marketing site for ARIS Risk Inc. — physics-based wildfire risk, building by building.

Live: **https://www.arisriskinc.com** (GitHub Pages, custom domain via `CNAME`).

## What this is

A hand-built, dependency-free **static site**. No framework, no build step — the files in
this repo *are* the site. Open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

## Structure

| File | Purpose |
|------|---------|
| `index.html` | Home page: model, proof, engine, Canada, team, insights, contact |
| `about/`, `contact/`, `privacy/` | Lean interior pages, linked from the footer |
| `insights/` | Notes on the model. Published when there is something to add — not on a weekly promise |
| `styles.css` | Design system + every component style (CSS variables at the top) |
| `app.js` | Sticky nav and mobile menu. Parcel-map code runs only if those elements are in the page. |
| `assets/aris-emblem.svg` | Primary logo mark (house-shield + flame) |
| `favicon.svg`, `favicon-64.png`, `apple-touch-icon.png` | Favicons |
| `assets/og-image.png` | Social share card (1200×630) |
| `assets/hero-fire.jpg` | Hero background (wildfire, on-brand) |
| `assets/avatar-mike.jpg`, `assets/avatar-jared.jpg` | Founder photos |
| Curtis team card | Headshot slot reads “Coming soon” until a photo exists |

## Brand

- **Type:** Outfit (headings, 800–900) + Inter (body) — self-hosted in `assets/fonts/`.
- **Color tokens:** defined as CSS variables in `:root` at the top of `styles.css`
  (navy `--navy-1` `#0a1424`, fire `--fire-1` `#ff6a1a` → amber `--fire-3` `#ffb43a`).
- **Logo:** `assets/aris-emblem.svg` — edit once, used in nav, hero, footer, and favicons.

## TODO before launch (needs real assets)

The original Manus build referenced media that was never committed to the repo, so these are
on-brand placeholders. Drop in the real files (keep the same filename, or update the `src`):

- **Curtis Theoret headshot** → the team card shows a visible “Coming soon” label in the photo slot.
  Replace that label with a real photo when Curtis sends one. Do not invent a photo.
  Mike and Jared use `assets/avatar-mike.jpg` and `assets/avatar-jared.jpg`.
- **Hero briefing video** → not wired on the current home page. Add the control
  back in `index.html` before dropping `assets/aris-briefing.mp4`.

## Conversion layer (added)

The homepage is built to convert, not just educate:

- **Proof** (`#proof`) — predictions sealed before the season and graded in the
  open. The public line is “Every prediction we publish is sealed in advance
  and checkable by anyone.” Do not restore “bit-for-bit,” “audited for data
  leakage,” “blind-tested,” a platform-deal line, a price, or a vendor comparison.
- **Contact** — the CTA is *Talk to us about a pilot.* A plain
  `partnerships@arisriskinc.com` link sits beside it. Do not offer a
  sealed-forecast brief or a parcel count. Tracked as a GA4 `generate_lead` event.
- **Insights hub** (`/insights/`) — add a note by copying a file in `insights/`,
  then add a card inside the `INSIGHTS:CARDS` markers in `insights/index.html`
  and the homepage `#insights` grid. Do not promise a weekly cadence.

## Deploy

GitHub Pages serves the repo root. Commit to the deploy branch and Pages publishes it.
`CNAME` and `.nojekyll` must stay at the root.
