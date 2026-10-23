"""Real-MongoDB integration checks.

Skipped unless an explicit test database URI is supplied, because it writes to a database:

    PACIO_TEST_MONGO_URL=mongodb://127.0.0.1:27017 .venv/Scripts/python.exe \
        -m pytest backend/tests/test_mongo_integration.py -q -s

The suite creates a uniquely named database, verifies index creation and that API writes
land in MongoDB, then drops only that database. Run it in its own pytest invocation: the
other suites deliberately force the in-memory store.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

MONGO = os.environ.get("PACIO_TEST_MONGO_URL", "").strip()
DB_NAME = f"pacio_it_{uuid.uuid4().hex[:8]}"

os.environ["MONGO_URL"] = MONGO
os.environ["DB_NAME"] = DB_NAME
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["SEED_DEMO_USERS"] = "false"
os.environ["JWT_SECRET"] = "integration-test-secret"
os.environ["ADMIN_EMAIL"] = "integration-admin@example.com"
os.environ["ADMIN_PASSWORD"] = "integration-admin-password"
os.environ["APP_ENV"] = "test"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://testserver"
os.environ["PUBLIC_BASE_URL"] = "http://localhost:3000"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

pytestmark = pytest.mark.skipif(not MONGO, reason="set PACIO_TEST_MONGO_URL to run against a real MongoDB")

import server  # noqa: E402

ADMIN_PASSWORD = "integration-admin-password"


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(scope="module")
def raw_db():
    sync = MongoClient(MONGO, serverSelectionTimeoutMS=5000)
    yield sync[DB_NAME]
    sync.close()


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    sync = MongoClient(MONGO, serverSelectionTimeoutMS=5000)
    sync.drop_database(DB_NAME)  # only the uniquely named test database this module created
    sync.close()


def admin_token(client) -> str:
    res = client.post("/api/auth/login", json={"email": "integration-admin@example.com",
                                               "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_indexes_exist_in_mongodb(client, raw_db):
    users = raw_db.users.index_information()
    assert any(idx["key"] == [("email", 1)] and idx.get("unique") for idx in users.values())
    sessions = raw_db.user_sessions.index_information()
    assert any(idx["key"] == [("jwt_id", 1)] and idx.get("unique") for idx in sessions.values())
    tokens = raw_db.password_reset_tokens.index_information()
    assert any("expireAfterSeconds" in idx for idx in tokens.values()), "reset tokens need a TTL index"


def test_admin_bootstrap_is_written_to_mongodb(client, raw_db):
    doc = raw_db.users.find_one({"email": "integration-admin@example.com"})
    assert doc and doc["role"] == "super_admin"


def test_api_writes_persist_to_mongodb(client, raw_db):
    token = admin_token(client)
    res = client.post(
        "/api/certificates/issue",
        headers={"Authorization": f"Bearer {token}"},
        json={"cert_id": "ST-IT-PERSIST01", "student_name": "Mongo Probe",
              "program": "Integration", "institution_id": server.DEFAULT_INSTITUTION_ID},
    )
    assert res.status_code == 200, res.text

    stored = raw_db.certificates.find_one({"cert_id": "ST-IT-PERSIST01"})
    assert stored is not None, "write did not reach MongoDB"
    assert stored["student_name"] == "Mongo Probe"
    assert raw_db.user_sessions.count_documents({}) >= 1
