"""
Delivery: send the finished briefing to Telegram.

A Telegram bot sends the MP3 as a playable audio message (with a phone push
notification) and the full narration script as a text file. Set
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as GitHub Actions secrets.

  Create a bot:   message @BotFather on Telegram -> /newbot -> copy the token
  Find your ID:   message @userinfobot -> it replies with your numeric chat id
                  (then send your bot any message once so it can DM you)
"""

import datetime

import requests

from . import config


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


def deliver_telegram(script: str, mp3_path: str, today: datetime.date | None = None) -> bool:
    """Send the MP3 (as audio) and the script (as a document) to Telegram.

    Returns True if delivery was attempted, False if not configured.
    """
    today = today or datetime.date.today()
    date_str = today.strftime("%A, %B %-d, %Y")

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — skipping Telegram delivery.")
        return False

    caption = f"🎧 ARIS Daily Intelligence Briefing — {date_str}"

    # 1) The MP3 as a playable audio message (this is what pushes to the phone).
    with open(mp3_path, "rb") as audio:
        resp = requests.post(
            _api("sendAudio"),
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "caption": caption,
                "title": f"ARIS Briefing {today.isoformat()}",
                "performer": "ARIS Risk Inc.",
            },
            files={"audio": (f"ARIS_Briefing_{today.isoformat()}.mp3", audio, "audio/mpeg")},
            timeout=120,
        )
    resp.raise_for_status()

    # 2) The full narration script as a downloadable text file (sent from memory).
    script_bytes = script.encode("utf-8")
    resp2 = requests.post(
        _api("sendDocument"),
        data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": "Full narration script"},
        files={"document": (f"narration_script_{today.isoformat()}.txt", script_bytes, "text/plain")},
        timeout=60,
    )
    resp2.raise_for_status()

    print(f"Delivery complete: sent briefing to Telegram chat {config.TELEGRAM_CHAT_ID}.")
    return True
