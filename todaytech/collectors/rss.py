"""RSS/Atom feed collector using feedparser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import feedparser
import structlog
import yaml

from todaytech.collectors import Collector, register_collector

log = structlog.get_logger()

# Default RSS feeds for opportunity discovery
DEFAULT_FEEDS = [
    "https://www.opportunitydesk.org/feed/",
    "https://www.scholarshippositions.com/feed/",
]


@register_collector("rss")
class RSSCollector(Collector):
    """Collect opportunities from RSS/Atom feeds."""

    @property
    def is_available(self) -> bool:
        return True

    async def collect(self, queries: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        # Gather feeds from defaults + sources.yaml + source packs
        feeds = list(DEFAULT_FEEDS)
        feeds.extend(self._load_user_feeds())

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:15]:
                    results.append({
                        "title": entry.get("title", ""),
                        "source_url": entry.get("link", ""),
                        "raw_text": entry.get("summary", "")[:500],
                        "source_name": f"rss:{feed.feed.get('title', feed_url)[:30]}",
                    })
                log.debug("rss.parsed", url=feed_url, entries=len(feed.entries))
            except Exception as exc:
                log.warning("rss.feed_failed", url=feed_url, error=str(exc))

        return results

    def _load_user_feeds(self) -> list[str]:
        """Load additional feed URLs from sources.yaml."""
        sources_path = Path("sources.yaml")
        if not sources_path.exists():
            return []
        try:
            with open(sources_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return [
                s["value"]
                for s in data.get("sources", [])
                if s.get("type") == "rss" and s.get("enabled", True)
            ]
        except Exception as exc:
            log.warning("rss.sources_load_failed", error=str(exc))
            return []
