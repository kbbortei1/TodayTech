"""Scam and quality filter.

Flags pay-to-apply schemes, unverifiable organizers, "guaranteed scholarship"
wording, suspicious or shortened links, and other red flags.
"""

from __future__ import annotations

from urllib.parse import urlparse

import structlog

from todaytech.core.models import Opportunity

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Red-flag patterns
# ---------------------------------------------------------------------------

_SCAM_PHRASES = [
    "guaranteed scholarship",
    "guaranteed admission",
    "100% acceptance",
    "pay to apply",
    "processing fee required",
    "send money",
    "wire transfer",
    "western union",
    "money gram",
    "whatsapp only",
    "dm for details",
    "limited slots remaining act now",
    "you have been selected",
    "congratulations you won",
]

_SUSPICIOUS_DOMAINS = [
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "adf.ly",
    "shorte.st",
]

_TRUSTED_DOMAINS = [
    "devpost.com",
    "mlh.io",
    "devfolio.co",
    "unstop.com",
    "hackerearth.com",
    "lablab.ai",
    "kaggle.com",
    "chevening.org",
    "daad.de",
    "erasmusplus.ec.europa.eu",
    "fulbright.org",
    "mastercardfdn.org",
    "google.com",
    "microsoft.com",
    "meta.com",
    "aws.amazon.com",
    "github.com",
    "ycombinator.com",
    "techstars.com",
    "outreachy.org",
    "opportunitydesk.org",
    "reddit.com",
    "linkedin.com",
]


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


def check_scam(opp: Opportunity) -> tuple[bool, str]:
    """Check if an opportunity looks suspicious.

    Returns (is_scam, reason).
    """
    reasons: list[str] = []
    combined_text = f"{opp.title} {opp.eligibility_text} {opp.reward} {opp.raw_text}".lower()

    # Check scam phrases
    for phrase in _SCAM_PHRASES:
        if phrase in combined_text:
            reasons.append(f"Contains suspicious phrase: '{phrase}'")

    # Check for high application fee
    if opp.cost > 100:
        reasons.append(f"High application fee: ${opp.cost:.0f}")

    # Check for shortened/suspicious URLs
    for url_field in [opp.application_url, opp.source_url]:
        if url_field:
            parsed = urlparse(url_field)
            domain = parsed.netloc.lower().removeprefix("www.")
            if domain in _SUSPICIOUS_DOMAINS:
                reasons.append(f"Uses URL shortener: {domain}")

    # No verifiable source URL
    if not opp.source_url and not opp.application_url:
        reasons.append("No verifiable source URL")

    # Check if organizer is vague
    if not opp.organizer or len(opp.organizer) < 3:
        reasons.append("Organizer not specified or very vague")

    is_scam = len(reasons) >= 2  # Two or more red flags
    reason = "; ".join(reasons) if reasons else ""

    if is_scam:
        log.info("scam_filter.flagged", title=opp.title, reasons=reason)

    return is_scam, reason


def is_trusted_source(url: str) -> bool:
    """Check if a URL is from a known trusted domain."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    return any(trusted in domain for trusted in _TRUSTED_DOMAINS)
