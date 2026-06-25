"""
Central configuration for Pepper Botts — the ARIS agentic Executive Assistant.

Everything is driven by environment variables so the same code runs on a laptop,
a VPS, or in a container. A local ``.env`` file (next to this package, in the repo
root) is loaded automatically if present — copy ``pepper/.env.example`` to ``.env``
and fill it in.

Hard requirements to start the bot:
  * PEPPER_BOT_TOKEN     — the Telegram bot token (from @BotFather)
  * ANTHROPIC_API_KEY    — Claude powers the agent (https://console.anthropic.com)

Strongly recommended:
  * PEPPER_OWNER_CHAT_ID — your numeric Telegram chat id. When set, Pepper ONLY
                           talks to you (and uses it for the 8 AM scripture and
                           reminder pushes). If you don't know it yet, just start
                           the bot and message it — it replies with your chat id.
"""

import os

# --- Load a local .env if one exists (optional convenience) ------------------
try:  # python-dotenv is in requirements but the bot still runs without it.
    from dotenv import load_dotenv

    _here = os.path.dirname(os.path.abspath(__file__))
    for _candidate in (os.path.join(_here, ".env"),
                       os.path.join(os.path.dirname(_here), ".env")):
        if os.path.exists(_candidate):
            load_dotenv(_candidate)
            break
except Exception:  # pragma: no cover - dotenv is best-effort only
    pass


def _clean(value: str) -> str:
    """Strip whitespace/quotes that sneak in when pasting secrets."""
    return (value or "").strip().strip('"').strip("'")


# --- Telegram ----------------------------------------------------------------
# Pepper uses its own bot token. We fall back to TELEGRAM_BOT_TOKEN so the bot
# can share credentials with the daily-briefing pipeline if you prefer one bot.
BOT_TOKEN = _clean(os.environ.get("PEPPER_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", ""))

# Your numeric chat id. When set, the bot only answers this chat and uses it as
# the destination for scheduled pushes (scripture + reminders).
OWNER_CHAT_ID = _clean(os.environ.get("PEPPER_OWNER_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", ""))

# Optional extra chat ids allowed to talk to Pepper (comma-separated).
_extra = _clean(os.environ.get("PEPPER_ALLOWED_CHAT_IDS", ""))
ALLOWED_CHAT_IDS = {c.strip() for c in _extra.split(",") if c.strip()}
if OWNER_CHAT_ID:
    ALLOWED_CHAT_IDS.add(OWNER_CHAT_ID)

# --- Claude (the agent brain) ------------------------------------------------
ANTHROPIC_API_KEY = _clean(os.environ.get("ANTHROPIC_API_KEY", ""))
# claude-opus-4-8 is the current frontier model. Set PEPPER_MODEL=claude-sonnet-4-6
# for faster / cheaper replies if you prefer.
MODEL = _clean(os.environ.get("PEPPER_MODEL", "claude-opus-4-8"))
MAX_TOKENS = int(os.environ.get("PEPPER_MAX_TOKENS", "2048"))
# How many past turns (user + assistant messages) to keep in context per chat.
HISTORY_TURNS = int(os.environ.get("PEPPER_HISTORY_TURNS", "20"))

# --- Tool: web research (Tavily) ---------------------------------------------
TAVILY_API_KEY = _clean(os.environ.get("TAVILY_API_KEY", ""))

# --- Tool: send email (Gmail SMTP, app password) -----------------------------
GMAIL_USERNAME = _clean(os.environ.get("GMAIL_USERNAME", ""))
GMAIL_APP_PASSWORD = _clean(os.environ.get("GMAIL_APP_PASSWORD", ""))
SMTP_HOST = _clean(os.environ.get("ARIS_SMTP_HOST", "smtp.gmail.com"))
SMTP_PORT = int(os.environ.get("ARIS_SMTP_PORT", "465"))
# Default "from" name on outgoing mail.
EMAIL_FROM_NAME = _clean(os.environ.get("PEPPER_EMAIL_FROM_NAME", "ARIS Risk Inc."))

# --- Scheduling --------------------------------------------------------------
# IANA timezone name for the 8 AM scripture and reminders (e.g. America/New_York,
# America/Chicago, America/Los_Angeles).
TIMEZONE = _clean(os.environ.get("PEPPER_TIMEZONE", "America/New_York"))
# Daily scripture send time, 24h "HH:MM". Empty string disables the daily verse.
SCRIPTURE_TIME = _clean(os.environ.get("PEPPER_SCRIPTURE_TIME", "08:00"))

# --- Owner / identity --------------------------------------------------------
OWNER_EMAIL = _clean(os.environ.get("PEPPER_OWNER_EMAIL", "admin@arisriskinc.com"))
OWNER_NAME = _clean(os.environ.get("PEPPER_OWNER_NAME", "")) or "the ARIS team"

# --- State persistence -------------------------------------------------------
STATE_DIR = _clean(os.environ.get("PEPPER_STATE_DIR", "")) or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state"
)


def telegram_api(method: str) -> str:
    """Build a Telegram Bot API URL for the configured token."""
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def missing_required() -> list[str]:
    """Return the names of required settings that are not configured."""
    missing = []
    if not BOT_TOKEN:
        missing.append("PEPPER_BOT_TOKEN")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    return missing
