"""Collector plugin interface and registry.

Every data source implements the ``Collector`` abstract class.  Collectors
handle their own retries, backoff, timeouts, and health tracking.
"""

from __future__ import annotations

import abc
from datetime import datetime
from typing import Any, Optional

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from todaytech.core.models import Opportunity

log = structlog.get_logger()


class CollectorHealth:
    """Track health of a collector."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.consecutive_failures: int = 0
        self.total_items: int = 0

    @property
    def is_healthy(self) -> bool:
        return self.consecutive_failures < 5

    def record_success(self, items: int) -> None:
        self.last_success = datetime.utcnow()
        self.last_error = None
        self.consecutive_failures = 0
        self.total_items += items

    def record_failure(self, error: str) -> None:
        self.last_error = error
        self.consecutive_failures += 1
        log.warning(
            "collector.failure",
            collector=self.name,
            error=error,
            consecutive=self.consecutive_failures,
        )


class Collector(abc.ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, name: str, settings: Any) -> None:
        self.name = name
        self.settings = settings
        self.health = CollectorHealth(name)

    @abc.abstractmethod
    async def collect(self, queries: list[str]) -> list[dict[str, Any]]:
        """Collect raw opportunity data.

        Args:
            queries: search queries derived from the user's profile.

        Returns:
            List of dicts with raw opportunity fields.
        """
        ...

    @property
    def is_available(self) -> bool:
        """Whether this collector has the required credentials."""
        return True

    async def safe_collect(self, queries: list[str]) -> list[dict[str, Any]]:
        """Collect with error handling and health tracking."""
        if not self.is_available:
            log.info("collector.unavailable", collector=self.name)
            return []

        if not self.health.is_healthy:
            log.warning("collector.unhealthy_skipped", collector=self.name)
            return []

        try:
            results = await self.collect(queries)
            self.health.record_success(len(results))
            log.info("collector.success", collector=self.name, items=len(results))
            return results
        except Exception as exc:
            self.health.record_failure(str(exc))
            return []


# ---------------------------------------------------------------------------
# Collector registry
# ---------------------------------------------------------------------------

_registry: dict[str, type[Collector]] = {}


def register_collector(name: str):
    """Decorator to register a collector class."""
    def decorator(cls: type[Collector]):
        _registry[name] = cls
        return cls
    return decorator


def get_all_collectors(settings: Any) -> list[Collector]:
    """Instantiate all registered collectors."""
    collectors = []
    for name, cls in _registry.items():
        try:
            collector = cls(name, settings)
            if collector.is_available:
                collectors.append(collector)
                log.debug("collector.registered", name=name)
        except Exception as exc:
            log.warning("collector.init_failed", name=name, error=str(exc))
    return collectors
