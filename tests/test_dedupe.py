"""Tests for the deduplication logic."""

from todaytech.core.pipeline import (
    canonicalize_url,
    generate_external_id,
    is_duplicate,
)


class TestCanonicalizeUrl:
    def test_strips_trailing_slash(self):
        assert canonicalize_url("https://example.com/path/") == "https://example.com/path"

    def test_lowercases(self):
        assert canonicalize_url("HTTPS://EXAMPLE.COM/Path") == "https://example.com/path"

    def test_removes_fragment(self):
        assert canonicalize_url("https://example.com/page#section") == "https://example.com/page"

    def test_removes_query_params(self):
        assert (
            canonicalize_url("https://example.com/page?utm_source=x") == "https://example.com/page"
        )

    def test_empty_string(self):
        assert canonicalize_url("") == ""


class TestGenerateExternalId:
    def test_same_url_same_id(self):
        item1 = {"source_url": "https://example.com/opportunity/1"}
        item2 = {"source_url": "https://example.com/opportunity/1/"}
        assert generate_external_id(item1) == generate_external_id(item2)

    def test_different_url_different_id(self):
        item1 = {"source_url": "https://example.com/opportunity/1"}
        item2 = {"source_url": "https://example.com/opportunity/2"}
        assert generate_external_id(item1) != generate_external_id(item2)

    def test_falls_back_to_title(self):
        item = {"title": "Amazing Hackathon 2025"}
        ext_id = generate_external_id(item)
        assert len(ext_id) == 16

    def test_title_case_insensitive(self):
        item1 = {"title": "Amazing Hackathon"}
        item2 = {"title": "amazing hackathon"}
        assert generate_external_id(item1) == generate_external_id(item2)


class TestIsDuplicate:
    def test_exact_url_match(self):
        seen = {}
        item1 = {"title": "Hackathon A", "source_url": "https://example.com/hack"}
        item1_id = generate_external_id(item1)
        seen[item1_id] = item1

        item2 = {"title": "Hackathon B", "source_url": "https://example.com/hack"}
        assert is_duplicate(item2, seen) is True

    def test_fuzzy_title_match(self):
        seen = {}
        item1 = {"title": "Global AI Hackathon 2025"}
        item1_id = generate_external_id(item1)
        seen[item1_id] = item1

        item2 = {"title": "Global AI Hackathon 2025 - Apply Now!"}
        assert is_duplicate(item2, seen, threshold=70) is True

    def test_no_match(self):
        seen = {}
        item1 = {"title": "Hackathon A", "source_url": "https://example.com/a"}
        item1_id = generate_external_id(item1)
        seen[item1_id] = item1

        item2 = {"title": "Scholarship B", "source_url": "https://other.com/b"}
        assert is_duplicate(item2, seen) is False
