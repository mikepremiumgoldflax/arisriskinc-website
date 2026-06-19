# ARIS Risk Inc. — Website

Marketing site for ARIS Risk Inc. — parcel-level wildfire risk intelligence for P&C insurance.

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
| `index.html` | All page markup and copy (single-page site) |
| `styles.css` | Design system + every component style (CSS variables at the top) |
| `app.js` | Sticky nav, mobile menu, scroll-reveal animations |
| `assets/aris-emblem.svg` | Primary logo mark (house-shield + flame) |
| `favicon.svg`, `favicon-64.png`, `apple-touch-icon.png` | Favicons |
| `assets/og-image.png` | Social share card (1200×630) |
| `assets/hero-fire.jpg` | Hero background (wildfire, on-brand) |
| `assets/avatar-mike.jpg`, `assets/avatar-jared.jpg` | **Placeholder** founder avatars |

## Brand

- **Type:** Outfit (headings, 800–900) + Inter (body) — loaded from Google Fonts.
- **Color tokens:** defined as CSS variables in `:root` at the top of `styles.css`
  (navy `--navy-1` `#0a1424`, fire `--fire-1` `#ff6a1a` → amber `--fire-3` `#ffb43a`).
- **Logo:** `assets/aris-emblem.svg` — edit once, used in nav, hero, footer, and favicons.

## TODO before launch (needs real assets)

The original Manus build referenced media that was never committed to the repo, so these are
on-brand placeholders. Drop in the real files (keep the same filename, or update the `src`):

- **Founder headshots** → replace `assets/avatar-mike.jpg` and `assets/avatar-jared.jpg`
  (square, ≥240×240). Currently monogram tiles (MM / JF).
- **Hero video (optional)** → if you want motion back, add the `.mp4` and swap the
  `.hero-bg` element/CSS for a `<video>`.

## Deploy

GitHub Pages serves the repo root. Commit to the deploy branch and Pages publishes it.
`CNAME` and `.nojekyll` must stay at the root.
