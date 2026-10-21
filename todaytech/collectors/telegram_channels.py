"""Telegram channel collector using Telethon (user's own API credentials).

Only reads from public channels that the user explicitly lists in their
sources.yaml.  Uses the user's own Telegram API credentials.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from todaytech.collectors import Collector, register_collector

log = structlog.get_logger()


@register_collector("telegram_channels")
class TelegramChannelCollector(Collector):
    """Read messages from public Telegram channels via Telethon."""

    @property
    def is_available(self) -> bool:
        return bool(self.settings.telegram_api_id and self.settings.telegram_api_hash)

    async def collect(self, queries: list[str]) -> list[dict[str, Any]]:
        from telethon import TelegramClient

        results: list[dict[str, Any]] = []
        channels = self._load_channels()
        if not channels:
            return results

        client = TelegramClient(
            "data/telethon_session",
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )

        try:
            await client.start()

            for channel_name in channels:
                try:
                    entity = await client.get_entity(channel_name)
                    async for message in client.iter_messages(entity, limit=20):
                        if message.text and len(message.text) > 30:
                            results.append(
                                {
                                    "title": message.text[:100].strip(),
                                    "source_url": f"https://t.me/{channel_name}/{message.id}",
                                    "raw_text": message.text[:500],
                                    "source_name": f"telegram:{channel_name}",
                                }
                            )
                except Exception as exc:
                    log.warning("telegram.channel_failed", channel=channel_name, error=str(exc))

        finally:
            await client.disconnect()

        return results

    def _load_channels(self) -> list[str]:
        """Load channel list from sources.yaml."""
        sources_path = Path("sources.yaml")
        if not sources_path.exists():
            return []
        try:
            with open(sources_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return [
                s["value"]
                for s in data.get("sources", [])
                if s.get("type") == "telegram_channel" and s.get("enabled", True)
            ]
        except Exception:
            return []
