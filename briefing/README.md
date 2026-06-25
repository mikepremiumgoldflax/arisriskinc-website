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
| Deliver | Emails the script + MP3 | Gmail SMTP |

The targeted queries cover: general AI news, InsurTech & competitors (ZestyAI, CoreLogic,
Cape Analytics), and California wildfire risk & regulation (FAIR Plan, CDI, State Farm).

## Running it every morning (GitHub Actions)

The workflow `.github/workflows/daily-briefing.yml` runs the pipeline daily on a cron
schedule (`0 13 * * *` UTC = 6 AM Pacific) and can also be triggered manually from the
**Actions** tab ("Run workflow").

### One-time setup — add these repository secrets

**Settings → Secrets and variables → Actions → New repository secret:**

| Secret | Where to get it |
|--------|-----------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |
| `TAVILY_API_KEY` | https://tavily.com (free tier) — recommended for fresh sources |
| `GMAIL_USERNAME` | the Gmail address that sends the briefing |
| `GMAIL_APP_PASSWORD` | https://myaccount.google.com/apppasswords (requires 2FA) |

Optionally set a repository **variable** `ARIS_EMAIL_TO` to change the recipient
(defaults to `admin@arisriskinc.com`).

> Without `TAVILY_API_KEY` the pipeline falls back to scraping a fixed list of source
> URLs, which is less fresh. The other three secrets are required for a full run.

## Running it locally

```bash
pip install -r briefing/requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
export TAVILY_API_KEY=tvly-...
export GMAIL_USERNAME=you@gmail.com
export GMAIL_APP_PASSWORD=...          # optional locally; omit to skip email

python -m briefing.run
```

Outputs are written to `briefing/output/` (`narration_script_<date>.txt` and
`ARIS_Briefing_<date>.mp3`) and emailed if Gmail credentials are present.

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
