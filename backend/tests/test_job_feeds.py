"""Job-feed adapter and lifecycle tests. Fixtures only - no network, no real data imported."""
from __future__ import annotations

import asyncio
import pathlib
import sys
import urllib.error
LF = chr(10)

BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import pytest  # noqa: E402

import data_import  # noqa: E402
import job_feeds  # noqa: E402
from memory_db import MemoryDB  # noqa: E402


def run(coro):
    return asyncio.run(coro)


BOARD = {"board_id": "exampleco", "provider": "greenhouse", "company": "ExampleCo",
         "careers_url": "https://exampleco.test/careers",
         "feed_url": "https://example.test/boards/exampleco/jobs"}

# Field names and nesting mirror the real provider responses seen during the pilot; the values are
# invented. Posting body text is included here precisely so the adapters can be shown to drop it.
GREENHOUSE_FIXTURE = {"jobs": [{
    "id": 4970739101, "internal_job_id": "4520058101", "requisition_id": "GRID-1",
    "title": "Software Engineer, Platform", "company_name": "ExampleCo",
    "location": {"name": "Bengaluru, India"},
    "absolute_url": "https://boards.example.test/exampleco/jobs/4970739101",
    "first_published": "2026-09-14T03:49:28-04:00", "updated_at": "2026-09-20T03:52:53-04:00",
    "content": "<html>Long employer job description, must never be stored</html>",
    "questions": [{"name": "resume"}],
}]}

LEVER_FIXTURE = [{
    "id": "aa98a938-45f5", "text": "software engineer", "country": "IN",
    "createdAt": 1790573982021, "workplaceType": "hybrid",
    "categories": {"department": "Engineering", "location": "bengaluru", "team": "Platform"},
    "hostedUrl": "https://jobs.lever.test/exampleco/aa98a938-45f5",
    "applyUrl": "https://jobs.lever.test/exampleco/aa98a938-45f5/apply",
    "description": "Full description body, must never be stored",
    "descriptionPlain": "Plain body, must never be stored",
    "lists": [{"content": "<div>sections</div>"}],
}]

ASHBY_FIXTURE = {"jobs": [
    {"id": "240d459b", "title": "Research Engineer", "department": "Research", "team": "Core",
     "employmentType": "FullTime", "location": "San Francisco", "isListed": True,
     "publishedAt": "2025-04-05T00:03:20.653+00:00",
     "address": {"postalAddress": {"addressLocality": "San Francisco", "addressRegion": "CA"}},
     "jobUrl": "https://jobs.ashby.test/exampleco/240d459b",
     "applyUrl": "https://jobs.ashby.test/exampleco/240d459b",
     "descriptionHtml": "<p>body</p>", "descriptionPlain": "body"},
    {"id": "unlisted1", "title": "Draft Role", "isListed": False,
     "jobUrl": "https://jobs.ashby.test/exampleco/unlisted1"},
]}


def test_greenhouse_normalizer_maps_metadata():
    rows = job_feeds.normalize_greenhouse(BOARD, GREENHOUSE_FIXTURE, "2026-10-24T00:00:00+00:00")
    assert len(rows) == 1
    row = rows[0]
    assert row["external_id"] == "4970739101"
    assert row["title"] == "Software Engineer, Platform"
    assert row["location"] == "Bengaluru, India"
    assert row["apply_url"].startswith("https://")
    assert row["posted_at"] == "2026-09-14"
    assert row["data_status"] == "published"
    assert "greenhouse" in row["attribution"]


def test_no_provider_body_text_survives_any_adapter():
    for provider, payload in (("greenhouse", GREENHOUSE_FIXTURE), ("lever", LEVER_FIXTURE),
                              ("ashby", ASHBY_FIXTURE)):
        board = {**BOARD, "provider": provider}
        for row in job_feeds.ADAPTERS[provider](board, payload, "2026-10-24T00:00:00+00:00"):
            assert not (job_feeds.FORBIDDEN_KEYS & set(row)), row
            assert not any("description" in key for key in row), row


def test_lever_keeps_provider_title_verbatim_and_epoch_date():
    rows = job_feeds.normalize_lever(BOARD, LEVER_FIXTURE, "2026-10-24T00:00:00+00:00")
    assert rows[0]["title"] == "software engineer", "must not silently re-case employer text"
    assert rows[0]["title_is_provider_lowercased"] is True
    assert rows[0]["posted_at"] == "2026-09-28"
    assert rows[0]["apply_url"] == "https://jobs.lever.test/exampleco/aa98a938-45f5"


def test_ashby_skips_unlisted_postings():
    rows = job_feeds.normalize_ashby(BOARD, ASHBY_FIXTURE, "2026-10-24T00:00:00+00:00")
    assert [row["external_id"] for row in rows] == ["240d459b"]


def test_adapter_refuses_a_record_carrying_body_text():
    with pytest.raises(ValueError, match="body text"):
        job_feeds._clean({"external_id": "1", "title": "T", "apply_url": "https://x.test",
                          "description": "leak"}, BOARD, "2026-10-24T00:00:00+00:00")


def test_deduplicate_collapses_same_board_and_id():
    rows = [{"board_id": "b", "external_id": "1"}, {"board_id": "b", "external_id": "1"},
            {"board_id": "b", "external_id": "2"}]
    kept, dropped = job_feeds.deduplicate(rows)
    assert [row["external_id"] for row in kept] == ["1", "2"] and dropped == 1


def test_board_snapshot_refuses_records_from_another_board(approved_db):
    with pytest.raises(ValueError, match="another board"):
        run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "wrongco", [job_row()], "pilot"))


def test_parse_reads_only_the_wildcard_group():
    rules = job_feeds.parse_robots(
        "User-agent: *" + LF + "Disallow: /embed/" + LF + "Crawl-delay: 2" + LF +
        "Allow: /jobs" + LF + "User-agent: PacioBot" + LF + "Disallow: /" + LF)
    assert rules["disallow"] == ["/embed/"] and rules["allow"] == ["/jobs"]
    assert rules["crawl_delay"] == 2.0


def test_longest_prefix_wins_and_bare_disallow_root_blocks_everything():
    assert job_feeds.path_allowed({"allow": ["/v1/boards"], "disallow": ["/"]}, "/v1/boards/x/jobs")
    assert not job_feeds.path_allowed({"allow": [], "disallow": ["/"]}, "/anything")
    assert job_feeds.path_allowed({"allow": [], "disallow": ["/embed/"]}, "/v1/boards/groww/jobs")
    assert not job_feeds.path_allowed({"allow": [], "disallow": ["/embed/"]}, "/embed/jobs")


def test_robots_policy_refuses_when_the_policy_file_is_unreadable(monkeypatch):
    """An API host that answers 401 for robots.txt is not an invitation; unknown means refusal."""
    job_feeds.reset_robots_cache()
    calls = []

    def fake_urlopen(request, timeout=None):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(job_feeds.urllib.request, "urlopen", fake_urlopen)
    policy = job_feeds.robots_policy("https://api.example.test/posting-api/job-board/x")
    assert policy["state"] == "unreadable" and policy["allowed"] is False
    assert policy["origin"] == "https://api.example.test"
    # cached: a second call for the same host makes no further request
    job_feeds.robots_policy("https://api.example.test/other")
    assert len(calls) == 1
    job_feeds.reset_robots_cache()


def test_feed_blocked_by_robots_never_makes_a_data_request(monkeypatch):
    job_feeds.reset_robots_cache()
    urls = []

    def fake_urlopen(request, timeout=None):
        url = request.full_url
        urls.append(url)
        if url.endswith("/robots.txt"):
            return _Response("User-agent: *" + LF + "Disallow: /boards/" + LF)
        raise AssertionError("the feed must not be fetched once robots.txt refuses")

    monkeypatch.setattr(job_feeds.urllib.request, "urlopen", fake_urlopen)
    result = job_feeds.fetch_board(BOARD)
    assert result["ok"] is False and "robots.txt" in result["error"]
    assert urls == ["https://example.test/robots.txt"]
    job_feeds.reset_robots_cache()


class _Response:
    """Minimal stand-in for a urllib response."""

    def __init__(self, body: str):
        self._body = body.encode("utf-8")
        self.status = 200
        self.headers = {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_board_reports_failure_instead_of_raising():
    result = job_feeds.fetch_board({**BOARD, "feed_url": "http://127.0.0.1:1/unreachable"})
    assert result["ok"] is False and result["records"] == [] and result["error"]


def test_fetch_board_rejects_unknown_provider():
    result = job_feeds.fetch_board({**BOARD, "provider": "slickdeals"})
    assert result["ok"] is False and "no adapter" in result["error"]


@pytest.fixture()
def approved_db():
    db = MemoryDB()
    run(data_import.register_source(db, {
        "source_id": "SRC-ATS", "name": "Employer-hosted boards (pilot)",
        "commercial_verdict": "APPROVED_WITH_LIMITATIONS", "licence": "public employer feed",
        "url": "https://example.test", "limitations": "metadata and canonical link only"}))
    return db


def job_row(external_id="1", title="Software Engineer"):
    return {"source_url": "https://example.test/feed", "retrieved_at": "2026-10-24T00:00:00+00:00",
            "board_id": "exampleco", "external_id": external_id, "title": title,
            "company": "ExampleCo", "apply_url": f"https://example.test/jobs/{external_id}",
            "posted_at": "2026-09-14", "data_status": "published"}


def test_polling_an_unchanged_posting_is_not_a_content_change(approved_db):
    """`retrieved_at` and `last_seen_at` are volatile provenance, not substance."""
    first = run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "exampleco",
                                                 [job_row()], "pilot"))
    assert first["counts"] == {"new": 1, "updated": 0, "unchanged": 0}
    second = run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "exampleco",
                                                 [job_row()], "pilot"))
    assert second["counts"] == {"new": 0, "updated": 0, "unchanged": 1}


def test_renaming_a_posting_is_a_content_change(approved_db):
    run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "exampleco", [job_row()], "pilot"))
    second = run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "exampleco",
                                                 [job_row(title="Staff Engineer")], "pilot"))
    assert second["counts"] == {"new": 0, "updated": 1, "unchanged": 0}


def test_visibility_lifecycle_absent_then_expired_then_reappeared(approved_db):
    run(job_feeds.import_board_snapshot(approved_db, "SRC-ATS", "exampleco",
                                        [job_row("1"), job_row("2")], "pilot"))
    day1 = "2026-10-24T00:00:00+00:00"
    summary = run(job_feeds.reconcile_visibility(approved_db, ["exampleco"], {"exampleco": {"1"}},
                                                 now=day1))
    assert summary["newly_absent"] == 1 and summary["expired"] == 0
    row2 = run(approved_db.job_postings.find_one({"external_id": "2"}, {"_id": 0}))
    assert row2["is_active"] is False and row2["absent_since"] == day1

    later = "2026-11-20T00:00:00+00:00"  # 27 days on, past the 14-day grace period
    summary = run(job_feeds.reconcile_visibility(approved_db, ["exampleco"], {"exampleco": {"1"}},
                                                 now=later))
    assert summary["expired"] == 1
    row2 = run(approved_db.job_postings.find_one({"external_id": "2"}, {"_id": 0}))
    assert row2["expired"] is True and row2["is_active"] is False

    reopened = run(job_feeds.reconcile_visibility(approved_db, ["exampleco"],
                                                  {"exampleco": {"1", "2"}}, now=later))
    assert reopened["reappeared"] == 1
    row2 = run(approved_db.job_postings.find_one({"external_id": "2"}, {"_id": 0}))
    assert row2["is_active"] is True and not row2.get("expired")
