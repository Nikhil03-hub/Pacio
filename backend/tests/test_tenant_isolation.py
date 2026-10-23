"""Role and tenant authorisation matrix.

Builds a synthetic second college ("Tenant B") and exercises every role against routes
that expose rosters, individual students, resumes, applications, MOUs, files, reports,
payouts, analytics and exports. The seeded demo colleges act as "Tenant A".

Run:  .venv/Scripts/python.exe -m pytest backend/tests/test_tenant_isolation.py -q
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Force the in-memory store. A developer's backend/.env may point at a real database,
# and tests must never write synthetic tenants into it or depend on its prior state.
os.environ["MONGO_URL"] = ""
os.environ["DB_NAME"] = "pacio_test_memory"
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-used-in-production")
os.environ.setdefault("DB_NAME", "careeros")
os.environ.setdefault("SEED_DEMO_DATA", "true")
os.environ.setdefault("SEED_DEMO_USERS", "true")
os.environ.setdefault("DEFAULT_DEMO_PASSWORD", "demo-password-for-tests")
os.environ.setdefault("ADMIN_EMAIL", "platform-admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "admin-password-for-tests")
os.environ.setdefault("EMERGENT_AUTH_ENABLED", "false")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000,http://testserver")
os.environ.setdefault("PUBLIC_BASE_URL", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402

PASSWORD = "demo-password-for-tests"
ADMIN_PASSWORD = "admin-password-for-tests"
A = "inst_kmit"
B = "inst_tenant_b"


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(scope="module")
def tenancy(client):
    """Create a second institution with one user per role and a single student."""
    now = datetime.now(timezone.utc).isoformat()
    run(server.db.institutions.insert_one({
        "institution_id": B, "name": "Tenant B Institute", "short_name": "TBI",
        "type": "Engineering", "city": "Pune", "state": "Maharashtra",
        "affiliated_university": "Test University", "departments": ["ECE"],
        "approved": True, "created_at": now,
    }))
    run(server.db.students.insert_one({
        "student_id": "stu_tenant_b_0001", "institution_id": B, "name": "B Student",
        "roll_number": "TB001", "department": "ECE", "email": "b.student@example.com",
        "cgpa": 7.4, "placement": {"placed": False}, "created_at": now,
    }))
    run(server.db.students.insert_one({
        "student_id": "stu_tenant_b_0002", "institution_id": B, "name": "B Student Two",
        "roll_number": "TB002", "department": "ECE", "email": "b.student2@example.com",
        "cgpa": 8.1, "placement": {"placed": False}, "created_at": now,
    }))

    def make_user(email, role, institution_id, approved=True, student_id=None):
        doc = server._new_user(email=email, name=f"B {role}", role=role,
                               institution_id=institution_id, password=PASSWORD,
                               approved=approved, department="ECE")
        if student_id:
            doc["student_id"] = student_id
        run(server.db.users.insert_one(doc))

    make_user("b.tpo@example.com", "tpo", B)
    make_user("b.admin@example.com", "institution_admin", B)
    make_user("b.faculty@example.com", "faculty", B)
    make_user("b.student@example.com", "student", B, student_id="stu_tenant_b_0001")
    make_user("b.recruiter@example.com", "recruiter", B)
    make_user("b.pending@example.com", "tpo", B, approved=False)

    def token(email, password=PASSWORD):
        res = client.post("/api/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, f"login failed for {email}: {res.text[:200]}"
        return res.json()["access_token"]

    a_peers = client.get("/api/students?limit=50", headers=auth(token("tpo@kmit.in"))).json()["items"]
    a_student = next(s for s in a_peers if s["institution_id"] == A)
    return {
        "b_tpo": token("b.tpo@example.com"),
        "b_admin": token("b.admin@example.com"),
        "b_faculty": token("b.faculty@example.com"),
        "b_student": token("b.student@example.com"),
        "b_recruiter": token("b.recruiter@example.com"),
        "b_pending": token("b.pending@example.com"),
        "a_tpo": token("tpo@kmit.in"),
        "a_student_user": token("student@kmit.in"),
        "admin": token("platform-admin@example.com", ADMIN_PASSWORD),
        "a_student_record": a_student["student_id"],
        "b_student_record": "stu_tenant_b_0001",
        "b_peer_record": "stu_tenant_b_0002",
    }


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ rosters

def test_b_tpo_roster_contains_only_b_students(client, tenancy):
    res = client.get("/api/students?limit=200", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 200
    items = res.json()["items"]
    assert items, "tenant B roster should contain its own students"
    assert {i["institution_id"] for i in items} == {B}


def test_b_tpo_cannot_open_tenant_a_student(client, tenancy):
    res = client.get(f"/api/students/{tenancy['a_student_record']}", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 403


def test_a_student_cannot_open_tenant_b_student(client, tenancy):
    res = client.get(f"/api/students/{tenancy['b_student_record']}", headers=auth(tenancy["a_student_user"]))
    assert res.status_code == 403


def test_student_cannot_open_a_classmate_record(client, tenancy):
    peers = client.get("/api/students?limit=50", headers=auth(tenancy["a_tpo"])).json()["items"]
    me = client.get("/api/auth/me", headers=auth(tenancy["a_student_user"])).json()
    peer = next(p for p in peers if p["student_id"] != me["student_id"])
    assert client.get(f"/api/students/{peer['student_id']}", headers=auth(tenancy["a_student_user"])).status_code == 403


def test_b_faculty_is_limited_to_their_own_department(client, tenancy):
    res = client.get("/api/students?limit=200", headers=auth(tenancy["b_faculty"]))
    assert res.status_code == 200
    assert {i["department"] for i in res.json()["items"]} == {"ECE"}


# ------------------------------------------------------------------ documents

def test_b_tpo_cannot_read_tenant_a_mou_by_parameter(client, tenancy):
    res = client.get(f"/api/mou?institution_id={A}", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 403


def test_b_tpo_mou_upload_lands_in_tenant_b(client, tenancy):
    upload = client.post(
        "/api/mou/upload",
        headers=auth(tenancy["b_tpo"]),
        files={"file": ("tenant-b-contract.pdf", b"%PDF-1.4 tenant B", "application/pdf")},
        data={"expires_on": "2027-12-31", "partnership_type": "CRT"},
    )
    assert upload.status_code == 200, upload.text

    own = client.get("/api/mou", headers=auth(tenancy["b_tpo"]))
    assert own.status_code == 200 and own.json()["institution_id"] == B

    # Tenant A's MOU must not have been overwritten by tenant B's upload.
    other = client.get("/api/mou", headers=auth(tenancy["a_tpo"]))
    assert other.status_code == 200
    assert other.json()["institution_id"] == A
    assert other.json()["document_name"] != "tenant-b-contract.pdf"


def test_students_and_recruiters_cannot_read_mou_documents(client, tenancy):
    for role in ("b_student", "b_recruiter"):
        assert client.get("/api/mou", headers=auth(tenancy[role])).status_code == 403
        assert client.get("/api/mou/download", headers=auth(tenancy[role])).status_code == 403


def test_b_tpo_cannot_download_tenant_a_built_resume(client, tenancy):
    # Create a resume artefact owned by an A student, then try to read it as B staff.
    run(server.db.resume_versions.insert_one({
        "version_id": "rv_tenant_a_probe", "student_id": tenancy["a_student_record"],
        "user_id": "user_tenant_a_probe", "download_token": "tenant-a-token",
        "sections": {"summary": "probe"}, "created_at": datetime.now(timezone.utc).isoformat(),
    }))
    res = client.get("/api/me/resume/download/tenant-a-token.pdf", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 404


# ------------------------------------------------------------------ money

def test_b_admin_cannot_post_revenue_into_tenant_a(client, tenancy):
    res = client.post(
        "/api/revenue/share", headers=auth(tenancy["b_admin"]),
        json={"institution_id": A, "amount_inr": 125000, "period": "2026-Q4", "type": "CRT"},
    )
    assert res.status_code == 200
    assert res.json()["institution_id"] == B


def test_b_tpo_revenue_view_has_no_tenant_a_records(client, tenancy):
    res = client.get("/api/revenue/me", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 200
    assert all(r["institution_id"] == B for r in res.json().get("records", []))


# ------------------------------------------------------------------ analytics

def test_placements_overview_is_tenant_scoped(client, tenancy):
    b = client.get("/api/placements/overview", headers=auth(tenancy["b_tpo"]))
    assert b.status_code == 200
    assert b.json()["students_total"] == 2, b.json().get("students_total")
    # A global leak would report the entire platform roster, not tenant B's two students.
    assert run(server.db.students.count_documents({})) > 2


def test_dsa_and_ats_intelligence_are_tenant_scoped(client, tenancy):
    dsa = client.get("/api/dsa/intelligence", headers=auth(tenancy["b_tpo"]))
    ats = client.get("/api/ats/intelligence", headers=auth(tenancy["b_tpo"]))
    assert dsa.status_code == ats.status_code == 200
    dsa_ids = {row.get("institution_id") for row in dsa.json().get("leaderboard", []) if row.get("institution_id")}
    ats_ids = {row.get("institution_id") for row in ats.json().get("rows", []) if row.get("institution_id")}
    assert A not in dsa_ids and A not in ats_ids


def test_benchmarking_self_is_the_callers_tenant(client, tenancy):
    res = client.get("/api/benchmarking/partner", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 200
    assert res.json()["self"]["institution_id"] == B


def test_comm_log_is_tenant_scoped(client, tenancy):
    res = client.get("/api/comm-log", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 200
    assert all(row.get("institution_id") == B for row in res.json()["items"])


# ------------------------------------------------------------------ exports

def test_roster_export_is_staff_only(client, tenancy):
    for role in ("b_student", "b_recruiter"):
        assert client.get("/api/reports/students.csv", headers=auth(tenancy[role])).status_code == 403
    assert client.get("/api/reports/students.csv", headers=auth(tenancy["b_tpo"])).status_code == 200


def test_roster_export_contains_only_the_callers_tenant(client, tenancy):
    res = client.get("/api/reports/students.csv", headers=auth(tenancy["b_tpo"]))
    assert res.status_code == 200
    body = res.text
    assert "B Student" in body
    assert "Aarav" not in body  # an A-tenant student


# ------------------------------------------------------------------ approval

def test_pending_account_is_blocked_from_data_but_can_read_its_identity(client, tenancy):
    me = client.get("/api/auth/me", headers=auth(tenancy["b_pending"]))
    assert me.status_code == 200
    assert me.json()["approved"] is False

    for path in ("/api/students", "/api/dsa/intelligence", "/api/mou", "/api/reports/students.csv"):
        res = client.get(path, headers=auth(tenancy["b_pending"]))
        assert res.status_code == 403, f"{path} leaked to a pending account ({res.status_code})"


# ------------------------------------------------------------------ platform admin

def test_super_admin_retains_global_read_access(client, tenancy):
    insts = client.get("/api/institutions", headers=auth(tenancy["admin"]))
    assert insts.status_code == 200
    ids = {i["institution_id"] for i in insts.json()["items"]}
    assert {A, B}.issubset(ids)

    # The admin sees every tenant; search keeps the response bounded (the demo seed alone
    # has 5,450 students, and the roster endpoint caps at 1000 rows).
    for needle, expected in (("Aarav", A), ("B Student", B)):
        roster = client.get(f"/api/students?q={needle}", headers=auth(tenancy["admin"]))
        assert roster.status_code == 200
        assert expected in {s["institution_id"] for s in roster.json()["items"]}


def test_super_admin_can_target_a_named_tenant_for_mou(client, tenancy):
    res = client.get(f"/api/mou?institution_id={B}", headers=auth(tenancy["admin"]))
    assert res.status_code in (200, 404)
