"""Tests for the scam and quality filter."""

from todaytech.core.models import Opportunity, OpportunityType
from todaytech.core.scam_filter import check_scam, is_trusted_source


def _make_opp(**kwargs) -> Opportunity:
    defaults = {
        "external_id": "test_id_99999999",
        "title": "Legitimate Open Source Grant",
        "type": OpportunityType.GRANT,
        "organizer": "Python Software Foundation",
        "source_type": "rss",
        "source_url": "https://www.python.org/psf/grants/",
        "application_url": "https://www.python.org/psf/grants/apply",
        "cost": 0.0,
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


class TestScamFilter:
    def test_legitimate_opp_passes(self):
        opp = _make_opp()
        is_scam, reason = check_scam(opp)
        assert is_scam is False
        assert reason == ""

    def test_guaranteed_scholarship_with_vague_organizer_flagged(self):
        opp = _make_opp(
            title="Guaranteed Scholarship for all applicants!",
            organizer="",  # Vague organizer (< 3 chars)
            raw_text="Congratulations you won 100% acceptance guaranteed scholarship.",
        )
        is_scam, reason = check_scam(opp)
        assert is_scam is True
        assert "guaranteed scholarship" in reason.lower()

    def test_shortened_url_and_fee_flagged(self):
        opp = _make_opp(
            title="Summer Coding Fellowship",
            organizer="Tech Group",
            cost=150.0,  # Fee > $100
            application_url="https://bit.ly/secret-application-form",
        )
        is_scam, reason = check_scam(opp)
        assert is_scam is True
        assert "fee" in reason.lower()
        assert "shortener" in reason.lower()

    def test_no_url_and_vague_organizer_flagged(self):
        opp = _make_opp(
            organizer="AB",
            source_url="",
            application_url="",
        )
        is_scam, reason = check_scam(opp)
        assert is_scam is True
        assert "No verifiable source URL" in reason


class TestTrustedDomains:
    def test_devpost_is_trusted(self):
        assert is_trusted_source("https://devpost.com/hackathons") is True

    def test_github_is_trusted(self):
        assert is_trusted_source("https://github.com/education") is True

    def test_random_domain_not_trusted(self):
        assert is_trusted_source("https://random-opportunity-site-123.biz") is False

    def test_empty_string_not_trusted(self):
        assert is_trusted_source("") is False
