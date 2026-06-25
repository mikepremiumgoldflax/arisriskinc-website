"""
The agent loop — Claude with tool use.

``respond`` takes the owner's message, replays recent conversation history, lets
Claude call tools until it's done, persists the updated history, and returns the
final text reply. Tool calls are executed via ``tools.dispatch``.
"""

import datetime

from anthropic import Anthropic

from . import config, storage, tools

_CLIENT = None


def _client() -> Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _CLIENT


def _system_prompt(now_local: datetime.datetime) -> str:
    return (
        "You are Pepper Botts, the agentic AI Executive Assistant for ARIS Risk Inc. "
        "(arisriskinc.com) — a company providing parcel-level wildfire risk intelligence "
        "for property & casualty insurance.\n\n"
        f"You assist {config.OWNER_NAME} (owner email: {config.OWNER_EMAIL}). "
        "Be warm, concise, and proactive — a sharp, trustworthy chief-of-staff. Use the "
        "owner's name sparingly and naturally. Replies are read on a phone in Telegram, "
        "so keep them tight and skimmable; use short paragraphs or compact bullet lists.\n\n"
        "You have real tools — use them rather than guessing:\n"
        "- web_search for anything current or factual.\n"
        "- send_email to send mail on the owner's behalf. For anything consequential, "
        "show a draft and get a clear go-ahead before sending.\n"
        "- add_reminder / list_reminders / cancel_reminder for time-based nudges.\n"
        "- add_task / list_tasks / complete_task for the to-do list.\n"
        "- run_daily_briefing to trigger the news briefing on demand.\n"
        "- get_scripture for an encouraging Bible verse.\n\n"
        f"The current local date and time is {now_local.strftime('%A, %B %-d, %Y at %-I:%M %p')} "
        f"({config.TIMEZONE}). Resolve relative times (e.g. 'in 2 hours', 'tomorrow 9am') "
        "against this when scheduling reminders, and pass them as ISO 'YYYY-MM-DDTHH:MM'.\n"
        "If a tool reports a missing API key, explain plainly what the owner needs to set. "
        "Never invent facts, email addresses, or confirmations."
    )


def _trim(history: list) -> list:
    """Keep the last N turns, but never start the window on an orphan tool_result.

    The Anthropic API requires that any 'tool_result' block be preceded by the
    matching 'tool_use'. After slicing we drop a leading user message whose
    content begins with tool_result blocks.
    """
    max_msgs = config.HISTORY_TURNS * 2
    if len(history) > max_msgs:
        history = history[-max_msgs:]
    while history and history[0].get("role") == "user":
        content = history[0].get("content")
        if isinstance(content, list) and content and isinstance(content[0], dict) \
                and content[0].get("type") == "tool_result":
            history = history[1:]
        else:
            break
    return history


def respond(chat_id: str, user_text: str, now_local: datetime.datetime, notify=None) -> str:
    """Run one agent turn for an incoming message; return the reply text."""
    history = storage.get_history(chat_id)
    history.append({"role": "user", "content": user_text})

    client = _client()
    system = _system_prompt(now_local)

    final_text = ""
    # Bound the tool-use loop so a misbehaving model can't spin forever.
    for _ in range(8):
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system,
            tools=tools.TOOL_SCHEMAS,
            messages=history,
        )

        # Record the assistant turn verbatim (text + any tool_use blocks).
        assistant_content = [block.model_dump() for block in message.content]
        history.append({"role": "assistant", "content": assistant_content})

        if message.stop_reason != "tool_use":
            final_text = "".join(
                b.text for b in message.content if getattr(b, "type", None) == "text"
            ).strip()
            break

        # Execute every tool the model asked for and feed the results back.
        tool_results = []
        for block in message.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            result = tools.dispatch(block.name, block.input or {}, chat_id, notify=notify)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
        history.append({"role": "user", "content": tool_results})
    else:
        final_text = ("I got stuck working through that — let's try again, maybe a bit "
                      "more specifically?")

    storage.set_history(chat_id, _trim(history))
    return final_text or "(no reply)"
