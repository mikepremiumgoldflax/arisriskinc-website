"""
Pepper's tools — the things Claude can actually *do*.

Each tool has (1) a JSON schema in ``TOOL_SCHEMAS`` that is sent to Claude and
(2) a Python implementation in ``dispatch``. Implementations return a short
human-readable string that is fed back to the model as the tool result.

Tools intentionally fail soft: if a key is missing or a call errors, they return
a clear message rather than raising, so the agent can explain the problem to the
owner instead of crashing the bot.
"""

import datetime
import smtplib
import threading
import traceback
from email.message import EmailMessage
from email.utils import formataddr

import requests

from . import config, scripture, storage

# ---------------------------------------------------------------------------
# Tool schemas advertised to Claude
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "web_search",
        "description": (
            "Search the live web for current information, news, facts, prices, or "
            "anything you don't already know. Returns the top results with snippets. "
            "Use this whenever a question depends on recent or factual information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "send_email",
        "description": (
            "Send an email on the owner's behalf from the ARIS account. Use only when "
            "the owner clearly wants an email sent. Confirm the recipient, subject, and "
            "body with the owner first if any of them are ambiguous."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Plain-text email body."},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "add_reminder",
        "description": (
            "Schedule a reminder. Pepper will message the owner at the given time. "
            "Provide the time as a local ISO-8601 timestamp 'YYYY-MM-DDTHH:MM'. "
            "Use the current local time provided in the system context to resolve "
            "relative phrases like 'in 2 hours' or 'tomorrow at 9am'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to be reminded about."},
                "due": {"type": "string", "description": "Local ISO-8601 time, e.g. 2026-06-26T09:00."},
            },
            "required": ["text", "due"],
        },
    },
    {
        "name": "list_reminders",
        "description": "List the owner's upcoming (not-yet-fired) reminders.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancel_reminder",
        "description": "Cancel a reminder by its id (ids are shown by list_reminders).",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "Reminder id."}},
            "required": ["id"],
        },
    },
    {
        "name": "add_task",
        "description": "Add a to-do item to the owner's task list.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The task."}},
            "required": ["text"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List the owner's open (not-done) tasks.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "complete_task",
        "description": "Mark a task done by its id (ids are shown by list_tasks).",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer", "description": "Task id."}},
            "required": ["id"],
        },
    },
    {
        "name": "run_daily_briefing",
        "description": (
            "Kick off the ARIS Daily Intelligence Briefing pipeline now (gather news, "
            "write the script, render the MP3, deliver it). It runs in the background "
            "and takes a few minutes; tell the owner it's started."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_scripture",
        "description": "Return a Bible verse (the verse of the day, or a fresh encouraging one).",
        "input_schema": {"type": "object", "properties": {}},
    },
]


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------
def _web_search(args: dict) -> str:
    query = (args.get("query") or "").strip()
    if not query:
        return "No query provided."
    if not config.TAVILY_API_KEY:
        return ("Web search is unavailable — TAVILY_API_KEY is not configured. "
                "Tell the owner to add it to enable research.")
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - report, don't crash
        return f"Web search failed: {exc}"

    lines = []
    if data.get("answer"):
        lines.append(f"Summary: {data['answer']}")
    for i, r in enumerate(data.get("results", [])[:5], 1):
        title = r.get("title", "(untitled)")
        url = r.get("url", "")
        snippet = (r.get("content") or "").strip().replace("\n", " ")
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        lines.append(f"{i}. {title}\n   {url}\n   {snippet}")
    return "\n".join(lines) if lines else "No results found."


def _send_email(args: dict) -> str:
    to = (args.get("to") or "").strip()
    subject = (args.get("subject") or "").strip()
    body = args.get("body") or ""
    if not to or not subject:
        return "Cannot send — recipient and subject are both required."
    if not config.GMAIL_USERNAME or not config.GMAIL_APP_PASSWORD:
        return ("Email is unavailable — GMAIL_USERNAME / GMAIL_APP_PASSWORD are not "
                "configured. Tell the owner to add a Gmail app password to enable sending.")
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr((config.EMAIL_FROM_NAME, config.GMAIL_USERNAME))
        msg["To"] = to
        msg.set_content(body)
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.login(config.GMAIL_USERNAME, config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        return f"Failed to send email: {exc}"
    return f"Email sent to {to} with subject “{subject}”."


def _add_reminder(chat_id: str, args: dict) -> str:
    text = (args.get("text") or "").strip()
    due = (args.get("due") or "").strip()
    if not text or not due:
        return "Need both a reminder text and a due time."
    # Validate / normalize the timestamp.
    try:
        dt = datetime.datetime.fromisoformat(due)
    except ValueError:
        return f"Couldn't parse the time '{due}'. Use ISO format YYYY-MM-DDTHH:MM."
    due_iso = dt.strftime("%Y-%m-%dT%H:%M")
    rid = storage.add_reminder(chat_id, text, due_iso)
    pretty = dt.strftime("%A, %B %-d at %-I:%M %p")
    return f"Reminder #{rid} set for {pretty}: {text}"


def _list_reminders(chat_id: str, _args: dict) -> str:
    rems = storage.list_reminders(chat_id)
    if not rems:
        return "No upcoming reminders."
    lines = []
    for r in rems:
        try:
            pretty = datetime.datetime.fromisoformat(r["due"]).strftime("%a %b %-d, %-I:%M %p")
        except ValueError:
            pretty = r["due"]
        lines.append(f"#{r['id']} — {pretty}: {r['text']}")
    return "\n".join(lines)


def _cancel_reminder(chat_id: str, args: dict) -> str:
    rid = args.get("id")
    if storage.cancel_reminder(chat_id, int(rid)):
        return f"Reminder #{rid} cancelled."
    return f"No reminder #{rid} found."


def _add_task(chat_id: str, args: dict) -> str:
    text = (args.get("text") or "").strip()
    if not text:
        return "Need the task text."
    tid = storage.add_task(chat_id, text)
    return f"Added task #{tid}: {text}"


def _list_tasks(chat_id: str, _args: dict) -> str:
    tasks = storage.list_tasks(chat_id)
    if not tasks:
        return "Your task list is clear. ✅"
    return "\n".join(f"#{t['id']} — {t['text']}" for t in tasks)


def _complete_task(chat_id: str, args: dict) -> str:
    tid = args.get("id")
    if storage.complete_task(chat_id, int(tid)):
        return f"Task #{tid} marked done. ✅"
    return f"No task #{tid} found."


# The briefing runs in a background thread so a long pipeline never blocks the bot.
_briefing_lock = threading.Lock()
_briefing_running = False


def _run_briefing_background(notify):
    global _briefing_running
    try:
        from briefing import run as briefing_run  # lazy: avoid importing heavy deps at startup
        rc = briefing_run.main()
        if notify:
            notify("✅ Daily briefing finished and was delivered." if rc == 0
                   else "⚠️ The briefing pipeline exited with an error — check the logs.")
    except Exception:  # noqa: BLE001
        if notify:
            notify("⚠️ The briefing pipeline crashed:\n" + traceback.format_exc()[-1500:])
    finally:
        with _briefing_lock:
            _briefing_running = False


def _run_daily_briefing(_args: dict, notify=None) -> str:
    global _briefing_running
    with _briefing_lock:
        if _briefing_running:
            return "A briefing run is already in progress — I'll let you know when it's done."
        _briefing_running = True
    threading.Thread(target=_run_briefing_background, args=(notify,), daemon=True).start()
    return ("Started the ARIS Daily Intelligence Briefing — it gathers news, writes the "
            "script, renders the audio, and delivers it. This takes a few minutes; I'll "
            "message you when it's ready.")


def _get_scripture(_args: dict) -> str:
    ref, text = scripture.random_verse()
    return f"{ref} — “{text}”"


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def dispatch(name: str, args: dict, chat_id: str, notify=None) -> str:
    """Execute a tool by name and return a string result for the model.

    ``notify`` is an optional callable(str) used by long-running tools to push a
    follow-up Telegram message to the owner when they finish.
    """
    try:
        if name == "web_search":
            return _web_search(args)
        if name == "send_email":
            return _send_email(args)
        if name == "add_reminder":
            return _add_reminder(chat_id, args)
        if name == "list_reminders":
            return _list_reminders(chat_id, args)
        if name == "cancel_reminder":
            return _cancel_reminder(chat_id, args)
        if name == "add_task":
            return _add_task(chat_id, args)
        if name == "list_tasks":
            return _list_tasks(chat_id, args)
        if name == "complete_task":
            return _complete_task(chat_id, args)
        if name == "run_daily_briefing":
            return _run_daily_briefing(args, notify=notify)
        if name == "get_scripture":
            return _get_scripture(args)
        return f"Unknown tool: {name}"
    except Exception as exc:  # noqa: BLE001 - never let a tool crash the loop
        return f"Tool '{name}' errored: {exc}"
