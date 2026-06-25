"""
Tiny JSON-backed persistence for Pepper.

Keeps everything in one human-readable file under ``pepper/state/state.json``
(git-ignored) so reminders, tasks, the Telegram update offset, and per-chat
conversation history all survive restarts. No database required.

Access is serialized with a lock so the poll loop and the scheduler thread can
both touch state safely.
"""

import json
import os
import threading

from . import config

_LOCK = threading.RLock()
_STATE_PATH = os.path.join(config.STATE_DIR, "state.json")

_DEFAULT = {
    "offset": 0,            # Telegram getUpdates offset
    "conversations": {},    # chat_id -> [ {role, content}, ... ]
    "reminders": [],        # see add_reminder()
    "tasks": [],            # see add_task()
    "last_scripture_date": None,  # ISO date string of the last 8 AM verse sent
    "next_id": 1,           # monotonic id for reminders/tasks
}


def _load() -> dict:
    if not os.path.exists(_STATE_PATH):
        return json.loads(json.dumps(_DEFAULT))
    try:
        with open(_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(_DEFAULT))
    # Backfill any keys added in later versions.
    for k, v in _DEFAULT.items():
        data.setdefault(k, json.loads(json.dumps(v)))
    return data


def _save(data: dict) -> None:
    os.makedirs(config.STATE_DIR, exist_ok=True)
    tmp = _STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _STATE_PATH)  # atomic on POSIX


# --- Telegram offset ---------------------------------------------------------
def get_offset() -> int:
    with _LOCK:
        return _load().get("offset", 0)


def set_offset(offset: int) -> None:
    with _LOCK:
        data = _load()
        data["offset"] = offset
        _save(data)


# --- Conversation history ----------------------------------------------------
def get_history(chat_id: str) -> list:
    with _LOCK:
        return _load()["conversations"].get(str(chat_id), [])


def set_history(chat_id: str, messages: list) -> None:
    """Persist a (already-trimmed) message list for a chat."""
    with _LOCK:
        data = _load()
        data["conversations"][str(chat_id)] = messages
        _save(data)


def clear_history(chat_id: str) -> None:
    with _LOCK:
        data = _load()
        data["conversations"].pop(str(chat_id), None)
        _save(data)


# --- Reminders ---------------------------------------------------------------
def add_reminder(chat_id: str, text: str, due_iso: str) -> int:
    """Store a reminder due at an ISO-8601 local timestamp. Returns its id."""
    with _LOCK:
        data = _load()
        rid = data["next_id"]
        data["next_id"] += 1
        data["reminders"].append({
            "id": rid,
            "chat_id": str(chat_id),
            "text": text,
            "due": due_iso,
            "fired": False,
        })
        _save(data)
        return rid


def list_reminders(chat_id: str, include_fired: bool = False) -> list:
    with _LOCK:
        rems = [r for r in _load()["reminders"] if r["chat_id"] == str(chat_id)]
    if not include_fired:
        rems = [r for r in rems if not r["fired"]]
    return sorted(rems, key=lambda r: r["due"])


def due_reminders(now_iso: str) -> list:
    """All un-fired reminders whose due time is at or before now_iso."""
    with _LOCK:
        return [r for r in _load()["reminders"]
                if not r["fired"] and r["due"] <= now_iso]


def mark_reminder_fired(rid: int) -> None:
    with _LOCK:
        data = _load()
        for r in data["reminders"]:
            if r["id"] == rid:
                r["fired"] = True
        _save(data)


def cancel_reminder(chat_id: str, rid: int) -> bool:
    with _LOCK:
        data = _load()
        before = len(data["reminders"])
        data["reminders"] = [
            r for r in data["reminders"]
            if not (r["id"] == rid and r["chat_id"] == str(chat_id))
        ]
        changed = len(data["reminders"]) != before
        if changed:
            _save(data)
        return changed


# --- Tasks (lightweight to-do list) ------------------------------------------
def add_task(chat_id: str, text: str) -> int:
    with _LOCK:
        data = _load()
        tid = data["next_id"]
        data["next_id"] += 1
        data["tasks"].append({
            "id": tid,
            "chat_id": str(chat_id),
            "text": text,
            "done": False,
        })
        _save(data)
        return tid


def list_tasks(chat_id: str, include_done: bool = False) -> list:
    with _LOCK:
        tasks = [t for t in _load()["tasks"] if t["chat_id"] == str(chat_id)]
    if not include_done:
        tasks = [t for t in tasks if not t["done"]]
    return tasks


def complete_task(chat_id: str, tid: int) -> bool:
    with _LOCK:
        data = _load()
        found = False
        for t in data["tasks"]:
            if t["id"] == tid and t["chat_id"] == str(chat_id):
                t["done"] = True
                found = True
        if found:
            _save(data)
        return found


# --- Scheduler bookkeeping ---------------------------------------------------
def get_last_scripture_date() -> str | None:
    with _LOCK:
        return _load().get("last_scripture_date")


def set_last_scripture_date(date_iso: str) -> None:
    with _LOCK:
        data = _load()
        data["last_scripture_date"] = date_iso
        _save(data)
