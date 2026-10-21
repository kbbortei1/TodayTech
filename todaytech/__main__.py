"""TodayTech — Application entry point."""

import asyncio
import sys

import structlog

from todaytech.core.config import get_settings

log = structlog.get_logger()


async def _run() -> None:
    """Start all TodayTech services."""
    settings = get_settings()

    from todaytech.core.logging import setup_logging

    setup_logging(settings.log_level)

    log.info("todaytech.starting", version="0.1.0")

    from todaytech.core.database import init_db

    await init_db(settings.database_url)

    from todaytech.bot.app import start_bot

    await start_bot(settings)


def main() -> None:
    """CLI-invocable entry point."""
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        log.info("todaytech.shutdown")
        sys.exit(0)


if __name__ == "__main__":
    main()
