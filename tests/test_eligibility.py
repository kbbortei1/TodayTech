"""Tests for the eligibility verification engine."""

from datetime import date, timedelta

from todaytech.core.eligibility import (
    _check_country,
    _check_deadline,
    _check_fee,
    _check_field,
    _check_level,
    rule_check,
)
from todaytech.core.models import (
    EligibilityVerdict,
    Opportunity,
    OpportunityType,
    UserProfile,
)


def _make_profile(**kwargs) -> UserProfile:
    defaults = {
        "country": "Ghana",
        "citizenship": ["Ghanaian"],
        "level": "undergraduate",
        "year": 3,
        "field_of_study": "Computer Science",
        "skills": ["Python", "FastAPI"],
        "interests": ["AI", "Open Source"],
        "max_application_fee": 0.0,
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


def _make_opp(**kwargs) -> Opportunity:
    defaults = {
        "external_id": "test_id_12345678",
        "title": "Global Student AI Fellowship",
        "type": OpportunityType.FELLOWSHIP,
        "organizer": "Global AI Lab",
        "source_type": "rss",
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


class TestDeadlineCheck:
    def test_past_deadline_ineligible(self):
        opp = _make_opp(deadline=date.today() - timedelta(days=2))
        res = _check_deadline(opp)
        assert res is not None
        assert res[0] == EligibilityVerdict.NOT_ELIGIBLE

    def test_future_deadline_passes(self):
        opp = _make_opp(deadline=date.today() + timedelta(days=14))
        assert _check_deadline(opp) is None

    def test_no_deadline_passes(self):
        opp = _make_opp(deadline=None)
        assert _check_deadline(opp) is None


class TestCountryCheck:
    def test_matching_country(self):
        profile = _make_profile(country="Ghana")
        opp = _make_opp(countries_allowed=["Ghana", "Nigeria", "Kenya"])
        assert _check_country(opp, profile) is None

    def test_restricted_country(self):
        profile = _make_profile(country="Ghana", citizenship=["Ghanaian"])
        opp = _make_opp(countries_allowed=["United States", "Canada"])
        res = _check_country(opp, profile)
        assert res is not None
        assert res[0] == EligibilityVerdict.NOT_ELIGIBLE

    def test_global_all_passes(self):
        profile = _make_profile(country="Ghana")
        opp = _make_opp(countries_allowed=["global"])
        assert _check_country(opp, profile) is None


class TestLevelCheck:
    def test_same_or_higher_level_passes(self):
        profile = _make_profile(level="undergraduate")
        opp = _make_opp(level_required="undergraduate")
        assert _check_level(opp, profile) is None

    def test_lower_level_fails(self):
        profile = _make_profile(level="undergraduate")
        opp = _make_opp(level_required="phd")
        res = _check_level(opp, profile)
        assert res is not None
        assert res[0] == EligibilityVerdict.NOT_ELIGIBLE


class TestFieldCheck:
    def test_exact_or_substring_field_passes(self):
        profile = _make_profile(field_of_study="Computer Science")
        opp = _make_opp(field_required="Computer Science")
        assert _check_field(opp, profile) is None

    def test_stem_related_fields_pass(self):
        profile = _make_profile(field_of_study="Software Engineering")
        opp = _make_opp(field_required="Technology")
        assert _check_field(opp, profile) is None

    def test_unrelated_field_returns_check(self):
        profile = _make_profile(field_of_study="Classical Literature")
        opp = _make_opp(field_required="Mechanical Engineering")
        res = _check_field(opp, profile)
        assert res is not None
        assert res[0] == EligibilityVerdict.CHECK


class TestFeeCheck:
    def test_zero_fee_passes(self):
        profile = _make_profile(max_application_fee=0.0)
        opp = _make_opp(cost=0.0)
        assert _check_fee(opp, profile) is None

    def test_fee_exceeding_max_fails(self):
        profile = _make_profile(max_application_fee=10.0)
        opp = _make_opp(cost=50.0)
        res = _check_fee(opp, profile)
        assert res is not None
        assert res[0] == EligibilityVerdict.NOT_ELIGIBLE


class TestRuleCheckIntegration:
    def test_fully_eligible_opportunity(self):
        profile = _make_profile()
        opp = _make_opp(
            deadline=date.today() + timedelta(days=20),
            countries_allowed=["global"],
            cost=0.0,
        )
        verdict, reason = rule_check(opp, profile)
        assert verdict == EligibilityVerdict.ELIGIBLE
