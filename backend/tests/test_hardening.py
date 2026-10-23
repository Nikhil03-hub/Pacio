"""Security and multi-tenancy regressions for Pacio / Campus Intelligence.

These run against the app in-process (FastAPI TestClient) with the in-memory data
layer, so they are reproducible on any machine without a deployed backend. Each test
pins a defect that was present in the June 2026 hackathon build.

Run:  .venv/Scripts/python.exe -m pytest backend/tests/test_hardening.py -v
"""
from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

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

import asyncio

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402

def db(coro):
    """MemoryCollection/Motor helpers are coroutines; awaiting them keeps tests honest."""
    return asyncio.run(coro)


DEMO_PASSWORD = "demo-password-for-tests"
ADMIN_PASSWORD = "admin-password-for-tests"


@pytest.fixture(scope="module")
def client():
    # TestClient keeps a cookie jar, and login sets a session cookie, so this client
    # must not be used to assert "anonymous" behaviour.
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(scope="module")
def anon_client():
    with TestClient(server.app, cookies={}) as c:
        yield c


def login(client, email: str, password: str = DEMO_PASSWORD) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"login failed for {email}: {res.text[:200]}"
    return res.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def tokens(client):
    return {
        "tpo": login(client, "tpo@kmit.in"),
        "student": login(client, "student@kmit.in"),
        "institution_admin": login(client, "institution@kmit.in"),
        "faculty": login(client, "faculty@kmit.in"),
        "recruiter": login(client, "recruiter@amazon.com"),
        "admin": login(client, "platform-admin@example.com", ADMIN_PASSWORD),
    }


# ---------------------------------------------------------------- auth surface

def test_login_failure_does_not_reveal_account_existence(client):
    bad_password = client.post("/api/auth/login", json={"email": "tpo@kmit.in", "password": "wrong"})
    missing_user = client.post("/api/auth/login", json={"email": "ghost.person@example.com", "password": "whatever"})
    assert bad_password.status_code == missing_user.status_code == 401
    assert bad_password.json()["detail"] == missing_user.json()["detail"]


def test_forgot_password_is_not_an_account_enumerator(client):
    unknown = client.post("/api/auth/forgot-password", json={"email": "nobody.person@example.com"})
    known = client.post("/api/auth/forgot-password", json={"email": "tpo@kmit.in"})
    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()


def test_public_registration_does_not_confirm_duplicate_emails(client):
    first = client.post("/api/auth/register", json={
        "name": "Probe One", "email": "duplicate-probe@example.com",
        "college_name": "Probe College", "affiliated_university": "Probe University",
        "department": "CSE", "partnership_type": "CRT",
    })
    second = client.post("/api/auth/register", json={
        "name": "Probe Two", "email": "duplicate-probe@example.com",
        "college_name": "Probe College", "affiliated_university": "Probe University",
        "department": "CSE", "partnership_type": "CRT",
    })
    assert first.status_code == 200
    assert second.status_code == 200
    assert "already" not in second.text.lower()


def test_google_callback_cannot_be_completed_without_state(client, monkeypatch):
    monkeypatch.setattr(server, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(server, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    res = client.get("/api/auth/google/callback?code=attacker-code")
    assert res.status_code == 400
    assert "state" in res.text.lower()


def test_legacy_emergent_session_auth_is_disabled(client):
    res = client.post("/api/auth/session", json={"session_id": "anything"})
    assert res.status_code == 410


def test_reset_token_is_stored_as_a_digest_not_plaintext(client):
    client.post("/api/auth/forgot-password", json={"email": "tpo@kmit.in"})
    stored = db(server.db.password_reset_tokens.find_one({"email": "tpo@kmit.in"}))
    assert stored, "a reset request must persist a token"
    digest = stored.get("token_hash", "")
    assert len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest)
    assert "token" not in stored, "the raw reset token must never be stored"


def test_password_reset_rejects_weak_password_and_revokes_sessions(client, tokens):
    email = "faculty@kmit.in"
    old_token = tokens["faculty"]
    raw = "fresh-single-use-reset-secret"
    db(server.db.password_reset_tokens.update_one(
        {"email": email},
        {"$set": {
            "token_hash": hashlib.sha256(raw.encode()).hexdigest(),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        }},
        upsert=True,
    ))

    too_short = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "short"})
    assert too_short.status_code == 422
    assert client.get("/api/auth/me", headers=auth(old_token)).status_code == 200

    ok = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "correct-horse-battery-9"})
    assert ok.status_code == 200

    assert client.get("/api/auth/me", headers=auth(old_token)).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD}).status_code == 401
    replay = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "another-long-password"})
    assert replay.status_code == 400

    # Restore the demo credential so later tests keep their fixture password.
    db(server.db.users.update_one(
        {"email": email},
        {"$set": {"password_hash": server.hash_password(DEMO_PASSWORD)}},
    ))
    tokens["faculty"] = login(client, email)


# ------------------------------------------------------- tenant and role scoping

def test_mou_documents_are_limited_to_college_leadership(client, tokens):
    for role in ("student", "faculty", "recruiter"):
        assert client.get("/api/mou", headers=auth(tokens[role])).status_code == 403
        assert client.get("/api/mou/download", headers=auth(tokens[role])).status_code == 403
    assert client.get("/api/mou", headers=auth(tokens["tpo"])).status_code in (200, 404)


def test_student_cannot_enumerate_the_class_roster(client, tokens):
    res = client.get("/api/students?limit=200", headers=auth(tokens["student"]))
    assert res.status_code == 200
    items = res.json()["items"]
    me = client.get("/api/auth/me", headers=auth(tokens["student"])).json()
    assert all(item["student_id"] == me["student_id"] for item in items)


def test_student_cannot_open_a_peer_record(client, tokens):
    peers = client.get("/api/students?limit=50", headers=auth(tokens["tpo"])).json()["items"]
    me = client.get("/api/auth/me", headers=auth(tokens["student"])).json()
    other = next(p for p in peers if p["student_id"] != me.get("student_id"))
    assert client.get(f"/api/students/{other['student_id']}", headers=auth(tokens["student"])).status_code == 403
    assert client.get(f"/api/students/{other['student_id']}", headers=auth(tokens["tpo"])).status_code == 200


def test_revenue_entry_is_pinned_to_the_callers_institution(client, tokens):
    res = client.post(
        "/api/revenue/share",
        headers=auth(tokens["institution_admin"]),
        json={"institution_id": "inst_of_another_college", "amount_inr": 50000,
              "period": "2026-Q1", "type": "CRT"},
    )
    assert res.status_code == 200
    assert res.json()["institution_id"] == "inst_kmit"


def test_tpo_may_record_revenue_share(client, tokens):
    res = client.post(
        "/api/revenue/share",
        headers=auth(tokens["tpo"]),
        json={"amount_inr": 25000, "period": "2026-Q2", "type": "FDP"},
    )
    assert res.status_code == 200
    assert res.json()["institution_id"] == "inst_kmit"


def test_negative_or_absurd_amounts_are_rejected(client, tokens):
    for amount in (0, -5, 10_000_000_001):
        res = client.post(
            "/api/revenue/share",
            headers=auth(tokens["tpo"]),
            json={"amount_inr": amount, "period": "2026-Q3", "type": "CRT"},
        )
        assert res.status_code == 422, f"amount {amount} was accepted"


def test_account_without_an_institution_cannot_see_a_default_tenant(client):
    """The old code silently fell back to inst_kmit, exposing one college's data."""
    orphan = {"user_id": "user_orphan_probe", "email": "orphan.unscoped@example.com", "name": "Orphan",
              "role": "tpo", "institution_id": None, "department": None, "approved": True,
              "password_hash": server.hash_password(DEMO_PASSWORD),
              "created_at": datetime.now(timezone.utc).isoformat()}
    db(server.db.users.insert_one(orphan))
    token = login(client, "orphan.unscoped@example.com")
    res = client.get("/api/mou", headers=auth(token))
    assert res.status_code == 403
    assert "institution" in res.json()["detail"].lower()


def test_roster_search_escapes_regex_metacharacters(client, tokens):
    res = client.get(r'/api/students?q=(a+)+$', headers=auth(tokens["tpo"]))
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_roster_limit_is_clamped(client, tokens):
    res = client.get("/api/students?limit=999999", headers=auth(tokens["tpo"]))
    assert res.status_code == 200
    assert len(res.json()["items"]) <= 1000


# ------------------------------------------------------------------ uploads

def test_mou_upload_rejects_executable_and_empty_files(client, tokens):
    bad = client.post(
        "/api/mou/upload",
        headers=auth(tokens["tpo"]),
        files={"file": ("payload.exe", b"MZ\x90\x00", "application/x-msdownload")},
        data={"expires_on": "2027-12-31", "partnership_type": "CRT"},
    )
    assert bad.status_code == 415
    empty = client.post(
        "/api/mou/upload",
        headers=auth(tokens["tpo"]),
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"expires_on": "2027-12-31", "partnership_type": "CRT"},
    )
    assert empty.status_code == 400


def test_mou_upload_strips_path_components_from_filename(client, tokens):
    res = client.post(
        "/api/mou/upload",
        headers=auth(tokens["tpo"]),
        files={"file": ("..\\..\\evil\\contract.pdf", b"%PDF-1.4 test bytes", "application/pdf")},
        data={"expires_on": "2027-12-31", "partnership_type": "CRT"},
    )
    assert res.status_code == 200
    assert "/" not in res.json()["document_name"] and "\\" not in res.json()["document_name"]


def test_mou_upload_is_rejected_for_students(client, tokens):
    res = client.post(
        "/api/mou/upload",
        headers=auth(tokens["student"]),
        files={"file": ("contract.pdf", b"%PDF-1.4", "application/pdf")},
        data={"expires_on": "2027-12-31", "partnership_type": "CRT"},
    )
    assert res.status_code == 403


# ------------------------------------------------------------- invitations

def test_invite_no_longer_hands_out_a_shared_password(client, tokens):
    res = client.post(
        "/api/invite",
        headers=auth(tokens["tpo"]),
        json={"name": "HOD Mechanics", "email": "hod.mech@kmit.in",
              "role": "faculty", "department": "MECH"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "temp_password" not in body
    assert body["status"] == "invited"
    created = db(server.db.users.find_one({"email": "hod.mech@kmit.in"}))
    assert created and not created.get("password_hash")
    assert created["role"] == "faculty" and created["institution_id"] == "inst_kmit"


def test_invite_of_an_existing_pending_user_updates_scope(client, tokens):
    db(server.db.users.insert_one({
        "user_id": "user_pending_probe", "email": "pending.probe@kmit.in", "name": "Pending Probe",
        "role": None, "institution_id": None, "department": None, "approved": False,
        "password_hash": None, "picture": None, "created_at": datetime.now(timezone.utc).isoformat(),
    }))
    res = client.post(
        "/api/invite",
        headers=auth(tokens["tpo"]),
        json={"name": "Pending Probe", "email": "pending.probe@kmit.in", "role": "tpo"},
    )
    assert res.status_code == 200
    updated = db(server.db.users.find_one({"email": "pending.probe@kmit.in"}))
    assert updated["approved"] is True and updated["role"] == "tpo"


# -------------------------------------------------------------- health surface

def test_deep_health_requires_platform_admin(anon_client, client, tokens):
    assert anon_client.get("/api/health/deep").status_code == 401
    assert client.get("/api/health/deep", headers=auth(tokens["student"])).status_code == 403
    assert client.get("/api/health/deep", headers=auth(tokens["admin"])).status_code == 200


def test_liveness_probe_stays_public_and_minimal(anon_client):
    res = anon_client.get("/api/health")
    assert res.status_code == 200
    assert set(res.json()) == {"status", "service"}


def test_startup_creates_indexes_on_the_real_database(monkeypatch):
    """Index creation used to live only in the in-memory branch, so production Atlas
    never received the unique email index or the reset-token TTL."""
    calls: list[tuple] = []

    class FakeCollection:
        async def create_index(self, *args, **kwargs):
            calls.append((args, kwargs))

    class FakeDB:
        def __getattr__(self, name):
            return FakeCollection()

    async def fake_ping(*_a, **_k):
        return None

    monkeypatch.setattr(server, "db", FakeDB())
    import asyncio
    asyncio.run(server._ensure_indexes())
    names = {repr(a[0]) for a, _ in calls}
    assert repr("email") in names, "unique index on user email is required"
    assert repr("token_hash") in names, "reset tokens must be looked up by digest"
    ttl = [k for a, k in calls if a == ("expires_at",) and k.get("expireAfterSeconds") == 0]
    assert ttl, "password reset tokens must expire in the database, not only in app code"
