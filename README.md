# ARIS Risk Inc.

Monorepo for ARIS Risk Inc. — parcel-level wildfire risk intelligence for P&C insurance.
It holds three independent parts: the **marketing site**, a **daily intelligence
briefing** automation, and **Pepper Botts**, the agentic AI executive assistant.

Live site: **https://www.arisriskinc.com** (GitHub Pages, custom domain via `CNAME`).

## Repository layout

```
arisriskinc-website/
│
├── Website  (static site, served by GitHub Pages from the repo root)
│   ├── index.html              # single-page marketing site
│   ├── dashboard.html          # internal dashboard
│   ├── styles.css              # design system + all component styles
│   ├── app.js                  # nav, mobile menu, scroll animations
│   ├── assets/                 # logo, hero image, founder avatars, OG card
│   ├── mike/  ·  jared/        # installable web-app business cards (PWA)
│   ├── favicon-64.png · apple-touch-icon.png
│   ├── CNAME · .nojekyll       # GitHub Pages config (must stay at root)
│
├── briefing/   📰  Daily Intelligence Briefing — automated morning audio briefing
│   └── README.md               # gather news → Claude script → MP3 → Telegram
│
├── pepper/     🤖  Pepper Botts — agentic AI executive assistant (Telegram)
│   └── README.md               # chat assistant: research, email, reminders, tasks
│
└── .github/workflows/          # CI / scheduled automation (daily-briefing.yml)
```

Each subsystem is self-contained and documented in its own `README.md`. The two
Python packages (`briefing/`, `pepper/`) are kept separate from the static site so
nothing about the automations affects what GitHub Pages serves.

> **Why the site files live at the repo root:** GitHub Pages publishes the repo
> root, and the pages link assets with absolute paths (`/styles.css`, `/assets/…`).
> Keeping them at root is what keeps the live site working — so the root stays the
> website, and all tooling lives in clearly-named subfolders.

---

## 1. Website

A hand-built, dependency-free **static site** — no framework, no build step. The
files in the repo root *are* the site.

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

**Brand:** Outfit (headings) + Inter (body); color tokens are CSS variables in
`:root` at the top of `styles.css` (navy `#0a1424`, fire `#ff6a1a` → amber `#ffb43a`).
The logo mark is `assets/aris-emblem.png`, reused in nav, hero, footer, and favicons.

**Deploy:** GitHub Pages serves the repo root; commit to the deploy branch and Pages
publishes. `CNAME` and `.nojekyll` must stay at the root.

## 2. Daily Intelligence Briefing → [`briefing/`](briefing/README.md)

A weekday-morning pipeline: it searches AI / InsurTech / wildfire news, has Claude
write a sharp executive narration script, renders it to an MP3 with a neural voice,
and delivers it to Telegram. Runs on GitHub Actions
(`.github/workflows/daily-briefing.yml`) or locally with `python -m briefing.run`.

## 3. Pepper Botts → [`pepper/`](pepper/README.md)

The agentic AI executive assistant you chat with in Telegram
([@Pepper_BottsBot](https://t.me/Pepper_BottsBot)). Powered by Claude with real
tool-use — it researches the web, drafts and sends email, sets reminders, tracks
tasks, can trigger the daily briefing on demand, and sends a Bible verse every
morning at 8 AM. Self-hosted as one long-running process: `python -m pepper.run`.

---

## Secrets & configuration

No secrets are committed. The automations read everything from environment
variables (and a git-ignored `.env` for local runs). For GitHub Actions, set them
under **Settings → Secrets and variables → Actions**. See each subsystem's README
for the exact keys it needs (`ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`,
`PEPPER_BOT_TOKEN`, `TAVILY_API_KEY`, Gmail app password, etc.).
