"""
The ARIS Daily Intelligence Briefing — end-to-end pipeline orchestrator.

  Phase 1  Gather   — search + scrape AI / InsurTech / wildfire sources
  Phase 2  Script   — Claude synthesizes the executive narration
  Phase 3  Audio    — edge-tts (en-US-GuyNeural) renders the MP3
  Verify            — ffprobe duration check (sub-8-minute target)
  Deliver           — email the script + MP3 to the team

Run locally:  python -m briefing.run
"""

import datetime
import os
import sys

from . import config, deliver, deliver_telegram, phase1_gather, phase2_script, phase3_audio


def main() -> int:
    today = datetime.date.today()
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    stamp = today.isoformat()
    script_path = os.path.join(config.OUTPUT_DIR, f"narration_script_{stamp}.txt")
    mp3_path = os.path.join(config.OUTPUT_DIR, f"ARIS_Briefing_{stamp}.mp3")

    # Phase 1 — Intelligence gathering
    raw_news = phase1_gather.gather(today)
    if not raw_news.strip():
        print("No source material gathered — aborting. Check TAVILY_API_KEY / network.")
        return 1

    # Phase 2 — Script generation
    if not config.ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set — cannot generate the script.")
        return 1
    script = phase2_script.generate_narration_script(raw_news, today)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    # Phase 3 — Audio synthesis
    phase3_audio.synthesize_text(script, mp3_path)

    # Verify — duration (best-effort; needs ffmpeg)
    phase3_audio.check_audio_duration(mp3_path)

    # Deliver — Telegram (primary); fall back to email only if Telegram isn't set.
    sent = deliver_telegram.deliver_telegram(script, mp3_path, today)
    if not sent:
        deliver.email_briefing(script, mp3_path, today)

    print(f"\nDone. Script: {script_path}\n      Audio:  {mp3_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
