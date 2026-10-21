"""Tests for the scoring engine."""

from datetime import date, timedelta

import pytest

from todaytech.core.models import (
    EligibilityVerdict,
    Opportunity,
    OpportunityType,
    UserProfile,
)
from todaytech.core.scoring import (
    _score_benefit,
    _score_effort,
    _score_eligibility,
    _score_relevance_heuristic,
    compute_fit_score,
)


def _make_profile(**kwargs) -> UserProfile:
    defaults = {
        "country": "Ghana",
        "citizenship": ["Ghanaian"],
        "level": "undergraduate",
        "year": 3,
        "field_of_study": "Computer Science",
        "skills": ["Python", "FastAPI", "React", "Docker"],
        "interests": ["AI", "Open Source", "Cloud"],
        "opportunity_types": ["hackathon", "fellowship", "internship"],
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


def _make_opp(**kwargs) -> Opportunity:
    defaults = {
        "external_id": "opp_test_score_1",
        "title": "Open Source AI Hackathon",
        "type": OpportunityType.HACKATHON,
        "organizer": "OpenAI Community",
        "reward": "$10,000 prize and mentorship",
        "eligibility_text": "Open to all undergraduate students with Python experience.",
        "cost": 0.0,
        "mode": "online",
        "deadline": date.today() + timedelta(days=20),
        "eligibility_verdict": EligibilityVerdict.ELIGIBLE,
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


class TestEligibilityScorer:
    def test_eligible_scores_100(self):
        opp = _make_opp(eligibility_verdict=EligibilityVerdict.ELIGIBLE)
        assert _score_eligibility(opp) == 100

    def test_likely_scores_75(self):
        opp = _make_opp(eligibility_verdict=EligibilityVerdict.LIKELY)
        assert _score_eligibility(opp) == 75

    def test_check_scores_40(self):
        opp = _make_opp(eligibility_verdict=EligibilityVerdict.CHECK)
        assert _score_eligibility(opp) == 40

    def test_not_eligible_scores_0(self):
        opp = _make_opp(eligibility_verdict=EligibilityVerdict.NOT_ELIGIBLE)
        assert _score_eligibility(opp) == 0


class TestBenefitScorer:
    def test_high_value_keywords_boost(self):
        opp = _make_opp(reward="fully funded stipend and full scholarship")
        score = _score_benefit(opp)
        assert score >= 60

    def test_low_benefit_has_base_score(self):
        opp = _make_opp(reward="T-shirt")
        score = _score_benefit(opp)
        assert score == 30


class TestEffortScorer:
    def test_expired_deadline_scores_zero(self):
        opp = _make_opp(deadline=date.today() - timedelta(days=1))
        assert _score_effort(opp) == 0

    def test_comfortable_deadline_and_free_scores_high(self):
        opp = _make_opp(deadline=date.today() + timedelta(days=45), cost=0.0, mode="online")
        score = _score_effort(opp)
        assert score >= 80


class TestRelevanceHeuristic:
    def test_skill_match_adds_score(self):
        profile = _make_profile(skills=["Python", "Docker"])
        opp = _make_opp(title="Python and Docker Developer Fellowship")
        score = _score_relevance_heuristic(opp, profile)
        assert score > 30


@pytest.mark.asyncio
async def test_compute_fit_score_heuristic():
    profile = _make_profile()
    opp = _make_opp(
        eligibility_verdict=EligibilityVerdict.ELIGIBLE,
        reward="stipend and mentorship",
        cost=0.0,
    )
    score, reason = await compute_fit_score(
        opp,
        profile,
        llm=None,  # type: ignore
        use_llm_relevance=False,
    )
    assert 0 <= score <= 100
    assert len(reason) > 0
