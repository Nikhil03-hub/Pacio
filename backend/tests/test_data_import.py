"""Import-pipeline safety tests: approval, provenance, PII, idempotency, rollback."""
from __future__ import annotations

import asyncio
import pathlib
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import pytest  # noqa: E402

import data_import  # noqa: E402
from memory_db import MemoryDB  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def source(status="APPROVED"):
    return {"source_id": "SRC-TEST", "name": "Test source", "commercial_verdict": status,
            "licence": "test", "url": "https://example.com/data"}


def institution(official_id="A1", name="Test Institute", **overrides):
    record = {"source_id": "SRC-TEST", "source_url": "https://example.com/a1",
              "retrieved_at": "2026-10-24T00:00:00Z", "official_id": official_id,
              "name": name, "data_status": "published", "state": "Telangana"}
    record.update(overrides)
    return record


@pytest.fixture()
def db():
    return MemoryDB()


def test_unregistered_source_is_refused(db):
    with pytest.raises(PermissionError):
        run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))


def test_rejected_source_is_refused(db):
    run(data_import.register_source(db, source("REJECTED")))
    with pytest.raises(PermissionError):
        run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))


def test_approved_with_limitations_is_allowed(db):
    run(data_import.register_source(db, source("APPROVED_WITH_LIMITATIONS")))
    report = run(data_import.dry_run(db, "institutions", [institution()], "SRC-TEST"))
    assert report["new"] == 1


def test_missing_provenance_is_invalid(db):
    run(data_import.register_source(db, source()))
    bad = institution()
    del bad["source_url"]
    report = run(data_import.dry_run(db, "institutions", [bad], "SRC-TEST"))
    assert report["new"] == 0 and report["invalid"]


def test_personal_data_is_rejected(db):
    run(data_import.register_source(db, source()))
    report = run(data_import.dry_run(db, "institutions", [institution(email="a@b.c")], "SRC-TEST"))
    assert report["invalid"], "PII fields must be refused"


def test_dry_run_writes_nothing(db):
    run(data_import.register_source(db, source()))
    run(data_import.dry_run(db, "institutions", [institution()], "SRC-TEST"))
    assert run(db.institutions_public.count_documents({})) == 0


def test_import_is_idempotent(db):
    run(data_import.register_source(db, source()))
    first = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    assert first["counts"] == {"new": 1, "updated": 0, "unchanged": 0}
    second = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    assert second["counts"] == {"new": 0, "updated": 0, "unchanged": 1}
    assert run(db.institutions_public.count_documents({})) == 1


def test_changed_record_is_updated(db):
    run(data_import.register_source(db, source()))
    run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    report = run(data_import.import_records(db, "institutions",
                                            [institution(name="Renamed Institute")], "SRC-TEST", "tester"))
    assert report["counts"] == {"new": 0, "updated": 1, "unchanged": 0}
    stored = run(db.institutions_public.find_one({"stable_key": "SRC-TEST:A1"}, {"_id": 0}))
    assert stored["name"] == "Renamed Institute"


def test_duplicate_stable_key_in_one_batch_is_refused(db):
    run(data_import.register_source(db, source()))
    with pytest.raises(ValueError):
        run(data_import.import_records(db, "institutions",
                                       [institution("A1"), institution("A1", name="Other")],
                                       "SRC-TEST", "tester"))
    assert run(db.institutions_public.count_documents({})) == 0


def test_rollback_deletes_only_that_batch(db):
    run(data_import.register_source(db, source()))
    batch_a = run(data_import.import_records(db, "institutions",
                                             [institution("A1"), institution("A2")], "SRC-TEST", "tester"))
    batch_b = run(data_import.import_records(db, "institutions", [institution("B1")], "SRC-TEST", "tester"))
    result = run(data_import.rollback_batch(db, batch_a["batch_id"]))
    assert result["deleted"] == 2
    remaining = run(db.institutions_public.find({}, {"_id": 0, "stable_key": 1}).to_list(10))
    assert [row["stable_key"] for row in remaining] == ["SRC-TEST:B1"]
    assert run(db.institutions_public.count_documents({"import_batch_id": batch_b["batch_id"]})) == 1


def test_rollback_of_update_restores_pre_image(db):
    run(data_import.register_source(db, source()))
    run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    batch_b = run(data_import.import_records(db, "institutions",
                                             [institution(name="Wrong Name")], "SRC-TEST", "tester"))
    result = run(data_import.rollback_batch(db, batch_b["batch_id"]))
    assert result["deleted"] == 0 and result["restored"] == 1
    stored = run(db.institutions_public.find_one({"stable_key": "SRC-TEST:A1"}, {"_id": 0}))
    assert stored["name"] == "Test Institute", "an update rollback must not delete the pre-existing record"


def test_rollback_refuses_when_a_later_batch_modified_the_record(db):
    run(data_import.register_source(db, source()))
    batch_a = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    run(data_import.import_records(db, "institutions", [institution(name="Changed later")],
                                   "SRC-TEST", "tester"))
    result = run(data_import.rollback_batch(db, batch_a["batch_id"]))
    assert result["status"] == "blocked_conflict"
    assert result["deleted"] == 0 and result["restored"] == 0
    stored = run(db.institutions_public.find_one({"stable_key": "SRC-TEST:A1"}, {"_id": 0}))
    assert stored["name"] == "Changed later", "a blocked rollback must leave data untouched"
    assert run(db.import_runs.find_one({"batch_id": batch_a["batch_id"]}, {"_id": 0}))["status"] == "completed"


def test_forced_rollback_overrides_conflict(db):
    run(data_import.register_source(db, source()))
    batch_a = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    run(data_import.import_records(db, "institutions", [institution(name="Changed later")],
                                   "SRC-TEST", "tester"))
    result = run(data_import.rollback_batch(db, batch_a["batch_id"], force=True))
    assert result["status"] == "rolled_back" and result["forced"] is True
    assert run(db.institutions_public.count_documents({})) == 0


def test_rollback_is_idempotent(db):
    run(data_import.register_source(db, source()))
    batch = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    assert run(data_import.rollback_batch(db, batch["batch_id"]))["deleted"] == 1
    again = run(data_import.rollback_batch(db, batch["batch_id"]))
    assert again["status"] == "already_rolled_back" and again["deleted"] == 0


def test_rollback_reports_which_batch_created_a_record(db):
    run(data_import.register_source(db, source()))
    batch_a = run(data_import.import_records(db, "institutions", [institution()], "SRC-TEST", "tester"))
    run(data_import.import_records(db, "institutions", [institution(name="Renamed")], "SRC-TEST", "tester"))
    stored = run(db.institutions_public.find_one({"stable_key": "SRC-TEST:A1"}, {"_id": 0}))
    assert stored["first_import_batch_id"] == batch_a["batch_id"], "creation batch must survive updates"


def test_placement_requires_definition_and_metric(db):
    run(data_import.register_source(db, source()))
    record = {"source_id": "SRC-TEST", "source_url": "https://example.com/p",
              "retrieved_at": "2026-10-24T00:00:00Z", "published_on": "2024",
              "institution_id": "inst_x", "academic_year": "2023-24",
              "metric": "median_ctc_lpa", "value": 6.5, "definition": "", "data_status": "published"}
    report = run(data_import.dry_run(db, "placement_stats", [record], "SRC-TEST"))
    assert report["invalid"]


def test_job_requires_canonical_http_apply_url(db):
    run(data_import.register_source(db, source()))
    record = {"source_id": "SRC-TEST", "source_url": "https://example.com/job",
              "retrieved_at": "2026-10-24T00:00:00Z", "board_id": "cred",
              "external_id": "123", "title": "Engineer", "company": "CRED",
              "apply_url": "javascript:alert(1)", "posted_at": "2026-10-20", "data_status": "published"}
    report = run(data_import.dry_run(db, "jobs", [record], "SRC-TEST"))
    assert report["invalid"], "non-http apply_url must be refused"


def test_stable_keys_are_domain_specific(db):
    assert data_import.DOMAINS["institutions"]["stable_key"]({"source_id": "S", "official_id": "A"}) == "S:A"
    assert data_import.DOMAINS["jobs"]["stable_key"](
        {"source_id": "S", "board_id": "b", "external_id": "e"}) == "S:b:e"
