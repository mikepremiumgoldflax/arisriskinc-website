"""
Phase 3: Audio Synthesis (MP3 Generation).

Converts the text script into an MP3 audio file using edge-tts, which talks to
Microsoft Edge's neural Text-to-Speech voices — high quality, no paid Azure
subscription required.

  TTS Engine: edge-tts
  Voice:      en-US-GuyNeural (a professional, male American voice)
"""

import asyncio
import subprocess

import edge_tts

from . import config


def generate_mp3(input_text_file: str, output_mp3_file: str) -> None:
    """Generate an MP3 from a text file using the edge-tts CLI (the ARIS default)."""
    command = [
        "edge-tts",
        "--voice", config.TTS_VOICE,
        "--file", input_text_file,
        "--write-media", output_mp3_file,
    ]
    print(f"Generating audio... saving to {output_mp3_file}")
    subprocess.run(command, check=True)
    print("Audio generation complete.")


async def _synthesize(text: str, output_mp3_file: str) -> None:
    communicate = edge_tts.Communicate(text, config.TTS_VOICE)
    await communicate.save(output_mp3_file)


def synthesize_text(text: str, output_mp3_file: str) -> None:
    """Generate an MP3 directly from a script string (no temp file needed)."""
    print(f"Generating audio with {config.TTS_VOICE}... saving to {output_mp3_file}")
    asyncio.run(_synthesize(text, output_mp3_file))
    print("Audio generation complete.")


def check_audio_duration(mp3_file: str) -> float | None:
    """Check the duration of an MP3 file using ffprobe (requires ffmpeg)."""
    import json

    command = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        mp3_file,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration_seconds = float(data["format"]["duration"])
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        print(f"Duration: {minutes}m {seconds}s")
        return duration_seconds
    except Exception as e:
        print(f"Error checking duration: {e}")
        return None
