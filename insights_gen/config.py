"""
Configuration for the ARIS Insights generator.

This is the content-velocity sibling of the `briefing/` pipeline: instead of an
audio briefing for the team, it drafts a publishable Insights article for the
website's content hub and (by default) opens a pull request for human review.

Everything is env-driven so the same code runs locally and in GitHub Actions.
It reuses the same secrets as the briefing pipeline — ANTHROPIC_API_KEY for
writing and (optionally) TAVILY_API_KEY for fresh source material.
"""

import os

# Repo paths (this file lives in <repo>/insights_gen/).
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
INSIGHTS_DIR = os.path.join(REPO_ROOT, "insights")
INSIGHTS_INDEX = os.path.join(INSIGHTS_DIR, "index.html")
HOMEPAGE = os.path.join(REPO_ROOT, "index.html")
HISTORY_FILE = os.path.join(PACKAGE_DIR, "history.json")

# How many cards the homepage grid keeps (newest first). The hub keeps all.
HOMEPAGE_MAX_CARDS = int(os.environ.get("ARIS_HOMEPAGE_MAX_CARDS", "3"))

# --- Source gathering (shared with the briefing pipeline) --------------------
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
RESULTS_PER_QUERY = int(os.environ.get("ARIS_RESULTS_PER_QUERY", "4"))
MAX_ARTICLES = int(os.environ.get("ARIS_MAX_ARTICLES", "10"))

# --- Article generation ------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# claude-opus-4-8 is the current frontier model (same default as the briefing).
WRITER_MODEL = os.environ.get("ARIS_INSIGHTS_MODEL", "claude-opus-4-8")

# Number of recent titles fed back to the writer so it picks a fresh angle.
RECENT_TITLES_WINDOW = int(os.environ.get("ARIS_RECENT_TITLES_WINDOW", "12"))
