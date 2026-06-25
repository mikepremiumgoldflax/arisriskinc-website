"""
Delivery: email the finished briefing (script in the body, MP3 attached).

Uses Gmail SMTP over SSL with an App Password. Set GMAIL_USERNAME and
GMAIL_APP_PASSWORD as GitHub Actions secrets.
"""

import datetime
import smtplib
from email.message import EmailMessage

from . import config


def email_briefing(script: str, mp3_path: str, today: datetime.date | None = None) -> None:
    """Send the daily briefing to EMAIL_TO with the MP3 attached."""
    today = today or datetime.date.today()
    date_str = today.strftime("%A, %B %-d, %Y")

    if not config.GMAIL_USERNAME or not config.GMAIL_APP_PASSWORD:
        print("GMAIL_USERNAME / GMAIL_APP_PASSWORD not set — skipping email delivery.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"ARIS Daily Intelligence Briefing — {date_str}"
    msg["From"] = config.GMAIL_USERNAME
    msg["To"] = config.EMAIL_TO
    msg.set_content(
        f"Good morning. Your ARIS Daily Intelligence Briefing for {date_str} is attached "
        f"as an MP3.\n\nThe full narration script is below.\n\n"
        f"{'=' * 60}\n\n{script}\n"
    )

    with open(mp3_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="audio",
            subtype="mpeg",
            filename=f"ARIS_Briefing_{today.isoformat()}.mp3",
        )

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.login(config.GMAIL_USERNAME, config.GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print(f"Delivery complete: emailed briefing to {config.EMAIL_TO}.")
