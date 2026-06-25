"""
Central configuration for The ARIS Daily Intelligence Briefing pipeline.

Everything is driven by environment variables so the same code runs locally
and inside GitHub Actions. The only hard requirements are the Anthropic key
(script generation) and the Gmail credentials (delivery). A Tavily key is
strongly recommended for fresh sources; without it the pipeline falls back to
a fixed list of source URLs.
"""

import os

# --- Phase 1: Intelligence gathering -----------------------------------------
# Tavily is a search API designed for LLM pipelines (https://tavily.com).
# Get a free key and set TAVILY_API_KEY as a GitHub Actions secret.
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# How many search results to pull per query, and how many to deep-scrape.
RESULTS_PER_QUERY = int(os.environ.get("ARIS_RESULTS_PER_QUERY", "4"))
MAX_ARTICLES = int(os.environ.get("ARIS_MAX_ARTICLES", "12"))

# Fallback sources used only when no TAVILY_API_KEY is configured.
FALLBACK_SOURCE_URLS = [
    "https://www.buildfastwithai.com/blogs",
    "https://www.insurancejournal.com/news/national/",
    "https://www.insurtechinsights.com/news/",
    "https://www.insurance.ca.gov/0400-news/0100-press-releases/",
]

# --- Phase 2: Script generation ----------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Claude writes the briefing script. claude-opus-4-8 is the current frontier model.
SCRIPT_MODEL = os.environ.get("ARIS_SCRIPT_MODEL", "claude-opus-4-8")

# --- Phase 3: Audio synthesis ------------------------------------------------
# edge-tts neural voice — the original ARIS default (professional male American).
TTS_VOICE = os.environ.get("ARIS_TTS_VOICE", "en-US-GuyNeural")

# --- Delivery: email ----------------------------------------------------------
# Use a Gmail account + App Password (https://myaccount.google.com/apppasswords).
GMAIL_USERNAME = os.environ.get("GMAIL_USERNAME", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
EMAIL_TO = os.environ.get("ARIS_EMAIL_TO", "admin@arisriskinc.com")
SMTP_HOST = os.environ.get("ARIS_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("ARIS_SMTP_PORT", "465"))

# --- Output -------------------------------------------------------------------
OUTPUT_DIR = os.environ.get("ARIS_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "output"))
