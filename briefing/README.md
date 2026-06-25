# The ARIS Daily Intelligence Briefing: End-to-End Pipeline

A repeated morning briefing for ARIS Risk Inc. It gathers AI / InsurTech / wildfire
news, has Claude synthesize a sharp executive narration script, renders it to an MP3
with a neural voice, and emails the result to the team every morning.

## The three phases

| Phase | What it does | Tool |
|-------|--------------|------|
| 1. Intelligence Gathering | Runs targeted search queries, then scrapes article text | Tavily search + `requests` + BeautifulSoup |
| 2. Script Generation | Synthesizes the raw text into the ARIS executive script | Claude (`claude-opus-4-8`) |
| 3. Audio Synthesis | Renders the script to MP3 | `edge-tts`, voice `en-US-GuyNeural` |
| Verify | Confirms the audio is under ~8 minutes | `ffprobe` (ffmpeg) |
| Deliver | Sends the MP3 (playable audio + phone push) and the script | Telegram bot (email is an optional fallback) |

The targeted queries cover: general AI news, InsurTech & competitors (ZestyAI, CoreLogic,
Cape Analytics), and California wildfire risk & regulation (FAIR Plan, CDI, State Farm).

## Running it every morning (GitHub Actions)

The workflow `.github/workflows/daily-briefing.yml` runs the pipeline on a weekday cron
schedule (`0 13 * * 1-5` UTC = 6 AM Pacific, Mon–Fri) and can also be triggered manually
from the **Actions** tab ("Run workflow").

### One-time setup — add these repository secrets

**Settings → Secrets and variables → Actions → New repository secret:**

| Secret | Where to get it |
|--------|-----------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |
| `TAVILY_API_KEY` | https://tavily.com (free tier) — recommended for fresh sources |
| `TELEGRAM_BOT_TOKEN` | message **@BotFather** on Telegram → `/newbot` → copy the token |
| `TELEGRAM_CHAT_ID` | message **@userinfobot** for your numeric id, then DM your new bot once so it can message you |
| `GMAIL_USERNAME` | *(optional)* Gmail address — only if you want email as a fallback |
| `GMAIL_APP_PASSWORD` | *(optional)* https://myaccount.google.com/apppasswords (requires 2FA) |

Delivery is **Telegram-first**: if `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are set, the
briefing goes there. Email is used only as a fallback when Telegram isn't configured.

> Without `TAVILY_API_KEY` the pipeline falls back to scraping a fixed list of source
> URLs, which is less fresh. `ANTHROPIC_API_KEY` and the Telegram secrets are required
> for a full, delivered run.

## Running it locally

```bash
pip install -r briefing/requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
export TAVILY_API_KEY=tvly-...
export TELEGRAM_BOT_TOKEN=123456:ABC...
export TELEGRAM_CHAT_ID=123456789

python -m briefing.run
```

Outputs are written to `briefing/output/` (`narration_script_<date>.txt` and
`ARIS_Briefing_<date>.mp3`) and sent to Telegram if the bot credentials are present.

## Configuration knobs (all optional env vars)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ARIS_SCRIPT_MODEL` | `claude-opus-4-8` | Claude model that writes the script |
| `ARIS_TTS_VOICE` | `en-US-GuyNeural` | edge-tts neural voice |
| `ARIS_MAX_ARTICLES` | `12` | Cap on articles fed to Claude |
| `ARIS_RESULTS_PER_QUERY` | `4` | Search results pulled per query |
| `ARIS_EMAIL_TO` | `admin@arisriskinc.com` | Recipient |

## Layout

```
briefing/
  run.py            # orchestrator (python -m briefing.run)
  config.py         # env-driven configuration
  phase1_gather.py  # search + scrape
  phase2_script.py  # Claude script generation
  phase3_audio.py   # edge-tts MP3 + ffprobe duration check
  deliver.py        # Gmail SMTP delivery
  requirements.txt
```
