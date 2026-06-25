# Pepper Botts — ARIS Agentic AI Executive Assistant

Pepper Botts ([@Pepper_BottsBot](https://t.me/Pepper_BottsBot)) is a conversational,
**agentic** executive assistant you talk to in Telegram. It's powered by Claude with
real tool-use, so it doesn't just chat — it *acts*.

## What Pepper can do

| Capability | How you use it |
|------------|----------------|
| 🔎 **Research** | "What's the latest on the California FAIR Plan?" — live web search (Tavily) |
| ✉️ **Email** | "Email jared@… about the Tuesday demo" — drafts, confirms, then sends via Gmail |
| ⏰ **Reminders** | "Remind me to call the broker at 3pm" — pushes a Telegram nudge at the time |
| ✅ **Tasks** | "Add task: review the underwriting memo" / `/tasks` — a persistent to-do list |
| 📰 **Daily briefing** | "Run my briefing now" or `/briefing` — kicks off the existing pipeline |
| 📖 **Daily scripture** | A verse every morning at **8:00 AM**, or `/verse` any time |

Pepper holds conversation context, resolves relative times ("tomorrow at 9"),
and only talks to **you** once you lock it down with your chat id.

## Architecture

A single long-running Python process — no servers, no webhooks, no database.

```
pepper/
  run.py        # entrypoint:  python -m pepper.run
  bot.py        # Telegram long-poll loop + scheduler thread (scripture + reminders)
  agent.py      # the Claude tool-use loop
  tools.py      # the tools Claude can call (search, email, reminders, tasks, briefing)
  scripture.py  # curated daily verses (public-domain KJV)
  storage.py    # JSON state (reminders, tasks, history, offset) — survives restarts
  config.py     # all settings, driven by environment / .env
  assets/       # Pepper's avatar
```

State lives in `pepper/state/state.json` (git-ignored). Secrets live in `.env`
(git-ignored) — **nothing sensitive is ever committed.**

## Setup (5 minutes)

### 1. Install

```bash
pip install -r pepper/requirements.txt
# Optional — only needed for the "run briefing" tool:
pip install -r briefing/requirements.txt
```

### 2. Configure

```bash
cp pepper/.env.example pepper/.env
```

Fill in `pepper/.env`:

| Variable | Required | Where to get it |
|----------|:--------:|-----------------|
| `PEPPER_BOT_TOKEN` | ✅ | @BotFather → your Pepper Botts bot token |
| `ANTHROPIC_API_KEY` | ✅ | https://console.anthropic.com |
| `PEPPER_OWNER_CHAT_ID` | ⭐ | Your numeric chat id — see step 4 |
| `TAVILY_API_KEY` | for research | https://tavily.com (free tier) |
| `GMAIL_USERNAME` / `GMAIL_APP_PASSWORD` | for email | https://myaccount.google.com/apppasswords (needs 2FA) |
| `PEPPER_TIMEZONE` | optional | e.g. `America/New_York` (sets the 8 AM scripture clock) |

### 3. Run it

```bash
python -m pepper.run
```

Keep it running with `nohup python -m pepper.run > pepper.log 2>&1 &`, or as a
`systemd` / `pm2` service, or in a container.

### 4. Lock it to you

Message your bot once. If `PEPPER_OWNER_CHAT_ID` isn't set yet, Pepper replies with
your chat id (and `/start` always shows it). Paste that into `pepper/.env` as
`PEPPER_OWNER_CHAT_ID` and restart — now Pepper only answers you, and the 8 AM
scripture + reminders go to your chat.

### 5. Give Pepper her face (avatar)

Telegram bot profile pictures can only be set through @BotFather (not the API):

> @BotFather → `/setuserpic` → choose **Pepper Botts** → upload
> `pepper/assets/pepper-avatar-square.png`

## Commands

`/help` · `/verse` · `/reminders` · `/tasks` · `/briefing` · `/reset` (clears history) · `/start`

## Security notes

- The bot token and all keys are read from the environment / `.env`; none are in git.
- With `PEPPER_OWNER_CHAT_ID` set, Pepper ignores everyone else.
- `send_email` is the one outward-facing action — Pepper is instructed to confirm
  recipient/subject/body before sending anything non-trivial.
