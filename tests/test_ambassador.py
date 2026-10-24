"""Tests for campus/student ambassador opportunity support."""

from todaytech.core.models import OpportunityType, UserProfile
from todaytech.core.pipeline import _dict_to_opportunity, generate_queries


def _profile(types: list[str]) -> UserProfile:
    return UserProfile(
        country="Ghana",
        level="undergraduate",
        field_of_study="Computer Science",
        opportunity_types=types,
    )


class TestAmbassadorQueries:
    def test_ambassador_type_adds_campus_queries(self):
        queries = generate_queries(_profile(["ambassador"]))
        assert any("campus ambassador" in q for q in queries)
        assert any("Ghana" in q and "ambassador" in q for q in queries)

    def test_no_ambassador_queries_unless_selected(self):
        queries = generate_queries(_profile(["hackathon"]))
        assert not any("ambassador" in q for q in queries)

    def test_ambassador_in_default_profile_types(self):
        assert "ambassador" in UserProfile().opportunity_types


class TestAmbassadorClassification:
    def test_llm_type_ambassador(self):
        opp = _dict_to_opportunity({"title": "Student Program", "type": "ambassador"})
        assert opp.type == OpportunityType.AMBASSADOR

    def test_title_fallback_when_type_unknown(self):
        opp = _dict_to_opportunity({"title": "Notion Campus Ambassador 2026", "type": "other"})
        assert opp.type == OpportunityType.AMBASSADOR

    def test_explicit_type_not_overridden(self):
        opp = _dict_to_opportunity(
            {"title": "Ambassador Scholarship for Women in Tech", "type": "scholarship"}
        )
        assert opp.type == OpportunityType.SCHOLARSHIP
