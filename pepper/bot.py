"""
The Pepper bot — Telegram long-polling loop + background scheduler.

* The main loop calls Telegram getUpdates (long poll), routes each message to the
  agent, and replies.
* A daemon scheduler thread sends the 8 AM daily scripture and fires due reminders.

Run with:  python -m pepper.run
"""

import datetime
import html
import threading
import time
from zoneinfo import ZoneInfo

import requests

from . import agent, config, scripture, storage

POLL_TIMEOUT = 50  # seconds for Telegram long polling
TELEGRAM_MAX = 4096  # Telegram message length cap


def _tz() -> ZoneInfo:
    try:
        return ZoneInfo(config.TIMEZONE)
    except Exception:  # noqa: BLE001 - bad tz name -> UTC
        return ZoneInfo("UTC")


def now_local() -> datetime.datetime:
    return datetime.datetime.now(_tz())


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------
def send_message(chat_id: str, text: str, markdown: bool = False) -> None:
    """Send a message, chunking to Telegram's length limit."""
    if not text:
        return
    for chunk in _chunks(text, TELEGRAM_MAX):
        data = {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}
        if markdown:
            data["parse_mode"] = "Markdown"
        try:
            requests.post(config.telegram_api("sendMessage"), data=data, timeout=30)
        except Exception as exc:  # noqa: BLE001
            print(f"[pepper] sendMessage failed: {exc}")


def _chunks(text: str, size: int):
    """Split on paragraph/line boundaries where possible, else hard-split."""
    while len(text) > size:
        cut = text.rfind("\n", 0, size)
        if cut <= 0:
            cut = size
        yield text[:cut]
        text = text[cut:].lstrip("\n")
    if text:
        yield text


def send_typing(chat_id: str) -> None:
    try:
        requests.post(config.telegram_api("sendChatAction"),
                      data={"chat_id": chat_id, "action": "typing"}, timeout=10)
    except Exception:  # noqa: BLE001
        pass


def get_updates(offset: int) -> list:
    try:
        resp = requests.get(
            config.telegram_api("getUpdates"),
            params={"offset": offset, "timeout": POLL_TIMEOUT},
            timeout=POLL_TIMEOUT + 15,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
    except requests.exceptions.Timeout:
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"[pepper] getUpdates failed: {exc}")
        time.sleep(3)
        return []


def is_allowed(chat_id: str) -> bool:
    """If no allowlist is configured, talk to anyone (and reveal the chat id)."""
    if not config.ALLOWED_CHAT_IDS:
        return True
    return str(chat_id) in config.ALLOWED_CHAT_IDS


# ---------------------------------------------------------------------------
# Message handling
# ---------------------------------------------------------------------------
HELP_TEXT = (
    "👋 I'm *Pepper Botts*, your ARIS executive assistant. Just talk to me naturally. "
    "I can:\n"
    "• 🔎 Research anything on the web\n"
    "• ✉️ Draft & send email for you\n"
    "• ⏰ Set reminders (\"remind me to call Jared at 3pm\")\n"
    "• ✅ Track your to-dos (\"add task: review the FAIR Plan memo\")\n"
    "• 📰 Run your daily intelligence briefing on demand\n"
    "• 📖 Send an encouraging Bible verse (and one every morning at 8)\n\n"
    "Commands: /help, /reminders, /tasks, /briefing, /verse, /reset"
)


def handle_command(chat_id: str, text: str) -> bool:
    """Handle slash commands. Returns True if the message was a command."""
    cmd = text.split()[0].lower().lstrip("/").split("@")[0]
    if cmd == "start":
        send_message(chat_id,
                     f"{HELP_TEXT}\n\n_Your chat id is_ `{chat_id}` _— set "
                     "PEPPER_OWNER_CHAT_ID to this so only you can reach me._",
                     markdown=True)
        return True
    if cmd == "help":
        send_message(chat_id, HELP_TEXT, markdown=True)
        return True
    if cmd == "verse":
        ref, body = scripture.random_verse()
        send_message(chat_id, f"📖 {ref}\n\n“{body}”", markdown=False)
        return True
    if cmd == "reminders":
        from . import tools
        send_message(chat_id, tools._list_reminders(chat_id, {}))
        return True
    if cmd == "tasks":
        from . import tools
        send_message(chat_id, tools._list_tasks(chat_id, {}))
        return True
    if cmd == "reset":
        storage.clear_history(chat_id)
        send_message(chat_id, "🧹 Cleared our conversation history. Fresh start.")
        return True
    if cmd == "briefing":
        from . import tools
        msg = tools._run_daily_briefing({}, notify=lambda m: send_message(chat_id, m))
        send_message(chat_id, msg)
        return True
    return False


def handle_message(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    chat_id = str(message["chat"]["id"])
    text = (message.get("text") or "").strip()

    if not is_allowed(chat_id):
        send_message(chat_id,
                     "Sorry, I'm a private assistant and not configured to talk to this "
                     f"chat. (chat id: {chat_id})")
        print(f"[pepper] ignored message from unallowed chat {chat_id}")
        return

    if not text:
        send_message(chat_id, "I can only read text messages right now. 🙂")
        return

    print(f"[pepper] {chat_id}: {text[:120]}")

    if text.startswith("/") and handle_command(chat_id, text):
        return

    send_typing(chat_id)
    try:
        reply = agent.respond(
            chat_id, text, now_local(),
            notify=lambda m: send_message(chat_id, m),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[pepper] agent error: {exc}")
        send_message(chat_id, f"⚠️ I hit an error handling that: {html.escape(str(exc))}")
        return
    send_message(chat_id, reply)


# ---------------------------------------------------------------------------
# Scheduler (daily scripture + due reminders)
# ---------------------------------------------------------------------------
def _scheduler_loop() -> None:
    print("[pepper] scheduler started")
    while True:
        try:
            _tick_scheduler()
        except Exception as exc:  # noqa: BLE001
            print(f"[pepper] scheduler error: {exc}")
        time.sleep(30)


def _tick_scheduler() -> None:
    now = now_local()

    # 1) Daily scripture, once per day at/after the configured time.
    if config.SCRIPTURE_TIME and config.OWNER_CHAT_ID:
        try:
            hh, mm = (int(x) for x in config.SCRIPTURE_TIME.split(":"))
        except ValueError:
            hh, mm = 8, 0
        today_iso = now.date().isoformat()
        already = storage.get_last_scripture_date() == today_iso
        if not already and (now.hour, now.minute) >= (hh, mm):
            send_message(config.OWNER_CHAT_ID, scripture.format_daily(now.date()), markdown=True)
            storage.set_last_scripture_date(today_iso)
            print(f"[pepper] sent daily scripture for {today_iso}")

    # 2) Due reminders.
    now_iso = now.strftime("%Y-%m-%dT%H:%M")
    for rem in storage.due_reminders(now_iso):
        send_message(rem["chat_id"], f"⏰ Reminder: {rem['text']}")
        storage.mark_reminder_fired(rem["id"])
        print(f"[pepper] fired reminder #{rem['id']}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def run() -> int:
    missing = config.missing_required()
    if missing:
        print("[pepper] missing required configuration: " + ", ".join(missing))
        print("        Set them as environment variables or in a .env file. "
              "See pepper/.env.example.")
        return 1

    # Identify the bot we're running as (nice sanity check on startup).
    try:
        me = requests.get(config.telegram_api("getMe"), timeout=15).json()
        username = me.get("result", {}).get("username", "?")
        print(f"[pepper] connected as @{username}")
    except Exception as exc:  # noqa: BLE001
        print(f"[pepper] warning: could not reach Telegram getMe: {exc}")

    if not config.ALLOWED_CHAT_IDS:
        print("[pepper] WARNING: PEPPER_OWNER_CHAT_ID not set — I will reply to ANYONE who "
              "messages the bot. Message the bot once and set PEPPER_OWNER_CHAT_ID to lock "
              "it down.")

    threading.Thread(target=_scheduler_loop, daemon=True).start()

    offset = storage.get_offset()
    print(f"[pepper] polling for messages (offset={offset})… Ctrl-C to stop.")
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            storage.set_offset(offset)
            try:
                handle_message(update)
            except Exception as exc:  # noqa: BLE001
                print(f"[pepper] handler error: {exc}")
