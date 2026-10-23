"""CareerOS v2.1 backend tests — adds PDF/CSV reports, interview scheduling,
team invites, GridFS MOU round-trip, and faculty-scoped DSA."""
import io
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://career-os-nexus.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
PWD = "careeros2026"

DEMO = {
    "admin": "admin@careeros.app",
    "tpo": "tpo@kmit.in",
    "faculty": "faculty@kmit.in",
    "student": "student@kmit.in",
}


def _login(email, password=PWD):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email} failed: {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_s():
    return _login(DEMO["admin"])


@pytest.fixture(scope="module")
def tpo_s():
    return _login(DEMO["tpo"])


@pytest.fixture(scope="module")
def faculty_s():
    return _login(DEMO["faculty"])


@pytest.fixture(scope="module")
def student_s():
    return _login(DEMO["student"])


# ---------- PDF reports ----------
class TestReportsPDF:
    def test_placement_pdf(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/placement.pdf")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("application/pdf")
        assert r.content[:4] == b"%PDF"
        assert len(r.content) >= 3 * 1024, f"PDF too small: {len(r.content)} bytes"

    def test_training_pdf(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/training.pdf")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("application/pdf")
        assert r.content[:4] == b"%PDF"
        assert len(r.content) >= 1024

    def test_department_pdf(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/department.pdf")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("application/pdf")
        assert r.content[:4] == b"%PDF"
        assert len(r.content) >= 1024


# ---------- CSV reports ----------
class TestReportsCSV:
    def test_students_csv(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/students.csv")
        assert r.status_code == 200, r.text
        assert "text/csv" in r.headers["content-type"]
        text = r.text
        lines = [l for l in text.splitlines() if l.strip()]
        assert len(lines) >= 101, f"expected >100 rows, got {len(lines)}"
        header = lines[0].lower()
        assert "roll_number" in header and "name" in header and "department" in header

    def test_applications_csv(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/applications.csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        lines = [l for l in r.text.splitlines() if l.strip()]
        assert len(lines) >= 2  # header + at least 1 row

    def test_placements_csv(self, tpo_s):
        r = tpo_s.get(f"{API}/reports/placements.csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        header = r.text.splitlines()[0].lower()
        assert "academic_year" in header


# ---------- Interview scheduling ----------
class TestInterviewSchedule:
    @pytest.fixture(scope="class")
    def scheduled(self, tpo_s, student_s):
        # Schedule interview for the DEMO student so student-scope test can re-login
        me = student_s.get(f"{API}/auth/me").json()
        sid = me["student_id"]
        payload = {
            "student_id": sid,
            "company": "TEST_Acme",
            "role": "SDE-1",
            "type": "Technical",
            "starts_at": "2026-03-10T10:00:00Z",
            "duration_min": 45,
            "location": "Zoom",
        }
        r = tpo_s.post(f"{API}/interviews/schedule", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "interview_id" in body and "starts_at" in body
        return {"interview_id": body["interview_id"], "student_id": sid}

    def test_schedule_creates_record(self, scheduled):
        assert scheduled["interview_id"].startswith("isch_")

    def test_tpo_lists_scheduled(self, tpo_s, scheduled):
        r = tpo_s.get(f"{API}/interviews/schedule")
        assert r.status_code == 200
        ids = [it["interview_id"] for it in r.json()["items"]]
        assert scheduled["interview_id"] in ids

    def test_student_scope(self, student_s, scheduled):
        r = student_s.get(f"{API}/interviews/schedule")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        assert any(it["interview_id"] == scheduled["interview_id"] for it in items)

    def test_notification_logged(self, admin_s, scheduled):
        log = admin_s.get(f"{API}/admin/notifications").json()["items"]
        rows = [n for n in log if n.get("event") == "interview_scheduled"]
        assert len(rows) > 0
        channels = {r.get("channel") for r in rows}
        assert "email" in channels
        assert "telegram" in channels

    def test_cancel_interview(self, tpo_s, scheduled):
        r = tpo_s.delete(f"{API}/interviews/schedule/{scheduled['interview_id']}")
        assert r.status_code == 200
        # Verify status = cancelled
        items = tpo_s.get(f"{API}/interviews/schedule").json()["items"]
        rec = next((it for it in items if it["interview_id"] == scheduled["interview_id"]), None)
        assert rec is not None
        assert rec["status"] == "cancelled"


# ---------- Multi-user invites ----------
class TestInvites:
    INVITE_EMAIL = f"test.invite.{uuid.uuid4().hex[:6]}@kmit.in"

    @pytest.fixture(scope="class")
    def invited_user(self, tpo_s):
        payload = {"email": self.INVITE_EMAIL, "name": "Dr. Test Invite",
                   "role": "faculty", "department": "IT"}
        r = tpo_s.post(f"{API}/invite", json=payload)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        # Invitations no longer mint a shared password; access activates on the
        # invitee's first Google sign-in for that email.
        assert body["user_id"] and "temp_password" not in body
        assert body["status"] == "invited"
        return body

    def test_invite_creates_user(self, invited_user):
        assert invited_user["email"].lower() == self.INVITE_EMAIL.lower()

    def test_invited_user_has_no_shared_password(self, invited_user):
        """A password-less invitation must not be guessable with the demo credential."""
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": self.INVITE_EMAIL,
                                              "password": PWD})
        assert r.status_code == 401, "invited account must not accept the demo password"

    def test_reinvite_updates_scope(self, tpo_s, invited_user):
        """Re-inviting must succeed and re-scope the existing account, not dead-end."""
        r = tpo_s.post(f"{API}/invite", json={
            "email": self.INVITE_EMAIL, "name": "Re-invited", "role": "tpo",
            "department": "CSE"})
        assert r.status_code == 200, r.text
        users = tpo_s.get(f"{API}/institution/users").json()["items"]
        match = next(u for u in users if u["email"].lower() == self.INVITE_EMAIL.lower())
        assert match["role"] == "tpo"

    def test_list_institution_users_includes_invite(self, tpo_s, invited_user):
        r = tpo_s.get(f"{API}/institution/users")
        assert r.status_code == 200
        emails = [u["email"].lower() for u in r.json()["items"]]
        assert self.INVITE_EMAIL.lower() in emails

    def test_cross_institution_invite_blocked(self, tpo_s):
        # TPO@kmit passes institution_id=inst_lim → should be ignored, user lands in inst_kmit
        email = f"cross.{uuid.uuid4().hex[:6]}@kmit.in"
        r = tpo_s.post(f"{API}/invite", json={
            "email": email, "name": "Cross Test", "role": "faculty",
            "institution_id": "inst_lim"})
        assert r.status_code in (200, 201), r.text
        # Verify the user was created in inst_kmit, not inst_lim
        users = tpo_s.get(f"{API}/institution/users").json()["items"]
        match = next((u for u in users if u["email"].lower() == email), None)
        assert match is not None, "Cross-invited user should appear in TPO's own institution"
        assert match["institution_id"] == "inst_kmit"

    def test_delete_institution_user(self, tpo_s, invited_user):
        r = tpo_s.delete(f"{API}/institution/users/{invited_user['user_id']}")
        assert r.status_code == 200
        # Verify removed
        users = tpo_s.get(f"{API}/institution/users").json()["items"]
        emails = [u["email"].lower() for u in users]
        assert self.INVITE_EMAIL.lower() not in emails


# ---------- MOU GridFS round-trip ----------
class TestMOUGridFS:
    PDF_BYTES = b"%PDF-1.4\n%CareerOS test MOU\n1 0 obj<</Type/Catalog>>endobj\ntrailer<<>>\n%%EOF\n" * 4

    def test_upload_and_download(self, tpo_s):
        files = {"file": ("test_mou.pdf", io.BytesIO(self.PDF_BYTES), "application/pdf")}
        data = {"expires_on": "2027-12-31", "partnership_type": "CRT"}
        r = tpo_s.post(f"{API}/mou/upload", files=files, data=data)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "gridfs_id" in body and body["gridfs_id"]
        upload_size = body["size_kb"]

        # GET /api/mou shows gridfs_id
        mou = tpo_s.get(f"{API}/mou").json()
        assert mou.get("gridfs_id") == body["gridfs_id"]

        # Download returns original bytes
        d = tpo_s.get(f"{API}/mou/download")
        assert d.status_code == 200
        assert "attachment" in d.headers.get("content-disposition", "").lower()
        assert d.content == self.PDF_BYTES, "Downloaded bytes differ from uploaded"
        # size_kb matches
        downloaded_kb = round(len(d.content) / 1024, 1)
        assert downloaded_kb == upload_size


# ---------- Faculty DSA scoping ----------
class TestFacultyDSAScope:
    def test_faculty_scope_department(self, faculty_s):
        # First confirm faculty department
        me = faculty_s.get(f"{API}/auth/me").json()
        dept = me.get("department")
        assert dept, "Faculty user should have a department"
        r = faculty_s.get(f"{API}/dsa/intelligence")
        assert r.status_code == 200
        data = r.json()
        assert data.get("scope") == f"department:{dept}", f"got scope={data.get('scope')}"

    def test_tpo_scope_institution(self, tpo_s):
        r = tpo_s.get(f"{API}/dsa/intelligence")
        assert r.status_code == 200
        assert r.json().get("scope") == "institution"

    def test_faculty_leaderboard_only_own_dept(self, faculty_s):
        me = faculty_s.get(f"{API}/auth/me").json()
        dept = me.get("department")
        data = faculty_s.get(f"{API}/dsa/intelligence").json()
        for row in data.get("leaderboard", []):
            assert row.get("department") == dept, f"leaderboard contains non-{dept} student: {row}"

    def test_faculty_counts_less_than_tpo(self, faculty_s, tpo_s):
        f = faculty_s.get(f"{API}/dsa/intelligence").json()
        t = tpo_s.get(f"{API}/dsa/intelligence").json()
        # Sum of solved across topics should be <= TPO (department subset of institution)
        f_solved = sum(t.get("solved", 0) for t in f["by_topic"])
        t_solved = sum(t.get("solved", 0) for t in t["by_topic"])
        assert f_solved <= t_solved
