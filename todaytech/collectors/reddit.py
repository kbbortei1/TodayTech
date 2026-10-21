"""Reddit collector using PRAW (official API via OAuth)."""

from __future__ import annotations

from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from todaytech.collectors import Collector, register_collector

log = structlog.get_logger()

# Default subreddits for opportunity discovery
DEFAULT_SUBREDDITS = [
    "hackathons",
    "scholarships",
    "csMajors",
    "cscareerquestions",
    "gradadmissions",
    "internships",
    "forhire",
    "remotework",
    "learnprogramming",
]


@register_collector("reddit")
class RedditCollector(Collector):
    """Collect opportunities from Reddit using the official API."""

    @property
    def is_available(self) -> bool:
        return bool(
            self.settings.reddit_client_id and self.settings.reddit_client_secret
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def collect(self, queries: list[str]) -> list[dict[str, Any]]:
        import asyncpraw

        results: list[dict[str, Any]] = []

        reddit = asyncpraw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent,
        )

        try:
            subreddits = DEFAULT_SUBREDDITS

            for sub_name in subreddits:
                try:
                    subreddit = await reddit.subreddit(sub_name)
                    async for post in subreddit.hot(limit=15):
                        # Filter for relevant posts
                        title_lower = post.title.lower()
                        is_relevant = any(
                            kw in title_lower
                            for kw in [
                                "hackathon", "scholarship", "internship", "fellowship",
                                "grant", "program", "competition", "opportunity",
                                "apply", "deadline", "application", "free", "funded",
                            ]
                        )
                        if is_relevant:
                            results.append({
                                "title": post.title,
                                "source_url": f"https://reddit.com{post.permalink}",
                                "raw_text": (post.selftext or "")[:500],
                                "source_name": f"reddit/r/{sub_name}",
                            })
                except Exception as exc:
                    log.warning("reddit.subreddit_failed", subreddit=sub_name, error=str(exc))

            # Also search with profile-based queries
            for query in queries[:3]:
                try:
                    subreddit = await reddit.subreddit("all")
                    async for post in subreddit.search(query, limit=10, time_filter="week"):
                        results.append({
                            "title": post.title,
                            "source_url": f"https://reddit.com{post.permalink}",
                            "raw_text": (post.selftext or "")[:500],
                            "source_name": "reddit/search",
                        })
                except Exception as exc:
                    log.warning("reddit.search_failed", query=query, error=str(exc))

        finally:
            await reddit.close()

        return results
