"""Pacio must never claim that learner code was executed or graded.

Pins the 2026-10-24 defect: `/api/me/dsa/submissions/*` used to invent "Accepted", fake
"Sample 1 / Sample 2 / Hidden edge" pass flags and fabricated runtime/memory numbers from a token
count, and a submission could therefore mark a problem solved and set mastery to 88.

Run:  .venv/Scripts/python.exe -m pytest backend/tests/test_dsa_grading_honesty.py -q
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

os.environ["MONGO_URL"] = ""
os.environ["DB_NAME"] = "pacio_test_memory"
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-used-in-production")
# Seed the in-memory demo tenant with the password this suite expects, so it passes both
# standalone and inside scripts/release_gate.sh.
os.environ["DEFAULT_DEMO_PASSWORD"] = "demo-password-for-tests"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402

DEMO_PASSWORD = "demo-password-for-tests"


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(scope="module")
def student_token(client):
    res = client.post("/api/auth/login", json={"email": "student@kmit.in", "password": DEMO_PASSWORD})
    assert res.status_code == 200, res.text[:200]
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def any_question_id(client):  # depends on client so app startup has seeded the catalogue
    row = run(server.db.dsa_questions.find_one({}, {"_id": 0}))
    assert row, "the in-memory store must have seeded the DSA catalogue"
    return row["question_id"]


def test_question_list_reports_gradability_from_the_spec_file(client, student_token):
    """A database seeded before the harness must not keep advertising drafts as gradable."""
    res = client.get("/api/dsa/questions", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, res.text[:200]
    body = res.json()
    gradable = [row for row in body["questions"] if row["gradable"]]
    assert len(gradable) == 20, "gradable must come from the harness, not from the seed"
    assert body["gradable_total"] == 20
    assert all(row["spec_status"] == "validated" for row in gradable)
    assert all(row["spec_status"] == "draft" for row in body["questions"] if not row["gradable"])


def test_static_review_is_honest_about_not_running_code(any_question_id):
    question = run(server.db.dsa_questions.find_one({"question_id": any_question_id}, {"_id": 0}))
    review = server._static_code_review(question, "python",
                                        "def solve(nums):\n    return sorted(nums)\n")
    assert review["executed"] is False
    assert review["graded"] is False
    assert review["status"] == "Not executed"
    assert "test_cases" not in review
    assert "runtime_ms" not in review and "memory_kb" not in review
    assert "passed" not in review and "total" not in review
    assert "nothing here is a correctness verdict" in review["note"]
    assert any(signal["met"] for signal in review["signals"]), "the review must still say something useful"


def test_empty_submission_is_not_reported_as_a_failure(any_question_id):
    review = server._static_code_review({"question_id": any_question_id}, "python", "   ")
    assert review["signals"] == [] and review["executed"] is False
    assert review["note"] == "No code was submitted, so nothing was reviewed."


def test_draft_questions_say_they_cannot_be_graded_yet():
    draft = run(server.db.dsa_questions.find_one({"gradable": False}, {"_id": 0}))
    if not draft:
        pytest.skip("no ungradable question seeded")
    review = server._static_code_review(draft, "python", "def f():\n    return 1\n")
    assert review["auto_gradable"] is False
    assert "no validated test specification" in review["note"]


def test_submitting_code_does_not_mark_the_problem_solved(client, student_token, any_question_id):
    before = run(server.db.dsa_question_progress.find_one(
        {"question_id": any_question_id, "student_id": {"$exists": True}}, {"_id": 0}))
    res = client.post("/api/me/dsa/submissions/submit",
                      json={"question_id": any_question_id, "language": "python",
                            "code": "def solve(nums):\n    return sorted(nums)\n"},
                      headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, res.text[:300]
    record = res.json()
    assert record["status"] == "Not executed"
    assert record["graded"] is False and record["executed"] is False
    assert record["result"]["kind"] == "static_review"

    stored = run(server.db.dsa_question_progress.find_one(
        {"question_id": any_question_id, "student_id": record["student_id"]}, {"_id": 0}))
    assert stored is not None
    assert stored["solved"] is False, "a non-executed submission cannot prove a problem was solved"
    assert stored["attempted"] is True
    assert stored["mastery"] != 88, "mastery must not be granted by a token-count heuristic"
    assert stored.get("best_submission_id") is None or stored["best_submission_id"] == (before or {}).get("best_submission_id")


def test_running_code_is_recorded_as_a_run_not_a_verdict(client, student_token, any_question_id):
    res = client.post("/api/me/dsa/submissions/run",
                      json={"question_id": any_question_id, "language": "python",
                            "code": "def solve(nums):\n    return sorted(nums)\n",
                            "custom_input": "3 1 2"},
                      headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, res.text[:300]
    result = res.json()["result"]
    assert result["status"] == "Not executed" and result["graded"] is False
    assert "never executed" in result["output"], "custom input must not look like it was run"
