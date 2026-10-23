"""CareerOS v2 backend tests.
Covers auth (6 demo roles + pending account), role isolation, public stats,
institutions, DSA/aptitude/ATS/interviews, placements, applications,
jobs/recruiters/talent-pool, announcements, MOU, admin panel + approvals.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://career-os-nexus.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
PWD = "careeros2026"

DEMO = {
    "admin": "admin@careeros.app",
    "institution": "institution@kmit.in",
    "tpo": "tpo@kmit.in",
    "faculty": "faculty@kmit.in",
    "student": "student@kmit.in",
    "recruiter": "recruiter@amazon.com",
    "pending": "tpo@vasavi.ac.in",
}

# ---------- helpers ----------
def _login(email, password=PWD):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password})
    return s, r

def _reset_pending_demo(admin_session=None):
    """The anonymous /api/test/reset-pending route was removed for security; this is the
    admin-authenticated equivalent used to restore the onboarding demo state."""
    if admin_session is not None:
        admin_session.post(f"{API}/admin/reset-pending-approval")
        return
    s, r = _login(DEMO["admin"])
    s.post(f"{API}/admin/reset-pending-approval")




@pytest.fixture(scope="module")
def admin_session():
    s, r = _login(DEMO["admin"])
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def tpo_session():
    s, r = _login(DEMO["tpo"])
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def student_session():
    s, r = _login(DEMO["student"])
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def recruiter_session():
    s, r = _login(DEMO["recruiter"])
    assert r.status_code == 200, r.text
    return s


# ---------- health & public ----------
def test_health():
    r = requests.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "X-CareerOS-Release" in r.headers


def test_deep_health():
    # Deep health reports tenant counts, so it is admin-only now; anonymous callers
    # must get 401 rather than a free map of the deployment.
    anon = requests.get(f"{API}/health/deep")
    assert anon.status_code == 401
    admin_s, admin_r = _login(DEMO["admin"])
    assert admin_r.status_code == 200
    r = admin_s.get(f"{API}/health/deep")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in {"ready", "degraded"}
    assert data["release"] == "v3-phases-7-10"
    assert data["checks"]["students"] > 0
    assert data["checks"]["institutions"] > 0


def test_public_landing_stats():
    r = requests.get(f"{API}/public/landing-stats")
    assert r.status_code == 200
    data = r.json()
    years = data["years"]
    yset = {y["academic_year"] for y in years}
    assert "2025-26" in yset
    assert "2017-18" in yset
    y25 = next(y for y in years if y["academic_year"] == "2025-26")
    assert y25["offers"] >= 700  # ~702
    assert y25["companies"] >= 140  # ~148
    assert isinstance(data["top_recruiters"], list) and len(data["top_recruiters"]) > 0
    assert data["totals"]["institutions"] >= 6
    assert data["totals"]["students"] >= 400


# ---------- auth: all 6 roles + pending ----------
@pytest.mark.parametrize("role,email,expected_role", [
    ("admin", DEMO["admin"], "super_admin"),
    ("institution", DEMO["institution"], "institution_admin"),
    ("tpo", DEMO["tpo"], "tpo"),
    ("faculty", DEMO["faculty"], "faculty"),
    ("student", DEMO["student"], "student"),
    ("recruiter", DEMO["recruiter"], "recruiter"),
])
def test_login_each_role(role, email, expected_role):
    s, r = _login(email)
    assert r.status_code == 200, f"{role} login failed: {r.text}"
    body = r.json()
    assert body["user"]["email"] == email
    assert body["user"]["role"] == expected_role
    # cookie set
    assert "session_token" in s.cookies
    # /auth/me with cookie
    me = s.get(f"{API}/auth/me")
    assert me.status_code == 200
    assert me.json()["role"] == expected_role


def test_login_pending_account():
    _reset_pending_demo()
    s, r = _login(DEMO["pending"])
    assert r.status_code == 200
    assert r.json()["user"]["approved"] is False


def test_login_wrong_password():
    s, r = _login(DEMO["tpo"], password="wrong-pw")
    assert r.status_code == 401


# ---------- RBAC isolation ----------
def test_tpo_cannot_access_admin(tpo_session):
    r = tpo_session.get(f"{API}/admin/platform-stats")
    assert r.status_code == 403


def test_admin_can_access_admin(admin_session):
    r = admin_session.get(f"{API}/admin/platform-stats")
    assert r.status_code == 200
    data = r.json()
    for key in ("institutions", "students", "applications", "jobs_open", "recruiters", "estimated_mrr_inr", "by_type"):
        assert key in data


# ---------- institutions ----------
def test_institutions_admin_sees_all(admin_session):
    r = admin_session.get(f"{API}/institutions")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 6


def test_institutions_tpo_only_own(tpo_session):
    r = tpo_session.get(f"{API}/institutions")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["institution_id"] == "inst_kmit"


# ---------- DSA ----------
def test_dsa_topics():
    r = requests.get(f"{API}/dsa/topics")
    assert r.status_code == 200
    topics = r.json()["topics"]
    assert len(topics) == 18
    codes = {t["code"] for t in topics}
    expected = {"BASICS", "SORTING", "ARRAYS", "BIN_SEARCH", "STR_BASIC", "LL", "RECURSION",
                "BIT_MANIP", "STACK", "SLIDING", "HEAP", "GREEDY", "TREE", "BST", "GRAPH",
                "DP", "TRIES", "STR_ADV"}
    assert expected.issubset(codes)
    assert r.json()["total"] == 474


def test_dsa_question_catalog(tpo_session):
    r = tpo_session.get(f"{API}/dsa/questions")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 474
    assert len(data["questions"]) == 474
    titles = {q["title"] for q in data["questions"]}
    assert {"Two Sum", "Kadane's Algorithm", "Rotate Matrix", "Merge Intervals"}.issubset(titles)


def test_dsa_intelligence_tpo(tpo_session):
    r = tpo_session.get(f"{API}/dsa/intelligence")
    assert r.status_code == 200
    data = r.json()
    assert len(data["by_topic"]) == 18
    assert data["total_problems"] == 474
    assert len(data["leaderboard"]) == 20


# ---------- student personal dashboard + DSA toggle ----------
def test_student_dashboard(student_session):
    r = student_session.get(f"{API}/me/dashboard")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["student"]["name"]
    assert len(d["dsa"]) == 18
    assert d["dsa_total"] == 474
    assert isinstance(d["aptitude"], list)
    assert isinstance(d["interviews"], list)
    assert isinstance(d["applications"], list)
    assert isinstance(d["recommended_jobs"], list)
    assert isinstance(d["topics"], list)

    q = student_session.get(f"{API}/me/dsa/questions")
    assert q.status_code == 200, q.text
    qp = q.json()
    assert qp["total"] == 474
    assert len(qp["questions"]) == 474
    assert len(qp["topics"]) == 18


def test_student_dsa_toggle(student_session):
    before = student_session.get(f"{API}/me/dashboard").json()
    arr_before = next(r for r in before["dsa"] if r["topic_code"] == "ARRAYS")
    r = student_session.post(f"{API}/me/dsa/toggle", json={"topic_code": "ARRAYS", "delta": 1})
    assert r.status_code == 200
    assert r.json()["solved"] >= arr_before["solved"]


def test_student_dsa_coding_workspace(student_session):
    q = student_session.get(f"{API}/me/dsa/questions")
    assert q.status_code == 200, q.text
    question = q.json()["questions"][0]
    run = student_session.post(f"{API}/me/dsa/submissions/run", json={
        "question_id": question["question_id"],
        "language": "python",
        "code": "def solve():\n    return 1\nprint(solve())",
        "custom_input": "1",
    })
    assert run.status_code == 200, run.text
    assert "result" in run.json()

    submit = student_session.post(f"{API}/me/dsa/submissions/submit", json={
        "question_id": question["question_id"],
        "language": "python",
        "code": "def solve():\n    return 1\nprint(solve())",
    })
    assert submit.status_code == 200, submit.text
    assert submit.json()["kind"] == "submit"

    attempts = student_session.get(f"{API}/dsa/student/{q.json()['student_id']}/attempts", params={"question_id": question["question_id"]})
    assert attempts.status_code == 200, attempts.text
    assert attempts.json()["count"] >= 2


def test_student_readiness_engine(student_session):
    r = student_session.get(f"{API}/readiness/me")
    assert r.status_code == 200, r.text
    readiness = r.json()["readiness"]
    assert 0 <= readiness["score"] <= 100
    assert readiness["band"] in {"placement_ready", "nearly_ready", "developing", "needs_intervention"}
    for key in ("dsa", "aptitude", "ats", "interview", "cgpa", "consistency"):
        assert key in readiness["components"]
        assert "score" in readiness["components"][key]


def test_staff_readiness_roster(tpo_session):
    r = tpo_session.get(f"{API}/readiness/students", params={"limit": 25})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["scope"] == "institution"
    assert data["count"] > 0
    assert 0 <= data["avg_readiness"] <= 100
    assert isinstance(data["weak_students"], list)
    assert {"dsa", "aptitude", "ats", "interview", "cgpa", "consistency"}.issubset(data["component_avgs"].keys())


def test_role_workspace_contracts():
    cases = [
        ("tpo", "tpo", None),
        ("faculty", "faculty", "CSE"),
        ("student", "student", "CSE"),
        ("recruiter", "recruiter", None),
    ]
    for key, expected_role, expected_department in cases:
        s, login = _login(DEMO[key])
        assert login.status_code == 200, login.text
        r = s.get(f"{API}/workspace/me")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["role"] == expected_role
        assert data["title"]
        assert data["headline"]
        assert len(data["kpis"]) >= 4
        assert len(data["actions"]) > 0
        assert "sections" in data
        if expected_department:
            assert data["scope"]["department"] == expected_department


# ---------- aptitude / ATS / interviews ----------
def test_aptitude_intelligence(tpo_session):
    r = tpo_session.get(f"{API}/aptitude/intelligence")
    assert r.status_code == 200
    data = r.json()
    sections = data["by_section"]
    codes = {s["_id"] for s in sections}
    assert {"QUANT", "REASON", "VERBAL", "DI"}.issubset(codes)
    assert "question_analytics" in data
    assert isinstance(data["weak_topics"], list)
    assert isinstance(data["speed_analysis"], list)
    assert isinstance(data["accuracy_analysis"], list)


def test_aptitude_question_tracking_and_analytics(tpo_session, student_session):
    catalog = tpo_session.get(f"{API}/aptitude/questions")
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    assert body["total"] > 100
    first = body["questions"][0]
    assert {"question_id", "topic", "section", "difficulty"}.issubset(first.keys())

    mine = student_session.get(f"{API}/me/aptitude/questions")
    assert mine.status_code == 200, mine.text
    data = mine.json()
    assert data["total"] == body["total"]
    assert len(data["questions"]) == body["total"]

    patch = student_session.patch(
        f"{API}/me/aptitude/questions/{first['question_id']}",
        json={"attempted": True, "solved": True, "accuracy": 92, "average_time": 48, "mastery_score": 88},
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()["question"]
    assert updated["solved"] is True
    assert updated["attempted"] is True
    assert updated["mastery_score"] >= 80

    analytics = tpo_session.get(f"{API}/aptitude/question-analytics")
    assert analytics.status_code == 200, analytics.text
    report = analytics.json()
    assert isinstance(report["weak_topics"], list)
    assert isinstance(report["priority_students"], list)
    assert "summary" in report


def test_student_aptitude_test_engine(student_session):
    mine = student_session.get(f"{API}/me/aptitude/questions")
    assert mine.status_code == 200, mine.text
    assert mine.json()["overall"]["total"] >= 250

    start = student_session.post(f"{API}/me/aptitude/tests/start", json={
        "mode": "sectional",
        "section_code": "QUANT",
        "question_count": 4,
        "duration_minutes": 5,
    })
    assert start.status_code == 200, start.text
    test = start.json()
    assert len(test["questions"]) == 4
    assert "answer_index" not in test["questions"][0]

    answers = {row["question_id"]: 0 for row in test["questions"]}
    submit = student_session.post(f"{API}/me/aptitude/tests/{test['test_id']}/submit", json={
        "answers": answers,
        "elapsed_seconds": 180,
        "review_later": [test["questions"][0]["question_id"]],
        "bookmarks": [test["questions"][1]["question_id"]],
    })
    assert submit.status_code == 200, submit.text
    result = submit.json()
    assert result["total"] == 4
    assert 0 <= result["score_pct"] <= 100
    assert isinstance(result["topic_performance"], list)

    attempts = student_session.get(f"{API}/me/aptitude/attempts")
    assert attempts.status_code == 200, attempts.text
    assert any(item["test_id"] == test["test_id"] for item in attempts.json()["items"])


def test_ats_intelligence(tpo_session):
    r = tpo_session.get(f"{API}/ats/intelligence")
    assert r.status_code == 200
    d = r.json()
    assert d["avg_score"] > 0
    assert isinstance(d["rows"], list)
    assert isinstance(d["resume_versions"], list)
    assert isinstance(d["version_history"], list)
    assert isinstance(d["skill_gaps"], list)
    assert isinstance(d["recruiter_compatibility"], list)


def test_ats_resume_versions_and_heatmap(tpo_session):
    versions = tpo_session.get(f"{API}/ats/resume-versions")
    assert versions.status_code == 200, versions.text
    data = versions.json()
    assert isinstance(data["items"], list)
    assert data["count"] == len(data["items"])
    if data["items"]:
        first = data["items"][0]
        assert {"resume_id", "version", "ats_score", "keyword_score", "recruiter_match_score"}.issubset(first.keys())

    heatmap = tpo_session.get(f"{API}/ats/heatmap")
    assert heatmap.status_code == 200, heatmap.text
    body = heatmap.json()
    assert isinstance(body["keyword_heatmap"], list)
    assert isinstance(body["skill_gaps"], list)
    assert isinstance(body["recruiter_compatibility"], list)


def test_interviews_intelligence(tpo_session):
    r = tpo_session.get(f"{API}/interviews/intelligence")
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["rows"], list)
    assert "avg_confidence" in d and "avg_technical" in d
    assert "rubric_avgs" in d
    assert isinstance(d["priority_students"], list)


def test_interview_history_timeline(tpo_session, student_session):
    staff = tpo_session.get(f"{API}/interviews/history")
    assert staff.status_code == 200, staff.text
    data = staff.json()
    assert isinstance(data["items"], list)
    assert isinstance(data["weak_area_detection"], list)
    assert isinstance(data["improvement_tracking"], list)
    if data["items"]:
        first = data["items"][0]
        assert {"student_id", "latest_score", "improvement", "weak_areas", "history"}.issubset(first.keys())

    mine = student_session.get(f"{API}/interviews/history")
    assert mine.status_code == 200, mine.text
    assert isinstance(mine.json()["student_timeline"], list)


def test_student_mock_interview_workflow(student_session):
    questions = student_session.get(f"{API}/me/interviews/mock/questions", params={"mode": "technical"})
    assert questions.status_code == 200, questions.text
    assert len(questions.json()["questions"]) >= 5

    start = student_session.post(f"{API}/me/interviews/mock/start", json={"mode": "technical", "camera_enabled": False, "microphone_enabled": False})
    assert start.status_code == 200, start.text
    session = start.json()
    first = session["questions"][0]

    answer = student_session.post(f"{API}/me/interviews/mock/{session['session_id']}/answer", json={
        "question_id": first["question_id"],
        "prompt": first["prompt"],
        "transcript": "I solved DSA problems using hash maps and explained time complexity for a Python API project with database indexing.",
        "response_seconds": 55,
    })
    assert answer.status_code == 200, answer.text

    complete = student_session.post(f"{API}/me/interviews/mock/{session['session_id']}/complete", json={"notes": "test"})
    assert complete.status_code == 200, complete.text
    report = complete.json()
    assert report["overall_score"] >= 0
    assert "communication_score" in report


def test_cross_module_intelligence(tpo_session):
    r = tpo_session.get(f"{API}/intelligence/modules")
    assert r.status_code == 200, r.text
    d = r.json()
    codes = {card["code"] for card in d["cards"]}
    assert {"placements", "dsa", "aptitude", "ats", "interviews", "training"}.issubset(codes)
    assert isinstance(d["critical_alerts"], list)
    assert isinstance(d["recommendations"], list)


def test_analytics_engine(tpo_session):
    r = tpo_session.get(f"{API}/analytics/engine")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["summary"]["command_score"] >= 0
    assert len(d["kpis"]) == 4
    assert len(d["funnel"]) == 6
    assert isinstance(d["department_health"], list)
    assert isinstance(d["risk_register"], list)
    assert "forecasted_offers" in d["forecast"]


# ---------- placements ----------
def test_placements_overview(tpo_session):
    r = tpo_session.get(f"{API}/placements/overview")
    assert r.status_code == 200
    d = r.json()
    assert len(d["year_summaries"]) >= 9
    assert len(d["records"]) > 0
    assert isinstance(d["top_recruiters"], list)
    dept_names = {x["department"] for x in d["department_breakdown"]}
    expected_some = {"CSE", "IT", "ECE"}
    assert expected_some.issubset(dept_names) or len(dept_names) >= 3


def test_placement_intelligence_engine(tpo_session):
    r = tpo_session.get(f"{API}/placements/intelligence")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "forecast" in data
    assert isinstance(data["placement_funnel"], list)
    assert isinstance(data["department_analytics"], list)
    assert isinstance(data["risk_students"], list)
    assert isinstance(data["recruiter_conversions"], list)
    assert isinstance(data["readiness_trends"], list)


def test_reports_manifest_and_board_packet(tpo_session):
    manifest = tpo_session.get(f"{API}/reports/manifest")
    assert manifest.status_code == 200, manifest.text
    data = manifest.json()
    assert len(data["items"]) >= 6
    assert data["board_packet"]["status"] in {"ready", "needs_review"}
    assert "recommended_sequence" in data["board_packet"]

    packet = tpo_session.get(f"{API}/reports/board-packet.json")
    assert packet.status_code == 200, packet.text
    body = packet.json()
    assert body["title"] == "CareerOS Intelligence Board Packet"
    assert "executive_summary" in body
    assert isinstance(body["module_health"], list)


# ---------- applications ----------
def test_applications_list_and_pipeline(tpo_session):
    r = tpo_session.get(f"{API}/applications")
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["items"], list) and len(d["items"]) > 0
    pipeline = d["pipeline"]
    # Stages should include at least some of the standard ones
    expected_stages = {"Applied", "Shortlisted", "Interview", "Selected", "Rejected"}
    assert expected_stages.intersection(set(pipeline.keys()))


def test_application_stage_update(tpo_session):
    r = tpo_session.get(f"{API}/applications")
    item = r.json()["items"][0]
    aid = item["application_id"]
    upd = tpo_session.patch(f"{API}/applications/{aid}", json={"stage": "Selected"})
    assert upd.status_code == 200
    assert upd.json()["updated"] >= 0  # may be 0 if already Selected
    # Verify persistence
    verify = tpo_session.get(f"{API}/applications", params={"stage": "Selected"})
    assert any(x["application_id"] == aid for x in verify.json()["items"])


# ---------- jobs / recruiters ----------
def test_jobs_open(tpo_session):
    r = tpo_session.get(f"{API}/jobs", params={"status": "open"})
    assert r.status_code == 200
    assert len(r.json()["items"]) > 1


def test_recruiters_list(tpo_session):
    r = tpo_session.get(f"{API}/recruiters")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 20


def test_talent_pool_recruiter(recruiter_session):
    r = recruiter_session.get(f"{API}/recruiters/rec_amazon/talent-pool", params={"min_cgpa": 7.0})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) > 0
    # Sorted by readiness_score desc
    scores = [s.get("readiness_score", 0) for s in items]
    assert scores == sorted(scores, reverse=True)


def test_talent_pool_recruiter_me_route(recruiter_session):
    r = recruiter_session.get(f"{API}/recruiters/me/talent-pool", params={"min_cgpa": 7.0})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["recruiter_id"] == "rec_amazon"
    assert data["count"] == len(data["items"])
    assert len(data["items"]) > 0


def test_talent_pool_recruiter_filters(recruiter_session):
    r = recruiter_session.get(f"{API}/recruiters/me/talent-pool", params={"min_cgpa": 7.0, "min_readiness": 50, "department": "CSE", "limit": 10})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["filters"]["department"] == "CSE"
    assert data["filters"]["min_readiness"] == 50
    assert data["count"] <= 10
    assert all(item["department"] == "CSE" and item["readiness_score"] >= 50 for item in data["items"])


def test_recruiter_analytics(recruiter_session):
    r = recruiter_session.get(f"{API}/recruiters/me/analytics")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["recruiter_id"] == "rec_amazon"
    assert "conversion_rate" in data["summary"]
    assert isinstance(data["job_funnels"], list)
    assert isinstance(data["institution_funnel"], list)
    assert isinstance(data["action_queue"], list) and len(data["action_queue"]) > 0


def test_recruiter_recommendations_shortlists_and_saved_filters(recruiter_session):
    recs = recruiter_session.get(f"{API}/recruiters/me/recommendations")
    assert recs.status_code == 200, recs.text
    data = recs.json()
    assert data["answer"] == "Which students should I interview next?"
    assert isinstance(data["items"], list)
    if data["items"]:
        candidate = data["items"][0]
        assert {"student_id", "job_id", "interview_next_score", "skill_match_score", "answer"}.issubset(candidate.keys())
        create = recruiter_session.post(f"{API}/recruiters/me/shortlists", json={
            "student_id": candidate["student_id"],
            "job_id": candidate["job_id"],
            "readiness_score": candidate["readiness_score"],
            "match_score": candidate["interview_next_score"],
            "notes": "Automated test shortlist",
        })
        assert create.status_code == 200, create.text
        assert create.json()["student_id"] == candidate["student_id"]

    shortlists = recruiter_session.get(f"{API}/recruiters/me/shortlists")
    assert shortlists.status_code == 200, shortlists.text
    assert isinstance(shortlists.json()["items"], list)

    saved = recruiter_session.post(f"{API}/recruiters/me/saved-filters", json={
        "name": f"TEST_filter_{uuid.uuid4().hex[:6]}",
        "min_cgpa": 7.2,
        "min_readiness": 68,
        "department": "CSE",
        "skill": "React",
    })
    assert saved.status_code == 200, saved.text
    assert saved.json()["filters"]["department"] == "CSE"

    filters = recruiter_session.get(f"{API}/recruiters/me/saved-filters")
    assert filters.status_code == 200, filters.text
    assert any(item["filter_id"] == saved.json()["filter_id"] for item in filters.json()["items"])


def test_talent_pool_forbidden_for_tpo(tpo_session):
    r = tpo_session.get(f"{API}/recruiters/rec_amazon/talent-pool")
    assert r.status_code == 403


# ---------- announcements ----------
def test_announcements_get_and_post(tpo_session, admin_session):
    r = tpo_session.get(f"{API}/announcements")
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)
    create = tpo_session.post(f"{API}/announcements", json={
        "title": f"TEST_ann_{uuid.uuid4().hex[:6]}",
        "body": "Automated test announcement",
        "audience": "students",
    })
    assert create.status_code == 200
    aid = create.json()["announcement_id"]
    # Verify in list
    after = tpo_session.get(f"{API}/announcements").json()["items"]
    assert any(x["announcement_id"] == aid for x in after)
    # Fan-out to notification log
    notif = admin_session.get(f"{API}/admin/notifications").json()["items"]
    assert any(n.get("event") == "announcement_posted" for n in notif)


# ---------- MOU ----------
def test_mou_tpo(tpo_session):
    r = tpo_session.get(f"{API}/mou")
    assert r.status_code == 200
    mou = r.json()
    assert mou["institution_id"] == "inst_kmit"
    assert "days_until_renewal" in mou
    assert isinstance(mou["days_until_renewal"], int)


# ---------- admin: approval flow ----------
def test_admin_pending_and_approve(admin_session):
    _reset_pending_demo(admin_session)
    pending = admin_session.get(f"{API}/admin/pending-signups")
    assert pending.status_code == 200
    items = pending.json()["items"]
    vasavi = next((u for u in items if u["email"] == DEMO["pending"]), None)
    assert vasavi is not None, "Vasavi pending account not found"
    uid = vasavi["user_id"]
    ap = admin_session.post(f"{API}/admin/approve/{uid}")
    assert ap.status_code == 200
    # Re-login as Vasavi and check approved=true
    s, r = _login(DEMO["pending"])
    assert r.status_code == 200
    me = s.get(f"{API}/auth/me").json()
    assert me["approved"] is True


# ---------- notification test ----------
def test_admin_test_notification(admin_session):
    r = admin_session.post(f"{API}/admin/test-notification")
    assert r.status_code == 200
    log = admin_session.get(f"{API}/admin/notifications").json()["items"]
    assert any(n.get("event") == "admin_test" for n in log)
