"""
Phase 2: Script Generation.

The raw text gathered in Phase 1 is synthesized into the executive-style
narration script. This is done with Claude (Anthropic API).
"""

import datetime

import anthropic

from . import config

SYSTEM_PROMPT = """\
You are an elite intelligence analyst producing a daily audio briefing for Mike, \
the founder of ARIS Risk Inc. (parcel-level wildfire risk intelligence for P&C \
insurance). Your goal is to synthesize the provided raw news text into a sharp, \
executive-style narration script.

Requirements:
1. Structure the script into these sections, spoken aloud as headers: HEADLINE \
STORY, FUNDING AND DEALS, NEW TECH AND PRODUCTS, WILDFIRE AND REGULATION, and \
WHAT IT MEANS FOR ARIS.
2. Flag anything relevant to ARIS Risk Inc. — wildfire risk, InsurTech, the \
California FAIR Plan and CDI, and competitors such as ZestyAI, CoreLogic, and \
Cape Analytics.
3. The tone must be sharp, professional, and direct.
4. The script must be designed to be read aloud: no markdown, no bullet symbols, \
no URLs, no special formatting. Spell out abbreviations and numbers where it \
helps the listener.
5. Open with a one-line greeting that includes today's date, and close with a \
brief sign-off.
6. Total spoken duration must be under 8 minutes (approximately 1,100 to 1,300 \
words). If the source material is thin, keep it shorter rather than padding.
Output only the narration script text — nothing else."""


def generate_narration_script(raw_news_text: str, today: datetime.date | None = None) -> str:
    """Generate the narration script from raw intelligence text using Claude."""
    today = today or datetime.date.today()
    date_str = today.strftime("%A, %B %-d, %Y")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)

    user_message = (
        f"Today is {date_str}. Here is today's raw intelligence data gathered "
        f"from AI news and InsurTech sources. Write the ARIS Daily Intelligence "
        f"Briefing script.\n\n{raw_news_text}"
    )

    # Stream so the large max_tokens doesn't hit HTTP timeouts; adaptive thinking
    # gives Claude room to plan the synthesis before writing.
    with client.messages.stream(
        model=config.SCRIPT_MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        message = stream.get_final_message()

    script = "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()
    print(f"Phase 2 complete: generated {len(script.split())} word script.")
    return script
