"""
Entrypoint for Pepper Botts.

    python -m pepper.run

Loads configuration from the environment (and an optional .env), then starts the
Telegram long-poll loop and the background scheduler.
"""

import sys

from . import bot


def main() -> int:
    try:
        return bot.run()
    except KeyboardInterrupt:
        print("\n[pepper] stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
