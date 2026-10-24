"""Tests for the TodayTech Web Dashboard REST APIs."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from todaytech.core.database import get_session, init_db
from todaytech.web.app import _seed_demo_if_empty, create_app


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path):
    # Isolated DB per test. ASGITransport doesn't fire startup events, so seed here.
    await init_db(f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    async with get_session() as session:
        await _seed_demo_if_empty(session)


@pytest.mark.asyncio
async def test_api_stats():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_opportunities" in data
        assert "closing_soon_count" in data
        assert "saved_count" in data


@pytest.mark.asyncio
async def test_api_opportunities_and_timeframe():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Fetch all radar items
        res = await client.get("/api/opportunities?status=radar")
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)

        # Test timeframe filtering: day, week, month
        res_day = await client.get("/api/opportunities?status=radar&timeframe=day")
        assert res_day.status_code == 200
        items_day = res_day.json()
        assert isinstance(items_day, list)

        res_week = await client.get("/api/opportunities?status=radar&timeframe=week")
        assert res_week.status_code == 200
        items_week = res_week.json()
        assert isinstance(items_week, list)

        res_month = await client.get("/api/opportunities?status=radar&timeframe=month")
        assert res_month.status_code == 200
        items_month = res_month.json()
        assert isinstance(items_month, list)


@pytest.mark.asyncio
async def test_save_and_unsave_workflow():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get one opportunity
        res = await client.get("/api/opportunities?status=all")
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        opp_id = items[0]["id"]

        # Save opportunity
        res_save = await client.post(
            f"/api/opportunity/{opp_id}/state",
            json={"status": "saved", "notes": "Saved for testing"},
        )
        assert res_save.status_code == 200
        assert res_save.json()["status"] == "saved"

        # Check it appears in pipeline
        res_pipeline = await client.get("/api/opportunities?status=pipeline")
        assert res_pipeline.status_code == 200
        pipeline_items = res_pipeline.json()
        pipeline_ids = [item["id"] for item in pipeline_items]
        assert opp_id in pipeline_ids

        # Unsave opportunity (set back to radar)
        res_unsave = await client.post(
            f"/api/opportunity/{opp_id}/state",
            json={"status": "radar", "notes": ""},
        )
        assert res_unsave.status_code == 200
        assert res_unsave.json()["status"] == "radar"

        # Verify it is removed from saved list
        res_saved = await client.get("/api/opportunities?status=saved")
        assert res_saved.status_code == 200
        saved_ids = [item["id"] for item in res_saved.json()]
        assert opp_id not in saved_ids


@pytest.mark.asyncio
async def test_search_query():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        async def search(q: str) -> list[str]:
            res = await client.get("/api/opportunities", params={"status": "all", "query": q})
            assert res.status_code == 200
            return [item["title"] for item in res.json()]

        # Case-insensitive, and multi-word terms need not be adjacent
        assert any("Google Summer of Code" in t for t in await search("GOOGLE"))
        assert any("Google Summer of Code" in t for t in await search("google code"))
        # Matches on type, not just title text
        assert any("Hackathon" in t for t in await search("hackathon"))
        # Every term must match
        assert await search("google zzz-no-such-term") == []
        # Campus ambassador programs are searchable by type and title text
        assert any("Campus Experts" in t for t in await search("campus ambassador"))


@pytest.mark.asyncio
async def test_ambassador_type_filter():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/opportunities", params={"status": "all", "type": "ambassador"})
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        assert all(item["type"] == "ambassador" for item in items)


@pytest.mark.asyncio
async def test_api_digest_horizons():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Day horizon
        res = await client.get("/api/digest?timeframe=day")
        assert res.status_code == 200
        data = res.json()
        assert "closing_soon" in data
        assert "hot_picks" in data
        assert "digest_markdown" in data
        assert data["timeframe"] == "day"

        # Week horizon
        res_week = await client.get("/api/digest?timeframe=week")
        assert res_week.status_code == 200
        assert res_week.json()["timeframe"] == "week"

        # Month horizon
        res_month = await client.get("/api/digest?timeframe=month")
        assert res_month.status_code == 200
        assert res_month.json()["timeframe"] == "month"
