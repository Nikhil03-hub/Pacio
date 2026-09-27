"""CareerOS Campus Intelligence — v2 backend.

Multi-role, multi-institution platform with 13 modules.
Auth: bcrypt password login + Emergent Google OAuth + cookie session token.
RBAC: super_admin, institution_admin, tpo, faculty, student, recruiter.
"""
from __future__ import annotations

import os
import io
import re
import uuid
import logging
import time
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Literal, Any

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from urllib.parse import urlencode
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic import BaseModel, EmailStr

from seed_data import (
    seed_payload, STRIVER_TOPICS, DSA_TOTAL, APTITUDE_SECTIONS, INSTITUTIONS,
    PROGRAMS, KMIT_PLACEMENT_RECORDS, YEAR_AGGREGATES, build_dsa_question_bank,
)
from notification_service import notify
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_session_user,
    require_roles,
    require_same_institution,
)
from reports import (
    placement_report_pdf, training_report_pdf, department_report_pdf,
    students_csv, applications_csv, placements_csv, build_ics,
)
from ai_service import ai_interview_feedback, ai_ats_score
from intelligence_engine import READINESS_WEIGHTS, build_readiness_roster, build_student_readiness
from ws_manager import manager as ws_manager
from fastapi import WebSocket, WebSocketDisconnect
from memory_db import MemoryDB, MemoryGridFS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("careeros")
ROOT = Path(__file__).parent

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "careeros")
EMERGENT_AUTH_URL = os.environ.get("EMERGENT_AUTH_URL", "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
DEFAULT_DEMO_PASSWORD = os.environ.get("DEFAULT_DEMO_PASSWORD")

client = None
if MONGO_URL:
    log.info("MONGO_URL configured; MongoDB Atlas will initialize on startup")
    db = MemoryDB()
    gridfs = MemoryGridFS()
else:
    log.warning("MONGO_URL not configured; using in-memory demo database")
    db = MemoryDB()
    gridfs = MemoryGridFS()

CORE_COLLECTIONS = [
    "users", "students", "institutions", "recruiters", "applications", "placements",
    "programs", "cohorts", "mous", "fdp_sessions", "revenue_share", "comm_logs",
    "saved_jobs", "notifications",
]

app = FastAPI(title="CareerOS")
FRONTEND_BUILD = ROOT.parent / "frontend" / "build"
SPA_HEADERS = {"Cache-Control": "no-store, max-age=0"}
DSA_TOPIC_BY_CODE = {topic["code"]: topic for topic in STRIVER_TOPICS}
DSA_TOPIC_CODES = list(DSA_TOPIC_BY_CODE.keys())
APTITUDE_PREP_SECTIONS = [
    {"code": "QUANT", "name": "Quantitative Aptitude", "topics": [
        "Number System", "Percentages", "Profit and Loss", "Time and Work", "Time and Distance",
        "Boats and Streams", "Averages", "Ratio and Proportion", "Simple Interest", "Compound Interest",
        "Permutations", "Combinations", "Probability", "Data Interpretation", "Mixtures and Alligation",
        "Ages", "Partnership", "Pipes and Cisterns", "Clocks", "Calendars",
    ]},
    {"code": "REASON", "name": "Logical Reasoning", "topics": [
        "Blood Relations", "Coding Decoding", "Syllogisms", "Seating Arrangement", "Direction Sense",
        "Puzzles", "Statement Assumptions", "Cause and Effect",
    ]},
    {"code": "VERBAL", "name": "Verbal Ability", "topics": [
        "Reading Comprehension", "Sentence Correction", "Synonyms", "Antonyms", "Error Detection",
        "Fill in the Blanks", "Para Jumbles",
    ]},
    {"code": "TECH", "name": "Technical MCQs", "topics": [
        "C", "C++", "Java", "Python", "DBMS", "Operating Systems", "Computer Networks", "OOPs",
    ]},
    {"code": "DI", "name": "Data Interpretation", "topics": ["Tables", "Pie Charts", "Bar Graphs", "Line Charts", "Caselets"]},
]
if FRONTEND_BUILD.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD / "static"), name="static")

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "https://pacio-two.vercel.app").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.middleware("http")
async def production_headers(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
    response.headers.setdefault("X-CareerOS-Release", "v3")
    response.headers.setdefault("X-Response-Time-Ms", str(round((time.perf_counter() - started) * 1000, 2)))
    return response

# ============== MODELS ==============
class LoginBody(BaseModel):
    email: EmailStr
    password: str


class SignupBody(BaseModel):
    college_name: str
    short_name: Optional[str] = None
    role: Literal["tpo", "hod", "coordinator"] = "tpo"
    affiliated_university: Optional[str] = None
    partnership_type: Optional[str] = None
    department: Optional[str] = None


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


class RegisterBody(BaseModel):
    role: Literal["student", "faculty", "recruiter", "tpo"]
    name: str
    email: EmailStr
    password: str
    roll_number: Optional[str] = None
    department: Optional[str] = None
    institution_id: Optional[str] = None
    company_name: Optional[str] = None
    college_name: Optional[str] = None
    affiliated_university: Optional[str] = None
    partnership_type: Optional[str] = None


# ============== SESSION ==============
def _cookie_secure(request: Request) -> bool:
    forced = os.environ.get("COOKIE_SECURE")
    if forced is not None:
        return forced.lower() in {"1", "true", "yes", "on"}
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    return forwarded_proto == "https" or request.url.scheme == "https"


def _public_origin(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",", 1)[0].strip()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


def _google_redirect_uri(request: Request) -> str:
    return GOOGLE_REDIRECT_URI or f"{_public_origin(request)}/api/auth/google/callback"


async def _create_session(user_id: str, response: Response, request: Request, token: Optional[str] = None) -> str:
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(401, "User not found")
    session_token, jwt_id, expires_at = create_access_token(user)
    await db.user_sessions.insert_one({
        "session_token": session_token,
        "external_session_token": token,
        "jwt_id": jwt_id,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    secure_cookie = _cookie_secure(request)
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=secure_cookie, samesite="none" if secure_cookie else "lax", path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return session_token


def _new_user(*, email: str, name: str, role: str, institution_id: Optional[str], password: Optional[str], approved: bool = True, department: Optional[str] = None) -> dict:
    normalized_email = email.lower()
    return {
        "user_id": f"user_{uuid.uuid5(uuid.NAMESPACE_DNS, normalized_email).hex[:12]}",
        "email": normalized_email,
        "name": name,
        "role": role,
        "institution_id": institution_id,
        "department": department,
        "approved": approved,
        "password_hash": hash_password(password) if password else None,
        "picture": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def _audit_log(
    event: str,
    *,
    user: Optional[dict] = None,
    institution_id: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    outcome: str = "success",
    metadata: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    actor = user or {}
    ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    await db.audit_logs.insert_one({
        "audit_id": f"audit_{uuid.uuid4().hex[:12]}",
        "event": event,
        "outcome": outcome,
        "actor_user_id": actor.get("user_id"),
        "actor_email": actor.get("email"),
        "actor_role": actor.get("role"),
        "institution_id": institution_id if institution_id is not None else actor.get("institution_id"),
        "resource": resource,
        "resource_id": resource_id,
        "metadata": metadata or {},
        "ip": ip,
        "user_agent": user_agent,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def _resolve_recruiter_id(user: dict) -> Optional[str]:
    if user.get("role") != "recruiter":
        return None
    if user.get("recruiter_id"):
        return user["recruiter_id"]
    email = user.get("email", "")
    domain = email.split("@", 1)[1].split(".", 1)[0] if "@" in email else ""
    candidate = f"rec_{domain.lower().replace('-', '_')}" if domain else None
    if candidate:
        recruiter = await db.recruiters.find_one({"recruiter_id": candidate}, {"_id": 0})
        if recruiter:
            await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"recruiter_id": candidate}})
            user["recruiter_id"] = candidate
            return candidate
    return None


# ============== STARTUP — seed + demo users ==============
# ============== ROLE WORKSPACE HELPERS ==============
def _first_name(name: Optional[str], fallback: str = "there") -> str:
    if not name:
        return fallback
    for part in name.replace("(", " ").split():
        clean = part.strip(".,)")
        if clean and clean.lower() not in {"dr", "mr", "mrs", "ms", "prof"}:
            return clean
    return fallback


def _pct(part: float, total: float, digits: int = 0) -> float:
    if not total:
        return 0
    return round((part / total) * 100, digits)


def _workspace_kpi(
    label: str,
    value: Any,
    *,
    sub: str = "",
    unit: str = "",
    status: str = "neutral",
    to: Optional[str] = None,
) -> dict:
    return {"label": label, "value": value, "unit": unit, "sub": sub, "status": status, "to": to}


def _workspace_action(label: str, to: str, *, priority: str, reason: str) -> dict:
    return {"label": label, "to": to, "priority": priority, "reason": reason}


def _workspace_alert(
    title: str,
    body: str,
    *,
    severity: str = "info",
    kind: str = "decision",
    to: Optional[str] = None,
) -> dict:
    return {"title": title, "body": body, "severity": severity, "kind": kind, "to": to}


def _pipeline_counts(items: list[dict]) -> dict[str, int]:
    stages = {"Applied": 0, "Shortlisted": 0, "Assessment": 0, "Interview": 0, "Selected": 0, "Rejected": 0}
    for item in items:
        stage = item.get("stage") or "Applied"
        stages[stage] = stages.get(stage, 0) + 1
    return stages


def _score_band(score: float) -> dict[str, str]:
    if score >= 85:
        return {"code": "placement_ready", "label": "Placement ready"}
    if score >= 72:
        return {"code": "nearly_ready", "label": "Nearly ready"}
    if score >= 58:
        return {"code": "developing", "label": "Developing"}
    return {"code": "needs_intervention", "label": "Needs intervention"}


def _component_status(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 65:
        return "on_track"
    if score >= 50:
        return "watch"
    return "critical"


def _clamp_score(value: float) -> float:
    return max(0, min(100, float(value or 0)))


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _difficulty_for_index(index: int) -> str:
    if index <= 2:
        return "Easy"
    if index <= 4:
        return "Medium"
    return "Hard"


def _build_aptitude_question_bank(now: Optional[str] = None) -> list[dict]:
    ts = now or datetime.now(timezone.utc).isoformat()
    questions = []
    global_order = 1
    for section in APTITUDE_PREP_SECTIONS:
        for topic_index, topic in enumerate(section["topics"], start=1):
            topic_slug = _slug(topic)
            for index in range(1, 7):
                difficulty = _difficulty_for_index(index)
                expected = 45 if difficulty == "Easy" else 75 if difficulty == "Medium" else 105
                answer_index = (topic_index + index) % 4
                options = [
                    f"{topic} option A",
                    f"{topic} option B",
                    f"{topic} option C",
                    f"{topic} option D",
                ]
                questions.append({
                    "question_id": f"apt_{section['code'].lower()}_{topic_slug}_{index:02d}",
                    "section": section["name"],
                    "section_code": section["code"],
                    "topic": topic,
                    "topic_code": topic_slug.upper(),
                    "difficulty": difficulty,
                    "title": f"{topic} drill {index}",
                    "prompt": f"{topic} placement aptitude drill {index}. Choose the most accurate answer from the options.",
                    "options": options,
                    "answer_index": answer_index,
                    "answer": options[answer_index],
                    "explanation": f"Review the core {topic} pattern, eliminate impossible choices, then solve within {expected} seconds.",
                    "order": index,
                    "topic_order": topic_index,
                    "global_order": global_order,
                    "expected_time_sec": expected,
                    "created_at": ts,
                    "active": True,
                })
                global_order += 1
    return questions


async def _ensure_aptitude_catalog() -> None:
    for question in _build_aptitude_question_bank():
        await db.aptitude_questions.update_one(
            {"question_id": question["question_id"]},
            {"$set": question},
            upsert=True,
        )


async def _ensure_student_aptitude_progress(student: dict) -> None:
    await _ensure_aptitude_catalog()
    existing = await db.aptitude_question_progress.count_documents({"student_id": student["student_id"]})
    if existing:
        return
    now = datetime.now(timezone.utc).isoformat()
    scores = await db.aptitude_scores.find({"student_id": student["student_id"]}, {"_id": 0}).to_list(100)
    score_by_section = {row["section_code"]: row for row in scores}
    questions = await db.aptitude_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(1000)
    inserts = []
    for section in APTITUDE_PREP_SECTIONS:
        section_questions = [q for q in questions if q["section_code"] == section["code"]]
        score = score_by_section.get(section["code"], {})
        score_pct = float(score.get("score_pct", 0) or 0)
        accuracy_pct = float(score.get("accuracy_pct", score_pct) or 0)
        avg_time = float(score.get("avg_time_sec", 90) or 90)
        attempted_count = int(round(len(section_questions) * min(1, max(0.35, (score.get("tests_taken", 2) or 2) / 18))))
        solved_count = int(round(len(section_questions) * min(1, max(0, score_pct / 100))))
        attempted_count = max(solved_count, min(len(section_questions), attempted_count))
        for index, question in enumerate(section_questions[:attempted_count], start=1):
            solved = index <= solved_count
            expected = float(question.get("expected_time_sec", 75) or 75)
            speed = _clamp_score(100 - max(0, avg_time - expected) * 0.9)
            mastery = round(_clamp_score((score_pct * 0.48) + (accuracy_pct * 0.32) + (speed * 0.20) + (8 if solved else -8)), 1)
            last_attempted = score.get("attempted_at") or now
            inserts.append({
                "progress_id": f"aptp_{uuid.uuid4().hex[:10]}",
                "student_id": student["student_id"],
                "institution_id": student["institution_id"],
                "question_id": question["question_id"],
                "topic": question["topic"],
                "topic_code": question["topic_code"],
                "section": question["section"],
                "section_code": question["section_code"],
                "difficulty": question["difficulty"],
                "solved": solved,
                "attempted": True,
                "accuracy": round(accuracy_pct, 1),
                "speed": round(speed, 1),
                "average_time": round(avg_time, 1),
                "mastery_score": mastery,
                "revision_due": mastery < 72,
                "last_attempted": last_attempted,
                "updated_at": now,
            })
    if inserts:
        await db.aptitude_question_progress.insert_many(inserts)


async def _ensure_aptitude_progress_for_students(students: list[dict]) -> None:
    await _ensure_aptitude_catalog()
    for student in students[:1200]:
        await _ensure_student_aptitude_progress(student)


async def _ensure_resume_versions_for_students(students: Optional[list[dict]] = None) -> None:
    query: dict[str, Any] = {}
    if students is not None:
        query["student_id"] = {"$in": [student["student_id"] for student in students]}
    reports = await db.ats_reports.find(query, {"_id": 0}).sort("created_at", 1).to_list(5000)
    if not reports:
        return
    existing_ids = {
        row["source_ats_id"]
        for row in await db.resume_versions.find({"source_ats_id": {"$in": [r["ats_id"] for r in reports]}}, {"_id": 0, "source_ats_id": 1}).to_list(5000)
        if row.get("source_ats_id")
    }
    counters: dict[str, int] = {}
    inserts = []
    for report in reports:
        if report["ats_id"] in existing_ids:
            continue
        sid = report["student_id"]
        counters[sid] = counters.get(sid, 0) + 1
        keyword_score = report.get("keyword_match_pct", 0) or 0
        recruiter_match = round((report.get("score", 0) * 0.48) + (keyword_score * 0.34) + (report.get("format_score", 0) * 0.18), 1)
        inserts.append({
            "resume_id": f"res_{uuid.uuid4().hex[:10]}",
            "source_ats_id": report["ats_id"],
            "student_id": sid,
            "institution_id": report["institution_id"],
            "version": counters[sid],
            "upload_date": report.get("created_at"),
            "uploaded_filename": report.get("uploaded_filename"),
            "ats_score": report.get("score", 0),
            "keyword_score": keyword_score,
            "missing_keywords": report.get("missing_keywords", []),
            "recruiter_match_score": recruiter_match,
            "format_score": report.get("format_score", 0),
            "improvement_suggestions": [
                f"Add evidence for {kw}" for kw in (report.get("missing_keywords", []) or [])[:3]
            ],
            "created_at": report.get("created_at"),
        })
    if inserts:
        await db.resume_versions.insert_many(inserts)


async def _batch_readiness_summary(
    iid: str,
    *,
    department: Optional[str] = None,
    limit: int = 1200,
) -> dict:
    """Bulk readiness summary for executive analytics without per-student query fan-out."""
    query: dict[str, Any] = {"institution_id": iid}
    if department:
        query["department"] = department
    safe_limit = max(1, min(limit, 1500))
    students = await db.students.find(query, {"_id": 0}).limit(safe_limit).to_list(safe_limit)
    sids = [student["student_id"] for student in students]
    if not sids:
        return {
            "rows": [],
            "avg_readiness": 0,
            "placement_ready": 0,
            "needs_intervention": 0,
            "by_band": {},
            "component_avgs": {key: 0 for key in READINESS_WEIGHTS},
            "weak_students": [],
            "institution_id": iid,
            "department": department,
        }

    dsa_rows = await db.dsa_progress.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(20000)
    aptitude_question_rows = await db.aptitude_question_progress.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(30000)
    aptitude_rows = await db.aptitude_scores.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(20000)
    ats_rows = await db.ats_reports.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(10000)
    resume_rows = await db.resume_versions.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(10000)
    interview_rows = await db.interview_reports.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(10000)
    application_rows = await db.applications.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(20000)

    dsa_by_student: dict[str, dict[str, float]] = {}
    for row in dsa_rows:
        bucket = dsa_by_student.setdefault(row["student_id"], {"solved": 0, "total": 0})
        bucket["solved"] += row.get("solved", 0) or 0
        bucket["total"] += row.get("total", 0) or 0

    aptitude_by_student: dict[str, list[dict]] = {}
    for row in aptitude_rows:
        aptitude_by_student.setdefault(row["student_id"], []).append(row)

    aptitude_questions_by_student: dict[str, list[dict]] = {}
    for row in aptitude_question_rows:
        aptitude_questions_by_student.setdefault(row["student_id"], []).append(row)

    ats_by_student: dict[str, dict] = {}
    for row in sorted(ats_rows, key=lambda item: item.get("created_at") or "", reverse=True):
        ats_by_student.setdefault(row["student_id"], row)

    resumes_by_student: dict[str, dict] = {}
    for row in sorted(resume_rows, key=lambda item: (item.get("version") or 0, item.get("upload_date") or ""), reverse=True):
        resumes_by_student.setdefault(row["student_id"], row)

    interviews_by_student: dict[str, list[dict]] = {}
    for row in interview_rows:
        interviews_by_student.setdefault(row["student_id"], []).append(row)

    applications_by_student: dict[str, list[dict]] = {}
    for row in application_rows:
        applications_by_student.setdefault(row["student_id"], []).append(row)

    rows = []
    for student in students:
        sid = student["student_id"]
        dsa = dsa_by_student.get(sid, {})
        dsa_score = (dsa.get("solved", 0) / max(1, dsa.get("total", 0))) * 100 if dsa else 0

        aptitude_questions = aptitude_questions_by_student.get(sid, [])
        aptitudes = aptitude_by_student.get(sid, [])
        if aptitude_questions:
            aptitude_score_avg = sum(row.get("mastery_score", 0) or 0 for row in aptitude_questions) / max(1, len(aptitude_questions))
            aptitude_accuracy = sum(row.get("accuracy", 0) or 0 for row in aptitude_questions) / max(1, len(aptitude_questions))
            speed_score = sum(row.get("speed", 0) or 0 for row in aptitude_questions) / max(1, len(aptitude_questions))
            solved = sum(1 for row in aptitude_questions if row.get("solved"))
            attempted = sum(1 for row in aptitude_questions if row.get("attempted"))
            aptitude_score = (aptitude_score_avg * 0.55) + (aptitude_accuracy * 0.25) + (speed_score * 0.15) + (min(100, solved / max(1, attempted) * 100) * 0.05)
        else:
            aptitude_score_avg = sum(row.get("score_pct", 0) or 0 for row in aptitudes) / max(1, len(aptitudes))
            aptitude_accuracy = sum(row.get("accuracy_pct", 0) or 0 for row in aptitudes) / max(1, len(aptitudes))
            aptitude_time = sum(row.get("avg_time_sec", 0) or 0 for row in aptitudes) / max(1, len(aptitudes))
            speed_score = _clamp_score(100 - max(0, aptitude_time - 45) * 1.15) if aptitudes else 0
            aptitude_score = (aptitude_score_avg * 0.65) + (aptitude_accuracy * 0.25) + (speed_score * 0.10)

        latest_resume = resumes_by_student.get(sid)
        latest_ats = ats_by_student.get(sid)
        ats_score = latest_resume.get("ats_score", 0) if latest_resume else latest_ats.get("score", 0) if latest_ats else student.get("ats_score", 0)

        interviews = interviews_by_student.get(sid, [])
        interview_scores = []
        for row in interviews:
            if row.get("overall_score") is not None:
                interview_scores.append(row.get("overall_score") or 0)
            else:
                interview_scores.append(sum([
                    row.get("confidence_score", 0) or 0,
                    row.get("communication_score", 0) or 0,
                    row.get("technical_score", 0) or 0,
                ]) / 3)
        interview_score = sum(interview_scores) / max(1, len(interview_scores))

        cgpa_score = _clamp_score(((float(student.get("cgpa") or 0) - 5.0) / 5.0) * 100)
        applications = applications_by_student.get(sid, [])
        active_pillars = sum([bool(dsa), bool(aptitude_questions or aptitudes), bool(latest_resume or latest_ats), bool(interviews), bool(applications)])
        active_applications = len([row for row in applications if row.get("stage") not in {"Rejected", "Selected"}])
        consistency_score = _clamp_score((active_pillars / 5 * 65) + (active_applications * 12) + (len(applications) * 3))

        component_scores = {
            "dsa": _clamp_score(dsa_score),
            "aptitude": _clamp_score(aptitude_score),
            "ats": _clamp_score(ats_score),
            "interview": _clamp_score(interview_score),
            "cgpa": _clamp_score(cgpa_score),
            "consistency": _clamp_score(consistency_score),
        }
        overall = round(sum(component_scores[key] * READINESS_WEIGHTS[key] for key in READINESS_WEIGHTS), 1)
        band = _score_band(overall)
        components = {
            key: {"score": round(score, 1), "weight": READINESS_WEIGHTS[key], "status": _component_status(score)}
            for key, score in component_scores.items()
        }
        rows.append({
            "student_id": sid,
            "name": student.get("name"),
            "roll_number": student.get("roll_number"),
            "department": student.get("department"),
            "cgpa": student.get("cgpa"),
            "placement": student.get("placement", {}),
            "readiness_score": overall,
            "readiness_band": band["code"],
            "readiness_label": band["label"],
            "components": components,
            "risks": [
                {"area": key, "severity": "high" if score < 45 else "medium", "score": round(score, 1)}
                for key, score in component_scores.items()
                if score < (55 if key == "cgpa" else 60)
            ][:3],
            "top_recommendations": [],
        })

    rows.sort(key=lambda row: row["readiness_score"], reverse=True)
    scores = [row["readiness_score"] for row in rows]
    by_band: dict[str, int] = {}
    for row in rows:
        by_band[row["readiness_band"]] = by_band.get(row["readiness_band"], 0) + 1
    component_avgs = {
        key: round(sum(row["components"][key]["score"] for row in rows) / max(1, len(rows)), 1)
        for key in READINESS_WEIGHTS
    }
    weak_students = sorted(rows, key=lambda row: row["readiness_score"])[:10]
    return {
        "rows": rows[:200],
        "avg_readiness": round(sum(scores) / max(1, len(scores)), 1),
        "placement_ready": sum(1 for row in rows if row["readiness_score"] >= 72),
        "needs_intervention": sum(1 for row in rows if row["readiness_score"] < 58),
        "by_band": by_band,
        "component_avgs": component_avgs,
        "weak_students": weak_students,
        "institution_id": iid,
        "department": department,
    }


async def _institution_operating_data(
    iid: str,
    *,
    department: Optional[str] = None,
    readiness_limit: int = 1000,
    fast_readiness: bool = False,
) -> dict:
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0}) or {}
    student_query: dict[str, Any] = {"institution_id": iid}
    if department:
        student_query["department"] = department
    students_total = await db.students.count_documents(student_query)
    students_placed = await db.students.count_documents({**student_query, "placement.placed": True})

    years = await db.year_summaries.find({"institution_id": iid}, {"_id": 0}).sort("academic_year", -1).to_list(20)
    latest = years[0] if years else {}
    top_pipe = [
        {"$match": {"institution_id": iid}},
        {"$group": {"_id": "$company", "selects": {"$sum": "$selects"}, "max_ctc": {"$max": "$ctc_lpa"}}},
        {"$sort": {"selects": -1}},
        {"$limit": 12},
    ]
    top_recruiters = await db.placement_records.aggregate(top_pipe).to_list(20)
    top_recruiters = [
        {"company": row["_id"], "selects": row["selects"], "max_ctc": row["max_ctc"]}
        for row in top_recruiters
    ]

    dept_breakdown = []
    for dept in inst.get("departments", []):
        if department and dept != department:
            continue
        placed = await db.students.count_documents({"institution_id": iid, "department": dept, "placement.placed": True})
        total = await db.students.count_documents({"institution_id": iid, "department": dept})
        dept_breakdown.append({"department": dept, "placed": placed, "total": total, "placement_rate": _pct(placed, total)})

    if fast_readiness:
        readiness = await _batch_readiness_summary(iid, department=department, limit=readiness_limit)
    else:
        readiness = await build_readiness_roster(
            db,
            institution_id=iid,
            department=department,
            limit=readiness_limit,
        )

    app_query: dict[str, Any] = {"institution_id": iid}
    if department:
        app_query["department"] = department
    applications = await db.applications.find(app_query, {"_id": 0}).sort("applied_at", -1).limit(500).to_list(500)
    pipeline = _pipeline_counts(applications)
    scheduled_interviews = await db.interview_schedule.count_documents(app_query)

    jobs = await db.jobs.find({"institutions": {"$in": [iid]}}, {"_id": 0}).sort("drive_date", -1).limit(200).to_list(200)
    open_jobs = [job for job in jobs if job.get("status") == "open"]

    enrollment_query: dict[str, Any] = {"institution_id": iid}
    if department:
        dept_students = await db.students.find(student_query, {"_id": 0, "student_id": 1}).to_list(1000)
        enrollment_query["student_id"] = {"$in": [student["student_id"] for student in dept_students]}
    enrollments = await db.enrollments.find(enrollment_query, {"_id": 0}).limit(1000).to_list(1000)
    training_avg = round(sum(row.get("completion_pct", 0) or 0 for row in enrollments) / max(1, len(enrollments)), 1)

    return {
        "institution": inst,
        "department": department,
        "year_summaries": years,
        "latest_year": latest,
        "top_recruiters": top_recruiters,
        "department_breakdown": dept_breakdown,
        "students_total": students_total,
        "students_placed": students_placed,
        "placement_rate": _pct(students_placed, students_total),
        "readiness": readiness,
        "applications": applications,
        "pipeline": pipeline,
        "jobs": jobs,
        "open_jobs": open_jobs,
        "scheduled_interviews": scheduled_interviews,
        "training_avg": training_avg,
    }


async def _recruiter_talent_pool_payload(
    recruiter_id: Optional[str],
    *,
    min_cgpa: float = 6.5,
    min_readiness: float = 0,
    department: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 60,
) -> dict:
    if not recruiter_id:
        return {"items": [], "count": 0, "recruiter_id": None, "institution_ids": []}
    jobs = await db.jobs.find({"recruiter_id": recruiter_id}, {"_id": 0}).to_list(500)
    institution_ids = sorted({iid for job in jobs for iid in job.get("institutions", [])})
    if not institution_ids:
        return {"items": [], "count": 0, "recruiter_id": recruiter_id, "institution_ids": []}
    safe_limit = max(1, min(limit, 120))
    query: dict[str, Any] = {"institution_id": {"$in": institution_ids}, "cgpa": {"$gte": min_cgpa}}
    if department:
        query["department"] = department
    candidates = await db.students.find(
        query,
        {"_id": 0},
    ).limit(120).to_list(120)
    items = []
    skill_filter = skill.lower().strip() if skill else None
    for candidate in candidates:
        if skill_filter and skill_filter not in " ".join(candidate.get("skills", [])).lower():
            continue
        readiness = await build_student_readiness(db, candidate)
        if readiness["score"] < min_readiness:
            continue
        candidate["readiness_score"] = readiness["score"]
        candidate["readiness_band"] = readiness["band"]
        candidate["readiness_label"] = readiness["label"]
        candidate["readiness_components"] = readiness["components"]
        candidate["readiness_risks"] = readiness["risks"][:3]
        candidate["match_reasons"] = [
            f"Readiness {readiness['score']}/100",
            f"CGPA {candidate.get('cgpa')}",
            f"{candidate.get('department')} / {candidate.get('institution_id')}",
        ]
        if skill_filter:
            candidate["match_reasons"].append(f"Skill match: {skill}")
        items.append(candidate)
    items.sort(key=lambda row: row.get("readiness_score", 0), reverse=True)
    items = items[:safe_limit]
    return {
        "items": items,
        "count": len(items),
        "recruiter_id": recruiter_id,
        "institution_ids": institution_ids,
        "filters": {
            "min_cgpa": min_cgpa,
            "min_readiness": min_readiness,
            "department": department,
            "skill": skill,
            "limit": safe_limit,
        },
    }


async def _student_scope_for_user(user: dict, *, department: Optional[str] = None) -> tuple[str, Optional[str], list[dict]]:
    iid = user.get("institution_id") or "inst_kmit"
    if user.get("role") == "student" and user.get("student_id"):
        student = await db.students.find_one({"student_id": user["student_id"]}, {"_id": 0})
        return iid, student.get("department") if student else None, [student] if student else []
    scoped_department = department
    if user.get("role") == "faculty" and user.get("department"):
        scoped_department = user["department"]
    query: dict[str, Any] = {"institution_id": iid}
    if scoped_department:
        query["department"] = scoped_department
    students = await db.students.find(query, {"_id": 0}).to_list(1200)
    return iid, scoped_department, students


def _avg_num(rows: list[dict], key: str) -> float:
    vals = [float(row.get(key) or 0) for row in rows]
    return round(sum(vals) / max(1, len(vals)), 1)


def _health(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 68:
        return "stable"
    if score >= 55:
        return "watch"
    return "critical"


def _module_action(area: str, score: float) -> str:
    if area == "aptitude":
        return "Run timed section drills for the weakest sections."
    if area == "ats":
        return "Push role-specific resume rewrites for low ATS and keyword-match rows."
    if area == "interviews":
        return "Schedule mock interview remediation for low rubric scores."
    if area == "training":
        return "Move low-completion learners into faculty follow-up cohorts."
    if area == "placements":
        return "Prioritize recruiter follow-ups and department-level readiness gaps."
    if area == "dsa":
        return "Assign question-level DSA recovery from the weakest topics."
    return "Review the underlying student queue."


# ============== DSA QUESTION HELPERS ==============
async def _resolve_student_for_user(user: dict) -> tuple[Optional[str], Optional[dict]]:
    sid = user.get("student_id")
    if not sid and user.get("institution_id"):
        student = await db.students.find_one({"institution_id": user.get("institution_id")}, {"_id": 0})
        if student:
            sid = student["student_id"]
            await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"student_id": sid}})
            return sid, student
    student = await db.students.find_one({"student_id": sid}, {"_id": 0}) if sid else None
    return sid, student


async def _sync_topic_progress_from_questions(student: dict, topic_code: str) -> dict:
    topic = DSA_TOPIC_BY_CODE.get(topic_code)
    if not topic:
        raise HTTPException(404, "topic not found")
    questions = await db.dsa_questions.find({"topic_code": topic_code}, {"_id": 0}).sort("order", 1).to_list(600)
    qids = [q["question_id"] for q in questions]
    progress = await db.dsa_question_progress.find(
        {"student_id": student["student_id"], "question_id": {"$in": qids}},
        {"_id": 0},
    ).to_list(600)
    solved = sum(1 for row in progress if row.get("solved"))
    attempted = sum(1 for row in progress if row.get("attempted") or row.get("solved"))
    last_dates = [row.get("last_solved_at") for row in progress if row.get("last_solved_at")]
    row = {
        "progress_id": f"dsa_{student['student_id']}_{topic_code}".lower(),
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "topic_code": topic_code,
        "topic_name": topic["name"],
        "topic_order": topic["order"],
        "total": topic["problems"],
        "solved": solved,
        "attempted": attempted,
        "last_solved_at": max(last_dates) if last_dates else None,
    }
    await db.dsa_progress.update_one(
        {"student_id": student["student_id"], "topic_code": topic_code},
        {"$set": row},
        upsert=True,
    )
    return row


async def _ensure_student_dsa_catalog(student: dict) -> None:
    """Backfill question progress from legacy topic rows and sync topic aggregates."""
    if await db.dsa_questions.count_documents({}) == 0:
        await db.dsa_questions.insert_many(build_dsa_question_bank())

    existing_question_rows = await db.dsa_question_progress.count_documents({"student_id": student["student_id"]})
    if existing_question_rows == 0:
        legacy_rows = await db.dsa_progress.find({"student_id": student["student_id"]}, {"_id": 0}).to_list(100)
        legacy_by_topic = {row["topic_code"]: row for row in legacy_rows}
        inserts = []
        now = datetime.now(timezone.utc).isoformat()
        for topic in STRIVER_TOPICS:
            questions = await db.dsa_questions.find({"topic_code": topic["code"]}, {"_id": 0}).sort("order", 1).to_list(600)
            legacy = legacy_by_topic.get(topic["code"], {})
            old_total = max(1, int(legacy.get("total") or topic["problems"]))
            solved_ratio = min(1, max(0, (legacy.get("solved", 0) or 0) / old_total))
            attempted_ratio = min(1, max(solved_ratio, (legacy.get("attempted", legacy.get("solved", 0)) or 0) / old_total))
            solved = min(topic["problems"], int(round(topic["problems"] * solved_ratio)))
            attempted = min(topic["problems"], max(solved, int(round(topic["problems"] * attempted_ratio))))
            last_solved_at = legacy.get("last_solved_at") or now
            for index, question in enumerate(questions[:attempted], start=1):
                is_solved = index <= solved
                inserts.append({
                    "progress_id": f"dsqp_{uuid.uuid4().hex[:10]}",
                    "student_id": student["student_id"],
                    "institution_id": student["institution_id"],
                    "question_id": question["question_id"],
                    "topic_code": question["topic_code"],
                    "subtopic_code": question["subtopic_code"],
                    "solved": is_solved,
                    "attempted": True,
                    "mastery": 86 if is_solved else 36,
                    "revision_count": 1 if is_solved else 0,
                    "notes": "",
                    "faculty_comments": [],
                    "difficulty": question["difficulty"],
                    "last_solved_at": last_solved_at if is_solved else None,
                    "updated_at": now,
                })
        if inserts:
            await db.dsa_question_progress.insert_many(inserts)

    for topic in STRIVER_TOPICS:
        await _sync_topic_progress_from_questions(student, topic["code"])


async def _student_dsa_question_payload(student: dict) -> dict:
    await _ensure_student_dsa_catalog(student)
    questions = await db.dsa_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(DSA_TOTAL)
    progress_rows = await db.dsa_question_progress.find(
        {"student_id": student["student_id"]},
        {"_id": 0},
    ).to_list(DSA_TOTAL)
    progress_by_question = {row["question_id"]: row for row in progress_rows}
    topic_groups = []
    merged_all = []
    for topic in STRIVER_TOPICS:
        topic_questions = []
        for question in [q for q in questions if q["topic_code"] == topic["code"]]:
            progress = progress_by_question.get(question["question_id"], {})
            merged = {
                **question,
                "solved": bool(progress.get("solved")),
                "attempted": bool(progress.get("attempted") or progress.get("solved")),
                "mastery": int(progress.get("mastery", 0) or 0),
                "revision_count": int(progress.get("revision_count", 0) or 0),
                "notes": progress.get("notes", ""),
                "faculty_comments": progress.get("faculty_comments", []),
                "last_solved_at": progress.get("last_solved_at"),
                "updated_at": progress.get("updated_at"),
            }
            topic_questions.append(merged)
            merged_all.append(merged)
        subtopics = []
        for subtopic_name in sorted({q["subtopic_name"] for q in topic_questions}):
            rows = [q for q in topic_questions if q["subtopic_name"] == subtopic_name]
            subtopics.append({
                "name": subtopic_name,
                "total": len(rows),
                "solved": sum(1 for q in rows if q["solved"]),
                "attempted": sum(1 for q in rows if q["attempted"]),
            })
        attempted = sum(1 for q in topic_questions if q["attempted"])
        topic_groups.append({
            "topic_code": topic["code"],
            "topic_name": topic["name"],
            "topic_order": topic["order"],
            "total": len(topic_questions),
            "solved": sum(1 for q in topic_questions if q["solved"]),
            "attempted": attempted,
            "mastery_avg": round(sum(q["mastery"] for q in topic_questions) / max(1, attempted), 1),
            "subtopics": subtopics,
            "questions": topic_questions,
        })
    return {
        "student_id": student["student_id"],
        "total": DSA_TOTAL,
        "solved": sum(1 for q in merged_all if q["solved"]),
        "attempted": sum(1 for q in merged_all if q["attempted"]),
        "topics": topic_groups,
        "questions": merged_all,
    }


# ============== STARTUP - seed + demo users ==============
async def _ensure_database():
    global client, db, gridfs
    if not MONGO_URL or client is not None:
        return
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    db = client[DB_NAME]
    gridfs = AsyncIOMotorGridFSBucket(db, bucket_name="mou_files")
    await db.command("ping")


async def _ensure_production_minimums():
    seed_columns = ["institutions", "students", "recruiters", "applications", "mous", "revenue_share"]
    missing_seed_columns = [col for col in seed_columns if await db[col].count_documents({}) == 0]
    if missing_seed_columns:
        payload = seed_payload()
        for col in missing_seed_columns:
            items = payload.get(col, [])
            if items:
                await db[col].insert_many(items)

    demo_users = [
        {"email": ADMIN_EMAIL, "name": "Platform Super Admin", "role": "super_admin", "institution_id": None, "department": None},
        {"email": "institution@kmit.in", "name": "KMIT - Institution Admin", "role": "institution_admin", "institution_id": "inst_kmit"},
        {"email": "tpo@kmit.in", "name": "Dr. Neil Gogte", "role": "tpo", "institution_id": "inst_kmit"},
        {"email": "faculty@kmit.in", "name": "Prof. Lavanya Iyer", "role": "faculty", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "student@kmit.in", "name": "Aarav Reddy", "role": "student", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "recruiter@amazon.com", "name": "Priya Sharma (Amazon)", "role": "recruiter", "institution_id": None, "department": None},
        {"email": "tpo@vasavi.ac.in", "name": "Dr. Suresh Kumar", "role": "tpo", "institution_id": "inst_vasavi_pending", "approved": False},
    ]
    for d in demo_users:
        existing = await db.users.find_one({"email": d["email"]})
        if existing is None:
            new = _new_user(
                email=d["email"], name=d["name"], role=d["role"],
                institution_id=d.get("institution_id"),
                department=d.get("department"),
                password=DEFAULT_DEMO_PASSWORD if d["role"] != "super_admin" else ADMIN_PASSWORD,
                approved=d.get("approved", True),
            )
            if d["role"] == "student":
                real_stu = await db.students.find_one(
                    {"institution_id": "inst_kmit", "department": "CSE"}, {"_id": 0}
                )
                if real_stu:
                    new["student_id"] = real_stu["student_id"]
                    await db.students.update_one(
                        {"student_id": real_stu["student_id"]},
                        {"$set": {"name": d["name"], "email": d["email"]}},
                    )
            try:
                await db.users.insert_one(new)
            except Exception as e:
                log.warning("Skipping user %s: %s", d["email"], e)
        else:
            await db.users.update_one({"email": d["email"]}, {"$set": {
                "role": d["role"],
                "institution_id": d.get("institution_id"),
                "department": d.get("department"),
                "approved": d.get("approved", True),
            }})
            if not existing.get("password_hash"):
                pw = ADMIN_PASSWORD if d["role"] == "super_admin" else DEFAULT_DEMO_PASSWORD
                await db.users.update_one({"email": d["email"]}, {"$set": {"password_hash": hash_password(pw)}})
            if d["role"] == "student" and not existing.get("student_id"):
                real_stu = await db.students.find_one(
                    {"institution_id": "inst_kmit", "department": "CSE"}, {"_id": 0}
                )
                if real_stu:
                    await db.users.update_one(
                        {"email": d["email"]},
                        {"$set": {"student_id": real_stu["student_id"]}},
                    )
                    await db.students.update_one(
                        {"student_id": real_stu["student_id"]},
                        {"$set": {"name": d["name"], "email": d["email"]}},
                    )

    if not await db.institutions.find_one({"institution_id": "inst_vasavi_pending"}):
        await db.institutions.insert_one({
            "institution_id": "inst_vasavi_pending",
            "name": "Vasavi College of Engineering",
            "short_name": "VCE",
            "type": "Engineering",
            "city": "Hyderabad", "state": "Telangana",
            "affiliated_university": "Osmania University",
            "departments": ["CSE", "ECE", "IT"],
            "approved": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


@app.on_event("startup")
async def _startup():
    await _ensure_database()
    if MONGO_URL:
        await _ensure_production_minimums()
        return
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("jwt_id", unique=True)
    await db.audit_logs.create_index("created_at")
    await db.dsa_questions.create_index("question_id", unique=True)
    await db.dsa_question_progress.create_index("student_id")
    await db.dsa_question_progress.create_index("question_id")
    await db.dsa_code_submissions.create_index("student_id")
    await db.dsa_code_submissions.create_index("question_id")
    await db.aptitude_questions.create_index("question_id", unique=True)
    await db.aptitude_question_progress.create_index("student_id")
    await db.aptitude_question_progress.create_index("question_id")
    await db.aptitude_test_sessions.create_index("student_id")
    await db.aptitude_test_attempts.create_index("student_id")
    await db.mock_interview_sessions.create_index("student_id")
    await db.resume_versions.create_index("student_id")
    await db.recruiter_shortlists.create_index("recruiter_id")
    await db.recruiter_saved_filters.create_index("recruiter_id")
    await db.password_reset_tokens.create_index("token", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.comm_log.create_index("institution_id")
    await db.revenue_share.create_index("institution_id")
    await db.saved_jobs.create_index([("user_id", 1), ("job_id", 1)], unique=True)
    n_inst = await db.institutions.count_documents({})
    n_students = await db.students.count_documents({})
    n_recruiters = await db.recruiters.count_documents({})
    n_apps = await db.applications.count_documents({})
    if n_inst == 0 or n_students == 0 or n_recruiters == 0 or n_apps == 0:
        log.info("Seeding institutions, students, recruiters, DSA, aptitude…")
        payload = seed_payload()
        for col, items in payload.items():
            if items and await db[col].count_documents({}) == 0:
                await db[col].insert_many(items)
        log.info("Seeded %d institutions, %d students, %d jobs, %d applications, %d DSA rows",
                 len(payload["institutions"]), len(payload["students"]),
                 len(payload["jobs"]), len(payload["applications"]), len(payload["dsa_progress"]))

    if await db.dsa_questions.count_documents({}) == 0:
        await db.dsa_questions.insert_many(build_dsa_question_bank())

    await _ensure_aptitude_catalog()

    # Demo users with password — idempotent
    if await db.dsa_question_progress.count_documents({}) == 0 and await db.dsa_progress.count_documents({}) > 0:
        students_with_dsa = await db.students.find({"institution_id": "inst_kmit"}, {"_id": 0}).to_list(1000)
        for student in students_with_dsa:
            await _ensure_student_dsa_catalog(student)

    if await db.aptitude_question_progress.count_documents({}) == 0 and await db.aptitude_scores.count_documents({}) > 0:
        students_with_aptitude = await db.students.find({"institution_id": "inst_kmit"}, {"_id": 0}).to_list(1000)
        await _ensure_aptitude_progress_for_students(students_with_aptitude)

    if await db.resume_versions.count_documents({}) == 0 and await db.ats_reports.count_documents({}) > 0:
        await _ensure_resume_versions_for_students()

    demo_users = [
        {"email": ADMIN_EMAIL, "name": "Platform Super Admin", "role": "super_admin", "institution_id": None, "department": None},
        {"email": "institution@kmit.in", "name": "KMIT — Institution Admin", "role": "institution_admin", "institution_id": "inst_kmit"},
        {"email": "tpo@kmit.in", "name": "Dr. Neil Gogte", "role": "tpo", "institution_id": "inst_kmit"},
        {"email": "faculty@kmit.in", "name": "Prof. Lavanya Iyer", "role": "faculty", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "student@kmit.in", "name": "Aarav Reddy", "role": "student", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "recruiter@amazon.com", "name": "Priya Sharma (Amazon)", "role": "recruiter", "institution_id": None, "department": None},
        # Legacy / approval-flow demo
        {"email": "tpo@vasavi.ac.in", "name": "Dr. Suresh Kumar", "role": "tpo", "institution_id": "inst_vasavi_pending", "approved": False},
    ]
    for d in demo_users:
        existing = await db.users.find_one({"email": d["email"]})
        if existing is None:
            new = _new_user(
                email=d["email"], name=d["name"], role=d["role"],
                institution_id=d.get("institution_id"),
                department=d.get("department"),
                password=DEFAULT_DEMO_PASSWORD if d["role"] != "super_admin" else ADMIN_PASSWORD,
                approved=d.get("approved", True),
            )
            # Bind student demo to a real seeded student row AND patch the student record
            # to match the User's display name so UI stays consistent across views.
            if d["role"] == "student":
                real_stu = await db.students.find_one(
                    {"institution_id": "inst_kmit", "department": "CSE"}, {"_id": 0}
                )
                if real_stu:
                    new["student_id"] = real_stu["student_id"]
                    await db.students.update_one(
                        {"student_id": real_stu["student_id"]},
                        {"$set": {"name": d["name"], "email": d["email"]}},
                    )
            try:
                await db.users.insert_one(new)
            except Exception as e:
                log.warning("Skipping user %s: %s", d["email"], e)
        else:
            # Reconcile core scope fields so demo accounts always resolve to their seeded
            # institution/department (fixes stale accounts that show empty rosters/zeros).
            await db.users.update_one({"email": d["email"]}, {"$set": {
                "role": d["role"],
                "institution_id": d.get("institution_id"),
                "department": d.get("department"),
                "approved": d.get("approved", True),
            }})
            # Refresh password if missing or admin-password-changed
            if not existing.get("password_hash"):
                pw = ADMIN_PASSWORD if d["role"] == "super_admin" else DEFAULT_DEMO_PASSWORD
                await db.users.update_one({"email": d["email"]}, {"$set": {"password_hash": hash_password(pw)}})
            # Ensure student↔student_id link is set and student name matches
            if d["role"] == "student" and not existing.get("student_id"):
                real_stu = await db.students.find_one(
                    {"institution_id": "inst_kmit", "department": "CSE"}, {"_id": 0}
                )
                if real_stu:
                    await db.users.update_one(
                        {"email": d["email"]},
                        {"$set": {"student_id": real_stu["student_id"]}},
                    )
                    await db.students.update_one(
                        {"student_id": real_stu["student_id"]},
                        {"$set": {"name": d["name"], "email": d["email"]}},
                    )

    # Pending college doc for approval flow
    if not await db.institutions.find_one({"institution_id": "inst_vasavi_pending"}):
        await db.institutions.insert_one({
            "institution_id": "inst_vasavi_pending",
            "name": "Vasavi College of Engineering",
            "short_name": "VCE",
            "type": "Engineering",
            "city": "Hyderabad", "state": "Telangana",
            "affiliated_university": "Osmania University",
            "departments": ["CSE", "ECE", "IT"],
            "approved": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Backfill college health scores so dashboards + the AI risk radar have data on first load.
    # Idempotent (only computes when missing) and fully guarded so it can never break startup.
    try:
        _insts_for_health = await db.institutions.find({}, {"_id": 0, "institution_id": 1, "health_score": 1}).to_list(500)
        for _inst in _insts_for_health:
            _iid = _inst.get("institution_id")
            if _iid and _inst.get("health_score") is None:
                try:
                    await _compute_institution_health(_iid)
                except Exception as _e:  # noqa: BLE001
                    log.warning("Health backfill skipped for %s: %s", _iid, _e)
    except Exception as _e:  # noqa: BLE001
        log.warning("Health backfill skipped: %s", _e)


# ============== HEALTH ==============
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "careeros-v2"}


@app.get("/api/health/deep")
async def deep_health():
    checks = {
        "database": "mongo" if MONGO_URL else "memory",
        "students": await db.students.count_documents({}),
        "institutions": await db.institutions.count_documents({}),
        "recruiters": await db.recruiters.count_documents({}),
        "jobs_open": await db.jobs.count_documents({"status": "open"}),
        "frontend_build": FRONTEND_BUILD.exists(),
    }
    ready = checks["students"] > 0 and checks["institutions"] > 0 and checks["recruiters"] > 0
    return {
        "status": "ready" if ready else "degraded",
        "service": "careeros-v3",
        "release": "v3-phases-7-10",
        "checks": checks,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============== PUBLIC ==============
@app.get("/api/public/landing-stats")
async def landing_stats():
    years = await db.year_summaries.find({"institution_id": "inst_kmit"}, {"_id": 0}).sort("academic_year", -1).to_list(20)
    pipeline = [
        {"$match": {"institution_id": "inst_kmit"}},
        {"$group": {"_id": "$company", "selects": {"$sum": "$selects"}, "max_ctc": {"$max": "$ctc_lpa"}}},
        {"$sort": {"selects": -1}}, {"$limit": 24},
    ]
    top = await db.placement_records.aggregate(pipeline).to_list(40)
    top = [{"company": r["_id"], "selects": r["selects"], "max_ctc": r["max_ctc"]} for r in top]
    n_students = await db.students.count_documents({})
    n_inst = await db.institutions.count_documents({"approved": True})
    return {"years": years, "top_recruiters": top, "totals": {"students": n_students, "institutions": n_inst}}


# ============== AUTH ==============
@app.post("/api/auth/login")
async def login(body: LoginBody, request: Request, response: Response):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        await _audit_log(
            "auth.login_failed",
            outcome="failure",
            metadata={"email": email},
            request=request,
        )
        raise HTTPException(401, "Invalid email or password")
    access_token = await _create_session(user["user_id"], response, request)
    user.pop("_id", None); user.pop("password_hash", None)
    await _audit_log("auth.login", user=user, request=request)
    return {"user": user, "access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/session")
async def auth_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(400, "session_id required")
    async with httpx.AsyncClient(timeout=15) as hx:
        r = await hx.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id})
        if r.status_code != 200:
            raise HTTPException(401, "Emergent auth failed")
        data = r.json()
    email = data["email"].lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"user_id": user_id}, {"$set": {"name": data.get("name", existing["name"]), "picture": data.get("picture")}})
    else:
        is_admin = email == ADMIN_EMAIL
        new = _new_user(email=email, name=data.get("name", email), role="super_admin" if is_admin else "tpo",
                        institution_id=None, password=None, approved=is_admin)
        new["picture"] = data.get("picture")
        await db.users.insert_one(new)
        user_id = new["user_id"]
    access_token = await _create_session(user_id, response, request, token=data.get("session_token"))
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    await _audit_log("auth.oauth_session", user=user_doc, request=request)
    return {"user": user_doc, "access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def auth_me(user=Depends(get_session_user)):
    return user


@app.post("/api/auth/logout")
async def auth_logout(request: Request, response: Response, user=Depends(get_session_user)):
    token = request.cookies.get("session_token")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if token:
        if token.count(".") == 2:
            try:
                claims = decode_access_token(token)
                await db.user_sessions.delete_one({"jwt_id": claims["jti"]})
            except HTTPException:
                await db.user_sessions.delete_one({"session_token": token})
        else:
            await db.user_sessions.delete_one({"session_token": token})
    secure_cookie = _cookie_secure(request)
    response.delete_cookie("session_token", path="/", secure=secure_cookie, samesite="none" if secure_cookie else "lax")
    await _audit_log("auth.logout", user=user, request=request)
    return {"ok": True}


# ============== SIGNUP / ONBOARDING ==============
@app.post("/api/signup")
async def signup(payload: SignupBody, request: Request, user=Depends(get_session_user)):
    if user.get("approved") and user.get("institution_id"):
        return {"status": "already-onboarded"}
    short = payload.short_name or "".join(w[0] for w in payload.college_name.split()).upper()[:6]
    inst_id = f"inst_{uuid.uuid4().hex[:10]}"
    await db.institutions.insert_one({
        "institution_id": inst_id,
        "name": payload.college_name, "short_name": short, "type": "Engineering",
        "affiliated_university": payload.affiliated_university,
        "departments": ["CSE", "IT", "CSE-AIML", "CSE-DS"],
        "partnership_types": [payload.partnership_type or "CRT"],
        "approved": False, "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {
        "role": payload.role, "institution_id": inst_id,
        "department": payload.department, "approved": False,
    }})
    await notify(db, event="signup_requested", to_email=ADMIN_EMAIL,
                 subject=f"New TPO signup — {payload.college_name}",
                 title="New partner signup",
                 body_html=f"<p>{user['name']} ({user['email']}) requested onboarding for <b>{payload.college_name}</b>.</p>",
                 telegram_text=f"🆕 TPO signup · {payload.college_name}")
    await _audit_log(
        "institution.signup_requested",
        user={**user, "institution_id": inst_id, "role": payload.role},
        institution_id=inst_id,
        resource="institution",
        resource_id=inst_id,
        metadata={"college_name": payload.college_name, "requested_role": payload.role},
        request=request,
    )
    return {"status": "pending_approval", "institution_id": inst_id}


# ============== INSTITUTIONS ==============
@app.get("/api/institutions")
async def list_institutions(user=Depends(get_session_user)):
    if user["role"] == "super_admin":
        items = await db.institutions.find({}, {"_id": 0}).to_list(500)
    elif user.get("institution_id"):
        items = await db.institutions.find({"institution_id": user["institution_id"]}, {"_id": 0}).to_list(10)
    else:
        items = []
    return {"items": items}


@app.get("/api/institutions/{institution_id}")
async def get_institution(institution_id: str, user=Depends(get_session_user)):
    if user["role"] != "super_admin" and user.get("institution_id") != institution_id:
        raise HTTPException(403, "Cross-institution access denied")
    inst = await db.institutions.find_one({"institution_id": institution_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "not found")
    return inst


@app.patch("/api/institutions/{institution_id}")
async def update_institution(
    institution_id: str,
    body: dict,
    request: Request,
    user=Depends(require_roles("super_admin", "institution_admin", "tpo")),
):
    require_same_institution(institution_id, user)
    allowed = {"name", "short_name", "city", "state", "affiliated_university", "departments", "tagline", "website"}
    update = {k: v for k, v in body.items() if k in allowed}
    if not update:
        return {"updated": 0}
    r = await db.institutions.update_one({"institution_id": institution_id}, {"$set": update})
    await _audit_log(
        "institution.updated",
        user=user,
        institution_id=institution_id,
        resource="institution",
        resource_id=institution_id,
        metadata={"fields": sorted(update.keys())},
        request=request,
    )
    return {"updated": r.modified_count}


@app.get("/api/institutions/{institution_id}/departments")
async def list_departments(institution_id: str, user=Depends(get_session_user)):
    if user["role"] != "super_admin" and user.get("institution_id") != institution_id:
        raise HTTPException(403, "forbidden")
    items = await db.departments.find({"institution_id": institution_id}, {"_id": 0}).to_list(50)
    return {"items": items}


# ============== STUDENTS ==============
@app.get("/api/students")
async def list_students(
    department: Optional[str] = None, placed: Optional[bool] = None,
    q: Optional[str] = None, limit: int = 200,
    user=Depends(get_session_user),
):
    query: dict = {}
    if user["role"] != "super_admin":
        if not user.get("institution_id"):
            return {"items": [], "count": 0}
        query["institution_id"] = user["institution_id"]
    if user["role"] == "faculty" and user.get("department"):
        query["department"] = user["department"]
    if department:
        query["department"] = department
    if placed is not None:
        query["placement.placed"] = placed
    if q:
        query["$or"] = [{"name": {"$regex": q, "$options": "i"}}, {"roll_number": {"$regex": q, "$options": "i"}}]
    items = await db.students.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return {"items": items, "count": len(items)}


@app.get("/api/search")
async def global_search(q: str = "", user=Depends(get_session_user)):
    """Command-palette search across students, institutions, recruiters, and jobs (role-scoped).

    Scope keys are placed before any $or so the in-memory matcher applies them correctly.
    """
    term = (q or "").strip()
    if len(term) < 2:
        return {"results": []}
    role = user.get("role")
    iid = user.get("institution_id")
    rx = {"$regex": term, "$options": "i"}
    results = []

    if role in {"super_admin", "institution_admin", "tpo", "faculty"}:
        sq = {}
        skip_students = False
        if role != "super_admin":
            if iid:
                sq["institution_id"] = iid
                if role == "faculty" and user.get("department"):
                    sq["department"] = user["department"]
            else:
                skip_students = True
        if not skip_students:
            sq["$or"] = [{"name": rx}, {"roll_number": rx}]
            for s in await db.students.find(sq, {"_id": 0}).limit(6).to_list(6):
                sub = " / ".join([x for x in [s.get("roll_number"), s.get("department")] if x])
                results.append({"category": "student", "label": s.get("name"), "sublabel": sub, "id": s.get("student_id")})

    if role == "super_admin":
        for inst in await db.institutions.find({"$or": [{"name": rx}, {"short_name": rx}]}, {"_id": 0}).limit(6).to_list(6):
            results.append({"category": "institution", "label": inst.get("name"), "sublabel": inst.get("short_name"), "id": inst.get("institution_id")})

    if role in {"super_admin", "institution_admin", "tpo"}:
        for rec in await db.recruiters.find({"name": rx}, {"_id": 0}).limit(6).to_list(6):
            results.append({"category": "recruiter", "label": rec.get("name"), "sublabel": rec.get("industry"), "id": rec.get("recruiter_id")})

    jq = {}
    if role != "super_admin" and iid:
        jq["institutions"] = {"$in": [iid]}
    jq["$or"] = [{"title": rx}, {"company": rx}]
    for job in await db.jobs.find(jq, {"_id": 0}).limit(6).to_list(6):
        results.append({"category": "job", "label": job.get("title"), "sublabel": job.get("company"), "id": job.get("job_id")})

    return {"results": results[:18]}


@app.post("/api/students")
async def add_student(
    body: dict,
    request: Request,
    user=Depends(require_roles("super_admin", "tpo", "institution_admin", "faculty")),
):
    body["student_id"] = body.get("student_id") or f"stu_{uuid.uuid4().hex[:10]}"
    if user["role"] == "super_admin":
        if not body.get("institution_id"):
            raise HTTPException(400, "institution_id required")
    else:
        if not user.get("institution_id"):
            raise HTTPException(403, "Institution scope required")
        body["institution_id"] = user["institution_id"]
        if user["role"] == "faculty" and user.get("department"):
            body["department"] = user["department"]
    body.setdefault("placement", {"placed": False})
    body.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    await db.students.insert_one(body)
    await _audit_log(
        "student.created",
        user=user,
        institution_id=body.get("institution_id"),
        resource="student",
        resource_id=body["student_id"],
        metadata={"department": body.get("department")},
        request=request,
    )
    return {"student_id": body["student_id"]}


@app.get("/api/students/{student_id}")
async def get_student(student_id: str, user=Depends(get_session_user)):
    s = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "not found")
    if user["role"] not in ("super_admin",) and s["institution_id"] != user.get("institution_id"):
        raise HTTPException(403, "forbidden")
    enrolls = await db.enrollments.find({"student_id": student_id}, {"_id": 0}).to_list(20)
    apps = await db.applications.find({"student_id": student_id}, {"_id": 0}).to_list(20)
    resumes = await db.resume_versions.find({"student_id": student_id}, {"_id": 0}).to_list(20)
    interviews = await db.interview_reports.find({"student_id": student_id}, {"_id": 0}).to_list(20)
    return {"student": s, "enrollments": enrolls, "applications": apps, "resume_versions": resumes, "interview_reports": interviews}


# ============== STUDENT PERSONAL (logged-in student) ==============
@app.get("/api/me/dashboard")
async def my_dashboard(user=Depends(require_roles("student"))):
    sid, s = await _resolve_student_for_user(user)
    if not s:
        raise HTTPException(404, "no student record bound")
    await _ensure_student_dsa_catalog(s)
    dsa = await db.dsa_progress.find(
        {"student_id": sid, "topic_code": {"$in": DSA_TOPIC_CODES}},
        {"_id": 0},
    ).sort("topic_order", 1).to_list(50)
    apt = await db.aptitude_scores.find({"student_id": sid}, {"_id": 0}).to_list(20)
    ats = await db.ats_reports.find({"student_id": sid}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    interviews = await db.interview_reports.find({"student_id": sid}, {"_id": 0}).sort("conducted_at", -1).limit(10).to_list(10)
    apps = await db.applications.find({"student_id": sid}, {"_id": 0}).sort("applied_at", -1).limit(20).to_list(20)
    readiness = await build_student_readiness(db, s)
    s["readiness_score"] = readiness["score"]
    s["readiness_band"] = readiness["band"]
    s["readiness_label"] = readiness["label"]
    # Recommendations: open jobs for this student's institution + stream
    inst_id = s["institution_id"]
    recs = await db.jobs.find({"institutions": inst_id, "status": "open"}, {"_id": 0}).limit(6).to_list(6)
    return {
        "student": s, "dsa": dsa, "aptitude": apt,
        "ats": ats[0] if ats else None, "interviews": interviews,
        "applications": apps, "recommended_jobs": recs,
        "readiness_engine": readiness,
        "topics": STRIVER_TOPICS, "aptitude_sections": APTITUDE_SECTIONS,
        "dsa_total": DSA_TOTAL,
    }


# ============== ROLE WORKSPACES ==============
@app.get("/api/workspace/me")
async def my_workspace(user=Depends(get_session_user)):
    role = user.get("role")
    name = _first_name(user.get("name"), "there")

    if role == "student":
        sid, student = await _resolve_student_for_user(user)
        if not student:
            raise HTTPException(404, "no student record bound")
        await _ensure_student_dsa_catalog(student)
        readiness = await build_student_readiness(db, student)
        apps = await db.applications.find({"student_id": sid}, {"_id": 0}).sort("applied_at", -1).limit(20).to_list(20)
        active_apps = [app for app in apps if app.get("stage") not in {"Rejected", "Selected"}]
        jobs = await db.jobs.find(
            {"institutions": {"$in": [student.get("institution_id")]}, "status": "open"},
            {"_id": 0},
        ).sort("drive_date", -1).limit(6).to_list(6)
        signals = readiness.get("signals", {})
        dsa_signal = signals.get("dsa", {})
        ats_signal = signals.get("ats", {})
        return {
            "role": role,
            "title": "Personal Placement OS",
            "eyebrow": "Student workspace",
            "headline": f"Hi {name}. Your next placement moves are ranked.",
            "subtitle": f"{readiness['label']} at {readiness['score']}/100 across DSA, ATS, aptitude, interviews, CGPA, and consistency.",
            "scope": {"institution_id": student.get("institution_id"), "student_id": sid, "department": student.get("department")},
            "kpis": [
                _workspace_kpi("Readiness", readiness["score"], unit="/100", sub=readiness["label"], status=readiness["band"], to="/student"),
                _workspace_kpi("DSA solved", dsa_signal.get("solved", 0), sub=f"of {dsa_signal.get('total', DSA_TOTAL)} A2Z questions", to="/student/dsa"),
                _workspace_kpi("ATS score", ats_signal.get("score", 0), unit="/100", sub=ats_signal.get("source", "profile"), to="/student/applications"),
                _workspace_kpi("Active applications", len(active_apps), sub=f"{len(apps)} total tracked", to="/student/applications"),
            ],
            "actions": [
                _workspace_action(rec["action"], "/student/dsa" if rec["area"] == "dsa" else "/student/applications", priority="high", reason=rec["area"])
                for rec in readiness.get("recommendations", [])
            ],
            "alerts": [
                _workspace_alert(risk["area"].upper(), risk["message"], severity=risk["severity"], to="/student")
                for risk in readiness.get("risks", [])[:3]
            ],
            "sections": {
                "student": student,
                "readiness": readiness,
                "applications": apps,
                "recommended_jobs": jobs,
            },
        }

    if role == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        recruiter = await db.recruiters.find_one({"recruiter_id": recruiter_id}, {"_id": 0}) if recruiter_id else None
        jobs = await db.jobs.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0}).sort("drive_date", -1).limit(120).to_list(120)
        job_ids = [job["job_id"] for job in jobs]
        app_query = {"job_id": {"$in": job_ids}} if job_ids else {"job_id": "__none__"}
        applications = await db.applications.find(app_query, {"_id": 0}).sort("applied_at", -1).limit(500).to_list(500)
        pipeline = _pipeline_counts(applications)
        talent = await _recruiter_talent_pool_payload(recruiter_id, min_cgpa=6.5, limit=24)
        open_jobs = [job for job in jobs if job.get("status") == "open"]
        return {
            "role": role,
            "title": "Talent Intelligence Platform",
            "eyebrow": "Recruiter workspace",
            "headline": f"Hi {name}. Your hiring funnel is live.",
            "subtitle": "Qualified students, open roles, and interview movement across partner institutions.",
            "scope": {"recruiter_id": recruiter_id, "company": recruiter.get("name") if recruiter else None},
            "kpis": [
                _workspace_kpi("Open roles", len(open_jobs), sub=f"{len(jobs)} total drives", to="/recruiter/jobs"),
                _workspace_kpi("Talent pool", talent["count"], sub="ranked by readiness", to="/recruiter/talent"),
                _workspace_kpi("In pipeline", sum(pipeline.values()), sub=f"{pipeline.get('Interview', 0)} interviews", to="/recruiter/applications"),
                _workspace_kpi("Selected", pipeline.get("Selected", 0), sub="conversion wins", status="strong", to="/recruiter/applications"),
            ],
            "actions": [
                _workspace_action("Review top-ready candidates", "/recruiter/talent", priority="high", reason="Talent ranked by readiness score"),
                _workspace_action("Move shortlisted candidates forward", "/recruiter/applications", priority="medium", reason="Pipeline stages need recruiter action"),
                _workspace_action("Schedule interview slots", "/recruiter/schedule", priority="medium", reason="Convert interview-ready candidates"),
            ],
            "alerts": [
                _workspace_alert("Interview backlog", f"{pipeline.get('Interview', 0)} candidates are waiting in Interview.", severity="medium", to="/recruiter/applications")
            ] if pipeline.get("Interview", 0) else [],
            "sections": {
                "recruiter": recruiter,
                "jobs": jobs,
                "applications": applications,
                "pipeline": pipeline,
                "talent": talent["items"],
            },
        }

    if role == "super_admin":
        n_inst = await db.institutions.count_documents({"approved": True})
        n_pending = await db.users.count_documents({"approved": False})
        n_students = await db.students.count_documents({})
        n_apps = await db.applications.count_documents({})
        n_jobs_open = await db.jobs.count_documents({"status": "open"})
        n_recruiters = await db.recruiters.count_documents({})
        placed = await db.students.count_documents({"placement.placed": True})
        estimated_mrr = round(placed * 0.18 * 6 * 1000 / 12, 0)
        by_type = await db.institutions.aggregate([{"$group": {"_id": "$type", "n": {"$sum": 1}}}]).to_list(20)
        pending = await db.users.find({"approved": False}, {"_id": 0, "password_hash": 0}).limit(8).to_list(8)
        audit = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(12).to_list(12)
        return {
            "role": role,
            "title": "Platform Control",
            "eyebrow": "Super admin workspace",
            "headline": f"Good morning, {name}. The platform layer is visible.",
            "subtitle": "Institutions, recruiter network, pending onboarding, audit trail, and revenue proxy in one command surface.",
            "scope": {"platform": "global"},
            "kpis": [
                _workspace_kpi("Institutions", n_inst, sub="approved partners", to="/platform/institutions"),
                _workspace_kpi("Pending signups", n_pending, sub="awaiting decision", status="watch", to="/platform/institutions"),
                _workspace_kpi("Open drives", n_jobs_open, sub=f"{n_recruiters} recruiters", to="/platform/recruiters"),
                _workspace_kpi("MRR proxy", estimated_mrr, unit="INR", sub="revenue-share estimate", to="/platform"),
            ],
            "actions": [
                _workspace_action("Review pending onboarding", "/platform/institutions", priority="high", reason=f"{n_pending} accounts need approval"),
                _workspace_action("Inspect recruiter network", "/platform/recruiters", priority="medium", reason="Network health drives marketplace liquidity"),
                _workspace_action("Check audit activity", "/platform", priority="medium", reason="Security and operations visibility"),
            ],
            "alerts": [
                _workspace_alert("Pending onboarding", f"{n_pending} institution users are waiting for approval.", severity="high", to="/platform/institutions")
            ] if n_pending else [],
            "sections": {
                "stats": {
                    "institutions": n_inst,
                    "pending_signups": n_pending,
                    "students": n_students,
                    "applications": n_apps,
                    "jobs_open": n_jobs_open,
                    "recruiters": n_recruiters,
                    "estimated_mrr_inr": estimated_mrr,
                    "by_type": [{"type": row["_id"], "count": row["n"]} for row in by_type],
                },
                "pending": pending,
                "audit": audit,
            },
        }

    iid = user.get("institution_id") or "inst_kmit"
    department = user.get("department") if role == "faculty" else None
    operating = await _institution_operating_data(iid, department=department)
    inst = operating["institution"]
    readiness = operating["readiness"]
    pipeline = operating["pipeline"]
    latest = operating["latest_year"]

    if role == "faculty":
        component_avgs = readiness.get("component_avgs", {})
        weak = readiness.get("weak_students", [])
        return {
            "role": role,
            "title": "Faculty Batch Intelligence",
            "eyebrow": f"{department or 'Department'} workspace",
            "headline": f"Hi {name}. Your batch risks are already ranked.",
            "subtitle": "Weak student detection across DSA, aptitude, interviews, ATS, consistency, and placement readiness.",
            "scope": {"institution_id": iid, "department": department},
            "kpis": [
                _workspace_kpi("Batch size", readiness.get("count", 0), sub=department or "department", to="/faculty/roster"),
                _workspace_kpi("Readiness avg", readiness.get("avg_readiness", 0), unit="/100", sub=f"{readiness.get('needs_intervention', 0)} need intervention", to="/faculty/roster"),
                _workspace_kpi("DSA avg", component_avgs.get("dsa", 0), unit="/100", sub="question-level A2Z progress", to="/faculty/dsa"),
                _workspace_kpi("Aptitude avg", component_avgs.get("aptitude", 0), unit="/100", sub=f"training avg {operating['training_avg']}%", to="/faculty/aptitude"),
            ],
            "actions": [
                _workspace_action("Open intervention roster", "/faculty/roster", priority="high", reason=f"{len(weak)} lowest readiness students"),
                _workspace_action("Review DSA topic gaps", "/faculty/dsa", priority="high", reason="Question-level DSA signal is now available"),
                _workspace_action("Check interview reports", "/faculty/interviews", priority="medium", reason="Communication and technical rubrics need follow-up"),
            ],
            "alerts": [
                _workspace_alert("Weak student queue", f"{readiness.get('needs_intervention', 0)} students need structured intervention.", severity="high", to="/faculty/roster"),
                _workspace_alert("DSA depth", f"Department DSA component is {component_avgs.get('dsa', 0)}/100.", severity="medium", to="/faculty/dsa"),
            ],
            "sections": operating,
        }

    if role == "institution_admin":
        title = "Institution Mission Control"
        eyebrow = f"{inst.get('short_name', 'Institution')} workspace"
        headline = f"Good morning, {name}. {inst.get('short_name', 'Your institution')} health is ready."
        subtitle = "Department health, recruiter pipeline, readiness, and board-report decisions for the institution layer."
        route = "/institution"
        actions = [
            _workspace_action("Review department health", "/institution/departments", priority="high", reason="Compare placed, ready, and intervention counts"),
            _workspace_action("Export board reports", "/institution/reports", priority="medium", reason="Leadership needs current placement and training packets"),
            _workspace_action("Coordinate announcements", "/institution/announcements", priority="medium", reason="Broadcast decisions to students and staff"),
        ]
    else:
        title = "Placement Command Center"
        eyebrow = f"{inst.get('short_name', 'TPO')} live workspace"
        headline = f"Good morning, {name}. The placement pipeline needs decisions."
        subtitle = "Open drives, application flow, interview scheduling, readiness risks, and recruiter movement for the TPO team."
        route = "/tpo"
        actions = [
            _workspace_action("Move application pipeline", "/tpo/applications", priority="high", reason=f"{sum(pipeline.values())} candidates across stages"),
            _workspace_action("Schedule interview slots", "/tpo/schedule", priority="high", reason=f"{pipeline.get('Interview', 0)} candidates are interview-stage"),
            _workspace_action("Review readiness risks", "/tpo/roster", priority="medium", reason=f"{readiness.get('needs_intervention', 0)} students need intervention"),
        ]

    alerts = []
    if readiness.get("needs_intervention", 0):
        alerts.append(_workspace_alert(
            "Readiness intervention",
            f"{readiness['needs_intervention']} students are below placement readiness threshold.",
            severity="high",
            to=f"{route}/roster" if role == "tpo" else "/institution/departments",
        ))
    if pipeline.get("Interview", 0):
        alerts.append(_workspace_alert(
            "Interview queue",
            f"{pipeline['Interview']} candidates are waiting for interview coordination.",
            severity="medium",
            to=f"{route}/schedule",
        ))

    return {
        "role": role,
        "title": title,
        "eyebrow": eyebrow,
        "headline": headline,
        "subtitle": subtitle,
        "scope": {"institution_id": iid, "institution": inst.get("short_name"), "department": department},
        "kpis": [
            _workspace_kpi("Placement rate", operating["placement_rate"], unit="%", sub=f"{operating['students_placed']}/{operating['students_total']} placed", to=f"{route}/outcomes" if role == "tpo" else "/institution/departments"),
            _workspace_kpi("Readiness avg", readiness.get("avg_readiness", 0), unit="/100", sub=f"{readiness.get('placement_ready', 0)} placement ready", to=f"{route}/roster" if role == "tpo" else "/institution/departments"),
            _workspace_kpi("Open drives", len(operating["open_jobs"]), sub=f"{latest.get('companies', 0)} recruiters this year", to=f"{route}/jobs" if role == "tpo" else "/institution/programs"),
            _workspace_kpi("Training avg", operating["training_avg"], unit="%", sub=f"{operating['scheduled_interviews']} scheduled interviews", to=f"{route}/training" if role == "tpo" else "/institution/programs"),
        ],
        "actions": actions,
        "alerts": alerts,
        "sections": operating,
    }


# ============== DSA INTELLIGENCE ==============
@app.get("/api/dsa/topics")
async def dsa_topics():
    return {"topics": STRIVER_TOPICS, "total": DSA_TOTAL}


@app.get("/api/dsa/questions")
async def dsa_questions(user=Depends(get_session_user)):
    questions = await db.dsa_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(DSA_TOTAL)
    return {"questions": questions, "topics": STRIVER_TOPICS, "total": DSA_TOTAL}


@app.get("/api/me/dsa/questions")
async def my_dsa_questions(user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    return await _student_dsa_question_payload(student)


@app.get("/api/dsa/student/{student_id}/questions")
async def get_student_dsa_questions(student_id: str, user=Depends(require_roles("faculty", "tpo", "institution_admin", "super_admin"))):
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    if user["role"] != "super_admin":
        require_same_institution(student.get("institution_id", ""), user)
    return await _student_dsa_question_payload(student)


@app.patch("/api/me/dsa/questions/{question_id}")
async def update_my_dsa_question(question_id: str, body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    question = await db.dsa_questions.find_one({"question_id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(404, "question not found")

    existing = await db.dsa_question_progress.find_one(
        {"student_id": student["student_id"], "question_id": question_id},
        {"_id": 0},
    ) or {}
    now = datetime.now(timezone.utc).isoformat()
    solved = bool(body.get("solved", existing.get("solved", False)))
    attempted = bool(body.get("attempted", existing.get("attempted", False)) or solved)
    mastery = int(body.get("mastery", existing.get("mastery", 85 if solved else 35) or 0))
    mastery = max(0, min(100, mastery))
    revision_count = int(existing.get("revision_count", 0) or 0)
    if "revision_count" in body:
        revision_count = int(body.get("revision_count") or 0)
    if "revision_delta" in body:
        revision_count += int(body.get("revision_delta") or 0)
    revision_count = max(0, revision_count)
    update = {
        "progress_id": existing.get("progress_id") or f"dsqp_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "question_id": question_id,
        "topic_code": question["topic_code"],
        "subtopic_code": question["subtopic_code"],
        "solved": solved,
        "attempted": attempted,
        "mastery": mastery,
        "revision_count": revision_count,
        "notes": body.get("notes", existing.get("notes", "")),
        "faculty_comments": existing.get("faculty_comments", []),
        "difficulty": question["difficulty"],
        "last_solved_at": now if solved else existing.get("last_solved_at"),
        "updated_at": now,
    }
    await db.dsa_question_progress.update_one(
        {"student_id": student["student_id"], "question_id": question_id},
        {"$set": update},
        upsert=True,
    )
    topic_row = await _sync_topic_progress_from_questions(student, question["topic_code"])
    await _audit_log(
        "dsa.question_progress_updated",
        user=user,
        institution_id=student["institution_id"],
        resource="dsa_question",
        resource_id=question_id,
        metadata={"topic_code": question["topic_code"], "solved": solved, "attempted": attempted},
        request=request,
    )
    return {"question": {**question, **update}, "topic": topic_row}


@app.get("/api/dsa/intelligence")
async def dsa_intelligence(user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if not iid:
        return {"by_topic": [], "leaderboard": []}
    # Faculty narrows to their department
    student_match = {"institution_id": iid}
    if user["role"] == "faculty" and user.get("department"):
        student_match["department"] = user["department"]
    dept_students = await db.students.find(student_match, {"_id": 0, "student_id": 1}).to_list(1000)
    dept_sids = [s["student_id"] for s in dept_students] if user["role"] == "faculty" else None

    match = {"institution_id": iid, "topic_code": {"$in": DSA_TOPIC_CODES}}
    if dept_sids is not None:
        match["student_id"] = {"$in": dept_sids}
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$topic_code", "topic_name": {"$first": "$topic_name"},
                    "topic_order": {"$first": "$topic_order"},
                    "total": {"$first": "$total"}, "solved": {"$sum": "$solved"},
                    "students": {"$sum": 1}}},
        {"$sort": {"topic_order": 1}},
    ]
    by_topic = await db.dsa_progress.aggregate(pipeline).to_list(30)
    by_topic.sort(key=lambda row: DSA_TOPIC_BY_CODE.get(row["_id"], {}).get("order", 999))

    leaderboard_pipe = [
        {"$match": match},
        {"$group": {"_id": "$student_id", "solved": {"$sum": "$solved"}}},
        {"$sort": {"solved": -1}},
        {"$limit": 20},
    ]
    lb = await db.dsa_progress.aggregate(leaderboard_pipe).to_list(30)
    sids = [r["_id"] for r in lb]
    students = await db.students.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(30)
    smap = {s["student_id"]: s for s in students}
    leaderboard = []
    for r in lb:
        s = smap.get(r["_id"], {})
        readiness = await build_student_readiness(db, s) if s else None
        leaderboard.append({
            "student_id": r["_id"], "name": s.get("name", "—"),
            "roll_number": s.get("roll_number", "—"), "department": s.get("department", "—"),
            "solved": r["solved"],
            "readiness": readiness["score"] if readiness else min(100, round(r["solved"] / DSA_TOTAL * 100, 1)),
            "readiness_band": readiness["band"] if readiness else None,
        })
    return {
        "by_topic": by_topic, "leaderboard": leaderboard, "total_problems": DSA_TOTAL,
        "scope": ("department:" + user["department"]) if user["role"] == "faculty" and user.get("department") else "institution",
    }


@app.post("/api/me/dsa/toggle")
async def dsa_toggle(body: dict, user=Depends(require_roles("student"))):
    """Increment/decrement solved count by marking a real question in the topic."""
    _sid, student = await _resolve_student_for_user(user)
    topic = body.get("topic_code")
    delta = int(body.get("delta", 1))
    if not (student and topic):
        raise HTTPException(400, "topic_code required")
    if topic not in DSA_TOPIC_BY_CODE:
        raise HTTPException(404, "topic not found")
    await _ensure_student_dsa_catalog(student)
    questions = await db.dsa_questions.find({"topic_code": topic}, {"_id": 0}).sort("order", 1).to_list(600)
    progress_rows = await db.dsa_question_progress.find(
        {"student_id": student["student_id"], "question_id": {"$in": [q["question_id"] for q in questions]}},
        {"_id": 0},
    ).to_list(600)
    progress_by_question = {row["question_id"]: row for row in progress_rows}
    target = None
    now = datetime.now(timezone.utc).isoformat()
    if delta >= 0:
        for question in questions:
            if not progress_by_question.get(question["question_id"], {}).get("solved"):
                target = question
                break
        if target:
            existing = progress_by_question.get(target["question_id"], {})
            await db.dsa_question_progress.update_one(
                {"student_id": student["student_id"], "question_id": target["question_id"]},
                {"$set": {
                    "progress_id": existing.get("progress_id") or f"dsqp_{uuid.uuid4().hex[:10]}",
                    "student_id": student["student_id"],
                    "institution_id": student["institution_id"],
                    "question_id": target["question_id"],
                    "topic_code": target["topic_code"],
                    "subtopic_code": target["subtopic_code"],
                    "solved": True,
                    "attempted": True,
                    "mastery": max(82, int(existing.get("mastery", 0) or 0)),
                    "revision_count": int(existing.get("revision_count", 0) or 0),
                    "notes": existing.get("notes", ""),
                    "faculty_comments": existing.get("faculty_comments", []),
                    "difficulty": target["difficulty"],
                    "last_solved_at": now,
                    "updated_at": now,
                }},
                upsert=True,
            )
    else:
        for question in reversed(questions):
            if progress_by_question.get(question["question_id"], {}).get("solved"):
                target = question
                break
        if target:
            existing = progress_by_question.get(target["question_id"], {})
            await db.dsa_question_progress.update_one(
                {"student_id": student["student_id"], "question_id": target["question_id"]},
                {"$set": {
                    **existing,
                    "student_id": student["student_id"],
                    "institution_id": student["institution_id"],
                    "question_id": target["question_id"],
                    "topic_code": target["topic_code"],
                    "subtopic_code": target["subtopic_code"],
                    "solved": False,
                    "attempted": True,
                    "mastery": min(50, int(existing.get("mastery", 35) or 35)),
                    "difficulty": target["difficulty"],
                    "updated_at": now,
                }},
                upsert=True,
            )
    row = await _sync_topic_progress_from_questions(student, topic)
    return {"solved": row["solved"], "attempted": row["attempted"], "total": row["total"]}


def _simulated_code_result(question: dict, language: str, code: str, custom_input: str = "") -> dict:
    source = (code or "").strip()
    if not source:
        return {"status": "Runtime Error", "passed": 0, "total": 3, "runtime_ms": 0, "memory_kb": 0, "output": "", "errors": "No code provided."}
    language = (language or "python").lower()
    language_tokens = {
        "python": ["def ", "return", "print("],
        "javascript": ["function", "const ", "let ", "return", "console.log"],
        "java": ["class", "public", "return"],
        "cpp": ["#include", "int main", "return"],
        "c++": ["#include", "int main", "return"],
    }
    tokens = language_tokens.get(language, [])
    structure_score = sum(1 for token in tokens if token in source)
    has_complexity = any(token in source.lower() for token in ["for", "while", "map", "set", "sort", "dp", "queue", "stack", "hash"])
    passed = min(3, structure_score + (1 if has_complexity else 0))
    status = "Accepted" if passed >= 3 else "Wrong Answer" if passed else "Compilation Error"
    runtime_ms = max(12, min(950, len(source) * 2 + (question.get("global_order", 1) % 70)))
    memory_kb = 12000 + (len(source) * 3) + (question.get("order", 1) * 19)
    return {
        "status": status,
        "passed": passed,
        "total": 3,
        "runtime_ms": runtime_ms,
        "memory_kb": memory_kb,
        "output": f"Custom input processed: {custom_input[:120]}" if custom_input else "Sample tests evaluated.",
        "errors": "" if status != "Compilation Error" else f"Add a complete {language} solution structure before running.",
        "test_cases": [
            {"name": "Sample 1", "passed": passed >= 1},
            {"name": "Sample 2", "passed": passed >= 2},
            {"name": "Hidden edge", "passed": passed >= 3},
        ],
    }


@app.get("/api/dsa/student/{student_id}/attempts")
async def get_dsa_attempts(student_id: str, question_id: Optional[str] = None, user=Depends(get_session_user)):
    if user.get("role") == "student" and user.get("student_id") != student_id:
        raise HTTPException(403, "forbidden")
    if user.get("role") not in {"student", "faculty", "tpo", "institution_admin", "super_admin"}:
        raise HTTPException(403, "forbidden")
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    if user.get("role") != "super_admin" and user.get("role") != "student":
        require_same_institution(student.get("institution_id"), user)
    query: dict[str, Any] = {"student_id": student_id}
    if question_id:
        query["question_id"] = question_id
    attempts = await db.dsa_code_submissions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"attempts": attempts, "count": len(attempts)}


@app.get("/api/dsa/student/{student_id}/comments")
async def get_dsa_comments(student_id: str, user=Depends(get_session_user)):
    if user.get("role") == "student" and user.get("student_id") != student_id:
        raise HTTPException(403, "forbidden")
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    if user.get("role") != "super_admin" and user.get("role") != "student":
        require_same_institution(student.get("institution_id"), user)
    comments = await db.dsa_comments.find({"student_id": student_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"comments": comments, "count": len(comments)}


@app.post("/api/dsa/student/{student_id}/attempt")
async def create_dsa_attempt(student_id: str, body: dict, request: Request, user=Depends(get_session_user)):
    if user.get("role") == "student" and user.get("student_id") != student_id:
        raise HTTPException(403, "forbidden")
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    if user.get("role") != "super_admin" and user.get("role") != "student":
        require_same_institution(student.get("institution_id"), user)
    question_id = body.get("question_id")
    question = await db.dsa_questions.find_one({"question_id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(404, "question not found")
    now = datetime.now(timezone.utc).isoformat()
    attempt = {
        "attempt_id": f"dsa_attempt_{uuid.uuid4().hex[:10]}",
        "student_id": student_id,
        "institution_id": student["institution_id"],
        "question_id": question_id,
        "question_title": question.get("title"),
        "topic_code": question.get("topic_code"),
        "status": body.get("status", "attempted"),
        "language": body.get("language"),
        "time_taken": body.get("time_taken"),
        "approach": body.get("approach", ""),
        "notes": body.get("notes", ""),
        "created_by": user["user_id"],
        "created_at": now,
    }
    await db.dsa_code_submissions.insert_one(attempt)
    await _audit_log("dsa.attempt_logged", user=user, institution_id=student["institution_id"], resource="dsa_question", resource_id=question_id, request=request)
    return attempt


@app.post("/api/me/dsa/submissions/run")
async def run_my_dsa_code(body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    question = await db.dsa_questions.find_one({"question_id": body.get("question_id")}, {"_id": 0})
    if not question:
        raise HTTPException(404, "question not found")
    result = _simulated_code_result(question, body.get("language"), body.get("code", ""), body.get("custom_input", ""))
    record = {
        "submission_id": f"dsa_run_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "question_id": question["question_id"],
        "question_title": question.get("title"),
        "topic_code": question.get("topic_code"),
        "language": body.get("language", "python"),
        "code": body.get("code", ""),
        "custom_input": body.get("custom_input", ""),
        "kind": "run",
        "status": result["status"],
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.dsa_code_submissions.insert_one(record)
    await _audit_log("dsa.code_run", user=user, institution_id=student["institution_id"], resource="dsa_question", resource_id=question["question_id"], metadata={"status": result["status"]}, request=request)
    if "_id" in record:
        del record["_id"]
    return record


@app.post("/api/me/dsa/submissions/submit")
async def submit_my_dsa_code(body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    question = await db.dsa_questions.find_one({"question_id": body.get("question_id")}, {"_id": 0})
    if not question:
        raise HTTPException(404, "question not found")
    result = _simulated_code_result(question, body.get("language"), body.get("code", ""), body.get("custom_input", ""))
    accepted = result["status"] == "Accepted"
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "submission_id": f"dsa_sub_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "question_id": question["question_id"],
        "question_title": question.get("title"),
        "topic_code": question.get("topic_code"),
        "language": body.get("language", "python"),
        "code": body.get("code", ""),
        "custom_input": body.get("custom_input", ""),
        "kind": "submit",
        "status": result["status"],
        "result": result,
        "runtime_ms": result["runtime_ms"],
        "memory_kb": result["memory_kb"],
        "created_at": now,
    }
    await db.dsa_code_submissions.insert_one(record)
    await db.dsa_question_progress.update_one(
        {"student_id": student["student_id"], "question_id": question["question_id"]},
        {"$set": {
            "progress_id": f"dsqp_{student['student_id']}_{question['question_id']}".lower(),
            "student_id": student["student_id"],
            "institution_id": student["institution_id"],
            "question_id": question["question_id"],
            "topic_code": question["topic_code"],
            "subtopic_code": question["subtopic_code"],
            "solved": accepted,
            "attempted": True,
            "mastery": 88 if accepted else 42,
            "revision_count": 0,
            "notes": body.get("notes", ""),
            "faculty_comments": [],
            "difficulty": question["difficulty"],
            "last_solved_at": now if accepted else None,
            "last_submission_id": record["submission_id"],
            "best_submission_id": record["submission_id"] if accepted else None,
            "updated_at": now,
        }},
        upsert=True,
    )
    await _sync_topic_progress_from_questions(student, question["topic_code"])
    await _audit_log("dsa.code_submitted", user=user, institution_id=student["institution_id"], resource="dsa_question", resource_id=question["question_id"], metadata={"status": result["status"]}, request=request)
    if "_id" in record:
        del record["_id"]
    return record


# ============== READINESS INTELLIGENCE ==============
@app.get("/api/readiness/me")
async def my_readiness(user=Depends(require_roles("student"))):
    sid = user.get("student_id")
    if not sid:
        raise HTTPException(404, "no student record bound")
    student = await db.students.find_one({"student_id": sid}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    readiness = await build_student_readiness(db, student)
    return {"student": student, "readiness": readiness}


@app.get("/api/me/readiness")
async def my_readiness_compat(user=Depends(require_roles("student"))):
    payload = await my_readiness(user)
    return {"student": payload["student"], **payload["readiness"]}


@app.get("/api/me/ai-analysis")
async def my_ai_analysis(user=Depends(require_roles("student"))):
    sid = user.get("student_id")
    if not sid:
        raise HTTPException(404, "no student record bound")
    student = await db.students.find_one({"student_id": sid}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")

    readiness = await build_student_readiness(db, student)
    dsa_payload = await _student_dsa_question_payload(student)
    dsa_topics = dsa_payload.get("topics", [])
    weak_dsa = sorted(dsa_topics, key=lambda row: row.get("solved", 0) / max(1, row.get("total", 1)))[:5]

    latest_ats = await db.ats_reports.find_one({"student_id": sid}, {"_id": 0}, sort=[("created_at", -1)])
    latest_resume = await db.resume_versions.find_one({"student_id": sid}, {"_id": 0}, sort=[("upload_date", -1)])
    aptitude_attempts = await db.aptitude_test_attempts.find({"student_id": sid}, {"_id": 0}).sort("submitted_at", -1).limit(10).to_list(10)
    aptitude_progress = await db.aptitude_progress.find({"student_id": sid}, {"_id": 0}).to_list(500)
    interviews = await db.interview_reports.find({"student_id": sid}, {"_id": 0}).sort("conducted_at", -1).limit(10).to_list(10)
    submissions = await db.dsa_code_submissions.find({"student_id": sid}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    applications = await db.applications.find({"student_id": sid}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)

    aptitude_accuracy = round(
        sum(float(row.get("accuracy", 0) or row.get("score", 0) or 0) for row in aptitude_progress) / max(1, len(aptitude_progress)),
        1,
    )
    interview_avg = round(
        sum(float(row.get("overall_score", 0) or 0) for row in interviews) / max(1, len(interviews)),
        1,
    ) if interviews else 0
    ats_score = float((latest_resume or {}).get("ats_score") or (latest_ats or {}).get("ats_score") or (latest_ats or {}).get("score") or 0)
    component_rows = [
        {"key": key, "label": key.replace("_", " ").title(), **value}
        for key, value in readiness.get("components", {}).items()
    ]
    weakest_components = sorted(component_rows, key=lambda row: float(row.get("score", 0)))[:3]
    actions = []
    for row in weakest_components:
        key = row["key"]
        if key == "dsa":
            actions.append("Solve two medium A2Z problems daily from your weakest DSA topics.")
        elif key == "aptitude":
            actions.append("Take one timed aptitude sectional test and review every wrong answer.")
        elif key == "ats":
            actions.append("Upload a revised resume and close the highest-impact missing keywords.")
        elif key == "interview":
            actions.append("Complete one mock interview and record STAR-format responses.")
        elif key == "consistency":
            actions.append("Build a 7-day streak across DSA, aptitude, and interview practice.")
        else:
            actions.append(f"Improve {row['label']} to lift placement readiness.")
    if not actions:
        actions = ["Maintain daily practice streaks and apply to matching drives."]

    prediction = await _student_prediction_payload(sid)
    return {
        "student": student,
        "readiness": readiness,
        "prediction": prediction.get("prediction"),
        "signals": {
            "dsa_solved": dsa_payload.get("solved", 0),
            "dsa_total": dsa_payload.get("total", DSA_TOTAL),
            "aptitude_accuracy": aptitude_accuracy,
            "aptitude_attempts": len(aptitude_attempts),
            "ats_score": ats_score,
            "interview_average": interview_avg,
            "interview_count": len(interviews),
            "applications": len(applications),
            "code_submissions": len(submissions),
        },
        "weak_dsa_topics": weak_dsa,
        "latest_ats": latest_ats or latest_resume,
        "latest_interviews": interviews[:5],
        "recent_submissions": submissions[:5],
        "actions": actions[:5],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/readiness/students")
async def readiness_students(
    department: Optional[str] = None,
    limit: int = 200,
    user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty")),
):
    institution_id = user.get("institution_id") or "inst_kmit"
    scoped_department = department
    if user["role"] == "faculty" and user.get("department"):
        scoped_department = user["department"]
    roster = await build_readiness_roster(
        db,
        institution_id=institution_id,
        department=scoped_department,
        limit=limit,
    )
    roster["scope"] = (
        f"department:{scoped_department}"
        if scoped_department
        else "institution"
    )
    return roster


# ============== APTITUDE INTELLIGENCE ==============
async def _aptitude_question_analytics(user: dict, department: Optional[str] = None) -> dict:
    iid, scoped_department, students = await _student_scope_for_user(user, department=department)
    if not iid:
        return {"questions": [], "topics": [], "sections": [], "priority_students": []}
    await _ensure_aptitude_progress_for_students(students)
    sids = [student["student_id"] for student in students]
    smap = {student["student_id"]: student for student in students}
    progress = await db.aptitude_question_progress.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(50000)
    questions = await db.aptitude_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(1000)
    qmap = {question["question_id"]: question for question in questions}

    by_topic: dict[str, dict[str, Any]] = {}
    by_section: dict[str, dict[str, Any]] = {}
    by_student: dict[str, dict[str, Any]] = {}
    for row in progress:
        question = qmap.get(row["question_id"], {})
        topic_key = f"{row.get('section_code')}::{row.get('topic')}"
        topic = by_topic.setdefault(topic_key, {
            "section_code": row.get("section_code"),
            "section": row.get("section"),
            "topic": row.get("topic"),
            "difficulty_mix": {},
            "attempted": 0,
            "solved": 0,
            "accuracy_sum": 0,
            "speed_sum": 0,
            "mastery_sum": 0,
            "time_sum": 0,
            "students": set(),
            "questions": set(),
        })
        section = by_section.setdefault(row.get("section_code"), {
            "section_code": row.get("section_code"),
            "section": row.get("section"),
            "attempted": 0,
            "solved": 0,
            "accuracy_sum": 0,
            "speed_sum": 0,
            "mastery_sum": 0,
            "time_sum": 0,
            "students": set(),
            "revision_due": 0,
        })
        student_bucket = by_student.setdefault(row["student_id"], {
            "student_id": row["student_id"],
            "attempted": 0,
            "solved": 0,
            "accuracy_sum": 0,
            "speed_sum": 0,
            "mastery_sum": 0,
            "time_sum": 0,
            "revision_due": 0,
            "weak_topics": [],
        })
        for bucket in (topic, section, student_bucket):
            bucket["attempted"] += 1 if row.get("attempted") else 0
            bucket["solved"] += 1 if row.get("solved") else 0
            bucket["accuracy_sum"] += row.get("accuracy", 0) or 0
            bucket["speed_sum"] += row.get("speed", 0) or 0
            bucket["mastery_sum"] += row.get("mastery_score", 0) or 0
            bucket["time_sum"] += row.get("average_time", 0) or 0
        topic["students"].add(row["student_id"])
        topic["questions"].add(row["question_id"])
        topic["difficulty_mix"][question.get("difficulty", row.get("difficulty"))] = topic["difficulty_mix"].get(question.get("difficulty", row.get("difficulty")), 0) + 1
        section["students"].add(row["student_id"])
        if row.get("revision_due"):
            section["revision_due"] += 1
            student_bucket["revision_due"] += 1
        if row.get("mastery_score", 0) < 60:
            student_bucket["weak_topics"].append(row.get("topic"))

    def finish(bucket: dict) -> dict:
        attempted = max(1, bucket.get("attempted", 0))
        return {
            **{k: v for k, v in bucket.items() if not isinstance(v, set) and not k.endswith("_sum")},
            "accuracy": round(bucket.get("accuracy_sum", 0) / attempted, 1),
            "speed": round(bucket.get("speed_sum", 0) / attempted, 1),
            "average_time": round(bucket.get("time_sum", 0) / attempted, 1),
            "mastery_score": round(bucket.get("mastery_sum", 0) / attempted, 1),
            "solve_rate": _pct(bucket.get("solved", 0), attempted, 1),
            "students": len(bucket.get("students", [])) if isinstance(bucket.get("students"), set) else bucket.get("students"),
        }

    topic_rows = [finish(row) for row in by_topic.values()]
    section_rows = [finish(row) for row in by_section.values()]
    student_rows = []
    for row in by_student.values():
        student = smap.get(row["student_id"], {})
        finished = finish(row)
        finished.update({
            "student_name": student.get("name", "-"),
            "roll_number": student.get("roll_number", "-"),
            "department": student.get("department", "-"),
            "weak_topics": sorted(set(row.get("weak_topics", [])))[:5],
        })
        student_rows.append(finished)
    topic_rows.sort(key=lambda row: (row["mastery_score"], row["accuracy"], -row["average_time"]))
    student_rows.sort(key=lambda row: (row["mastery_score"], row["accuracy"], -row["revision_due"]))
    attempted_total = sum(row.get("attempted", 0) for row in section_rows)
    solved_total = sum(row.get("solved", 0) for row in section_rows)
    avg_mastery = round(sum(row.get("mastery_score", 0) for row in section_rows) / max(1, len(section_rows)), 1)
    avg_accuracy = round(sum(row.get("accuracy", 0) for row in section_rows) / max(1, len(section_rows)), 1)
    avg_speed = round(sum(row.get("speed", 0) for row in section_rows) / max(1, len(section_rows)), 1)
    return {
        "catalog_total": len(questions),
        "summary": {
            "students": len(student_rows),
            "attempted": attempted_total,
            "solved": solved_total,
            "solve_rate": _pct(solved_total, max(1, attempted_total), 1),
            "avg_mastery": avg_mastery,
            "avg_accuracy": avg_accuracy,
            "avg_speed": avg_speed,
            "revision_due": sum(row.get("revision_due", 0) for row in section_rows),
            "health": _health((avg_mastery * 0.55) + (avg_accuracy * 0.30) + (avg_speed * 0.15)),
        },
        "sections": sorted(section_rows, key=lambda row: row["mastery_score"]),
        "topics": topic_rows,
        "weak_topics": topic_rows[:8],
        "speed_analysis": sorted(topic_rows, key=lambda row: row["speed"])[:8],
        "accuracy_analysis": sorted(topic_rows, key=lambda row: row["accuracy"])[:8],
        "priority_students": student_rows[:15],
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
    }


@app.get("/api/aptitude/questions")
async def aptitude_questions(user=Depends(get_session_user)):
    await _ensure_aptitude_catalog()
    questions = await db.aptitude_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(1000)
    return {"questions": questions, "sections": APTITUDE_SECTIONS, "total": len(questions)}


@app.get("/api/me/aptitude/questions")
async def my_aptitude_questions(user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    await _ensure_student_aptitude_progress(student)
    questions = await db.aptitude_questions.find({}, {"_id": 0}).sort("global_order", 1).to_list(1000)
    progress = await db.aptitude_question_progress.find({"student_id": student["student_id"]}, {"_id": 0}).to_list(1000)
    by_question = {row["question_id"]: row for row in progress}
    merged = [{**question, **by_question.get(question["question_id"], {})} for question in questions]
    section_rows = []
    for section in APTITUDE_PREP_SECTIONS:
        rows = [row for row in merged if row.get("section_code") == section["code"]]
        attempted = [row for row in rows if row.get("attempted")]
        section_rows.append({
            **section,
            "section_code": section["code"],
            "section_name": section["name"],
            "total": len(rows),
            "solved": sum(1 for row in rows if row.get("solved")),
            "attempted": len(attempted),
            "accuracy": round(sum(row.get("accuracy", 0) or 0 for row in attempted) / max(1, len(attempted)), 1),
            "avg_time": round(sum(row.get("average_time", 0) or 0 for row in attempted) / max(1, len(attempted)), 1),
            "mastery": round(sum(row.get("mastery_score", 0) or 0 for row in attempted) / max(1, len(attempted)), 1),
        })
    attempted_rows = [row for row in merged if row.get("attempted")]
    solved_count = sum(1 for row in merged if row.get("solved"))
    weak_by_topic: dict[str, dict[str, Any]] = {}
    for row in attempted_rows:
        bucket = weak_by_topic.setdefault(f"{row.get('section_code')}::{row.get('topic')}", {
            "section_code": row.get("section_code"),
            "topic": row.get("topic"),
            "attempted": 0,
            "accuracy_sum": 0,
            "mastery_sum": 0,
        })
        bucket["attempted"] += 1
        bucket["accuracy_sum"] += row.get("accuracy", 0) or 0
        bucket["mastery_sum"] += row.get("mastery_score", 0) or 0
    weak_topics = []
    for row in weak_by_topic.values():
        attempted = max(1, row["attempted"])
        weak_topics.append({
            "section_code": row["section_code"],
            "topic": row["topic"],
            "attempted": row["attempted"],
            "accuracy": round(row["accuracy_sum"] / attempted, 1),
            "mastery_score": round(row["mastery_sum"] / attempted, 1),
        })
    weak_topics.sort(key=lambda row: (row["mastery_score"], row["accuracy"]))
    overall_mastery = round(sum(row.get("mastery_score", 0) or 0 for row in attempted_rows) / max(1, len(attempted_rows)), 1)
    overall_accuracy = round(sum(row.get("accuracy", 0) or 0 for row in attempted_rows) / max(1, len(attempted_rows)), 1)
    overall_avg_time = round(sum(row.get("average_time", 0) or 0 for row in attempted_rows) / max(1, len(attempted_rows)), 1)
    return {
        "student_id": student["student_id"],
        "sections": section_rows,
        "catalog_sections": APTITUDE_PREP_SECTIONS,
        "overall": {
            "total": len(merged),
            "attempted": len(attempted_rows),
            "solved": solved_count,
            "score": round((overall_mastery * 0.55) + (overall_accuracy * 0.30) + (_clamp_score(100 - max(0, overall_avg_time - 65) * 0.7) * 0.15), 1),
            "accuracy": overall_accuracy,
            "avg_time": overall_avg_time,
            "mastery": overall_mastery,
        },
        "weak_topics": weak_topics[:8],
        "total": len(questions),
        "attempted": sum(1 for row in merged if row.get("attempted")),
        "solved": sum(1 for row in merged if row.get("solved")),
        "revision_due": sum(1 for row in merged if row.get("revision_due")),
        "questions": merged,
    }


@app.patch("/api/me/aptitude/questions/{question_id}")
async def update_my_aptitude_question(question_id: str, body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    await _ensure_student_aptitude_progress(student)
    question = await db.aptitude_questions.find_one({"question_id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(404, "question not found")
    existing = await db.aptitude_question_progress.find_one({"student_id": student["student_id"], "question_id": question_id}, {"_id": 0}) or {}
    solved = bool(body.get("solved", existing.get("solved", False)))
    attempted = bool(body.get("attempted", existing.get("attempted", False)) or solved)
    accuracy = _clamp_score(body.get("accuracy", existing.get("accuracy", 85 if solved else 45)))
    average_time = max(1, float(body.get("average_time", existing.get("average_time", question.get("expected_time_sec", 75)))))
    speed = _clamp_score(body.get("speed", 100 - max(0, average_time - question.get("expected_time_sec", 75)) * 0.9))
    mastery = _clamp_score(body.get("mastery_score", (accuracy * 0.45) + (speed * 0.35) + (20 if solved else 0)))
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "progress_id": existing.get("progress_id") or f"aptp_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "question_id": question_id,
        "topic": question["topic"],
        "topic_code": question["topic_code"],
        "section": question["section"],
        "section_code": question["section_code"],
        "difficulty": question["difficulty"],
        "solved": solved,
        "attempted": attempted,
        "accuracy": round(accuracy, 1),
        "speed": round(speed, 1),
        "average_time": round(average_time, 1),
        "mastery_score": round(mastery, 1),
        "revision_due": bool(body.get("revision_due", mastery < 72)),
        "last_attempted": now,
        "updated_at": now,
    }
    await db.aptitude_question_progress.update_one(
        {"student_id": student["student_id"], "question_id": question_id},
        {"$set": update},
        upsert=True,
    )
    await _audit_log(
        "aptitude.question_progress_updated",
        user=user,
        institution_id=student["institution_id"],
        resource="aptitude_question",
        resource_id=question_id,
        metadata={"solved": solved, "mastery_score": update["mastery_score"]},
        request=request,
    )
    return {"question": {**question, **update}}


def _public_aptitude_question(question: dict) -> dict:
    return {key: value for key, value in question.items() if key not in {"answer", "answer_index", "explanation"}}


@app.post("/api/me/aptitude/tests/start")
async def start_my_aptitude_test(body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    await _ensure_student_aptitude_progress(student)
    mode = body.get("mode", "sectional")
    section_code = body.get("section_code")
    topic = body.get("topic")
    question_count = int(body.get("question_count") or (30 if mode == "mock" else 12))
    duration_minutes = int(body.get("duration_minutes") or (45 if mode == "mock" else 20))
    query: dict[str, Any] = {"active": True}
    if mode != "mock" and section_code:
        query["section_code"] = section_code
    if topic:
        query["topic"] = topic
    questions = await db.aptitude_questions.find(query, {"_id": 0}).sort("global_order", 1).to_list(1000)
    if not questions:
        raise HTTPException(404, "no questions available for this test")
    selected = questions[:max(1, min(question_count, len(questions)))]
    now = datetime.now(timezone.utc).isoformat()
    session = {
        "test_id": f"apt_test_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "mode": mode,
        "section_code": section_code,
        "topic": topic,
        "question_ids": [q["question_id"] for q in selected],
        "duration_minutes": duration_minutes,
        "status": "in_progress",
        "started_at": now,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat(),
        "answers": {},
        "review_later": [],
        "bookmarks": [],
    }
    await db.aptitude_test_sessions.insert_one(session)
    await _audit_log(
        "aptitude.test_started",
        user=user,
        institution_id=student["institution_id"],
        resource="aptitude_test",
        resource_id=session["test_id"],
        metadata={"mode": mode, "question_count": len(selected)},
        request=request,
    )
    if "_id" in session:
        del session["_id"]
    return {**session, "questions": [_public_aptitude_question(q) for q in selected]}


@app.get("/api/me/aptitude/tests/{test_id}")
async def get_my_aptitude_test(test_id: str, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    session = await db.aptitude_test_sessions.find_one({"test_id": test_id, "student_id": student["student_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(404, "test not found")
    questions = await db.aptitude_questions.find({"question_id": {"$in": session.get("question_ids", [])}}, {"_id": 0}).to_list(500)
    qmap = {q["question_id"]: q for q in questions}
    ordered = [qmap[qid] for qid in session.get("question_ids", []) if qid in qmap]
    return {**session, "questions": [_public_aptitude_question(q) for q in ordered]}


@app.post("/api/me/aptitude/tests/{test_id}/submit")
async def submit_my_aptitude_test(test_id: str, body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    session = await db.aptitude_test_sessions.find_one({"test_id": test_id, "student_id": student["student_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(404, "test not found")
    answers = body.get("answers") or {}
    elapsed_seconds = max(1, int(body.get("elapsed_seconds") or 1))
    review_later = body.get("review_later") or []
    bookmarks = body.get("bookmarks") or []
    questions = await db.aptitude_questions.find({"question_id": {"$in": session.get("question_ids", [])}}, {"_id": 0}).to_list(500)
    now = datetime.now(timezone.utc).isoformat()
    results = []
    correct_count = 0
    attempted_count = 0
    section_perf: dict[str, dict[str, Any]] = {}
    topic_perf: dict[str, dict[str, Any]] = {}
    per_question_time = round(elapsed_seconds / max(1, len(questions)), 1)
    for question in questions:
        qid = question["question_id"]
        selected = answers.get(qid)
        attempted = selected is not None and selected != ""
        correct = attempted and int(selected) == int(question.get("answer_index", -1))
        attempted_count += 1 if attempted else 0
        correct_count += 1 if correct else 0
        accuracy = 100 if correct else 0 if attempted else 0
        speed = _clamp_score(100 - max(0, per_question_time - question.get("expected_time_sec", 75)) * 0.9)
        mastery = _clamp_score((accuracy * 0.55) + (speed * 0.25) + (20 if correct else 8 if attempted else 0))
        progress_update = {
            "progress_id": f"aptp_{student['student_id']}_{qid}".lower(),
            "student_id": student["student_id"],
            "institution_id": student["institution_id"],
            "question_id": qid,
            "topic": question["topic"],
            "topic_code": question["topic_code"],
            "section": question["section"],
            "section_code": question["section_code"],
            "difficulty": question["difficulty"],
            "solved": correct,
            "attempted": attempted,
            "accuracy": accuracy,
            "speed": round(speed, 1),
            "average_time": per_question_time,
            "mastery_score": round(mastery, 1),
            "revision_due": not correct or mastery < 72,
            "last_attempted": now,
            "updated_at": now,
        }
        await db.aptitude_question_progress.update_one(
            {"student_id": student["student_id"], "question_id": qid},
            {"$set": progress_update},
            upsert=True,
        )
        for key, bucket_map in [(question["section_code"], section_perf), (question["topic"], topic_perf)]:
            bucket = bucket_map.setdefault(key, {"name": key, "attempted": 0, "correct": 0, "total": 0, "time": 0})
            bucket["attempted"] += 1 if attempted else 0
            bucket["correct"] += 1 if correct else 0
            bucket["total"] += 1
            bucket["time"] += per_question_time
        results.append({
            "question_id": qid,
            "selected": selected,
            "correct": correct,
            "answer_index": question.get("answer_index"),
            "answer": question.get("answer"),
            "explanation": question.get("explanation"),
            "topic": question.get("topic"),
            "section_code": question.get("section_code"),
            "time_taken": per_question_time,
        })
    score_pct = round(correct_count / max(1, len(questions)) * 100, 1)
    accuracy_pct = round(correct_count / max(1, attempted_count) * 100, 1)
    def finish_perf(rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for row in rows.values():
            output.append({
                **row,
                "accuracy": round(row["correct"] / max(1, row["attempted"]) * 100, 1),
                "avg_time": round(row["time"] / max(1, row["total"]), 1),
            })
        output.sort(key=lambda row: (row["accuracy"], -row["avg_time"]))
        return output
    attempt = {
        "attempt_id": f"apt_attempt_{uuid.uuid4().hex[:10]}",
        "test_id": test_id,
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "mode": session.get("mode"),
        "score_pct": score_pct,
        "accuracy_pct": accuracy_pct,
        "correct": correct_count,
        "attempted": attempted_count,
        "total": len(questions),
        "time_taken_sec": elapsed_seconds,
        "avg_time_sec": round(elapsed_seconds / max(1, len(questions)), 1),
        "section_performance": finish_perf(section_perf),
        "topic_performance": finish_perf(topic_perf),
        "weak_areas": finish_perf(topic_perf)[:5],
        "review_later": review_later,
        "bookmarks": bookmarks,
        "results": results,
        "submitted_at": now,
    }
    await db.aptitude_test_attempts.insert_one(attempt)
    await db.aptitude_test_sessions.update_one(
        {"test_id": test_id, "student_id": student["student_id"]},
        {"$set": {"status": "submitted", "answers": answers, "review_later": review_later, "bookmarks": bookmarks, "submitted_at": now, "score_pct": score_pct}},
    )
    await _audit_log(
        "aptitude.test_submitted",
        user=user,
        institution_id=student["institution_id"],
        resource="aptitude_test",
        resource_id=test_id,
        metadata={"score_pct": score_pct, "accuracy_pct": accuracy_pct},
        request=request,
    )
    if "_id" in attempt:
        del attempt["_id"]
    return attempt


@app.get("/api/me/aptitude/attempts")
async def my_aptitude_attempts(user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    items = await db.aptitude_test_attempts.find({"student_id": student["student_id"]}, {"_id": 0}).sort("submitted_at", -1).to_list(100)
    return {"items": items, "count": len(items)}


@app.get("/api/aptitude/question-analytics")
async def aptitude_question_analytics(department: Optional[str] = None, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    return await _aptitude_question_analytics(user, department=department)


@app.get("/api/aptitude/intelligence")
async def aptitude_intelligence(department: Optional[str] = None, user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if not iid:
        return {"by_section": [], "summary": {"overall_score": 0, "overall_accuracy": 0}}
    _iid, scoped_department, students = await _student_scope_for_user(user, department=department)
    sids = [student["student_id"] for student in students]
    match: dict[str, Any] = {"institution_id": iid}
    if user.get("role") == "student":
        match["student_id"] = {"$in": sids}
    elif scoped_department:
        match["student_id"] = {"$in": sids}
    rows = await db.aptitude_scores.find(match, {"_id": 0}).to_list(5000)
    smap = {student["student_id"]: student for student in students}

    by_code: dict[str, list[dict]] = {}
    for row in rows:
        by_code.setdefault(row["section_code"], []).append(row)

    sections = []
    for section in APTITUDE_SECTIONS:
        section_rows = by_code.get(section["code"], [])
        avg_score = _avg_num(section_rows, "score_pct")
        avg_accuracy = _avg_num(section_rows, "accuracy_pct")
        avg_time = _avg_num(section_rows, "avg_time_sec")
        weakness_index = round(max(0, 75 - avg_score) + max(0, 72 - avg_accuracy) + max(0, avg_time - 75) * 0.35, 1)
        sections.append({
            "_id": section["code"],
            "section_code": section["code"],
            "section_name": section["name"],
            "avg_score": avg_score,
            "avg_accuracy": avg_accuracy,
            "avg_time_sec": avg_time,
            "tests": sum(row.get("tests_taken", 0) or 0 for row in section_rows),
            "students": len({row["student_id"] for row in section_rows}),
            "weakness_index": weakness_index,
            "health": _health((avg_score * 0.7) + (avg_accuracy * 0.3)),
        })

    weak_rows = sorted(
        [row for row in rows if (row.get("score_pct", 0) < 62 or row.get("accuracy_pct", 0) < 65 or row.get("avg_time_sec", 0) > 95)],
        key=lambda row: (row.get("score_pct", 0), row.get("accuracy_pct", 0)),
    )[:15]
    priority_students = []
    for row in weak_rows:
        student = smap.get(row["student_id"], {})
        priority_students.append({
            **row,
            "student_name": student.get("name", "-"),
            "roll_number": student.get("roll_number", "-"),
            "department": student.get("department", "-"),
            "reason": "Low score" if row.get("score_pct", 0) < 62 else "Speed or accuracy risk",
        })

    weak_sections = sorted(sections, key=lambda row: row["weakness_index"], reverse=True)[:3]
    overall_score = _avg_num(rows, "score_pct")
    overall_accuracy = _avg_num(rows, "accuracy_pct")
    question_analytics = await _aptitude_question_analytics(user, department=department) if user.get("role") in {"super_admin", "institution_admin", "tpo", "faculty"} else {}
    recommendations = [
        {
            "area": section["section_name"],
            "action": f"Run timed {section['section_name']} drills; current score {section['avg_score']}% and accuracy {section['avg_accuracy']}%.",
            "severity": "high" if section["weakness_index"] >= 25 else "medium",
        }
        for section in weak_sections
        if section["weakness_index"] > 0
    ]
    return {
        "by_section": sections,
        "sections": APTITUDE_SECTIONS,
        "summary": {
            "overall_score": overall_score,
            "overall_accuracy": overall_accuracy,
            "avg_time_sec": _avg_num(rows, "avg_time_sec"),
            "students": len(sids),
            "tests": sum(row.get("tests_taken", 0) or 0 for row in rows),
            "health": _health((overall_score * 0.7) + (overall_accuracy * 0.3)),
        },
        "weak_sections": weak_sections,
        "priority_students": priority_students,
        "question_analytics": question_analytics,
        "weak_topics": question_analytics.get("weak_topics", []),
        "speed_analysis": question_analytics.get("speed_analysis", []),
        "accuracy_analysis": question_analytics.get("accuracy_analysis", []),
        "recommendations": recommendations,
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
    }


# ============== RESUME ATS ==============
@app.get("/api/ats/intelligence")
async def ats_intelligence(department: Optional[str] = None, user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if not iid:
        return {"avg_score": 0, "rows": [], "summary": {"health": "critical"}}
    _iid, scoped_department, scoped_students = await _student_scope_for_user(user, department=department)
    await _ensure_resume_versions_for_students(scoped_students)
    scoped_sids = [student["student_id"] for student in scoped_students]
    query: dict[str, Any] = {"institution_id": iid}
    if user.get("role") == "student":
        query["student_id"] = {"$in": scoped_sids}
    elif scoped_department:
        query["student_id"] = {"$in": scoped_sids}
    pipeline = [{"$match": query},
                {"$group": {"_id": None, "avg": {"$avg": "$score"}, "count": {"$sum": 1}}}]
    agg = await db.ats_reports.aggregate(pipeline).to_list(1)
    rows = await db.ats_reports.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    version_query: dict[str, Any] = {"institution_id": iid}
    if scoped_sids:
        version_query["student_id"] = {"$in": scoped_sids}
    versions = await db.resume_versions.find(version_query, {"_id": 0}).sort("upload_date", -1).limit(250).to_list(250)
    sids = list({r["student_id"] for r in rows})
    students = await db.students.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(200)
    smap = {s["student_id"]: s for s in students}
    for r in rows:
        s = smap.get(r["student_id"], {})
        r["student_name"] = s.get("name", "—")
        r["roll_number"] = s.get("roll_number", "—")
        r["department"] = s.get("department", "—")
    for row in rows:
        row["risk_level"] = "high" if row.get("score", 0) < 60 else "medium" if row.get("score", 0) < 75 else "low"
    keyword_counts: dict[str, int] = {}
    for row in rows + versions:
        for keyword in row.get("missing_keywords", []):
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    keyword_heatmap = [
        {"keyword": keyword, "missing_count": count, "coverage_gap_pct": _pct(count, max(1, len(rows)), 1)}
        for keyword, count in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True)
    ]
    priority_students = sorted(
        [row for row in rows if row.get("score", 0) < 72 or row.get("keyword_match_pct", 0) < 65],
        key=lambda row: (row.get("score", 0), row.get("keyword_match_pct", 0)),
    )[:12]
    avg_score = round(agg[0]["avg"], 1) if agg else 0
    avg_keyword = _avg_num(rows, "keyword_match_pct")
    avg_format = _avg_num(rows, "format_score")
    latest_versions: dict[str, dict] = {}
    version_history: dict[str, list[dict]] = {}
    for version in sorted(versions, key=lambda row: (row.get("student_id"), row.get("version") or 0)):
        version_history.setdefault(version["student_id"], []).append(version)
        latest_versions[version["student_id"]] = version
    version_rows = []
    for sid, history in version_history.items():
        student = smap.get(sid, {})
        latest = history[-1]
        first = history[0]
        version_rows.append({
            "student_id": sid,
            "student_name": student.get("name", "-"),
            "roll_number": student.get("roll_number", "-"),
            "department": student.get("department", "-"),
            "versions": len(history),
            "latest_resume_id": latest.get("resume_id"),
            "latest_version": latest.get("version"),
            "ats_score": latest.get("ats_score", 0),
            "keyword_score": latest.get("keyword_score", 0),
            "recruiter_match_score": latest.get("recruiter_match_score", 0),
            "score_delta": round((latest.get("ats_score", 0) or 0) - (first.get("ats_score", 0) or 0), 1),
            "missing_keywords": latest.get("missing_keywords", []),
            "suggestions": latest.get("improvement_suggestions", []),
        })
    version_rows.sort(key=lambda row: (row["ats_score"], row["keyword_score"]))
    skill_gaps = [
        {
            "keyword": item["keyword"],
            "missing_count": item["missing_count"],
            "coverage_gap_pct": item["coverage_gap_pct"],
            "suggestion": f"Add quantified project or internship evidence for {item['keyword']}.",
        }
        for item in keyword_heatmap[:10]
    ]
    recruiter_compatibility = sorted(version_rows, key=lambda row: row["recruiter_match_score"], reverse=True)[:20]
    recommendations = []
    if keyword_heatmap:
        recommendations.append({
            "area": "keyword_heatmap",
            "action": f"Build resume clinics around {keyword_heatmap[0]['keyword']} and adjacent role keywords.",
            "severity": "high" if keyword_heatmap[0]["coverage_gap_pct"] >= 30 else "medium",
        })
    if priority_students:
        recommendations.append({
            "area": "low_ats",
            "action": f"Prioritize {len(priority_students)} low ATS resumes for targeted rewrite.",
            "severity": "high",
        })
    return {
        "avg_score": avg_score,
        "count": agg[0]["count"] if agg else 0,
        "rows": rows[:40],
        "summary": {
            "avg_score": avg_score,
            "avg_keyword_match": avg_keyword,
            "avg_format_score": avg_format,
            "low_score_count": len([row for row in rows if row.get("score", 0) < 65]),
            "format_risk_count": len([row for row in rows if row.get("format_score", 0) < 70]),
            "health": _health((avg_score * 0.65) + (avg_keyword * 0.25) + (avg_format * 0.10)),
        },
        "keyword_heatmap": keyword_heatmap[:12],
        "skill_gaps": skill_gaps,
        "resume_versions": versions[:80],
        "version_history": version_rows[:40],
        "recruiter_compatibility": recruiter_compatibility,
        "priority_students": priority_students,
        "recommendations": recommendations,
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
    }


@app.get("/api/ats/resume-versions")
async def ats_resume_versions(user=Depends(get_session_user)):
    _iid, _dept, students = await _student_scope_for_user(user)
    await _ensure_resume_versions_for_students(students)
    sids = [student["student_id"] for student in students]
    query: dict[str, Any] = {"student_id": {"$in": sids}} if sids else {"student_id": "__none__"}
    versions = await db.resume_versions.find(query, {"_id": 0}).sort("upload_date", -1).to_list(500)
    return {"items": versions, "count": len(versions)}


@app.get("/api/ats/heatmap")
async def ats_heatmap(user=Depends(get_session_user)):
    data = await ats_intelligence(user=user)
    return {
        "keyword_heatmap": data.get("keyword_heatmap", []),
        "skill_gaps": data.get("skill_gaps", []),
        "recruiter_compatibility": data.get("recruiter_compatibility", []),
        "scope": data.get("scope"),
    }


# ============== INTERVIEW REPORTS ==============
@app.get("/api/interviews/intelligence")
async def interviews_intelligence(department: Optional[str] = None, user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if not iid:
        return {"rows": [], "summary": {"health": "critical"}}
    _iid, scoped_department, scoped_students = await _student_scope_for_user(user, department=department)
    scoped_sids = [student["student_id"] for student in scoped_students]
    query: dict[str, Any] = {"institution_id": iid}
    if user.get("role") == "student":
        query["student_id"] = {"$in": scoped_sids}
    elif scoped_department:
        query["student_id"] = {"$in": scoped_sids}
    rows = await db.interview_reports.find(query, {"_id": 0}).sort("conducted_at", -1).limit(120).to_list(120)
    sids = list({r["student_id"] for r in rows})
    students = await db.students.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(120)
    smap = {s["student_id"]: s for s in students}
    for r in rows:
        s = smap.get(r["student_id"], {})
        r["student_name"] = s.get("name", "—")
        r["roll_number"] = s.get("roll_number", "—")
    avg_conf = round(sum(r["confidence_score"] for r in rows) / max(1, len(rows)), 1)
    avg_tech = round(sum(r["technical_score"] for r in rows) / max(1, len(rows)), 1)
    for row in rows:
        student = smap.get(row["student_id"], {})
        row["department"] = student.get("department", row.get("department", "-"))
    rubric_avgs = {
        "confidence": avg_conf,
        "communication": _avg_num(rows, "communication_score"),
        "technical": avg_tech,
        "body_language": _avg_num(rows, "body_language_score"),
        "overall": _avg_num(rows, "overall_score"),
    }
    by_type_map: dict[str, list[dict]] = {}
    for row in rows:
        by_type_map.setdefault(row.get("type", "Mock"), []).append(row)
    by_type = [
        {
            "type": interview_type,
            "count": len(type_rows),
            "avg_overall": _avg_num(type_rows, "overall_score"),
            "avg_technical": _avg_num(type_rows, "technical_score"),
            "avg_communication": _avg_num(type_rows, "communication_score"),
        }
        for interview_type, type_rows in sorted(by_type_map.items())
    ]
    weak_rubrics = [
        {"rubric": key, "score": value, "gap_to_benchmark": round(max(0, 75 - value), 1)}
        for key, value in rubric_avgs.items()
        if key != "overall" and value < 75
    ]
    weak_rubrics.sort(key=lambda row: row["gap_to_benchmark"], reverse=True)
    priority_students = sorted(
        [row for row in rows if row.get("overall_score", 0) < 68 or row.get("technical_score", 0) < 62],
        key=lambda row: (row.get("overall_score", 0), row.get("technical_score", 0)),
    )[:12]
    recommendations = [
        {
            "area": row["rubric"],
            "action": f"Run focused mock interviews for {row['rubric'].replace('_', ' ')}; benchmark gap is {row['gap_to_benchmark']}.",
            "severity": "high" if row["gap_to_benchmark"] >= 15 else "medium",
        }
        for row in weak_rubrics[:3]
    ]
    return {
        "rows": rows[:60],
        "avg_confidence": avg_conf,
        "avg_technical": avg_tech,
        "summary": {
            "reports": len(rows),
            "avg_overall": rubric_avgs["overall"],
            "weak_student_count": len(priority_students),
            "health": _health(rubric_avgs["overall"]),
        },
        "rubric_avgs": rubric_avgs,
        "weak_rubrics": weak_rubrics,
        "by_type": by_type,
        "priority_students": priority_students,
        "recommendations": recommendations,
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
    }


@app.get("/api/interviews/history")
async def interviews_history(user=Depends(get_session_user)):
    _iid, scoped_department, students = await _student_scope_for_user(user)
    sids = [student["student_id"] for student in students]
    smap = {student["student_id"]: student for student in students}
    query: dict[str, Any] = {"student_id": {"$in": sids}} if sids else {"student_id": "__none__"}
    rows = await db.interview_reports.find(query, {"_id": 0}).sort("conducted_at", 1).to_list(1000)
    by_student: dict[str, list[dict]] = {}
    for row in rows:
        by_student.setdefault(row["student_id"], []).append(row)

    timelines = []
    for sid, history in by_student.items():
        student = smap.get(sid, {})
        first = history[0]
        latest = history[-1]
        rubric_latest = {
            "communication": latest.get("communication_score", 0),
            "confidence": latest.get("confidence_score", 0),
            "technical": latest.get("technical_score", 0),
            "hr": latest.get("hr_score", latest.get("body_language_score", 0)),
            "overall": latest.get("overall_score", 0),
        }
        weak_areas = [
            {"area": area, "score": score, "gap": round(max(0, 75 - (score or 0)), 1)}
            for area, score in rubric_latest.items()
            if area != "overall" and (score or 0) < 75
        ]
        weak_areas.sort(key=lambda row: row["gap"], reverse=True)
        timelines.append({
            "student_id": sid,
            "student_name": student.get("name", "-"),
            "roll_number": student.get("roll_number", "-"),
            "department": student.get("department", "-"),
            "interviews": len(history),
            "first_score": first.get("overall_score", 0),
            "latest_score": latest.get("overall_score", 0),
            "improvement": round((latest.get("overall_score", 0) or 0) - (first.get("overall_score", 0) or 0), 1),
            "interview_readiness": _health(latest.get("overall_score", 0) or 0),
            "weak_areas": weak_areas[:4],
            "latest_feedback": latest.get("feedback"),
            "history": history[-6:],
        })
    timelines.sort(key=lambda row: (row["latest_score"], -row["interviews"]))
    return {
        "items": timelines,
        "weak_area_detection": timelines[:15],
        "improvement_tracking": sorted(timelines, key=lambda row: row["improvement"])[:15],
        "student_timeline": timelines[0]["history"] if user.get("role") == "student" and timelines else [],
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
    }


# ============== PLACEMENT INTELLIGENCE ==============
@app.get("/api/placements/overview")
async def placements_overview(user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    if user["role"] == "super_admin":
        iid = "inst_kmit"
    years = await db.year_summaries.find({"institution_id": iid}, {"_id": 0}).sort("academic_year", -1).to_list(20)
    records = await db.placement_records.find({"institution_id": iid}, {"_id": 0}).to_list(500)
    placed = await db.students.count_documents({"institution_id": iid, "placement.placed": True})
    total = await db.students.count_documents({"institution_id": iid})
    pipeline = [{"$match": {"institution_id": iid}},
                {"$group": {"_id": "$company", "selects": {"$sum": "$selects"}, "max_ctc": {"$max": "$ctc_lpa"}}},
                {"$sort": {"selects": -1}}, {"$limit": 12}]
    top = await db.placement_records.aggregate(pipeline).to_list(20)
    top = [{"company": r["_id"], "selects": r["selects"], "max_ctc": r["max_ctc"]} for r in top]
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0})
    dept_breakdown = []
    for d in (inst["departments"] if inst else []):
        p = await db.students.count_documents({"institution_id": iid, "department": d, "placement.placed": True})
        t = await db.students.count_documents({"institution_id": iid, "department": d})
        dept_breakdown.append({"department": d, "placed": p, "total": t, "placement_rate": _pct(p, t)})
    readiness = await build_readiness_roster(db, institution_id=iid, limit=1000)
    latest = years[0] if years else {}
    previous = years[1] if len(years) > 1 else {}
    active_jobs = await db.jobs.find({"institutions": {"$in": [iid]}, "status": "open"}, {"_id": 0}).to_list(200)
    open_capacity = sum(job.get("openings", 0) or 0 for job in active_jobs)
    interview_count = await db.applications.count_documents({"institution_id": iid, "stage": "Interview"})
    historical_conversion = _pct(latest.get("offers", 0), max(1, total), 3) / 100
    forecasted_offers = int(round((latest.get("offers", placed) or placed) + (open_capacity * max(0.08, historical_conversion * 0.22)) + (interview_count * 0.28)))
    risk_departments = sorted(
        [
            {
                **dept,
                "readiness_gap": max(0, 72 - readiness["avg_readiness"]),
                "placement_gap": max(0, 70 - dept.get("placement_rate", 0)),
            }
            for dept in dept_breakdown
            if dept.get("placement_rate", 0) < 70
        ],
        key=lambda row: row["placement_rate"],
    )
    return {
        "year_summaries": years, "records": records, "top_recruiters": top,
        "department_breakdown": dept_breakdown,
        "students_placed": placed, "students_total": total,
        "forecast": {
            "latest_year": latest.get("academic_year"),
            "current_offers": latest.get("offers", placed),
            "previous_offers": previous.get("offers", 0),
            "gap_to_previous": (latest.get("offers", 0) or 0) - (previous.get("offers", 0) or 0),
            "open_drive_capacity": open_capacity,
            "interview_stage_count": interview_count,
            "forecasted_offers": forecasted_offers,
            "confidence": "medium" if active_jobs else "low",
        },
        "risk_departments": risk_departments[:5],
        "recommendations": [
            {
                "area": "department_health",
                "action": f"Intervene in {risk_departments[0]['department']} placement readiness first.",
                "severity": "high",
            }
        ] if risk_departments else [],
        "readiness": {
            "avg_readiness": readiness["avg_readiness"],
            "placement_ready": readiness["placement_ready"],
            "needs_intervention": readiness["needs_intervention"],
            "by_band": readiness["by_band"],
            "component_avgs": readiness["component_avgs"],
            "weak_students": readiness["weak_students"],
        },
    }


@app.get("/api/placements/intelligence")
async def placement_intelligence(department: Optional[str] = None, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    analytics = await _analytics_engine_payload(user, department=department)
    iid = analytics["scope"]["institution_id"]
    scoped_department = analytics["scope"].get("department")
    readiness = await _batch_readiness_summary(iid, department=scoped_department, limit=1500)
    risk_students = sorted(
        [
            row for row in readiness.get("weak_students", [])
            if row.get("readiness_score", 0) < 68 or not row.get("placement", {}).get("placed")
        ],
        key=lambda row: row.get("readiness_score", 0),
    )[:20]
    app_query: dict[str, Any] = {"institution_id": iid}
    if scoped_department:
        app_query["department"] = scoped_department
    applications = await db.applications.find(app_query, {"_id": 0}).to_list(5000)
    recruiter_map: dict[str, dict[str, Any]] = {}
    for application in applications:
        company = application.get("company") or "Unknown"
        row = recruiter_map.setdefault(company, {"company": company, "applications": 0, "selected": 0, "interviews": 0, "rejected": 0})
        row["applications"] += 1
        if application.get("stage") == "Selected":
            row["selected"] += 1
        elif application.get("stage") == "Interview":
            row["interviews"] += 1
        elif application.get("stage") == "Rejected":
            row["rejected"] += 1
    recruiter_conversions = []
    for row in recruiter_map.values():
        row["conversion_rate"] = _pct(row["selected"], max(1, row["applications"]), 1)
        row["interview_rate"] = _pct(row["interviews"], max(1, row["applications"]), 1)
        recruiter_conversions.append(row)
    recruiter_conversions.sort(key=lambda row: (row["conversion_rate"], row["applications"]), reverse=True)
    readiness_trends = [
        {
            "band": band,
            "students": count,
            "share": _pct(count, max(1, len(readiness.get("rows", []))), 1),
        }
        for band, count in readiness.get("by_band", {}).items()
    ]
    return {
        "scope": analytics["scope"],
        "forecast": analytics["forecast"],
        "placement_funnel": analytics["funnel"],
        "department_analytics": analytics["department_health"],
        "institution_analytics": analytics["summary"],
        "risk_students": risk_students,
        "recruiter_conversions": recruiter_conversions[:20],
        "readiness_trends": readiness_trends,
        "recommendations": analytics["recommendations"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============== TRAINING ==============
@app.get("/api/cohorts")
async def list_cohorts(user=Depends(get_session_user)):
    iid = user.get("institution_id")
    query = {} if user["role"] == "super_admin" else {"institution_id": iid}
    items = await db.training_programs.find(query, {"_id": 0}).to_list(200)
    return {"items": items, "programs": PROGRAMS}


@app.get("/api/training/completion")
async def training_completion(user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    pipeline = [{"$match": {"institution_id": iid}},
                {"$group": {"_id": "$program_code",
                            "avg_completion": {"$avg": "$completion_pct"},
                            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                            "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
                            "enrolled": {"$sum": 1}}}]
    by_program = await db.enrollments.aggregate(pipeline).to_list(20)
    prog_map = {p["code"]: p for p in PROGRAMS}
    for r in by_program:
        meta = prog_map.get(r["_id"], {})
        r["program_code"] = r["_id"]; r["program_name"] = meta.get("name", r["_id"])
        r["modules"] = meta.get("modules"); r["avg_completion"] = round(r["avg_completion"] or 0, 1)
    enroll_rows = await db.enrollments.find({"institution_id": iid}, {"_id": 0}).sort("completion_pct", -1).limit(80).to_list(80)
    sids = list({e["student_id"] for e in enroll_rows})
    students = await db.students.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(200)
    smap = {s["student_id"]: s for s in students}
    for e in enroll_rows:
        s = smap.get(e["student_id"], {})
        e["student_name"] = s.get("name", "—")
        e["roll_number"] = s.get("roll_number", "—")
        e["department"] = s.get("department", "—")
    for row in enroll_rows:
        row["risk_level"] = "high" if row.get("completion_pct", 0) < 45 else "medium" if row.get("completion_pct", 0) < 65 else "low"
    weak_programs = sorted(
        [
            {
                **program,
                "completion_gap": round(max(0, 75 - (program.get("avg_completion", 0) or 0)), 1),
                "health": _health(program.get("avg_completion", 0) or 0),
            }
            for program in by_program
        ],
        key=lambda row: row["avg_completion"],
    )
    priority_students = sorted(
        [row for row in enroll_rows if row.get("completion_pct", 0) < 60],
        key=lambda row: row.get("completion_pct", 0),
    )[:12]
    avg_completion = round(
        sum(program.get("avg_completion", 0) or 0 for program in by_program) / max(1, len(by_program)),
        1,
    )
    return {
        "by_program": by_program,
        "rows": enroll_rows,
        "summary": {
            "avg_completion": avg_completion,
            "programs": len(by_program),
            "enrollments": sum(program.get("enrolled", 0) or 0 for program in by_program),
            "low_completion_count": len(priority_students),
            "health": _health(avg_completion),
        },
        "weak_programs": weak_programs[:5],
        "priority_students": priority_students,
        "recommendations": [
            {
                "area": "training_completion",
                "action": f"Move {len(priority_students)} low-completion learners into faculty follow-up.",
                "severity": "high" if len(priority_students) >= 8 else "medium",
            }
        ] if priority_students else [],
    }


# ============== CROSS-MODULE INTELLIGENCE ==============
@app.get("/api/intelligence/modules")
async def module_intelligence(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    role = user.get("role")
    iid = user.get("institution_id") or "inst_kmit"
    if role == "super_admin":
        iid = "inst_kmit"
    scoped_department = user.get("department") if role == "faculty" and user.get("department") else None
    operating = await _institution_operating_data(
        iid,
        department=scoped_department,
        readiness_limit=1500,
        fast_readiness=True,
    )
    readiness = operating["readiness"]

    student_query: dict[str, Any] = {"institution_id": iid}
    if scoped_department:
        student_query["department"] = scoped_department
    scoped_students = await db.students.find(student_query, {"_id": 0, "student_id": 1}).to_list(1500)
    scoped_sids = [student["student_id"] for student in scoped_students]
    dsa_match: dict[str, Any] = {"institution_id": iid, "topic_code": {"$in": DSA_TOPIC_CODES}}
    if scoped_department:
        dsa_match["student_id"] = {"$in": scoped_sids}
    dsa_rows = await db.dsa_progress.find(dsa_match, {"_id": 0}).to_list(20000)
    aptitude = await aptitude_intelligence(user=user)
    ats = await ats_intelligence(user=user)
    interviews = await interviews_intelligence(user=user)
    training = await training_completion(user=user)

    dsa_score = 0
    if dsa_rows:
        by_topic: dict[str, dict[str, int]] = {}
        for row in dsa_rows:
            bucket = by_topic.setdefault(row["topic_code"], {"solved": 0, "total": 0, "students": 0})
            bucket["solved"] += row.get("solved", 0) or 0
            bucket["total"] += row.get("total", 0) or 0
            bucket["students"] += 1
        topic_scores = [
            (row["solved"] / max(1, row["total"])) * 100
            for row in by_topic.values()
        ]
        dsa_score = round(sum(topic_scores) / max(1, len(topic_scores)), 1)
    dsa_leaders = len([row for row in dsa_rows if (row.get("solved", 0) or 0) >= 30])

    cards = [
        {
            "module": "Placement Intelligence",
            "code": "placements",
            "score": readiness["avg_readiness"],
            "health": _health(readiness["avg_readiness"]),
            "primary": f"{operating['students_placed']}/{operating['students_total']} placed",
            "risk": f"{readiness['needs_intervention']} readiness interventions",
            "action": _module_action("placements", readiness["avg_readiness"]),
            "to": "/tpo/outcomes" if user.get("role") == "tpo" else "/institution/departments",
        },
        {
            "module": "DSA Intelligence",
            "code": "dsa",
            "score": dsa_score,
            "health": _health(dsa_score),
            "primary": f"{DSA_TOTAL} A2Z questions",
            "risk": f"{dsa_leaders} leaders tracked",
            "action": _module_action("dsa", dsa_score),
            "to": "/faculty/dsa" if user.get("role") == "faculty" else "/tpo/dsa",
        },
        {
            "module": "Aptitude Intelligence",
            "code": "aptitude",
            "score": aptitude["summary"]["overall_score"],
            "health": aptitude["summary"]["health"],
            "primary": f"{aptitude['summary']['tests']} tests",
            "risk": f"{len(aptitude.get('priority_students', []))} weak rows",
            "action": _module_action("aptitude", aptitude["summary"]["overall_score"]),
            "to": "/faculty/aptitude" if user.get("role") == "faculty" else "/tpo/aptitude",
        },
        {
            "module": "Resume ATS",
            "code": "ats",
            "score": ats["summary"]["avg_score"],
            "health": ats["summary"]["health"],
            "primary": f"{ats['count']} resumes",
            "risk": f"{ats['summary']['low_score_count']} low ATS",
            "action": _module_action("ats", ats["summary"]["avg_score"]),
            "to": "/tpo/ats",
        },
        {
            "module": "Interview Intelligence",
            "code": "interviews",
            "score": interviews["summary"]["avg_overall"],
            "health": interviews["summary"]["health"],
            "primary": f"{interviews['summary']['reports']} reports",
            "risk": f"{interviews['summary']['weak_student_count']} remediation rows",
            "action": _module_action("interviews", interviews["summary"]["avg_overall"]),
            "to": "/faculty/interviews" if user.get("role") == "faculty" else "/tpo/interviews",
        },
        {
            "module": "Training Intelligence",
            "code": "training",
            "score": training["summary"]["avg_completion"],
            "health": training["summary"]["health"],
            "primary": f"{training['summary']['programs']} programs",
            "risk": f"{training['summary']['low_completion_count']} low completion",
            "action": _module_action("training", training["summary"]["avg_completion"]),
            "to": "/faculty/training" if user.get("role") == "faculty" else "/tpo/training",
        },
    ]
    critical_alerts = [
        {
            "module": card["module"],
            "risk": card["risk"],
            "action": card["action"],
            "to": card["to"],
        }
        for card in cards
        if card["health"] in {"critical", "watch"}
    ][:6]
    return {
        "scope": f"department:{scoped_department}" if scoped_department else "institution",
        "cards": cards,
        "critical_alerts": critical_alerts,
        "recommendations": (
            [{
                "area": "placement_readiness",
                "action": f"Move {readiness.get('needs_intervention', 0)} readiness interventions into owned cohorts.",
                "severity": "high" if readiness.get("needs_intervention", 0) else "medium",
            }]
            + aptitude.get("recommendations", [])
            + ats.get("recommendations", [])
            + interviews.get("recommendations", [])
            + training.get("recommendations", [])
        )[:10],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _delta_pct(current: float, previous: float) -> float:
    if not previous:
        return 0
    return round(((current - previous) / previous) * 100, 1)


def _funnel_action(stage: str, leakage: float) -> str:
    if stage == "Applied":
        return "Tighten eligibility screening and publish clearer role-fit criteria."
    if stage == "Shortlisted":
        return "Move shortlist rows into assessment or interview slots within 48 hours."
    if stage == "Assessment":
        return "Add aptitude and coding prep boosters for assessment-stage drop-off."
    if stage == "Interview":
        return "Run recruiter-specific mock interviews and interviewer calibration."
    if stage == "Selected":
        return "Convert selected rows into offer records and package intelligence."
    if leakage >= 35:
        return "Open a review with TPO, faculty owner, and recruiter owner."
    return "Monitor stage movement and remove aging rows."


async def _analytics_engine_payload(user: dict, department: Optional[str] = None) -> dict:
    role = user.get("role")
    iid = user.get("institution_id") or "inst_kmit"
    if role == "super_admin":
        iid = "inst_kmit"
    scoped_department = user.get("department") if role == "faculty" and user.get("department") else department

    operating = await _institution_operating_data(
        iid,
        department=scoped_department,
        readiness_limit=1500,
        fast_readiness=True,
    )
    readiness = operating["readiness"]
    years = operating["year_summaries"]
    latest = years[0] if years else {}
    previous = years[1] if len(years) > 1 else {}
    training = await training_completion(user=user)

    placement_score = operating["placement_rate"]
    readiness_score = readiness.get("avg_readiness", 0)
    training_score = training["summary"]["avg_completion"]
    funnel = operating["pipeline"]
    active_pipeline = funnel.get("Applied", 0) + funnel.get("Shortlisted", 0) + funnel.get("Assessment", 0) + funnel.get("Interview", 0)
    conversion = _pct(funnel.get("Selected", 0), max(1, sum(funnel.values())), 1)
    command_score = round((placement_score * 0.28) + (readiness_score * 0.34) + (training_score * 0.20) + (conversion * 0.18), 1)

    stage_order = ["Applied", "Shortlisted", "Assessment", "Interview", "Selected", "Rejected"]
    funnel_rows = []
    prior_count = None
    for stage in stage_order:
        count = funnel.get(stage, 0)
        leakage = 0 if prior_count in (None, 0) else round(max(0, 1 - (count / prior_count)) * 100, 1)
        funnel_rows.append({
            "stage": stage,
            "count": count,
            "share": _pct(count, max(1, sum(funnel.values())), 1),
            "conversion_from_previous": 100 if prior_count in (None, 0) else round(min(100, (count / prior_count) * 100), 1),
            "leakage": leakage,
            "action": _funnel_action(stage, leakage),
        })
        if stage != "Rejected":
            prior_count = count

    department_health = []
    for dept in operating["department_breakdown"]:
        dept_readiness = await _batch_readiness_summary(iid, department=dept["department"], limit=500)
        placed_rate = dept.get("placement_rate", 0)
        ready_avg = dept_readiness.get("avg_readiness", 0)
        health_score = round((placed_rate * 0.45) + (ready_avg * 0.45) + (training_score * 0.10), 1)
        department_health.append({
            "department": dept["department"],
            "placement_rate": placed_rate,
            "placed": dept.get("placed", 0),
            "total": dept.get("total", 0),
            "readiness_avg": ready_avg,
            "ready_students": dept_readiness.get("placement_ready", 0),
            "interventions": dept_readiness.get("needs_intervention", 0),
            "health_score": health_score,
            "health": _health(health_score),
        })
    department_health.sort(key=lambda row: row["health_score"])

    trend = []
    for index, year in enumerate(reversed(years)):
        prior = list(reversed(years))[index - 1] if index else {}
        trend.append({
            "academic_year": year.get("academic_year"),
            "offers": year.get("offers", 0),
            "companies": year.get("companies", 0),
            "avg_lpa": year.get("avg_lpa", 0),
            "top_offer_lpa": year.get("top_offer_lpa", 0),
            "offer_delta_pct": _delta_pct(year.get("offers", 0), prior.get("offers", 0)),
            "company_delta_pct": _delta_pct(year.get("companies", 0), prior.get("companies", 0)),
        })

    risk_register = []
    if readiness.get("needs_intervention", 0):
        risk_register.append({
            "risk": "Readiness intervention load",
            "severity": "high" if readiness.get("needs_intervention", 0) >= 40 else "medium",
            "signal": f"{readiness.get('needs_intervention', 0)} students need intervention",
            "owner": "Faculty + TPO",
            "action": "Assign cohort owners to the lowest readiness band this week.",
        })
    for dept in department_health[:3]:
        if dept["health"] in {"critical", "watch"}:
            risk_register.append({
                "risk": f"{dept['department']} department health",
                "severity": "high" if dept["health"] == "critical" else "medium",
                "signal": f"{dept['placement_rate']}% placed, {dept['readiness_avg']}/100 readiness",
                "owner": "Department faculty",
                "action": "Run department-specific placement clinic and recruiter matching.",
            })
    worst_funnel = max(funnel_rows[:-1], key=lambda row: row["leakage"], default=None)
    if worst_funnel and worst_funnel["leakage"] >= 25:
        risk_register.append({
            "risk": "Application funnel leakage",
            "severity": "high" if worst_funnel["leakage"] >= 45 else "medium",
            "signal": f"{worst_funnel['leakage']}% leakage around {worst_funnel['stage']}",
            "owner": "TPO operations",
            "action": worst_funnel["action"],
        })

    open_capacity = sum(job.get("openings", 0) or 0 for job in operating["open_jobs"])
    forecast_offers = int(round((latest.get("offers", 0) or operating["students_placed"]) + open_capacity * 0.12 + funnel.get("Interview", 0) * 0.3))
    forecast_confidence = "high" if active_pipeline >= 75 and open_capacity >= 50 else "medium" if active_pipeline >= 30 else "low"
    recommendations = [
        {
            "title": "Protect the conversion path",
            "body": worst_funnel["action"] if worst_funnel else "Keep weekly stage aging reviews in place.",
            "priority": "high" if worst_funnel and worst_funnel["leakage"] >= 35 else "medium",
            "to": "/tpo/applications" if role == "tpo" else "/institution/departments",
        },
        {
            "title": "Move low-readiness students into owned cohorts",
            "body": f"{readiness.get('needs_intervention', 0)} learners need a named faculty intervention owner.",
            "priority": "high" if readiness.get("needs_intervention", 0) >= 40 else "medium",
            "to": "/tpo/roster" if role == "tpo" else "/faculty/roster",
        },
        {
            "title": "Prepare board packet",
            "body": "Export the leadership packet after reviewing forecast confidence and department health.",
            "priority": "medium",
            "to": "/tpo/reports" if role == "tpo" else "/institution/reports",
        },
    ]

    return {
        "scope": {
            "institution_id": iid,
            "institution": operating["institution"].get("short_name") or operating["institution"].get("name"),
            "department": scoped_department,
            "role": role,
        },
        "summary": {
            "command_score": command_score,
            "health": _health(command_score),
            "placement_rate": placement_score,
            "readiness_avg": readiness_score,
            "training_avg": training_score,
            "conversion_rate": conversion,
            "active_pipeline": active_pipeline,
            "offers_latest": latest.get("offers", 0),
            "offers_delta_pct": _delta_pct(latest.get("offers", 0), previous.get("offers", 0)),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "kpis": [
            {"label": "Command score", "value": command_score, "unit": "/100", "health": _health(command_score), "question": "Can leadership trust the current operating rhythm?"},
            {"label": "Forecasted offers", "value": forecast_offers, "unit": "", "health": forecast_confidence, "question": "Where do we land if current pipeline converts?"},
            {"label": "Funnel conversion", "value": conversion, "unit": "%", "health": _health(conversion), "question": "How efficiently does demand become selection?"},
            {"label": "Intervention load", "value": readiness.get("needs_intervention", 0), "unit": "", "health": "watch" if readiness.get("needs_intervention", 0) else "strong", "question": "How much faculty work is required now?"},
        ],
        "trend": trend,
        "funnel": funnel_rows,
        "department_health": department_health,
        "forecast": {
            "forecasted_offers": forecast_offers,
            "confidence": forecast_confidence,
            "open_capacity": open_capacity,
            "interview_stage": funnel.get("Interview", 0),
            "previous_offers": previous.get("offers", 0),
            "latest_offers": latest.get("offers", 0),
        },
        "risk_register": risk_register[:8],
        "recommendations": recommendations,
    }


@app.get("/api/analytics/engine")
async def analytics_engine(
    department: Optional[str] = None,
    user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty")),
):
    return await _analytics_engine_payload(user, department=department)


# ============== APPLICATIONS / JOBS ==============
@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = "open", user=Depends(get_session_user)):
    query = {}
    if status and status != "all":
        query["status"] = status
    if user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        query["recruiter_id"] = recruiter_id or "__none__"
    elif user["role"] != "super_admin" and user.get("institution_id"):
        query["institutions"] = {"$in": [user["institution_id"]]}
    items = await db.jobs.find(query, {"_id": 0}).sort("drive_date", -1).limit(80).to_list(80)
    return {"items": items}


@app.post("/api/jobs")
async def create_job(
    body: dict,
    request: Request,
    user=Depends(require_roles("recruiter", "super_admin", "tpo", "institution_admin")),
):
    body["job_id"] = f"job_{uuid.uuid4().hex[:10]}"
    body.setdefault("status", "open")
    body.setdefault("applied_count", 0)
    body.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    body["created_by"] = user["user_id"]
    if user["role"] != "super_admin" and user.get("institution_id"):
        body["institutions"] = [user["institution_id"]]
    if user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        body["recruiter_id"] = recruiter_id or "__none__"
        body.setdefault("institutions", ["inst_kmit"])
        recruiter = await db.recruiters.find_one({"recruiter_id": recruiter_id}, {"_id": 0}) if recruiter_id else None
        if recruiter and not body.get("company"):
            body["company"] = recruiter.get("name")
    await db.jobs.insert_one(body)
    await _audit_log(
        "job.created",
        user=user,
        institution_id=(body.get("institutions") or [user.get("institution_id") or "global"])[0],
        resource="job",
        resource_id=body["job_id"],
        metadata={"company": body.get("company"), "role": body.get("role")},
        request=request,
    )
    return {"job_id": body["job_id"]}


@app.get("/api/applications")
async def list_applications(stage: Optional[str] = None, company: Optional[str] = None, user=Depends(get_session_user)):
    query = {}
    if user["role"] == "student":
        query["student_id"] = user.get("student_id") or "__none__"
    elif user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        jobs = await db.jobs.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0, "job_id": 1}).to_list(500)
        query["job_id"] = {"$in": [job["job_id"] for job in jobs]}
    elif user["role"] != "super_admin":
        if user.get("institution_id"):
            query["institution_id"] = user["institution_id"]
    if user["role"] == "faculty" and user.get("department"):
        query["department"] = user["department"]
    if stage:
        query["stage"] = stage
    if company:
        query["company"] = company
    items = await db.applications.find(query, {"_id": 0}).sort("applied_at", -1).limit(200).to_list(200)
    # Pipeline counts (same filter without stage)
    pipe_query = {k: v for k, v in query.items() if k != "stage"}
    pipeline = [{"$match": pipe_query},
                {"$group": {"_id": "$stage", "n": {"$sum": 1}}}]
    counts = await db.applications.aggregate(pipeline).to_list(20)
    pipeline_counts = _pipeline_counts(items)
    for count in counts:
        pipeline_counts[count["_id"]] = count["n"]
    total = sum(pipeline_counts.values())
    selected = pipeline_counts.get("Selected", 0)
    rejected = pipeline_counts.get("Rejected", 0)
    active = total - selected - rejected
    analytics = {
        "total": total,
        "active": active,
        "conversion_rate": _pct(selected, max(1, total), 1),
        "interview_rate": _pct(pipeline_counts.get("Interview", 0), max(1, total), 1),
        "drop_rate": _pct(rejected, max(1, total), 1),
        "next_actions": [
            _workspace_action("Advance shortlisted candidates", "/recruiter/applications" if user["role"] == "recruiter" else "/tpo/applications", priority="high", reason=f"{pipeline_counts.get('Shortlisted', 0)} shortlisted candidates need a next step"),
            _workspace_action("Schedule interview queue", "/recruiter/schedule" if user["role"] == "recruiter" else "/tpo/schedule", priority="high", reason=f"{pipeline_counts.get('Interview', 0)} interview-stage candidates"),
        ],
    }
    return {"items": items, "pipeline": pipeline_counts, "analytics": analytics}


@app.patch("/api/applications/{application_id}")
async def update_application(
    application_id: str,
    body: dict,
    request: Request,
    user=Depends(require_roles("super_admin", "tpo", "recruiter", "institution_admin")),
):
    app_doc = await db.applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app_doc:
        raise HTTPException(404, "application not found")
    if user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        job = await db.jobs.find_one({"job_id": app_doc.get("job_id"), "recruiter_id": recruiter_id or "__none__"}, {"_id": 0})
        if not job:
            raise HTTPException(403, "forbidden")
    else:
        require_same_institution(app_doc.get("institution_id"), user)
    allowed = {"stage", "next_step_at", "recruiter_notes", "notes"}
    update = {k: v for k, v in body.items() if k in allowed}
    if not update:
        return {"updated": 0}
    if "stage" in update and update["stage"] not in {"Applied", "Shortlisted", "Assessment", "Interview", "Selected", "Rejected"}:
        raise HTTPException(400, "Invalid application stage")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user["user_id"]
    r = await db.applications.update_one({"application_id": application_id}, {"$set": update})
    # Broadcast live update
    app_doc = await db.applications.find_one({"application_id": application_id}, {"_id": 0})
    if app_doc:
        await ws_manager.broadcast(app_doc["institution_id"], {
            "type": "application.updated",
            "application_id": application_id,
            "stage": app_doc.get("stage"),
            "student_name": app_doc.get("student_name"),
            "company": app_doc.get("company"),
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    await _audit_log(
        "application.updated",
        user=user,
        institution_id=app_doc.get("institution_id") if app_doc else None,
        resource="application",
        resource_id=application_id,
        metadata={"fields": sorted(update.keys()), "stage": update.get("stage")},
        request=request,
    )
    return {"updated": r.modified_count}


# ============== RECRUITER INTELLIGENCE ==============
@app.get("/api/recruiters")
async def list_recruiters(user=Depends(get_session_user)):
    items = await db.recruiters.find({}, {"_id": 0}).sort("hires_total", -1).limit(60).to_list(60)
    return {"items": items}


@app.get("/api/recruiters/me/talent-pool")
async def my_recruiter_talent_pool(
    min_cgpa: float = 6.5,
    min_readiness: float = 0,
    department: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 60,
    user=Depends(require_roles("recruiter")),
):
    recruiter_id = await _resolve_recruiter_id(user)
    return await _recruiter_talent_pool_payload(
        recruiter_id,
        min_cgpa=min_cgpa,
        min_readiness=min_readiness,
        department=department,
        skill=skill,
        limit=limit,
    )


@app.get("/api/recruiters/me/analytics")
async def my_recruiter_analytics(user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    recruiter = await db.recruiters.find_one({"recruiter_id": recruiter_id}, {"_id": 0}) if recruiter_id else None
    jobs = await db.jobs.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0}).sort("drive_date", -1).to_list(500)
    job_ids = [job["job_id"] for job in jobs]
    app_query = {"job_id": {"$in": job_ids}} if job_ids else {"job_id": "__none__"}
    applications = await db.applications.find(app_query, {"_id": 0}).sort("applied_at", -1).to_list(1000)
    pipeline = _pipeline_counts(applications)
    selected = pipeline.get("Selected", 0)
    rejected = pipeline.get("Rejected", 0)
    total = sum(pipeline.values())
    open_jobs = [job for job in jobs if job.get("status") == "open"]
    package_values = [job.get("ctc_lpa", 0) or 0 for job in jobs]

    apps_by_job: dict[str, list[dict]] = {}
    for application in applications:
        apps_by_job.setdefault(application.get("job_id"), []).append(application)
    job_funnels = []
    for job in jobs:
        job_apps = apps_by_job.get(job["job_id"], [])
        counts = _pipeline_counts(job_apps)
        job_funnels.append({
            "job_id": job["job_id"],
            "company": job.get("company"),
            "title": job.get("title"),
            "status": job.get("status"),
            "ctc_lpa": job.get("ctc_lpa"),
            "openings": job.get("openings"),
            "applications": sum(counts.values()),
            "pipeline": counts,
            "conversion_rate": _pct(counts.get("Selected", 0), max(1, sum(counts.values())), 1),
            "interview_rate": _pct(counts.get("Interview", 0), max(1, sum(counts.values())), 1),
        })
    job_funnels.sort(key=lambda row: (row["applications"], row["conversion_rate"]), reverse=True)

    by_inst: dict[str, dict[str, Any]] = {}
    for application in applications:
        iid = application.get("institution_id", "unknown")
        row = by_inst.setdefault(iid, {"institution_id": iid, "applications": 0, "selected": 0, "interview": 0, "rejected": 0})
        row["applications"] += 1
        stage = application.get("stage")
        if stage == "Selected":
            row["selected"] += 1
        elif stage == "Interview":
            row["interview"] += 1
        elif stage == "Rejected":
            row["rejected"] += 1
    inst_docs = await db.institutions.find({"institution_id": {"$in": list(by_inst.keys())}}, {"_id": 0}).to_list(100)
    inst_names = {inst["institution_id"]: inst.get("short_name") or inst.get("name") for inst in inst_docs}
    institution_funnel = []
    for row in by_inst.values():
        row["institution"] = inst_names.get(row["institution_id"], row["institution_id"])
        row["conversion_rate"] = _pct(row["selected"], max(1, row["applications"]), 1)
        institution_funnel.append(row)
    institution_funnel.sort(key=lambda row: row["applications"], reverse=True)

    scheduled = await db.interview_schedule.find(
        {"job_id": {"$in": job_ids}} if job_ids else {"job_id": "__none__"},
        {"_id": 0},
    ).sort("starts_at", 1).to_list(200)
    upcoming = [
        item for item in scheduled
        if item.get("status") != "cancelled" and item.get("starts_at", "") >= datetime.now(timezone.utc).isoformat()
    ][:10]
    talent = await _recruiter_talent_pool_payload(recruiter_id, min_cgpa=6.5, min_readiness=72, limit=20)
    interview_backlog = pipeline.get("Interview", 0)
    shortlist_backlog = pipeline.get("Shortlisted", 0)
    action_queue = [
        _workspace_action("Review high-readiness talent", "/recruiter/talent", priority="high", reason=f"{talent['count']} candidates above readiness 72"),
        _workspace_action("Advance shortlist backlog", "/recruiter/applications", priority="high", reason=f"{shortlist_backlog} shortlisted candidates need action"),
        _workspace_action("Schedule interview backlog", "/recruiter/schedule", priority="medium", reason=f"{interview_backlog} candidates are interview-stage"),
    ]
    return {
        "recruiter": recruiter,
        "recruiter_id": recruiter_id,
        "summary": {
            "jobs": len(jobs),
            "open_jobs": len(open_jobs),
            "applications": total,
            "selected": selected,
            "rejected": rejected,
            "active": total - selected - rejected,
            "conversion_rate": _pct(selected, max(1, total), 1),
            "interview_rate": _pct(pipeline.get("Interview", 0), max(1, total), 1),
            "avg_package_lpa": round(sum(package_values) / max(1, len(package_values)), 1),
            "top_package_lpa": max(package_values) if package_values else 0,
            "talent_ready": talent["count"],
            "upcoming_interviews": len(upcoming),
        },
        "pipeline": pipeline,
        "job_funnels": job_funnels[:12],
        "institution_funnel": institution_funnel[:12],
        "package_intelligence": {
            "avg_lpa": round(sum(package_values) / max(1, len(package_values)), 1),
            "top_lpa": max(package_values) if package_values else 0,
            "open_role_capacity": sum(job.get("openings", 0) or 0 for job in open_jobs),
        },
        "upcoming_interviews": upcoming,
        "action_queue": action_queue,
    }


def _candidate_skill_match(candidate: dict, job: dict) -> dict:
    candidate_skills = {skill.lower() for skill in candidate.get("skills", [])}
    required = {skill.lower() for skill in job.get("skills", []) or []}
    if not required:
        title = " ".join([job.get("title", ""), job.get("role", "")]).lower()
        required = {skill for skill in ["python", "java", "react", "sql", "aws", "dsa", "machine learning"] if skill in title}
    overlap = sorted(candidate_skills.intersection(required))
    missing = sorted(required.difference(candidate_skills))
    score = _pct(len(overlap), max(1, len(required)), 1) if required else min(100, candidate.get("readiness_score", 0) or 0)
    return {"score": score, "matched_skills": overlap, "missing_skills": missing}


@app.get("/api/recruiters/me/recommendations")
async def my_recruiter_recommendations(user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    jobs = await db.jobs.find({"recruiter_id": recruiter_id or "__none__", "status": "open"}, {"_id": 0}).sort("drive_date", -1).to_list(20)
    base_pool = await _recruiter_talent_pool_payload(recruiter_id, min_cgpa=6.0, min_readiness=0, limit=120)
    recommendations = []
    for job in jobs[:8]:
        for candidate in base_pool.get("items", []):
            match = _candidate_skill_match(candidate, job)
            readiness = candidate.get("readiness_score", 0) or 0
            ats = candidate.get("ats_score", 0) or 0
            cgpa = float(candidate.get("cgpa") or 0)
            interview_next_score = round((readiness * 0.45) + (ats * 0.20) + (match["score"] * 0.25) + (min(100, cgpa * 10) * 0.10), 1)
            recommendations.append({
                "job_id": job["job_id"],
                "job_title": job.get("title"),
                "company": job.get("company"),
                "student_id": candidate["student_id"],
                "student_name": candidate.get("name"),
                "roll_number": candidate.get("roll_number"),
                "department": candidate.get("department"),
                "cgpa": candidate.get("cgpa"),
                "readiness_score": readiness,
                "ats_score": ats,
                "skill_match_score": match["score"],
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
                "interview_next_score": interview_next_score,
                "answer": "Interview next" if interview_next_score >= 76 else "Keep warm" if interview_next_score >= 64 else "Needs evidence",
            })
    recommendations.sort(key=lambda row: row["interview_next_score"], reverse=True)
    return {
        "items": recommendations[:40],
        "jobs_considered": len(jobs),
        "answer": "Which students should I interview next?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/recruiters/me/shortlists")
async def my_recruiter_shortlists(user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    items = await db.recruiter_shortlists.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"items": items, "count": len(items)}


@app.post("/api/recruiters/me/shortlists")
async def create_recruiter_shortlist(body: dict, request: Request, user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    student_id = body.get("student_id")
    if not student_id:
        raise HTTPException(400, "student_id required")
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    item = {
        "shortlist_id": f"short_{uuid.uuid4().hex[:10]}",
        "recruiter_id": recruiter_id,
        "student_id": student_id,
        "job_id": body.get("job_id"),
        "student_name": student.get("name"),
        "roll_number": student.get("roll_number"),
        "department": student.get("department"),
        "institution_id": student.get("institution_id"),
        "readiness_score": body.get("readiness_score"),
        "match_score": body.get("match_score"),
        "status": body.get("status", "shortlisted"),
        "notes": body.get("notes", ""),
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.recruiter_shortlists.update_one(
        {"recruiter_id": recruiter_id, "student_id": student_id, "job_id": item.get("job_id")},
        {"$set": item},
        upsert=True,
    )
    await _audit_log(
        "recruiter.shortlisted_candidate",
        user=user,
        institution_id=student.get("institution_id"),
        resource="student",
        resource_id=student_id,
        metadata={"job_id": item.get("job_id"), "match_score": item.get("match_score")},
        request=request,
    )
    return item


@app.get("/api/recruiters/me/saved-filters")
async def my_recruiter_saved_filters(user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    items = await db.recruiter_saved_filters.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"items": items, "count": len(items)}


@app.post("/api/recruiters/me/saved-filters")
async def create_recruiter_saved_filter(body: dict, request: Request, user=Depends(require_roles("recruiter"))):
    recruiter_id = await _resolve_recruiter_id(user)
    item = {
        "filter_id": f"filter_{uuid.uuid4().hex[:10]}",
        "recruiter_id": recruiter_id,
        "name": body.get("name") or "Saved talent view",
        "filters": {
            "min_cgpa": body.get("min_cgpa", 7),
            "min_readiness": body.get("min_readiness", 70),
            "department": body.get("department"),
            "skill": body.get("skill"),
        },
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.recruiter_saved_filters.insert_one(item)
    await _audit_log(
        "recruiter.saved_filter_created",
        user=user,
        institution_id=None,
        resource="recruiter_saved_filter",
        resource_id=item["filter_id"],
        metadata=item["filters"],
        request=request,
    )
    item.pop("_id", None)
    return item


@app.get("/api/recruiters/{recruiter_id}/talent-pool")
async def talent_pool(recruiter_id: str, min_cgpa: float = 6.5, user=Depends(require_roles("recruiter", "super_admin"))):
    if user["role"] != "super_admin":
        resolved = await _resolve_recruiter_id(user)
        if recruiter_id != resolved:
            raise HTTPException(403, "forbidden")
        jobs = await db.jobs.find({"recruiter_id": resolved or "__none__"}, {"_id": 0}).to_list(500)
        institution_ids = sorted({iid for job in jobs for iid in job.get("institutions", [])})
        if not institution_ids:
            return {"items": [], "count": 0}
        query = {"institution_id": {"$in": institution_ids}, "cgpa": {"$gte": min_cgpa}}
    else:
        query = {"cgpa": {"$gte": min_cgpa}}
    candidates = await db.students.find(query, {"_id": 0}).limit(120).to_list(120)
    students = []
    for candidate in candidates:
        readiness = await build_student_readiness(db, candidate)
        candidate["readiness_score"] = readiness["score"]
        candidate["readiness_band"] = readiness["band"]
        candidate["readiness_label"] = readiness["label"]
        candidate["readiness_components"] = readiness["components"]
        candidate["readiness_risks"] = readiness["risks"][:3]
        students.append(candidate)
    students.sort(key=lambda row: row.get("readiness_score", 0), reverse=True)
    students = students[:60]
    return {"items": students, "count": len(students)}


# ============== ANNOUNCEMENTS ==============
@app.get("/api/announcements")
async def list_announcements(user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    items = await db.announcements.find({"institution_id": iid}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"items": items}


@app.post("/api/announcements")
async def create_announcement(
    body: dict,
    request: Request,
    user=Depends(require_roles("tpo", "institution_admin", "faculty", "super_admin")),
):
    body["announcement_id"] = f"ann_{uuid.uuid4().hex[:10]}"
    body["institution_id"] = user.get("institution_id") or "inst_kmit"
    body["by_role"] = user["role"]
    body["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.announcements.insert_one(body)
    await notify(db, event="announcement_posted",
                 to_email=ADMIN_EMAIL, subject=f"Announcement: {body.get('title')}",
                 title=body.get("title", "Announcement"),
                 body_html=f"<p>{body.get('body', '')}</p>",
                 telegram_text=f"📣 {body.get('title')}")
    await _audit_log(
        "announcement.created",
        user=user,
        institution_id=body["institution_id"],
        resource="announcement",
        resource_id=body["announcement_id"],
        metadata={"audience": body.get("audience"), "title": body.get("title")},
        request=request,
    )
    return {"announcement_id": body["announcement_id"]}


# ============== MOU ==============
@app.get("/api/mou")
async def get_mou(user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    if user["role"] == "super_admin":
        iid = "inst_kmit"
    mou = await db.mous.find_one({"institution_id": iid}, {"_id": 0})
    if not mou:
        raise HTTPException(404, "no MOU")
    exp = datetime.fromisoformat(mou["expires_on"])
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    mou["days_until_renewal"] = (exp - datetime.now(timezone.utc)).days
    return mou


@app.post("/api/mou/upload")
async def upload_mou(
    request: Request,
    file: UploadFile = File(...),
    expires_on: str = Form(...),
    partnership_type: str = Form("CRT"),
    user=Depends(require_roles("super_admin", "tpo", "institution_admin")),
):
    iid = user.get("institution_id") or "inst_kmit"
    content = await file.read()
    size_kb = round(len(content) / 1024, 1)
    # Persist actual bytes in GridFS
    gridfs_id = await gridfs.upload_from_stream(
        f"{iid}__{file.filename}",
        content,
        metadata={"institution_id": iid, "uploader_user_id": user["user_id"],
                  "content_type": file.content_type, "uploaded_at": datetime.now(timezone.utc).isoformat()},
    )
    await db.mous.update_one({"institution_id": iid}, {"$set": {
        "institution_id": iid, "document_name": file.filename,
        "document_size_kb": size_kb, "partnership_type": partnership_type,
        "expires_on": expires_on, "signed_on": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "gridfs_id": str(gridfs_id),
        "content_type": file.content_type or "application/pdf",
    }}, upsert=True)
    await notify(db, event="mou_uploaded", to_email=ADMIN_EMAIL,
                 subject=f"MOU uploaded — {iid}", title="MOU received",
                 body_html=f"<p>{file.filename} ({size_kb} KB) uploaded.</p>",
                 telegram_text=f"📄 MOU · {iid}")
    await _audit_log(
        "mou.uploaded",
        user=user,
        institution_id=iid,
        resource="mou",
        resource_id=str(gridfs_id),
        metadata={"filename": file.filename, "size_kb": size_kb, "partnership_type": partnership_type},
        request=request,
    )
    return {"ok": True, "document_name": file.filename, "size_kb": size_kb, "gridfs_id": str(gridfs_id)}


@app.get("/api/mou/download")
async def download_mou(user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    if user["role"] == "super_admin":
        iid = "inst_kmit"
    mou = await db.mous.find_one({"institution_id": iid}, {"_id": 0})
    if not mou or not mou.get("gridfs_id"):
        raise HTTPException(404, "No file on record")
    file_id: Any = mou["gridfs_id"]
    if client is not None:
        from bson import ObjectId
        file_id = ObjectId(file_id)
    stream = await gridfs.open_download_stream(file_id)
    data = await stream.read()

    def gen():
        yield data

    return StreamingResponse(
        gen(),
        media_type=mou.get("content_type", "application/pdf"),
        headers={"Content-Disposition": f"attachment; filename=\"{mou['document_name']}\""},
    )


# ============== ADMIN PANEL ==============
@app.get("/api/admin/pending-signups")
async def pending_signups(admin=Depends(require_roles("super_admin"))):
    pending = await db.users.find({"approved": False}, {"_id": 0, "password_hash": 0}).to_list(200)
    ids = list({u["institution_id"] for u in pending if u.get("institution_id")})
    insts = await db.institutions.find({"institution_id": {"$in": ids}}, {"_id": 0}).to_list(200)
    imap = {i["institution_id"]: i for i in insts}
    for u in pending:
        u["institution"] = imap.get(u.get("institution_id"))
    return {"items": pending}


@app.post("/api/admin/approve/{user_id}")
async def approve_user(user_id: str, request: Request, admin=Depends(require_roles("super_admin"))):
    t = await db.users.find_one({"user_id": user_id})
    if not t:
        raise HTTPException(404, "not found")
    await db.users.update_one({"user_id": user_id}, {"$set": {"approved": True}})
    if t.get("institution_id"):
        await db.institutions.update_one({"institution_id": t["institution_id"]},
                                         {"$set": {"approved": True, "approved_at": datetime.now(timezone.utc).isoformat()}})
    await notify(db, event="account_approved", to_email=t["email"],
                 subject="Your CareerOS access is live",
                 title="Welcome aboard",
                 body_html=f"<p>Hi {t['name']}, your CareerOS access is now active.</p>",
                 telegram_text=f"Approved - {t['email']}")
    await _audit_log(
        "admin.user_approved",
        user=admin,
        institution_id=t.get("institution_id"),
        resource="user",
        resource_id=user_id,
        metadata={"target_email": t.get("email"), "target_role": t.get("role")},
        request=request,
    )
    return {"ok": True}


@app.post("/api/admin/reject/{user_id}")
async def reject_user(user_id: str, request: Request, admin=Depends(require_roles("super_admin"))):
    t = await db.users.find_one({"user_id": user_id})
    if not t:
        raise HTTPException(404, "not found")
    await db.users.delete_one({"user_id": user_id})
    if t.get("institution_id"):
        await db.institutions.delete_one({"institution_id": t["institution_id"], "approved": False})
    await _audit_log(
        "admin.user_rejected",
        user=admin,
        institution_id=t.get("institution_id"),
        resource="user",
        resource_id=user_id,
        metadata={"target_email": t.get("email"), "target_role": t.get("role")},
        request=request,
    )
    return {"ok": True}


@app.get("/api/admin/notifications")
async def admin_notifications(admin=Depends(require_roles("super_admin"))):
    items = await db.notification_log.find({}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return {"items": items}


@app.get("/api/admin/audit-logs")
async def admin_audit_logs(
    institution_id: Optional[str] = None,
    event: Optional[str] = None,
    limit: int = 100,
    admin=Depends(require_roles("super_admin")),
):
    query: dict[str, Any] = {}
    if institution_id:
        query["institution_id"] = institution_id
    if event:
        query["event"] = event
    safe_limit = max(1, min(limit, 500))
    items = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(safe_limit).to_list(safe_limit)
    return {"items": items}


@app.post("/api/admin/test-notification")
async def test_notification(admin=Depends(require_roles("super_admin"))):
    await notify(db, event="admin_test", to_email=ADMIN_EMAIL,
                 subject="CareerOS · Test notification",
                 title="Heartbeat",
                 body_html="<p>Test fan-out triggered.</p>",
                 telegram_text="🔔 CareerOS test")
    return {"ok": True}


@app.get("/api/admin/platform-stats")
async def platform_stats(admin=Depends(require_roles("super_admin"))):
    n_inst = await db.institutions.count_documents({"approved": True})
    n_pending = await db.users.count_documents({"approved": False})
    n_students = await db.students.count_documents({})
    n_apps = await db.applications.count_documents({})
    n_jobs_open = await db.jobs.count_documents({"status": "open"})
    n_recruiters = await db.recruiters.count_documents({})
    # MRR-style proxy: 18% rev share × placed offer count × avg LPA × ₹/lpa-share
    placed = await db.students.count_documents({"placement.placed": True})
    estimated_mrr = round(placed * 0.18 * 6 * 1000 / 12, 0)  # rough proxy
    by_type_pipeline = [{"$group": {"_id": "$type", "n": {"$sum": 1}}}]
    by_type = await db.institutions.aggregate(by_type_pipeline).to_list(20)
    return {
        "institutions": n_inst, "pending_signups": n_pending,
        "students": n_students, "applications": n_apps,
        "jobs_open": n_jobs_open, "recruiters": n_recruiters,
        "estimated_mrr_inr": estimated_mrr,
        "by_type": [{"type": b["_id"], "count": b["n"]} for b in by_type],
    }


@app.get("/api/admin/colleges")
async def admin_colleges(admin=Depends(require_roles("super_admin"))):
    items = await db.institutions.find({}, {"_id": 0}).to_list(500)
    return {"items": items}


@app.post("/api/digest/send")
async def send_periodic_digest(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    if not iid:
        raise HTTPException(400, "institution_id required")
    
    total_students = await db.students.count_documents({"institution_id": iid})
    placed_students = await db.students.count_documents({"institution_id": iid, "placement.placed": True})
    
    cohorts = await db.training_programs.find({"institution_id": iid}).to_list(100)
    avg_completion = sum(c.get("completion_pct", 0) for c in cohorts) / len(cohorts) if cohorts else 0.0
    
    title = "Periodic Placement & Training Digest"
    body_text = f"As of today, your institution has {placed_students}/{total_students} placed students ({round(placed_students / max(1, total_students) * 100, 1)}%). Average training cohort completion is {round(avg_completion, 1)}% across {len(cohorts)} cohorts."
    
    notif = await _create_system_notification(
        institution_id=iid,
        type_="digest.sent",
        title=title,
        body=body_text,
        channels=["in_app", "email"]
    )
    
    await notify(
        db,
        event="digest_sent",
        to_email=user["email"],
        subject="CareerOS · Periodic Digest Report",
        title=title,
        body_html=f"<p>{body_text}</p>",
        telegram_text=f"🔔 {title}: {body_text}"
    )
    
    return {"success": True, "notification": notif}


@app.post("/api/admin/reseed-demo")
async def reseed_demo(admin=Depends(require_roles("super_admin"))):
    UNIQUE_KEYS = {
        "institutions": "institution_id",
        "departments": "department_id",
        "students": "student_id",
        "recruiters": "recruiter_id",
        "jobs": "job_id",
        "applications": "application_id",
        "dsa_questions": "question_id",
        "dsa_progress": "progress_id",
        "dsa_question_progress": "progress_id",
        "aptitude_scores": "score_id",
        "ats_reports": "ats_id",
        "interview_reports": "interview_id",
        "announcements": "announcement_id",
        "training_programs": "cohort_id",
        "enrollments": "enrollment_id",
        "placement_records": "record_id",
        "year_summaries": "summary_id",
        "mous": "mou_id",
        "comm_log": "log_id",
        "revenue_share": "revenue_id"
    }

    now = datetime.now(timezone.utc)
    payload = seed_payload()
    for col, items in payload.items():
        if not items:
            continue
        unique_key = UNIQUE_KEYS.get(col)
        if not unique_key:
            for k in items[0].keys():
                if k != "_id" and k.endswith("_id"):
                    unique_key = k
                    break
            if not unique_key:
                unique_key = "_id"

        # Query existing IDs in the collection
        existing_docs = await db[col].find({}, {unique_key: 1}).to_list(1000000)
        existing_ids = {d[unique_key] for d in existing_docs if unique_key in d}

        to_insert = [item for item in items if item.get(unique_key) not in existing_ids]
        if to_insert:
            await db[col].insert_many(to_insert)
            log.info(f"Reseeded {len(to_insert)} missing records into {col}")

    # Seed DSA questions safely
    dsa_bank = build_dsa_question_bank()
    if dsa_bank:
        existing_q = await db.dsa_questions.find({}, {"question_id": 1}).to_list(100000)
        existing_q_ids = {q["question_id"] for q in existing_q if "question_id" in q}
        to_insert_q = [q for q in dsa_bank if q.get("question_id") not in existing_q_ids]
        if to_insert_q:
            await db.dsa_questions.insert_many(to_insert_q)

    await _ensure_aptitude_catalog()

    # Recreate demo catalogs
    students_with_dsa = await db.students.find({"institution_id": "inst_kmit"}, {"_id": 0}).to_list(1000)
    for student in students_with_dsa:
        await _ensure_student_dsa_catalog(student)

    students_with_aptitude = await db.students.find({"institution_id": "inst_kmit"}, {"_id": 0}).to_list(1000)
    await _ensure_aptitude_progress_for_students(students_with_aptitude)
    await _ensure_resume_versions_for_students()

    # Setup demo users
    demo_users = [
        {"email": ADMIN_EMAIL, "name": "Platform Super Admin", "role": "super_admin", "institution_id": None, "department": None},
        {"email": "institution@kmit.in", "name": "KMIT — Institution Admin", "role": "institution_admin", "institution_id": "inst_kmit"},
        {"email": "tpo@kmit.in", "name": "Dr. Neil Gogte", "role": "tpo", "institution_id": "inst_kmit"},
        {"email": "faculty@kmit.in", "name": "Prof. Lavanya Iyer", "role": "faculty", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "student@kmit.in", "name": "Aarav Reddy", "role": "student", "institution_id": "inst_kmit", "department": "CSE"},
        {"email": "recruiter@amazon.com", "name": "Priya Sharma (Amazon)", "role": "recruiter", "institution_id": None, "department": None},
        {"email": "tpo@vasavi.ac.in", "name": "Dr. Suresh Kumar", "role": "tpo", "institution_id": "inst_vasavi_pending", "approved": False},
    ]
    for d in demo_users:
        exists = await db.users.count_documents({"email": d["email"]})
        if not exists:
            new = _new_user(
                email=d["email"], name=d["name"], role=d["role"],
                institution_id=d.get("institution_id"),
                department=d.get("department"),
                password=DEFAULT_DEMO_PASSWORD if d["role"] != "super_admin" else ADMIN_PASSWORD,
                approved=d.get("approved", True),
            )
            if d["role"] == "student":
                real_stu = await db.students.find_one(
                    {"institution_id": "inst_kmit", "department": "CSE"}, {"_id": 0}
                )
                if real_stu:
                    new["student_id"] = real_stu["student_id"]
                    await db.students.update_one(
                        {"student_id": real_stu["student_id"]},
                        {"$set": {"name": d["name"], "email": d["email"]}},
                    )
            await db.users.insert_one(new)

    return {"success": True, "message": "Demo data reseeded successfully"}


@app.get("/api/admin/cohorts/{program_code}/students")
async def list_cohort_students(program_code: str, user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if not iid:
        if user["role"] == "super_admin":
            iid = "inst_kmit"
        else:
            return {"items": []}
    
    enrolls = await db.enrollments.find({"institution_id": iid, "program_code": program_code}, {"_id": 0}).to_list(1000)
    student_ids = [e["student_id"] for e in enrolls]
    
    students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0})
    college_name = inst.get("name") if inst else "Keshav Memorial Institute of Technology"
    
    items = []
    enroll_map = {e["student_id"]: e for e in enrolls}
    for s in students:
        e = enroll_map.get(s["student_id"], {})
        items.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "roll_number": s["roll_number"],
            "department": s["department"],
            "college_name": college_name,
            "completion_pct": e.get("completion_pct", 0),
            "status": e.get("status", "enrolled")
        })
        
    return {"items": items}


# ============== REPORTS (PDF + CSV) ==============
REPORT_MANIFEST = [
    {
        "report_id": "placement_pdf",
        "title": "Placement board report",
        "kind": "pdf",
        "audience": "Board / leadership",
        "cadence": "Weekly during drive season",
        "href": "/reports/placement.pdf",
        "file": "placement-report.pdf",
        "decision": "Are offers, CTC, departments, and recruiters moving in the right direction?",
        "phase": "Phase 8",
    },
    {
        "report_id": "training_pdf",
        "title": "Training intervention report",
        "kind": "pdf",
        "audience": "TPO / faculty",
        "cadence": "Twice per week",
        "href": "/reports/training.pdf",
        "file": "training-report.pdf",
        "decision": "Which cohorts need faculty action before the next drive?",
        "phase": "Phase 8",
    },
    {
        "report_id": "department_pdf",
        "title": "Department health report",
        "kind": "pdf",
        "audience": "HOD / institution admin",
        "cadence": "Weekly",
        "href": "/reports/department.pdf",
        "file": "department-report.pdf",
        "decision": "Which department is underperforming and why?",
        "phase": "Phase 8",
    },
    {
        "report_id": "students_csv",
        "title": "Student intelligence export",
        "kind": "csv",
        "audience": "Ops / downstream tooling",
        "cadence": "On demand",
        "href": "/reports/students.csv",
        "file": "students.csv",
        "decision": "Which students should move into action lists?",
        "phase": "Phase 8",
    },
    {
        "report_id": "applications_csv",
        "title": "Application pipeline export",
        "kind": "csv",
        "audience": "TPO / recruiters",
        "cadence": "Daily during drives",
        "href": "/reports/applications.csv",
        "file": "applications.csv",
        "decision": "Where are applications stuck?",
        "phase": "Phase 8",
    },
    {
        "report_id": "placements_csv",
        "title": "Placement ledger export",
        "kind": "csv",
        "audience": "Analytics / audit",
        "cadence": "Monthly",
        "href": "/reports/placements.csv",
        "file": "placements.csv",
        "decision": "Which recruiter relationships compound over time?",
        "phase": "Phase 8",
    },
]


def _stream(content: io.BytesIO, filename: str, media_type: str):
    content.seek(0)
    return StreamingResponse(
        iter([content.read()]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/reports/manifest")
async def reports_manifest(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    analytics = await _analytics_engine_payload(user)
    exports_generated = await db.audit_logs.count_documents({"event": {"$in": [
        "report.placement_exported",
        "report.training_exported",
        "report.department_exported",
        "report.csv_exported",
    ]}})
    return {
        "items": REPORT_MANIFEST,
        "board_packet": {
            "title": "CareerOS Intelligence Board Packet",
            "status": "ready" if analytics["summary"]["health"] not in {"critical"} else "needs_review",
            "command_score": analytics["summary"]["command_score"],
            "forecasted_offers": analytics["forecast"]["forecasted_offers"],
            "risk_count": len(analytics["risk_register"]),
            "recommended_sequence": ["placement_pdf", "department_pdf", "training_pdf", "applications_csv"],
        },
        "usage": {
            "exports_generated": exports_generated,
            "last_generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


@app.get("/api/reports/board-packet.json")
async def reports_board_packet(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    analytics = await _analytics_engine_payload(user)
    modules = await module_intelligence(user=user)
    return {
        "title": "CareerOS Intelligence Board Packet",
        "scope": analytics["scope"],
        "executive_summary": analytics["summary"],
        "forecast": analytics["forecast"],
        "risk_register": analytics["risk_register"],
        "recommendations": analytics["recommendations"],
        "module_health": modules["cards"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _institution_overview_for_reports(iid: str) -> dict:
    """Lightweight version of placements_overview that doesn't require auth coupling."""
    years = await db.year_summaries.find({"institution_id": iid}, {"_id": 0}).sort("academic_year", -1).to_list(20)
    records = await db.placement_records.find({"institution_id": iid}, {"_id": 0}).to_list(500)
    placed = await db.students.count_documents({"institution_id": iid, "placement.placed": True})
    total = await db.students.count_documents({"institution_id": iid})
    pipeline = [{"$match": {"institution_id": iid}},
                {"$group": {"_id": "$company", "selects": {"$sum": "$selects"}, "max_ctc": {"$max": "$ctc_lpa"}}},
                {"$sort": {"selects": -1}}, {"$limit": 15}]
    top = await db.placement_records.aggregate(pipeline).to_list(20)
    top = [{"company": r["_id"], "selects": r["selects"], "max_ctc": r["max_ctc"]} for r in top]
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0})
    dept = []
    for d in (inst["departments"] if inst else []):
        p = await db.students.count_documents({"institution_id": iid, "department": d, "placement.placed": True})
        t = await db.students.count_documents({"institution_id": iid, "department": d})
        dept.append({"department": d, "placed": p, "total": t})
    return {"year_summaries": years, "records": records, "top_recruiters": top,
            "department_breakdown": dept, "students_placed": placed, "students_total": total}


@app.get("/api/reports/placement.pdf")
async def report_placement_pdf(request: Request, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0}) or {}
    overview = await _institution_overview_for_reports(iid)
    pdf = placement_report_pdf(inst, overview)
    await _audit_log("report.placement_exported", user=user, institution_id=iid, resource="report", resource_id="placement_pdf", request=request)
    return _stream(pdf, f"placement-report-{inst.get('short_name', 'institution')}.pdf", "application/pdf")


@app.get("/api/reports/training.pdf")
async def report_training_pdf(request: Request, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0}) or {}
    pipeline = [{"$match": {"institution_id": iid}},
                {"$group": {"_id": "$program_code",
                            "avg_completion": {"$avg": "$completion_pct"},
                            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                            "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
                            "enrolled": {"$sum": 1}}}]
    by_program = await db.enrollments.aggregate(pipeline).to_list(20)
    prog_map = {p["code"]: p for p in PROGRAMS}
    for r in by_program:
        meta = prog_map.get(r["_id"], {})
        r["program_code"] = r["_id"]; r["program_name"] = meta.get("name", r["_id"])
        r["avg_completion"] = round(r["avg_completion"] or 0, 1)
    enroll = await db.enrollments.find({"institution_id": iid}, {"_id": 0}).sort("completion_pct", -1).limit(60).to_list(60)
    sids = list({e["student_id"] for e in enroll})
    students = await db.students.find({"student_id": {"$in": sids}}, {"_id": 0}).to_list(200)
    smap = {s["student_id"]: s for s in students}
    for e in enroll:
        s = smap.get(e["student_id"], {})
        e["student_name"] = s.get("name", "—"); e["roll_number"] = s.get("roll_number", "—"); e["department"] = s.get("department", "—")
    pdf = training_report_pdf(inst, {"by_program": by_program, "rows": enroll})
    await _audit_log("report.training_exported", user=user, institution_id=iid, resource="report", resource_id="training_pdf", request=request)
    return _stream(pdf, f"training-report-{inst.get('short_name', 'institution')}.pdf", "application/pdf")


@app.get("/api/reports/department.pdf")
async def report_department_pdf(request: Request, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0}) or {}
    overview = await _institution_overview_for_reports(iid)
    students = await db.students.find({"institution_id": iid}, {"_id": 0}).to_list(1000)
    pdf = department_report_pdf(inst, overview, students)
    await _audit_log("report.department_exported", user=user, institution_id=iid, resource="report", resource_id="department_pdf", request=request)
    return _stream(pdf, f"department-report-{inst.get('short_name', 'institution')}.pdf", "application/pdf")


@app.get("/api/reports/students.csv")
async def report_students_csv(request: Request, department: Optional[str] = None, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    if user["role"] == "super_admin":
        iid = "inst_kmit"
    q = {"institution_id": iid}
    if department:
        q["department"] = department
    items = await db.students.find(q, {"_id": 0}).to_list(2000)
    buf = students_csv(items)
    await _audit_log("report.csv_exported", user=user, institution_id=iid, resource="report", resource_id="students_csv", metadata={"rows": len(items)}, request=request)
    return _stream(buf, "students.csv", "text/csv")


@app.get("/api/reports/applications.csv")
async def report_applications_csv(request: Request, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    items = await db.applications.find({"institution_id": iid}, {"_id": 0}).to_list(2000)
    buf = applications_csv(items)
    await _audit_log("report.csv_exported", user=user, institution_id=iid, resource="report", resource_id="applications_csv", metadata={"rows": len(items)}, request=request)
    return _stream(buf, "applications.csv", "text/csv")


@app.get("/api/reports/placements.csv")
async def report_placements_csv(request: Request, user=Depends(get_session_user)):
    iid = user.get("institution_id") or "inst_kmit"
    records = await db.placement_records.find({"institution_id": iid}, {"_id": 0}).to_list(2000)
    buf = placements_csv(records)
    await _audit_log("report.csv_exported", user=user, institution_id=iid, resource="report", resource_id="placements_csv", metadata={"rows": len(records)}, request=request)
    return _stream(buf, "placements.csv", "text/csv")


# ============== INTERVIEW SCHEDULING ==============
class InterviewScheduleBody(BaseModel):
    student_id: str
    job_id: Optional[str] = None
    company: str
    role: str
    type: Literal["Technical", "HR", "System Design", "Behavioral", "Final"] = "Technical"
    starts_at: str  # ISO datetime
    duration_min: int = 45
    location: str = "Online · Zoom"
    notes: Optional[str] = None


@app.get("/api/interviews/schedule")
async def list_scheduled_interviews(user=Depends(get_session_user)):
    iid = user.get("institution_id")
    if user["role"] == "student":
        items = await db.interview_schedule.find({"student_id": user.get("student_id")}, {"_id": 0}).sort("starts_at", 1).to_list(60)
    elif user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        jobs = await db.jobs.find({"recruiter_id": recruiter_id or "__none__"}, {"_id": 0, "job_id": 1}).to_list(500)
        job_ids = [job["job_id"] for job in jobs]
        items = await db.interview_schedule.find(
            {"job_id": {"$in": job_ids}} if job_ids else {"job_id": "__none__"},
            {"_id": 0},
        ).sort("starts_at", 1).to_list(120)
    elif iid:
        items = await db.interview_schedule.find({"institution_id": iid}, {"_id": 0}).sort("starts_at", 1).to_list(120)
    else:
        items = []
    return {"items": items}


@app.post("/api/interviews/schedule")
async def schedule_interview(
    body: InterviewScheduleBody,
    request: Request,
    user=Depends(require_roles("tpo", "institution_admin", "recruiter", "super_admin")),
):
    student = await db.students.find_one({"student_id": body.student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    if user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        if not body.job_id:
            raise HTTPException(400, "job_id required for recruiter scheduling")
        job = await db.jobs.find_one({"job_id": body.job_id, "recruiter_id": recruiter_id or "__none__"}, {"_id": 0})
        if not job or student["institution_id"] not in job.get("institutions", []):
            raise HTTPException(403, "forbidden")
    else:
        require_same_institution(student.get("institution_id"), user)
    start_dt = datetime.fromisoformat(body.starts_at.replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(minutes=body.duration_min)
    interview_id = f"isch_{uuid.uuid4().hex[:10]}"
    record = {
        "interview_id": interview_id,
        "student_id": body.student_id,
        "student_name": student["name"],
        "student_email": student["email"],
        "roll_number": student["roll_number"],
        "department": student["department"],
        "institution_id": student["institution_id"],
        "company": body.company,
        "role": body.role,
        "type": body.type,
        "starts_at": start_dt.isoformat(),
        "ends_at": end_dt.isoformat(),
        "duration_min": body.duration_min,
        "location": body.location,
        "notes": body.notes,
        "status": "scheduled",
        "scheduled_by": user["user_id"],
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
        "job_id": body.job_id,
    }
    await db.interview_schedule.insert_one(record)

    # Build .ics + send notification with attachment
    ics_bytes = build_ics(
        uid=f"{interview_id}@careeros.app",
        summary=f"{body.company} · {body.role} interview",
        description=f"{body.type} interview with {body.company}.\nLocation: {body.location}\n{(body.notes or '')}",
        location=body.location,
        start_utc=start_dt,
        end_utc=end_dt,
        organizer_email=os.environ.get("SENDER_EMAIL", "careeros.notify@careeros.app"),
        attendee_emails=[student["email"]],
    )
    await notify(
        db,
        event="interview_scheduled",
        to_email=student["email"],
        subject=f"Interview scheduled — {body.company}",
        title=f"You have an interview with {body.company}",
        body_html=(f"<p>Hi {student['name'].split()[0]},</p>"
                   f"<p>Your <b>{body.type}</b> interview for the <b>{body.role}</b> role at <b>{body.company}</b> is scheduled.</p>"
                   f"<p><b>When:</b> {start_dt.strftime('%A, %d %B %Y · %H:%M UTC')}<br/>"
                   f"<b>Duration:</b> {body.duration_min} min<br/>"
                   f"<b>Where:</b> {body.location}</p>"
                   f"<p>The calendar invite is attached. Good luck.</p>"),
        telegram_text=f"📅 Interview · {student['name']} · {body.company} · {start_dt.strftime('%d %b %H:%M UTC')}",
        attachments=[{"content": ics_bytes, "filename": "careeros-interview.ics", "mime_type": "text/calendar"}],
    )

    # Update related application to Interview stage if a job_id is provided
    if body.job_id:
        await db.applications.update_one(
            {"student_id": body.student_id, "job_id": body.job_id},
            {"$set": {"stage": "Interview", "next_step_at": start_dt.isoformat()}},
        )

    # Broadcast live update to anyone watching this institution
    await ws_manager.broadcast(student["institution_id"], {
        "type": "interview.scheduled",
        "interview_id": interview_id,
        "student_name": student["name"],
        "company": body.company,
        "starts_at": record["starts_at"],
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    await _audit_log(
        "interview.scheduled",
        user=user,
        institution_id=student["institution_id"],
        resource="interview_schedule",
        resource_id=interview_id,
        metadata={"student_id": body.student_id, "company": body.company, "job_id": body.job_id},
        request=request,
    )
    return {"interview_id": interview_id, "starts_at": record["starts_at"]}


@app.delete("/api/interviews/schedule/{interview_id}")
async def cancel_interview(
    interview_id: str,
    request: Request,
    user=Depends(require_roles("tpo", "institution_admin", "recruiter", "super_admin")),
):
    sched = await db.interview_schedule.find_one({"interview_id": interview_id}, {"_id": 0})
    if not sched:
        raise HTTPException(404, "interview not found")
    if user["role"] == "recruiter":
        recruiter_id = await _resolve_recruiter_id(user)
        job = await db.jobs.find_one({"job_id": sched.get("job_id"), "recruiter_id": recruiter_id or "__none__"}, {"_id": 0})
        if not job:
            raise HTTPException(403, "forbidden")
    else:
        require_same_institution(sched.get("institution_id"), user)
    await db.interview_schedule.update_one({"interview_id": interview_id},
                                           {"$set": {"status": "cancelled", "cancelled_by": user["user_id"],
                                                     "cancelled_at": datetime.now(timezone.utc).isoformat()}})
    if sched:
        await ws_manager.broadcast(sched["institution_id"], {
            "type": "interview.cancelled",
            "interview_id": interview_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    await _audit_log(
        "interview.cancelled",
        user=user,
        institution_id=sched.get("institution_id"),
        resource="interview_schedule",
        resource_id=interview_id,
        request=request,
    )
    return {"ok": True}


# ============== AI: INTERVIEW FEEDBACK ==============
INTERVIEW_QUESTION_BANK = {
    "hr": [
        "Tell me about yourself.",
        "What are your strengths?",
        "What is one weakness you are actively improving?",
        "Describe a leadership moment.",
        "Tell me about a time you worked in a team.",
        "How do you handle conflict?",
        "What are your career goals?",
    ],
    "technical": [
        "Explain your strongest DSA topic with an example.",
        "Explain OOP principles using a project you built.",
        "How does indexing work in DBMS?",
        "What happens during process scheduling in an operating system?",
        "Explain TCP vs UDP in computer networks.",
        "Describe exception handling in Java.",
        "What makes Python suitable for rapid prototyping?",
    ],
    "ai": [
        "Introduce yourself for a software engineering interview.",
        "Walk through a DSA problem you solved recently.",
        "Explain one database design decision from a project.",
        "Tell me about a difficult bug and how you debugged it.",
        "Why should a recruiter shortlist you today?",
    ],
}


@app.get("/api/me/interviews/mock/questions")
async def my_mock_interview_questions(mode: str = "hr", user=Depends(require_roles("student"))):
    selected = INTERVIEW_QUESTION_BANK.get(mode, INTERVIEW_QUESTION_BANK["hr"])
    return {
        "mode": mode,
        "questions": [
            {"question_id": f"{mode}_{index}", "prompt": prompt, "order": index}
            for index, prompt in enumerate(selected, start=1)
        ],
    }


@app.post("/api/me/interviews/mock/start")
async def start_my_mock_interview(body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    if not student:
        raise HTTPException(404, "no student record bound")
    mode = body.get("mode", "hr")
    selected = INTERVIEW_QUESTION_BANK.get(mode, INTERVIEW_QUESTION_BANK["hr"])
    now = datetime.now(timezone.utc).isoformat()
    session = {
        "session_id": f"mock_int_{uuid.uuid4().hex[:10]}",
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "mode": mode,
        "status": "in_progress",
        "camera_enabled": bool(body.get("camera_enabled", False)),
        "microphone_enabled": bool(body.get("microphone_enabled", False)),
        "started_at": now,
        "questions": [
            {"question_id": f"{mode}_{index}", "prompt": prompt, "order": index}
            for index, prompt in enumerate(selected, start=1)
        ],
        "answers": [],
        "notes": body.get("notes", ""),
    }
    await db.mock_interview_sessions.insert_one(session)
    await _audit_log("interview.mock_started", user=user, institution_id=student["institution_id"], resource="mock_interview", resource_id=session["session_id"], metadata={"mode": mode}, request=request)
    if "_id" in session:
        del session["_id"]
    return session


@app.post("/api/me/interviews/mock/{session_id}/answer")
async def answer_my_mock_interview(session_id: str, body: dict, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    session = await db.mock_interview_sessions.find_one({"session_id": session_id, "student_id": student["student_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(404, "mock session not found")
    answer = {
        "answer_id": f"mock_ans_{uuid.uuid4().hex[:8]}",
        "question_id": body.get("question_id"),
        "prompt": body.get("prompt"),
        "transcript": body.get("transcript", ""),
        "response_seconds": max(0, int(body.get("response_seconds") or 0)),
        "recording_id": body.get("recording_id") or f"local_rec_{uuid.uuid4().hex[:8]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    answers = [row for row in session.get("answers", []) if row.get("question_id") != answer["question_id"]]
    answers.append(answer)
    await db.mock_interview_sessions.update_one({"session_id": session_id}, {"$set": {"answers": answers, "updated_at": answer["created_at"]}})
    return {"answer": answer, "answers": answers}


@app.post("/api/me/interviews/mock/{session_id}/complete")
async def complete_my_mock_interview(session_id: str, body: dict, request: Request, user=Depends(require_roles("student"))):
    _sid, student = await _resolve_student_for_user(user)
    session = await db.mock_interview_sessions.find_one({"session_id": session_id, "student_id": student["student_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(404, "mock session not found")
    answers = session.get("answers", [])
    text = " ".join(row.get("transcript", "") for row in answers).strip()
    word_count = len(text.split())
    total_seconds = sum(row.get("response_seconds", 0) or 0 for row in answers)
    pace = round((word_count / max(1, total_seconds)) * 60, 1)
    response_length_score = _clamp_score((word_count / max(1, len(session.get("questions", [])))) * 2.5)
    pace_score = _clamp_score(100 - abs(pace - 125) * 0.45)
    technical_keywords = ["complexity", "database", "index", "api", "algorithm", "project", "java", "python", "network", "process", "oop"]
    technical_depth = _clamp_score(sum(1 for kw in technical_keywords if kw in text.lower()) * 10 + response_length_score * 0.35)
    communication = _clamp_score(response_length_score * 0.45 + pace_score * 0.55)
    confidence = _clamp_score(60 + min(30, len(answers) * 5) + (10 if body.get("camera_enabled") else 0))
    hr_score = _clamp_score(communication * 0.55 + confidence * 0.45)
    overall = round((communication * 0.28) + (confidence * 0.22) + (technical_depth * 0.32) + (hr_score * 0.18), 1)
    weak_areas = [
        {"area": "communication", "score": round(communication, 1), "gap": round(max(0, 75 - communication), 1)},
        {"area": "confidence", "score": round(confidence, 1), "gap": round(max(0, 75 - confidence), 1)},
        {"area": "technical_depth", "score": round(technical_depth, 1), "gap": round(max(0, 75 - technical_depth), 1)},
        {"area": "speaking_pace", "score": round(pace_score, 1), "gap": round(max(0, 75 - pace_score), 1)},
    ]
    weak_areas = [row for row in weak_areas if row["gap"] > 0]
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "interview_id": f"int_{uuid.uuid4().hex[:10]}",
        "session_id": session_id,
        "student_id": student["student_id"],
        "institution_id": student["institution_id"],
        "type": f"{session.get('mode', 'mock').upper()} Mock",
        "date": now[:10],
        "conducted_at": now,
        "communication_score": round(communication, 1),
        "confidence_score": round(confidence, 1),
        "technical_score": round(technical_depth, 1),
        "hr_score": round(hr_score, 1),
        "body_language_score": round(confidence, 1),
        "overall_score": overall,
        "speaking_pace": pace,
        "response_length": word_count,
        "technical_depth": round(technical_depth, 1),
        "weak_areas": weak_areas,
        "feedback": "Keep answers structured with situation, action, result, and measurable technical detail." if weak_areas else "Strong mock interview. Maintain clarity and technical evidence.",
        "answers": answers,
        "recording_status": "stored" if answers else "not_recorded",
        "notes": body.get("notes", session.get("notes", "")),
    }
    await db.interview_reports.insert_one(report)
    await db.mock_interview_sessions.update_one({"session_id": session_id}, {"$set": {"status": "completed", "completed_at": now, "report_id": report["interview_id"], "analysis": report}})
    await _audit_log("interview.mock_completed", user=user, institution_id=student["institution_id"], resource="interview_report", resource_id=report["interview_id"], metadata={"overall_score": overall}, request=request)
    report.pop("_id", None)
    return report


@app.post("/api/interviews/{interview_id}/ai-feedback")
async def regenerate_ai_feedback(interview_id: str, request: Request, user=Depends(get_session_user)):
    report = await db.interview_reports.find_one({"interview_id": interview_id}, {"_id": 0})
    if not report:
        raise HTTPException(404, "interview report not found")
    if user["role"] in ("tpo", "institution_admin", "faculty"):
        require_same_institution(report.get("institution_id"), user)
    elif user["role"] != "super_admin" and user.get("student_id") != report["student_id"]:
        raise HTTPException(403, "forbidden")
    # Hydrate names if not present
    if not report.get("student_name"):
        s = await db.students.find_one({"student_id": report["student_id"]}, {"_id": 0})
        if s:
            report["student_name"] = s.get("name")
            report["roll_number"] = s.get("roll_number")
            report["department"] = s.get("department")
    result = await ai_interview_feedback(report)
    await db.interview_reports.update_one(
        {"interview_id": interview_id},
        {"$set": {"ai_feedback": result["feedback"], "ai_source": result["source"],
                  "ai_model": result.get("model"), "ai_generated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await _audit_log(
        "interview.ai_feedback_generated",
        user=user,
        institution_id=report.get("institution_id"),
        resource="interview_report",
        resource_id=interview_id,
        metadata={"ai_source": result.get("source"), "ai_model": result.get("model")},
        request=request,
    )
    return result


# ============== AI: REAL RESUME ATS ==============
def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # noqa: BLE001
        log.warning("PDF parse failed: %s", exc)
        return ""


def _extract_docx_text(content: bytes) -> str:
    try:
        from xml.etree import ElementTree
        with zipfile.ZipFile(io.BytesIO(content)) as docx:
            xml = docx.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        return "\n".join(node.text or "" for node in root.findall(".//w:t", ns)).strip()
    except Exception as exc:  # noqa: BLE001
        log.warning("DOCX parse failed: %s", exc)
        return ""


def _clean_resume_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _resume_text_from_upload(content: bytes, filename: str = "", content_type: str = "") -> str:
    suffix = Path(filename or "").suffix.lower()
    ctype = (content_type or "").lower()
    if suffix == ".pdf" or "pdf" in ctype:
        return _clean_resume_text(_extract_pdf_text(content))
    if suffix in {".docx", ".doc"} or "word" in ctype or "officedocument" in ctype:
        return _clean_resume_text(_extract_docx_text(content))
    if suffix in {".txt", ".md", ".csv"} or "text" in ctype:
        return _clean_resume_text(content.decode("utf-8", errors="ignore"))
    return ""


async def _fallback_resume_text_for_user(user: dict, filename: str, job_description: str = "") -> str:
    student = None
    if user.get("student_id"):
        student = await db.students.find_one({"student_id": user["student_id"]}, {"_id": 0})
    skills = ["Python", "Java", "SQL", "React", "DSA", "DBMS", "Operating Systems", "Computer Networks"]
    if student:
        if student.get("skills"):
            skills = student.get("skills")
        return _clean_resume_text(
            f"{student.get('name', user.get('name', 'Student'))} {student.get('department', 'CSE')} "
            f"CGPA {student.get('cgpa', 7.6)} placement resume. Skills: {', '.join(skills)}. "
            f"Projects include full stack web applications, data structures practice, database systems, APIs, and cloud deployment. "
            f"Career goal: software engineering, product engineering, data analytics. "
            f"Uploaded file {filename}. Target role: {job_description or 'software engineer'}."
        )
    return _clean_resume_text(
        f"{user.get('name', 'CareerOS candidate')} resume upload {filename}. "
        "Skills: Python, Java, SQL, React, DSA, DBMS, communication, projects, internships. "
        f"Target role: {job_description or 'software engineer'}."
    )


@app.post("/api/ats/upload")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(""),
    user=Depends(get_session_user),
):
    """Student (or staff on behalf of) uploads a resume; we extract text and always produce a useful score."""
    content = await file.read()
    size_kb = round(len(content) / 1024, 1)
    student_id = user.get("student_id")
    if not student_id and user["role"] != "student":
        student_id = None
    text = _resume_text_from_upload(content, file.filename or "", file.content_type or "")
    used_fallback_text = False
    if len(text.split()) < 25:
        text = await _fallback_resume_text_for_user(user, file.filename or "resume", job_description)
        used_fallback_text = True
    scoring = await ai_ats_score(text, job_description)
    if not scoring.get("ats_score"):
        scoring = {
            **scoring,
            "ats_score": 68,
            "keyword_match_pct": max(scoring.get("keyword_match_pct") or 0, 62),
            "format_score": max(scoring.get("format_score") or 0, 72),
            "missing_keywords": scoring.get("missing_keywords") or ["system design", "cloud", "testing", "metrics"],
            "strengths": scoring.get("strengths") or ["Relevant placement keywords detected", "Readable resume structure"],
            "weaknesses": scoring.get("weaknesses") or ["Add measurable project outcomes", "Include role-specific keywords"],
            "verdict": scoring.get("verdict") or "Readable resume found. Improve keyword coverage and quantified impact.",
            "source": "fallback",
        }

    # Persist to GridFS for download
    gridfs_id = await gridfs.upload_from_stream(
        f"resume_{user['user_id']}_{file.filename}",
        content,
        metadata={"user_id": user["user_id"], "kind": "resume",
                  "uploaded_at": datetime.now(timezone.utc).isoformat()},
    )
    normalized_score = int(round(float(scoring.get("ats_score") or 0)))
    keyword_score = int(round(float(scoring.get("keyword_match_pct") or 0)))
    format_score = int(round(float(scoring.get("format_score") or 0)))
    record = {
        "ats_id": f"ats_{uuid.uuid4().hex[:10]}",
        "student_id": student_id,
        "user_id": user["user_id"],
        "institution_id": user.get("institution_id"),
        "score": normalized_score,
        "ats_score": normalized_score,
        "keyword_match_pct": keyword_score,
        "keyword_score": keyword_score,
        "format_score": format_score,
        "missing_keywords": scoring.get("missing_keywords", []),
        "strengths": scoring.get("strengths", []),
        "weaknesses": scoring.get("weaknesses", []),
        "recommendations": [
            f"Add quantified evidence for {keyword}"
            for keyword in (scoring.get("missing_keywords", []) or [])[:4]
        ] or ["Add measurable project outcomes", "Tailor summary to the target role"],
        "verdict": scoring.get("verdict"),
        "ai_source": scoring.get("source", "fallback"),
        "ai_model": scoring.get("model"),
        "uploaded_filename": file.filename,
        "content_type": file.content_type,
        "file_size_kb": size_kb,
        "gridfs_id": str(gridfs_id),
        "extracted_chars": len(text),
        "parser_fallback_used": used_fallback_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ats_reports.insert_one(record)
    if student_id:
        previous_versions = await db.resume_versions.count_documents({"student_id": student_id})
        recruiter_match = round(
            ((record.get("score") or 0) * 0.48)
            + ((record.get("keyword_match_pct") or 0) * 0.34)
            + ((record.get("format_score") or 0) * 0.18),
            1,
        )
        await db.resume_versions.insert_one({
            "resume_id": f"res_{uuid.uuid4().hex[:10]}",
            "source_ats_id": record["ats_id"],
            "student_id": student_id,
            "institution_id": record.get("institution_id"),
            "version": previous_versions + 1,
            "upload_date": record["created_at"],
            "uploaded_filename": file.filename,
            "ats_score": record.get("score"),
            "keyword_score": record.get("keyword_match_pct"),
            "missing_keywords": record.get("missing_keywords", []),
            "recruiter_match_score": recruiter_match,
            "format_score": record.get("format_score"),
            "strengths": record.get("strengths", []),
            "weaknesses": record.get("weaknesses", []),
            "verdict": record.get("verdict"),
            "improvement_suggestions": [
                f"Add role-specific evidence for {keyword}"
                for keyword in (record.get("missing_keywords", []) or [])[:4]
            ] or record.get("recommendations", []),
            "created_at": record["created_at"],
        })
    record.pop("_id", None)
    await _audit_log(
        "ats.uploaded",
        user=user,
        institution_id=record.get("institution_id"),
        resource="ats_report",
        resource_id=record["ats_id"],
        metadata={"filename": file.filename, "score": record.get("score"), "size_kb": size_kb},
        request=request,
    )
    return record


@app.get("/api/ats/me/latest")
async def my_latest_ats(user=Depends(get_session_user)):
    sid = user.get("student_id")
    if not sid:
        return {"item": None, "report": None}
    item = await db.ats_reports.find_one({"student_id": sid}, {"_id": 0}, sort=[("created_at", -1)])
    if not item:
        latest_resume = await db.resume_versions.find_one({"student_id": sid}, {"_id": 0}, sort=[("upload_date", -1)])
        item = latest_resume
    return {"item": item, "report": item}


# ============== WEBSOCKET: LIVE UPDATES ==============
@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket, institution_id: Optional[str] = None, token: Optional[str] = None):
    # Auth: verify session token (cookies aren't readable cross-domain by browser WS in many cases,
    # so we accept ?token= as query param too).
    if not token:
        token = websocket.cookies.get("session_token")
    if not token:
        await websocket.close(code=4401); return
    session_query = {"session_token": token}
    claims: Optional[dict] = None
    if token.count(".") == 2:
        try:
            claims = decode_access_token(token)
            session_query = {"jwt_id": claims["jti"]}
        except HTTPException:
            await websocket.close(code=4401); return
    sess = await db.user_sessions.find_one(session_query, {"_id": 0})
    if not sess:
        await websocket.close(code=4401); return
    user = await db.users.find_one({"user_id": claims["sub"] if claims else sess["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        await websocket.close(code=4401); return
    room = institution_id or user.get("institution_id") or "global"
    # super_admin can subscribe to any room they ask for; others scoped to their own institution
    if user["role"] != "super_admin" and room != user.get("institution_id"):
        await websocket.close(code=4403); return
    await ws_manager.connect(room, websocket)
    try:
        # Send a welcome packet so the client knows it's live
        await websocket.send_json({"type": "hello", "room": room,
                                   "user": user.get("name"), "role": user["role"],
                                   "ts": datetime.now(timezone.utc).isoformat()})
        while True:
            msg = await websocket.receive_text()
            # Echo keep-alives if needed
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(room, websocket)


# ============== MULTI-USER INVITES ==============
class InviteBody(BaseModel):
    email: EmailStr
    name: str
    role: Literal["tpo", "institution_admin", "faculty", "coordinator"] = "faculty"
    department: Optional[str] = None
    institution_id: Optional[str] = None  # super_admin can override


@app.post("/api/invite")
async def invite_user(
    body: InviteBody,
    request: Request,
    user=Depends(require_roles("super_admin", "tpo", "institution_admin")),
):
    iid = body.institution_id if user["role"] == "super_admin" else user.get("institution_id")
    if not iid:
        raise HTTPException(400, "institution_id required")
    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(409, "User already exists")
    pw = DEFAULT_DEMO_PASSWORD  # auto-set; user changes after first login (out of scope)
    new = _new_user(email=body.email, name=body.name, role=body.role,
                    institution_id=iid, password=pw, approved=True, department=body.department)
    await db.users.insert_one(new)
    inst = await db.institutions.find_one({"institution_id": iid}, {"_id": 0}) or {}
    await notify(
        db, event="user_invited",
        to_email=body.email,
        subject=f"Welcome to CareerOS — {inst.get('name', 'your institution')}",
        title="You've been invited to CareerOS",
        body_html=(f"<p>Hi {body.name},</p>"
                   f"<p>{user['name']} has invited you to <b>{inst.get('name')}</b>'s placement command center as a <b>{body.role.replace('_', ' ')}</b>.</p>"
                   f"<p>Sign in at <a href='https://career-os-nexus.preview.emergentagent.com/login'>CareerOS</a> using:</p>"
                   f"<p><b>Email:</b> {body.email}<br/><b>Temporary password:</b> {pw}</p>"
                   f"<p>Please change your password after first login.</p>"),
        telegram_text=f"👥 New invite · {body.email} → {inst.get('short_name', iid)} · {body.role}",
    )
    await _audit_log(
        "user.invited",
        user=user,
        institution_id=iid,
        resource="user",
        resource_id=new["user_id"],
        metadata={"target_email": body.email.lower(), "target_role": body.role, "department": body.department},
        request=request,
    )
    return {"user_id": new["user_id"], "email": body.email, "temp_password": pw}


@app.get("/api/institution/users")
async def list_institution_users(user=Depends(require_roles("tpo", "institution_admin", "super_admin"))):
    iid = user.get("institution_id")
    if user["role"] == "super_admin":
        iid = iid or "inst_kmit"
    items = await db.users.find({"institution_id": iid}, {"_id": 0, "password_hash": 0}).to_list(200)
    return {"items": items}


@app.delete("/api/institution/users/{user_id}")
async def remove_institution_user(
    user_id: str,
    request: Request,
    user=Depends(require_roles("tpo", "institution_admin", "super_admin")),
):
    if user_id == user["user_id"]:
        raise HTTPException(400, "Cannot remove yourself")
    target = await db.users.find_one({"user_id": user_id})
    if not target:
        raise HTTPException(404, "not found")
    if user["role"] != "super_admin" and target.get("institution_id") != user.get("institution_id"):
        raise HTTPException(403, "forbidden")
    await db.users.delete_one({"user_id": user_id})
    await _audit_log(
        "user.removed",
        user=user,
        institution_id=target.get("institution_id"),
        resource="user",
        resource_id=user_id,
        metadata={"target_email": target.get("email"), "target_role": target.get("role")},
        request=request,
    )
    return {"ok": True}


# ============== PARTNER INTELLIGENCE WORKFLOWS ==============
def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def _label_from_score(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Average"
    if score >= 40:
        return "Below Average"
    return "Poor"


def _weighted_score(factors: list[dict]) -> int:
    total_weight = sum(float(f.get("weight", 0)) for f in factors) or 1
    raw = sum(float(f.get("value", 0)) * float(f.get("weight", 0)) for f in factors) / total_weight
    return int(max(0, min(100, round(raw))))


async def _compute_institution_health(institution_id: str) -> dict:
    now = datetime.now(timezone.utc)
    students = await db.students.find({"institution_id": institution_id}, {"_id": 0}).to_list(5000)
    total_students = len(students)
    placed_students = sum(1 for s in students if s.get("placement", {}).get("placed"))
    placement_rate = round((placed_students / total_students) * 100) if total_students else 0

    cohorts = await db.training_programs.find({"institution_id": institution_id}, {"_id": 0}).to_list(500)
    active_cohorts = [c for c in cohorts if c.get("status") != "upcoming"]
    training_completion = round(sum(float(c.get("completion_pct", 0)) for c in active_cohorts) / len(active_cohorts)) if active_cohorts else 0

    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    comm_logs = await db.comm_log.find({"institution_id": institution_id, "at": {"$gte": thirty_days_ago}}, {"_id": 0}).to_list(200)
    comm_score = min(100, round((len(comm_logs) / 10) * 100))

    mou = await db.mous.find_one({"institution_id": institution_id}, {"_id": 0}) or {}
    expires_on = _parse_dt(mou.get("expires_on"))
    if not mou:
        mou_status = "none"
    elif expires_on and expires_on < now:
        mou_status = "expired"
    elif expires_on and (expires_on - now).days <= 30:
        mou_status = "expiring"
    else:
        mou_status = mou.get("status") or "active"
    mou_score = 100 if mou_status == "active" else 50 if mou_status == "expiring" else 0

    one_year_ago = (now - timedelta(days=365)).isoformat()
    fdp_sessions = await db.fdp_sessions.find({"institution_id": institution_id, "date": {"$gte": one_year_ago}}, {"_id": 0}).to_list(200)
    fdp_score = min(100, round((len(fdp_sessions) / 5) * 100))

    revenue_rows = await db.revenue_share.find({"institution_id": institution_id}, {"_id": 0}).to_list(200)
    revenue_this_year = sum(float(r.get("share_amount", 0) or r.get("amount", 0) or 0) for r in revenue_rows)
    if not revenue_this_year:
        revenue_this_year = float(mou.get("accrued_share_inr", 0) or 0)
    expected_revenue = float((mou.get("seats_purchased") or max(total_students, 1)) * 15000)
    revenue_score = min(100, round((revenue_this_year / expected_revenue) * 100)) if expected_revenue else 0

    factors = [
        {"label": "Placement Rate", "value": placement_rate, "weight": 0.30, "contribution": placement_rate * 0.30, "detail": f"{placed_students} placed of {total_students} students"},
        {"label": "Training Completion", "value": training_completion, "weight": 0.25, "contribution": training_completion * 0.25, "detail": f"Average {training_completion}% across {len(active_cohorts)} cohorts"},
        {"label": "Communication Activity", "value": comm_score, "weight": 0.15, "contribution": comm_score * 0.15, "detail": f"{len(comm_logs)} touchpoints in the last 30 days"},
        {"label": "MOU Status", "value": mou_score, "weight": 0.15, "contribution": mou_score * 0.15, "detail": f"MOU status is {mou_status}"},
        {"label": "FDP Participation", "value": fdp_score, "weight": 0.10, "contribution": fdp_score * 0.10, "detail": f"{len(fdp_sessions)} FDP sessions in the last 12 months"},
        {"label": "Revenue Contribution", "value": revenue_score, "weight": 0.05, "contribution": revenue_score * 0.05, "detail": f"INR {int(revenue_this_year)} accrued vs INR {int(expected_revenue)} expected"},
    ]
    score = _weighted_score(factors)
    result = {
        "institution_id": institution_id,
        "score": score,
        "grade": _grade_from_score(score),
        "label": _label_from_score(score),
        "factors": factors,
        "computed_at": now.isoformat(),
    }
    await db.institutions.update_one({"institution_id": institution_id}, {"$set": {"health_score": score, "health_label": result["label"], "health_computed_at": result["computed_at"]}})
    await db.college_health_history.insert_one({
        "history_id": f"health_{uuid.uuid4().hex[:10]}",
        **result,
    })
    return result


@app.get("/api/health-score/{institution_id}")
async def institution_health_score(institution_id: str, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    if user["role"] != "super_admin" and institution_id != user.get("institution_id"):
        raise HTTPException(403, "forbidden")
    inst = await db.institutions.find_one({"institution_id": institution_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "institution not found")
    return await _compute_institution_health(institution_id)


@app.post("/api/admin/recompute-health")
async def recompute_health(request: Request, admin=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    if admin["role"] == "super_admin":
        institutions = await db.institutions.find({}, {"_id": 0}).to_list(500)
    else:
        institutions = await db.institutions.find({"institution_id": admin.get("institution_id")}, {"_id": 0}).to_list(1)
    results = [await _compute_institution_health(inst["institution_id"]) for inst in institutions if inst.get("institution_id")]
    await _audit_log("health_scores.recomputed", user=admin, institution_id=admin.get("institution_id"), resource="institution", metadata={"count": len(results)}, request=request)
    return {"success": True, "count": len(results), "items": results}


@app.post("/api/users/toggle-status")
async def toggle_user_status(body: dict, request: Request, admin=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    user_id = body.get("user_id") or body.get("userId")
    if not user_id:
        raise HTTPException(400, "user_id required")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "user not found")
    if admin["role"] != "super_admin" and target.get("institution_id") != admin.get("institution_id"):
        raise HTTPException(403, "forbidden")
    status = str(body.get("new_status") or body.get("newStatus") or body.get("status") or "").lower()
    approved = body.get("approved")
    if approved is None:
        approved = status not in {"inactive", "disabled", "blocked", "false", "0"}
    await db.users.update_one({"user_id": user_id}, {"$set": {"approved": bool(approved), "status": "active" if approved else "inactive", "updated_at": datetime.now(timezone.utc).isoformat()}})
    await _audit_log("user.status_toggled", user=admin, institution_id=target.get("institution_id"), resource="user", resource_id=user_id, metadata={"approved": bool(approved)}, request=request)
    return {"success": True, "user_id": user_id, "approved": bool(approved)}


async def _student_prediction_payload(student_id: str) -> dict:
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "student not found")
    readiness = await build_student_readiness(db, student)
    readiness_components = readiness.get("components", {})
    component_score = lambda key: float((readiness_components.get(key) or {}).get("score", 0))
    enrollments = await db.enrollments.find({"student_id": student_id}, {"_id": 0}).to_list(100)
    training_completion = round(sum(float(e.get("completion_pct", 0)) for e in enrollments) / len(enrollments)) if enrollments else float(student.get("training_completion", 0) or 0)
    aptitude_rows = await db.aptitude_scores.find({"student_id": student_id}, {"_id": 0}).to_list(50)
    assessment_score = round(sum(float(a.get("score", 0)) for a in aptitude_rows) / len(aptitude_rows)) if aptitude_rows else component_score("aptitude")
    dsa_score = component_score("dsa")
    interview_score = component_score("interview")
    attendance = float(student.get("attendance_pct", student.get("attendance", 86)))
    cgpa = float(student.get("cgpa", 0))
    factors = [
        {"label": "Attendance", "value": attendance, "weight": 0.25, "contribution": attendance * 0.25, "detail": f"{attendance}%"},
        {"label": "Training Completion", "value": training_completion, "weight": 0.25, "contribution": training_completion * 0.25, "detail": f"{training_completion}%"},
        {"label": "Assessment Score", "value": assessment_score, "weight": 0.20, "contribution": assessment_score * 0.20, "detail": f"{assessment_score}/100"},
        {"label": "DSA / Mock Interviews", "value": round((dsa_score + interview_score) / 2), "weight": 0.15, "contribution": round((dsa_score + interview_score) / 2) * 0.15, "detail": f"DSA {dsa_score}, interview {interview_score}"},
        {"label": "CGPA", "value": min(100, round((cgpa / 10) * 100)), "weight": 0.15, "contribution": min(100, round((cgpa / 10) * 100)) * 0.15, "detail": f"{cgpa} CGPA"},
    ]
    probability = _weighted_score(factors)
    band = 12.4 if probability >= 80 else 8.6 if probability >= 60 else 6.2 if probability >= 40 else 4.8
    weak = sorted(readiness_components.items(), key=lambda kv: float((kv[1] or {}).get("score", 0)))[:3]
    recommended = [name.replace("_", " ").title() for name, _ in weak] or ["Data Structures", "SQL", "Communication"]
    return {
        "student": {"student_id": student_id, "name": student.get("name"), "department": student.get("department"), "cgpa": cgpa},
        "prediction": {
            "probability": probability,
            "expected_package_lpa": band,
            "risk_level": "low" if probability >= 70 else "medium" if probability >= 40 else "high",
            "recommended_skills": recommended,
            "breakdown": factors,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


@app.get("/api/students/{student_id}/prediction")
async def get_student_prediction(student_id: str, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty", "student"))):
    payload = await _student_prediction_payload(student_id)
    student = payload["student"]
    if user["role"] == "student" and user.get("student_id") != student_id:
        raise HTTPException(403, "forbidden")
    if user["role"] not in {"super_admin", "student"} and student.get("department") and user.get("institution_id"):
        full_student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
        if full_student and full_student.get("institution_id") != user.get("institution_id"):
            raise HTTPException(403, "forbidden")
    return payload


@app.post("/api/students/predict")
async def post_student_prediction(body: dict, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty", "student"))):
    student_id = body.get("student_id") or body.get("studentId") or body.get("id") or user.get("student_id")
    if not student_id:
        raise HTTPException(400, "student_id required")
    return await get_student_prediction(student_id, user)


@app.get("/api/fdp/sessions")
async def list_fdp_sessions(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = user.get("institution_id") or "inst_kmit"
    query = {} if user["role"] == "super_admin" else {"institution_id": iid}
    return {"items": await db.fdp_sessions.find(query, {"_id": 0}).sort("date", -1).limit(200).to_list(200)}


@app.post("/api/fdp/schedule")
async def schedule_fdp(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    if not iid:
        raise HTTPException(400, "institution_id required")
    now = datetime.now(timezone.utc).isoformat()
    session = {
        "session_id": f"fdp_{uuid.uuid4().hex[:10]}",
        "institution_id": iid,
        "title": body.get("title") or "Faculty Development Program",
        "date": body.get("date") or now,
        "duration_hours": float(body.get("duration_hours", body.get("durationHours", 2))),
        "facilitator": body.get("facilitator") or user.get("name"),
        "status": body.get("status") or "scheduled",
        "attendance_count": int(body.get("attendance_count", 0) or 0),
        "created_by": user["user_id"],
        "created_at": now,
    }
    await db.fdp_sessions.insert_one(session)
    await _audit_log("fdp.scheduled", user=user, institution_id=iid, resource="fdp_session", resource_id=session["session_id"], request=request)
    return {"success": True, "item": session}


@app.post("/api/fdp/attendance")
async def mark_fdp_attendance(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    session_id = body.get("session_id") or body.get("sessionId")
    if not session_id:
        raise HTTPException(400, "session_id required")
    session = await db.fdp_sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(404, "session not found")
    if user["role"] != "super_admin" and session.get("institution_id") != user.get("institution_id"):
        raise HTTPException(403, "forbidden")
    update = {
        "attendance_count": int(body.get("attendance_count", body.get("attendanceCount", 0)) or 0),
        "attendees": body.get("attendees", []),
        "status": "completed",
        "attendance_marked_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.fdp_sessions.update_one({"session_id": session_id}, {"$set": update})
    await _audit_log("fdp.attendance_marked", user=user, institution_id=session.get("institution_id"), resource="fdp_session", resource_id=session_id, metadata=update, request=request)
    return {"success": True, "session_id": session_id, **update}


@app.post("/api/mou/renew")
async def renew_mou(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    if not iid:
        raise HTTPException(400, "institution_id required")
    now = datetime.now(timezone.utc)
    expires_on = body.get("expires_on") or (now + timedelta(days=int(body.get("term_days", 365)))).isoformat()
    update = {
        "institution_id": iid,
        "status": "active",
        "signed_on": now.isoformat(),
        "expires_on": expires_on,
        "partnership_type": body.get("partnership_type") or body.get("partnershipType") or "External Placement Partner + CRT + FDP",
        "seats_purchased": int(body.get("seats_purchased", body.get("seatsPurchased", 240))),
        "revenue_share_pct": float(body.get("revenue_share_pct", body.get("revenueSharePct", 18))),
        "renewed_by": user["user_id"],
        "renewed_at": now.isoformat(),
    }
    await db.mous.update_one({"institution_id": iid}, {"$set": update}, upsert=True)
    await _audit_log("mou.renewed", user=user, institution_id=iid, resource="mou", resource_id=iid, metadata=update, request=request)
    return {"success": True, "item": await db.mous.find_one({"institution_id": iid}, {"_id": 0})}


@app.post("/api/mou/esign")
async def esign_mou(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    if not iid:
        raise HTTPException(400, "institution_id required")
    now = datetime.now(timezone.utc)
    esign_update = {
        "esign_status": "signed",
        "esign_by": user["name"] if user.get("name") else user["email"],
        "esign_ip": request.client.host if request.client else "unknown",
        "esign_at": now.isoformat(),
    }
    await db.mous.update_one({"institution_id": iid}, {"$set": esign_update})
    await _audit_log("mou.signed", user=user, institution_id=iid, resource="mou", resource_id=iid, metadata=esign_update, request=request)
    return {"success": True, "item": await db.mous.find_one({"institution_id": iid}, {"_id": 0})}


async def _create_system_notification(*, institution_id: Optional[str], type_: str, title: str, body: str, channels: Optional[list[str]] = None) -> dict:
    item = {
        "notification_id": f"notif_{uuid.uuid4().hex[:10]}",
        "institution_id": institution_id,
        "event": type_,
        "type": type_,
        "title": title,
        "body": body,
        "channels": channels or ["in_app"],
        "status": "sent",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.notification_log.insert_one(item)
    return item


@app.post("/api/notifications/generate-alerts")
async def generate_alerts(request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    query = {} if user["role"] == "super_admin" else {"institution_id": user.get("institution_id")}
    now = datetime.now(timezone.utc)
    created: list[dict] = []
    mous = await db.mous.find(query, {"_id": 0}).to_list(500)
    for mou in mous:
        exp = _parse_dt(mou.get("expires_on"))
        if exp and 0 <= (exp - now).days <= 30:
            created.append(await _create_system_notification(
                institution_id=mou.get("institution_id"),
                type_="mou.expiring",
                title=f"MOU expiring in {(exp - now).days} days",
                body=f"{mou.get('partnership_type', 'MOU')} expires on {exp.date().isoformat()}. Start renewal now.",
                channels=["in_app", "email"] if (exp - now).days <= 10 else ["in_app"],
            ))
            await db.mous.update_one({"institution_id": mou.get("institution_id")}, {"$set": {"status": "expiring"}})
    cohorts = await db.training_programs.find(query, {"_id": 0}).to_list(500)
    for cohort in cohorts:
        if float(cohort.get("completion_pct", 0)) < 50:
            created.append(await _create_system_notification(
                institution_id=cohort.get("institution_id"),
                type_="training.low_completion",
                title=f"Low training completion - {cohort.get('program_name')}",
                body=f"{cohort.get('program_name')} is at {cohort.get('completion_pct')}% completion. Intervention recommended.",
            ))
    students = await db.students.find(query, {"_id": 0}).to_list(5000)
    risk_by_iid: dict[str, int] = {}
    for s in students:
        score = (await build_student_readiness(db, s)).get("score", 0)
        if score < 45:
            risk_by_iid[s.get("institution_id")] = risk_by_iid.get(s.get("institution_id"), 0) + 1
    for iid, count in risk_by_iid.items():
        if iid and count >= 10:
            created.append(await _create_system_notification(
                institution_id=iid,
                type_="student.high_risk_cluster",
                title=f"{count} high-risk students detected",
                body="Readiness engine found a concentrated risk cluster. Review coaching and training plans.",
                channels=["in_app", "email"],
            ))
    await _audit_log("notifications.alerts_generated", user=user, institution_id=user.get("institution_id"), resource="notification", metadata={"created": len(created)}, request=request)
    return {"success": True, "created": len(created), "items": created}


@app.post("/api/notifications/broadcast")
async def broadcast_notification(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    title = body.get("title")
    message = body.get("body") or body.get("message")
    if not title or not message:
        raise HTTPException(400, "title and body required")
    item = await _create_system_notification(institution_id=iid, type_=body.get("type", "broadcast"), title=title, body=message, channels=body.get("channels") or ["in_app"])
    await db.announcements.insert_one({
        "announcement_id": f"ann_{uuid.uuid4().hex[:10]}",
        "institution_id": iid,
        "title": title,
        "body": message,
        "kind": body.get("type", "broadcast"),
        "by_role": user.get("role"),
        "pinned": bool(body.get("pinned", False)),
        "created_at": item["created_at"],
    })
    if iid:
        await ws_manager.broadcast(iid, {"type": "notification.broadcast", "title": title, "body": message, "ts": item["created_at"]})
    await _audit_log("notifications.broadcast", user=user, institution_id=iid, resource="notification", resource_id=item["notification_id"], request=request)
    return {"success": True, "item": item}


@app.post("/api/notifications/mark-read")
async def mark_notifications_read(body: dict, user=Depends(get_session_user)):
    ids = body.get("ids") or body.get("notification_ids") or []
    if isinstance(ids, str):
        ids = [ids]
    if not ids:
        query = {"institution_id": user.get("institution_id")} if user.get("role") != "super_admin" else {}
        items = await db.notification_log.find(query, {"_id": 0}).limit(200).to_list(200)
        ids = [i.get("notification_id") for i in items if i.get("notification_id")]
    count = 0
    for notification_id in ids:
        result = await db.notification_log.update_one({"notification_id": notification_id}, {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}})
        count += getattr(result, "modified_count", 0)
    return {"success": True, "updated": count}


@app.post("/api/revenue/approve-payout")
async def approve_revenue_payout(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    payout_id = body.get("payout_id") or body.get("payoutId") or f"payout_{uuid.uuid4().hex[:10]}"
    amount = float(body.get("amount", 0) or 0)
    period = body.get("period") or datetime.now(timezone.utc).strftime("%Y-Q%q").replace("%q", str((datetime.now(timezone.utc).month - 1) // 3 + 1))
    payout = {
        "payout_id": payout_id,
        "institution_id": iid,
        "amount": amount,
        "period": period,
        "status": "paid",
        "approved_by": user["user_id"],
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payouts.update_one({"payout_id": payout_id}, {"$set": payout}, upsert=True)
    if iid:
        await db.mous.update_one({"institution_id": iid}, {"$set": {"payout_status": f"Paid - {period}", "last_payout_at": payout["approved_at"]}})
    await _audit_log("revenue.payout_approved", user=user, institution_id=iid, resource="payout", resource_id=payout_id, metadata={"amount": amount, "period": period}, request=request)
    return {"success": True, "item": payout}


@app.post("/api/reports/create")
async def create_report_run(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = body.get("institution_id") if user["role"] == "super_admin" else user.get("institution_id")
    report = {
        "report_id": f"report_{uuid.uuid4().hex[:10]}",
        "institution_id": iid,
        "type": body.get("type", "placement"),
        "status": "created",
        "title": body.get("title") or f"{body.get('type', 'placement').title()} report",
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filters": body.get("filters", {}),
    }
    await db.report_runs.insert_one(report)
    await _audit_log("report.created", user=user, institution_id=iid, resource="report", resource_id=report["report_id"], request=request)
    return {"success": True, "item": report}


@app.post("/api/reports/generate")
async def generate_report_run(body: dict, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    report_id = body.get("report_id") or body.get("reportId")
    if report_id:
        report = await db.report_runs.find_one({"report_id": report_id}, {"_id": 0})
        if not report:
            raise HTTPException(404, "report not found")
    else:
        report = (await create_report_run(body, request, user))["item"]
        report_id = report["report_id"]
    iid = report.get("institution_id") or user.get("institution_id") or "inst_kmit"
    overview = await _institution_overview_for_reports(iid)
    generated = {
        "status": "generated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "placement_rate": overview.get("placement_rate"),
            "students": overview.get("students"),
            "placed": overview.get("placed"),
            "offers": overview.get("offers"),
        },
        "exports": {
            "placement_pdf": "/api/reports/placement.pdf",
            "training_pdf": "/api/reports/training.pdf",
            "students_csv": "/api/reports/students.csv",
        },
    }
    await db.report_runs.update_one({"report_id": report_id}, {"$set": generated})
    await _audit_log("report.generated", user=user, institution_id=iid, resource="report", resource_id=report_id, metadata=generated["summary"], request=request)
    return {"success": True, "item": {**report, **generated}}


@app.post("/api/college/action")
async def college_action(body: dict, request: Request, admin=Depends(require_roles("super_admin"))):
    institution_id = body.get("institution_id") or body.get("college_id") or body.get("collegeId")
    action = body.get("action")
    if not institution_id or not action:
        raise HTTPException(400, "institution_id and action required")
    status_by_action = {
        "approve": {"approved": True, "status": "active"},
        "activate": {"approved": True, "status": "active"},
        "suspend": {"approved": True, "status": "suspended"},
        "reject": {"approved": False, "status": "rejected"},
    }
    update = status_by_action.get(str(action).lower())
    if not update:
        raise HTTPException(400, "unsupported action")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.institutions.update_one({"institution_id": institution_id}, {"$set": update})
    await _audit_log("institution.action", user=admin, institution_id=institution_id, resource="institution", resource_id=institution_id, metadata={"action": action, **update}, request=request)
    return {"success": True, "institution_id": institution_id, **update}


# ============== GOOGLE OAUTH ==============
@app.get("/api/auth/google/start")
async def google_oauth_start(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(503, "Google OAuth is not configured")

    state = uuid.uuid4().hex
    redirect_uri = _google_redirect_uri(request)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    response = RedirectResponse(
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params),
        status_code=302,
    )
    secure_cookie = _cookie_secure(request)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=secure_cookie,
        samesite="none" if secure_cookie else "lax",
        path="/",
        max_age=10 * 60,
    )
    return response


@app.get("/api/auth/google/callback")
async def google_oauth_callback(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(503, "Google OAuth is not configured")

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Google authorization code missing")

    state = request.query_params.get("state")
    cookie_state = request.cookies.get("oauth_state")
    if cookie_state and state != cookie_state:
        raise HTTPException(400, "Invalid Google OAuth state")

    redirect_uri = _google_redirect_uri(request)
    async with httpx.AsyncClient(timeout=15) as hx:
        token_resp = await hx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            await _audit_log(
                "auth.google_token_failed",
                outcome="failure",
                metadata={"status_code": token_resp.status_code},
                request=request,
            )
            raise HTTPException(401, "Google token exchange failed")

        token_data = token_resp.json()
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(401, "Google ID token missing")

        profile_resp = await hx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
        if profile_resp.status_code != 200:
            raise HTTPException(401, "Google profile validation failed")
        profile = profile_resp.json()

    if profile.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Invalid Google audience")
    if str(profile.get("email_verified", "")).lower() not in {"true", "1"}:
        raise HTTPException(401, "Google email is not verified")

    email = profile["email"].lower()
    name = profile.get("name") or email
    picture = profile.get("picture")
    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name or existing.get("name"), "picture": picture}},
        )
    else:
        is_admin = email == ADMIN_EMAIL
        new = _new_user(
            email=email,
            name=name,
            role="super_admin" if is_admin else "tpo",
            institution_id=None,
            password=None,
            approved=is_admin,
        )
        new["picture"] = picture
        await db.users.insert_one(new)
        user_id = new["user_id"]

    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    target = "/app" if user_doc.get("approved") or user_doc.get("role") == "super_admin" else "/pending"
    response = RedirectResponse(url=target, status_code=303)
    response.delete_cookie("oauth_state", path="/")
    await _create_session(user_id, response, request, token=token_data.get("access_token"))
    await _audit_log("auth.google_oauth", user=user_doc, request=request)
    return response


# ============== EXTRA AUTH ENDPOINTS ==============
@app.post("/api/auth/forgot-password")
async def forgot_password(body: ForgotPasswordBody, request: Request):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")
    
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_reset_tokens.update_one(
        {"email": email},
        {"$set": {"token": token, "expires_at": expires_at}},
        upsert=True
    )
    
    reset_url = f"{_public_origin(request)}/reset-password?token={token}"
    await notify(
        db,
        event="auth.password_reset",
        to_email=email,
        subject="Reset Your CareerOS Password",
        title="Password Reset Request",
        body_html=f"Please reset your password using <a href='{reset_url}'>this link</a>."
    )
    
    return {"success": True}


@app.post("/api/auth/reset-password")
async def reset_password(body: ResetPasswordBody, request: Request):
    tok_doc = await db.password_reset_tokens.find_one({"token": body.token})
    if not tok_doc:
        raise HTTPException(400, "Invalid or expired token")
        
    expires_at = tok_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        await db.password_reset_tokens.delete_one({"token": body.token})
        raise HTTPException(400, "Token expired")
        
    email = tok_doc["email"]
    password_hash = hash_password(body.new_password)
    
    await db.users.update_one({"email": email}, {"$set": {"password_hash": password_hash}})
    await db.password_reset_tokens.delete_one({"token": body.token})
    
    await _audit_log("auth.password_reset_complete", metadata={"email": email}, request=request)
    return {"success": True}


@app.post("/api/auth/refresh")
async def auth_refresh(request: Request, response: Response):
    token = request.cookies.get("session_token")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    from auth import JWT_SECRET, JWT_ALGORITHM, JWT_ISSUER
    import jwt
    try:
        claims = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti"], "verify_exp": False}
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, "Invalid session") from exc

    jti = claims["jti"]
    sess = await db.user_sessions.find_one({"jwt_id": jti})
    if not sess:
        raise HTTPException(401, "Session not found")
    
    expires_at = sess["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"jwt_id": jti})
        raise HTTPException(401, "Session expired")
    
    user_id = sess["user_id"]
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(401, "User not found")
        
    new_token, new_jti, new_exp = create_access_token(user)
    
    await db.user_sessions.update_one(
        {"jwt_id": jti},
        {"$set": {
            "session_token": new_token,
            "jwt_id": new_jti,
            "expires_at": new_exp.isoformat()
        }}
    )
    
    secure_cookie = _cookie_secure(request)
    response.set_cookie(
        key="session_token", value=new_token,
        httponly=True, secure=secure_cookie, samesite="none" if secure_cookie else "lax", path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return {"access_token": new_token, "user": user}


@app.post("/api/auth/register")
async def auth_register(payload: RegisterBody, request: Request, response: Response):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(400, "Email already registered")
        
    approved = False
    inst_id = payload.institution_id
    
    if payload.role == "student":
        if not inst_id:
            raise HTTPException(400, "Institution ID is required for students")
        inst = await db.institutions.find_one({"institution_id": inst_id})
        if not inst:
            raise HTTPException(404, "Institution not found")
        if inst.get("approved", True):
            approved = True
            
    elif payload.role == "tpo":
        if not payload.college_name:
            raise HTTPException(400, "College name is required for TPO registration")
        inst_id = f"inst_{uuid.uuid4().hex[:10]}"
        short = payload.college_name.split()
        short_name = "".join(w[0] for w in short).upper()[:6] if short else "COLL"
        await db.institutions.insert_one({
            "institution_id": inst_id,
            "name": payload.college_name,
            "short_name": short_name,
            "affiliated_university": payload.affiliated_university or "JNTUH",
            "partnership_type": payload.partnership_type or "CRT",
            "departments": [payload.department] if payload.department else [],
            "approved": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        approved = False
        
    elif payload.role == "recruiter":
        if not payload.company_name:
            raise HTTPException(400, "Company name is required for recruiters")
        approved = False
        
    elif payload.role == "faculty":
        if not inst_id:
            raise HTTPException(400, "Institution ID is required for faculty")
        approved = False
        
    new_user_doc = _new_user(
        email=email,
        name=payload.name,
        role=payload.role,
        institution_id=inst_id,
        password=payload.password,
        approved=approved,
        department=payload.department
    )
    
    if payload.role == "recruiter":
        new_user_doc["company_name"] = payload.company_name
        await db.recruiters.insert_one({
            "recruiter_id": new_user_doc["user_id"],
            "name": payload.name,
            "company": payload.company_name,
            "email": email,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
    elif payload.role == "student":
        await db.students.insert_one({
            "student_id": new_user_doc["user_id"],
            "name": payload.name,
            "email": email,
            "roll_number": payload.roll_number or f"STU{uuid.uuid4().hex[:6].upper()}",
            "department": payload.department or "CSE",
            "institution_id": inst_id,
            "cgpa": 7.5,
            "readiness_score": 50,
            "consistency_score": 50,
            "placement_status": "unplaced",
            "skills": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    await db.users.insert_one(new_user_doc)
    await _audit_log("auth.register", user=new_user_doc, request=request)
    
    await notify(
        db,
        event="auth.register_welcome",
        to_email=email,
        subject="Welcome to CareerOS",
        title="Welcome to CareerOS",
        body_html=f"Hi {payload.name},<br/><br/>Thank you for registering on CareerOS as a {payload.role}. " + 
                  ("Your account has been auto-approved and is ready to use!" if approved else "Your account is pending administrator approval.")
    )
    
    if approved:
        access_token = await _create_session(new_user_doc["user_id"], response, request)
        return {
            "status": "approved",
            "user": {k: v for k, v in new_user_doc.items() if k not in ("password_hash", "_id")},
            "access_token": access_token
        }
    else:
        return {
            "status": "pending_approval",
            "message": "Registration successful. Pending admin approval."
        }


@app.get("/api/public/institutions")
async def list_public_institutions():
    items = await db.institutions.find({}, {"_id": 0, "institution_id": 1, "name": 1, "departments": 1}).to_list(100)
    return {"items": items}


# ============== COMM LOG CRUD ==============
class CommLogBody(BaseModel):
    type: Literal["meeting", "note", "follow_up", "comment"]
    subject: str
    summary: str
    by: str


class UpdateCommLogBody(BaseModel):
    subject: Optional[str] = None
    summary: Optional[str] = None


@app.get("/api/comm-log")
async def get_comm_logs(user=Depends(get_session_user)):
    if user["role"] not in ("tpo", "faculty", "institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
    
    query = {}
    if user["role"] != "super_admin":
        query["institution_id"] = user.get("institution_id")
        
    logs = await db.comm_log.find(query).sort("at", -1).to_list(100)
    for l in logs:
        l["log_id"] = str(l.get("log_id", ""))
        if "_id" in l:
            del l["_id"]
    return {"items": logs}


@app.post("/api/comm-log")
async def create_comm_log(payload: CommLogBody, request: Request, user=Depends(get_session_user)):
    if user["role"] not in ("tpo", "faculty", "institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
    
    inst_id = user.get("institution_id")
    if user["role"] == "super_admin":
        inst_id = inst_id or "inst_kmit"
        
    log_doc = {
        "log_id": f"log_{uuid.uuid4().hex[:10]}",
        "institution_id": inst_id,
        "type": payload.type,
        "subject": payload.subject,
        "summary": payload.summary,
        "by": payload.by,
        "at": datetime.now(timezone.utc).isoformat()
    }
    await db.comm_log.insert_one(log_doc)
    await _audit_log("comm_log.create", user=user, metadata={"log_id": log_doc["log_id"]}, request=request)
    if "_id" in log_doc:
        del log_doc["_id"]
    return log_doc


@app.patch("/api/comm-log/{log_id}")
async def update_comm_log(log_id: str, payload: UpdateCommLogBody, request: Request, user=Depends(get_session_user)):
    if user["role"] not in ("tpo", "faculty", "institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
        
    existing = await db.comm_log.find_one({"log_id": log_id})
    if not existing:
        raise HTTPException(404, "Log entry not found")
        
    if user["role"] != "super_admin" and existing.get("institution_id") != user.get("institution_id"):
        raise HTTPException(403, "Access denied")
        
    upd = {}
    if payload.subject is not None:
        upd["subject"] = payload.subject
    if payload.summary is not None:
        upd["summary"] = payload.summary
        
    if upd:
        await db.comm_log.update_one({"log_id": log_id}, {"$set": upd})
        await _audit_log("comm_log.update", user=user, metadata={"log_id": log_id}, request=request)
        
    updated = await db.comm_log.find_one({"log_id": log_id}, {"_id": 0})
    return updated


@app.delete("/api/comm-log/{log_id}")
async def delete_comm_log(log_id: str, request: Request, user=Depends(get_session_user)):
    if user["role"] not in ("tpo", "faculty", "institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
        
    existing = await db.comm_log.find_one({"log_id": log_id})
    if not existing:
        raise HTTPException(404, "Log entry not found")
        
    if user["role"] != "super_admin" and existing.get("institution_id") != user.get("institution_id"):
        raise HTTPException(403, "Access denied")
        
    await db.comm_log.delete_one({"log_id": log_id})
    await _audit_log("comm_log.delete", user=user, metadata={"log_id": log_id}, request=request)
    return {"ok": True}


# ============== WORKSHOPS, BENCHMARKING, PARTNER CHAT ==============
class WorkshopBody(BaseModel):
    title: str
    type: Literal["workshop", "hackathon", "bootcamp", "webinar"] = "workshop"
    preferred_date: Optional[str] = None
    attendees: int = 60
    notes: Optional[str] = None
    institution_id: Optional[str] = None


class WorkshopStatusBody(BaseModel):
    status: Literal["requested", "reviewing", "approved", "declined", "scheduled"]
    scheduled_date: Optional[str] = None
    admin_notes: Optional[str] = None


class ChatMessageBody(BaseModel):
    content: str
    institution_id: Optional[str] = None


def _partner_scope(user: dict, explicit_institution_id: Optional[str] = None) -> str:
    if user.get("role") == "super_admin":
        return explicit_institution_id or user.get("institution_id") or "inst_kmit"
    iid = user.get("institution_id")
    if explicit_institution_id and explicit_institution_id != iid:
        raise HTTPException(403, "Cross-institution access denied")
    if not iid:
        raise HTTPException(400, "institution_id required")
    return iid


async def _workshop_counts(institution_id: Optional[str] = None) -> dict:
    query = {"institution_id": institution_id} if institution_id else {}
    rows = await db.workshop_requests.find(query, {"_id": 0}).to_list(500)
    return {
        "total": len(rows),
        "requested": sum(1 for r in rows if r.get("status") == "requested"),
        "reviewing": sum(1 for r in rows if r.get("status") == "reviewing"),
        "approved": sum(1 for r in rows if r.get("status") == "approved"),
        "scheduled": sum(1 for r in rows if r.get("status") == "scheduled"),
        "declined": sum(1 for r in rows if r.get("status") == "declined"),
    }


@app.get("/api/workshops")
async def list_workshops(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    query = {}
    if user["role"] != "super_admin":
        query["institution_id"] = user.get("institution_id")
    items = await db.workshop_requests.find(query, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    summary = await _workshop_counts(None if user["role"] == "super_admin" else user.get("institution_id"))
    return {"items": items, "summary": summary}


@app.post("/api/workshops")
async def create_workshop(payload: WorkshopBody, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = _partner_scope(user, payload.institution_id)
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "workshop_id": f"workshop_{uuid.uuid4().hex[:10]}",
        "institution_id": iid,
        "title": payload.title,
        "type": payload.type,
        "preferred_date": payload.preferred_date,
        "attendees": int(payload.attendees or 0),
        "notes": payload.notes or "",
        "status": "requested",
        "requested_by": user.get("user_id"),
        "requested_by_name": user.get("name") or user.get("email"),
        "created_at": now,
        "updated_at": now,
    }
    await db.workshop_requests.insert_one(doc)
    await _create_system_notification(
        institution_id=iid,
        type_="workshop.requested",
        title="Workshop request submitted",
        body=f"{doc['title']} is waiting for platform review.",
        channels=["in_app"],
    )
    await _audit_log("workshop.requested", user=user, institution_id=iid, resource="workshop", resource_id=doc["workshop_id"], request=request)
    await ws_manager.broadcast(iid, {"type": "workshop.requested", "item": {k: v for k, v in doc.items() if k != "_id"}})
    doc.pop("_id", None)
    return {"success": True, "item": doc}


@app.patch("/api/workshops/{workshop_id}/status")
async def update_workshop_status(workshop_id: str, payload: WorkshopStatusBody, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo"))):
    existing = await db.workshop_requests.find_one({"workshop_id": workshop_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "workshop not found")
    if user["role"] != "super_admin" and existing.get("institution_id") != user.get("institution_id"):
        raise HTTPException(403, "forbidden")
    update = {
        "status": payload.status,
        "admin_notes": payload.admin_notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if payload.scheduled_date:
        update["scheduled_date"] = payload.scheduled_date
    await db.workshop_requests.update_one({"workshop_id": workshop_id}, {"$set": update})
    item = await db.workshop_requests.find_one({"workshop_id": workshop_id}, {"_id": 0})
    await _create_system_notification(
        institution_id=item.get("institution_id"),
        type_="workshop.updated",
        title=f"Workshop {payload.status}",
        body=f"{item.get('title')} moved to {payload.status}.",
        channels=["in_app"],
    )
    await _audit_log("workshop.status_updated", user=user, institution_id=item.get("institution_id"), resource="workshop", resource_id=workshop_id, metadata={"status": payload.status}, request=request)
    await ws_manager.broadcast(item.get("institution_id"), {"type": "workshop.updated", "item": item})
    return {"success": True, "item": item}


async def _institution_benchmark_row(inst: dict) -> dict:
    iid = inst.get("institution_id")
    students = await db.students.find({"institution_id": iid}, {"_id": 0}).to_list(5000)
    student_count = len(students)
    placed = sum(1 for s in students if s.get("placement", {}).get("placed"))
    readiness_values = [float(s.get("readiness_score", 0) or s.get("readiness", 0) or 0) for s in students]
    placement_rate = round((placed / student_count) * 100, 1) if student_count else 0
    avg_readiness = round(sum(readiness_values) / len(readiness_values), 1) if readiness_values else 0
    cohorts = await db.training_programs.find({"institution_id": iid}, {"_id": 0}).to_list(500)
    completion = round(sum(float(c.get("completion_pct", 0) or 0) for c in cohorts) / len(cohorts), 1) if cohorts else 0
    mou = await db.mous.find_one({"institution_id": iid}, {"_id": 0}) or {}
    seats_purchased = int(mou.get("seats_purchased", student_count) or student_count or 0)
    seats_used = int(mou.get("seats_used", min(student_count, seats_purchased)) or 0)
    health = float(inst.get("health_score", 0) or 0)
    if not health:
        health = round((placement_rate * 0.35) + (avg_readiness * 0.35) + (completion * 0.2) + (min(100, (seats_used / max(1, seats_purchased)) * 100) * 0.1), 1)
    return {
        "institution_id": iid,
        "name": inst.get("name"),
        "short_name": inst.get("short_name") or inst.get("name"),
        "student_count": student_count,
        "placement_rate": placement_rate,
        "avg_readiness": avg_readiness,
        "training_completion": completion,
        "health_score": health,
        "seats_purchased": seats_purchased,
        "seats_used": seats_used,
    }


@app.get("/api/benchmarking/partner")
async def partner_benchmarking(user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = _partner_scope(user, None)
    institutions = await db.institutions.find({}, {"_id": 0}).to_list(500)
    rows = [await _institution_benchmark_row(inst) for inst in institutions if inst.get("institution_id")]
    rows = [r for r in rows if r["student_count"] or r["institution_id"] == iid]
    if not rows:
        return {"self": None, "averages": {}, "top_band": {}, "leaderboard": []}
    metrics = ["placement_rate", "avg_readiness", "training_completion", "health_score"]
    averages = {m: round(sum(float(r.get(m, 0)) for r in rows) / len(rows), 1) for m in metrics}
    sorted_by_health = sorted(rows, key=lambda r: r.get("health_score", 0), reverse=True)
    top_n = max(1, round(len(sorted_by_health) * 0.1))
    top_rows = sorted_by_health[:top_n]
    top_band = {m: round(sum(float(r.get(m, 0)) for r in top_rows) / len(top_rows), 1) for m in metrics}
    self_row = next((r for r in rows if r["institution_id"] == iid), rows[0])
    rank = next((idx + 1 for idx, r in enumerate(sorted_by_health) if r["institution_id"] == self_row["institution_id"]), len(rows))
    percentile = round(((len(rows) - rank + 1) / len(rows)) * 100)
    return {
        "self": {**self_row, "rank": rank, "percentile": percentile},
        "averages": averages,
        "top_band": top_band,
        "leaderboard": sorted_by_health[:12],
        "insight": f"{self_row['short_name']} is rank {rank} of {len(rows)} with a {self_row['health_score']} health score.",
    }


@app.get("/api/chat/room")
async def get_chat_room(institution_id: Optional[str] = None, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = _partner_scope(user, institution_id)
    room = await db.chat_rooms.find_one({"institution_id": iid}, {"_id": 0})
    if not room:
        room = {
            "room_id": f"room_{uuid.uuid5(uuid.NAMESPACE_DNS, iid).hex[:12]}",
            "institution_id": iid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.chat_rooms.insert_one(room)
        room.pop("_id", None)
    return {"room": room}


@app.get("/api/chat/messages")
async def list_chat_messages(institution_id: Optional[str] = None, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    iid = _partner_scope(user, institution_id)
    room = (await get_chat_room(iid, user))["room"]
    items = await db.chat_messages.find({"room_id": room["room_id"]}, {"_id": 0}).sort("created_at", 1).limit(200).to_list(200)
    return {"room": room, "items": items}


@app.post("/api/chat/messages")
async def create_chat_message(payload: ChatMessageBody, request: Request, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    if not payload.content.strip():
        raise HTTPException(400, "message required")
    iid = _partner_scope(user, payload.institution_id)
    room = (await get_chat_room(iid, user))["room"]
    item = {
        "message_id": f"msg_{uuid.uuid4().hex[:10]}",
        "room_id": room["room_id"],
        "institution_id": iid,
        "sender_user_id": user.get("user_id"),
        "sender_name": user.get("name") or user.get("email"),
        "sender_role": user.get("role"),
        "content": payload.content.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.chat_messages.insert_one(item)
    await _audit_log("chat.message_sent", user=user, institution_id=iid, resource="chat_message", resource_id=item["message_id"], request=request)
    clean = {k: v for k, v in item.items() if k != "_id"}
    await ws_manager.broadcast(iid, {"type": "chat.message", "item": clean})
    return {"success": True, "item": clean}


# ============== REVENUE ==============
class RevenueShareBody(BaseModel):
    institution_id: str
    amount_inr: float
    period: str
    type: str


@app.get("/api/revenue/me")
async def get_my_revenue(user=Depends(get_session_user)):
    if user["role"] not in ("tpo", "institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
        
    inst_id = user.get("institution_id")
    if not inst_id and user["role"] == "super_admin":
        inst_id = "inst_kmit"
        
    records = await db.revenue_share.find({"institution_id": inst_id}).sort("date", -1).to_list(100)
    for r in records:
        if "_id" in r:
            del r["_id"]
            
    total_accrued = sum(r.get("amount_inr", 0) for r in records)
    expected = total_accrued * 1.1
    
    mou = await db.mous.find_one({"institution_id": inst_id})
    mou_terms = {
        "share_percentage": 15,
        "billing_cycle": "Quarterly",
        "partnership_type": mou.get("partnership_type", "CRT") if mou else "CRT"
    }
    
    return {
        "total_accrued_inr": total_accrued,
        "expected_inr": expected,
        "revenue_score": 85 if total_accrued > 0 else 0,
        "payout_status": "Active" if total_accrued > 0 else "Pending",
        "records": records,
        "mou_terms": mou_terms
    }


@app.post("/api/revenue/share")
async def create_revenue_share(payload: RevenueShareBody, request: Request, user=Depends(get_session_user)):
    if user["role"] not in ("institution_admin", "super_admin"):
        raise HTTPException(403, "Forbidden")
        
    doc = {
        "revenue_id": f"rev_{uuid.uuid4().hex[:10]}",
        "institution_id": payload.institution_id,
        "amount_inr": payload.amount_inr,
        "period": payload.period,
        "type": payload.type,
        "date": datetime.now(timezone.utc).isoformat()
    }
    await db.revenue_share.insert_one(doc)
    await _audit_log("revenue.create", user=user, metadata={"revenue_id": doc["revenue_id"]}, request=request)
    if "_id" in doc:
        del doc["_id"]
    return doc


# ============== CAREEROS INTELLIGENCE COPILOT ==============
class CopilotBody(BaseModel):
    question: str
    surface: str = "overview"
    what_if: Optional[dict] = None


def _chart_type_for_question(question: str) -> str:
    q = (question or "").lower()
    if re.search(r"\b(trend|forecast|over time|year|history|line)\b", q):
        return "line"
    if re.search(r"\b(distribution|share|pie|mix|proportion)\b", q):
        return "pie"
    if re.search(r"\b(funnel|pipeline|conversion|bottleneck|drop)\b", q):
        return "funnel"
    if re.search(r"\b(heatmap|weak|risk|readiness|department)\b", q):
        return "heatmap"
    return "bar"


def _rows_for_chart(question: str, analytics: dict, platform: dict, recruiter: Optional[dict] = None) -> list[dict]:
    q = (question or "").lower()
    if "funnel" in q or "pipeline" in q or "conversion" in q or "bottleneck" in q:
        return [{"category": r.get("stage"), "value": r.get("count", 0), "secondary": r.get("leakage", 0)} for r in analytics.get("funnel", [])]
    if "trend" in q or "forecast" in q or "package" in q or "year" in q:
        return [{"category": r.get("academic_year"), "value": r.get("offers", 0), "secondary": r.get("avg_lpa", 0)} for r in analytics.get("trend", [])]
    if "college" in q or "institution" in q or "platform" in q:
        return [{"category": r.get("type") or "Institution", "value": r.get("count", 0)} for r in platform.get("by_type", [])]
    if recruiter and ("recruiter" in q or "hiring" in q or "interview" in q):
        return [{"category": r.get("title") or r.get("company") or "Role", "value": r.get("applications", 0), "secondary": r.get("conversion_rate", 0)} for r in recruiter.get("job_funnels", [])[:8]]
    return [{"category": r.get("department"), "value": r.get("health_score", 0), "secondary": r.get("placement_rate", 0)} for r in analytics.get("department_health", [])]


def _infer_copilot_intent(question: str) -> str:
    q = (question or "").lower()
    if "what if" in q or "increase" in q or "+10" in q or "improve" in q:
        return "what_if"
    if "risk" in q or "anomal" in q or "weak" in q or "bottleneck" in q:
        return "anomaly"
    if "report" in q or "summary" in q or "executive" in q:
        return "executive_report"
    if "compare" in q:
        return "compare"
    if "forecast" in q or "predict" in q or "package" in q:
        return "forecast"
    return "analytics"


def _what_if_projection(analytics: dict, body: CopilotBody) -> dict:
    summary = analytics.get("summary", {})
    forecast = analytics.get("forecast", {})
    knobs = body.what_if or {}
    q = (body.question or "").lower()
    training_delta = float(knobs.get("training", 10 if "training" in q or "+10" in q else 0) or 0)
    resume_delta = float(knobs.get("resume", 15 if "resume" in q else 0) or 0)
    interview_delta = float(knobs.get("interview", 20 if "interview" in q else 0) or 0)
    dsa_delta = float(knobs.get("dsa", 12 if "dsa" in q else 0) or 0)
    lift = (training_delta * 0.18) + (resume_delta * 0.16) + (interview_delta * 0.22) + (dsa_delta * 0.19)
    base_offers = forecast.get("forecasted_offers", summary.get("offers_latest", 0) or 0)
    base_conversion = summary.get("conversion_rate", 0)
    base_package = max(analytics.get("trend", [{}])[-1].get("avg_lpa", 0) if analytics.get("trend") else 0, 5.5)
    return {
        "inputs": {
            "training_delta": training_delta,
            "resume_delta": resume_delta,
            "interview_delta": interview_delta,
            "dsa_delta": dsa_delta,
        },
        "placements": int(round(base_offers + lift * 1.8)),
        "package_lpa": round(base_package + (lift * 0.035), 1),
        "conversion_rate": round(min(96, base_conversion + lift * 0.22), 1),
        "risk_reduction": round(min(65, lift * 0.4), 1),
        "confidence": "high" if forecast.get("confidence") == "high" or lift >= 8 else "medium",
    }


def _copilot_anomalies(analytics: dict) -> list[dict]:
    anomalies = []
    for risk in analytics.get("risk_register", []):
        anomalies.append({
            "title": risk.get("risk"),
            "severity": risk.get("severity", "medium"),
            "confidence": 86 if risk.get("severity") == "high" else 74,
            "recommendation": risk.get("action") or "Assign an owner and review the signal this week.",
        })
    for dept in analytics.get("department_health", [])[:4]:
        if dept.get("health") in {"critical", "watch"} or dept.get("placement_rate", 100) < 65:
            anomalies.append({
                "title": f"{dept.get('department')} readiness drift",
                "severity": "high" if dept.get("health") == "critical" else "medium",
                "confidence": 82,
                "recommendation": f"Run a {dept.get('department')} intervention sprint focused on readiness, DSA, ATS, and interviews.",
            })
    return anomalies[:8]


def _copilot_answer(question: str, intent: str, analytics: dict, platform: dict, what_if: dict, anomalies: list[dict]) -> str:
    summary = analytics.get("summary", {})
    dept_rows = analytics.get("department_health", [])
    weakest = dept_rows[0] if dept_rows else {}
    forecast = analytics.get("forecast", {})
    if intent == "what_if":
        return (
            f"If the selected levers improve, projected placements move to {what_if['placements']} with "
            f"{what_if['conversion_rate']}% conversion and an expected package band around {what_if['package_lpa']} LPA. "
            f"Risk should reduce by about {what_if['risk_reduction']} points with {what_if['confidence']} confidence."
        )
    if intent == "anomaly":
        lead = anomalies[0] if anomalies else {"title": "No severe anomaly", "recommendation": "Keep weekly monitoring active."}
        return f"The leading anomaly is {lead['title']}. Recommendation: {lead['recommendation']}"
    if intent == "compare":
        top = dept_rows[-1] if dept_rows else {}
        return f"{top.get('department', 'Top department')} leads at {top.get('health_score', 0)}/100 health, while {weakest.get('department', 'the weakest department')} needs action at {weakest.get('health_score', 0)}/100."
    if intent == "forecast":
        return f"Current forecast is {forecast.get('forecasted_offers', 0)} offers with {forecast.get('confidence', 'medium')} confidence. Placement health is {summary.get('placement_rate', 0)}% and conversion is {summary.get('conversion_rate', 0)}%."
    if intent == "executive_report":
        return f"Executive summary: command score is {summary.get('command_score', 0)}/100. Strength is placement momentum; weakness is {weakest.get('department', 'department')} health. Priority is to reduce intervention load and protect funnel conversion."
    return f"{weakest.get('department', 'Department')} is the weakest visible signal with {weakest.get('health_score', 0)}/100 health. Overall command score is {summary.get('command_score', 0)}/100."


@app.post("/api/ai/copilot")
async def ai_copilot(body: CopilotBody, user=Depends(require_roles("super_admin", "institution_admin", "tpo", "faculty"))):
    question = (body.question or "").strip() or "Generate executive summary"
    analytics = await _analytics_engine_payload(user)
    if user.get("role") == "super_admin":
        platform = await platform_stats(admin=user)
    else:
        _iid, _dept, scoped_students = await _student_scope_for_user(user)
        platform = {
            "institutions": 1,
            "pending_signups": 0,
            "students": len(scoped_students) or 5000,
            "applications": sum((analytics.get("summary", {}).get("active_pipeline", 0), analytics.get("summary", {}).get("offers_latest", 0))),
            "jobs_open": analytics.get("forecast", {}).get("open_capacity", 0),
            "recruiters": len(analytics.get("trend", [])) * 6,
            "estimated_mrr_inr": 0,
            "by_type": [{"type": analytics.get("scope", {}).get("institution") or "Institution", "count": 1}],
        }
    recruiter_data = None
    intent = _infer_copilot_intent(question)
    chart_type = _chart_type_for_question(question)
    chart_rows = _rows_for_chart(question, analytics, platform, recruiter_data)
    anomalies = _copilot_anomalies(analytics)
    what_if = _what_if_projection(analytics, body)
    answer = _copilot_answer(question, intent, analytics, platform, what_if, anomalies)
    executive_summary = {
        "summary": answer,
        "strengths": [
            f"Command score {analytics.get('summary', {}).get('command_score', 0)}/100",
            f"Forecast confidence {analytics.get('forecast', {}).get('confidence', 'medium')}",
        ],
        "weaknesses": [a["title"] for a in anomalies[:3]] or ["No severe weakness detected"],
        "predictions": [
            f"{analytics.get('forecast', {}).get('forecasted_offers', 0)} forecasted offers",
            f"{what_if['placements']} offers under selected what-if scenario",
        ],
        "recommendations": [r.get("title") or r.get("body") for r in analytics.get("recommendations", [])[:4]],
        "risk_factors": [a["title"] for a in anomalies[:4]],
        "opportunities": ["Improve DSA and ATS readiness", "Convert interview-stage pipeline", "Run department-specific clinics"],
    }
    memory_doc = {
        "user_id": user["user_id"],
        "role": user.get("role"),
        "surface": body.surface,
        "question": question,
        "intent": intent,
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ai_copilot_memory.insert_one(memory_doc)
    memory = await db.ai_copilot_memory.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).limit(6).to_list(6)
    primary_chart = {
        "type": chart_type,
        "title": question[:80],
        "data": chart_rows or [{"category": "Readiness", "value": analytics.get("summary", {}).get("readiness_avg", 0)}],
    }
    charts = [primary_chart]
    charts.append({
        "type": "bar",
        "title": "Trend Performance",
        "data": [
            {"category": "DSA Mastery", "value": analytics.get("summary", {}).get("dsa_mastery_avg", 65.0)},
            {"category": "Aptitude Accuracy", "value": analytics.get("summary", {}).get("aptitude_accuracy_avg", 70.0)},
            {"category": "ATS Average", "value": analytics.get("summary", {}).get("ats_avg", 68.0)}
        ]
    })
    trend_explanation = (
        "Based on recent placement trends, we see a 12% year-over-year increase in product engineering offers, "
        "driven by stronger performance in DSA benchmarks. However, services companies have slightly tightened "
        "their eligibility cut-offs, making high aptitude accuracy critical for the upcoming cycles."
    )
    voice_narration = f"Here is the analysis for: '{question}'. {answer[:200]}..."

    return {
        "answer": answer,
        "intent": intent,
        "surface": body.surface,
        "chart": primary_chart,
        "charts": charts,
        "trend_explanation": trend_explanation,
        "voice_narration": voice_narration,
        "what_if": what_if,
        "anomalies": anomalies,
        "executive_report": executive_summary,
        "followups": [
            "Why?",
            "Show details",
            "What if training completion increases by 10%?",
            "Compare CSE and AIML",
            "Show placement bottlenecks",
        ],
        "memory": list(reversed(memory)),
        "confidence": 88 if chart_rows else 72,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============== STUDENT WORKSPACE ==============
class ResumeBuildBody(BaseModel):
    template: str
    sections: dict


@app.post("/api/me/resume/build")
async def build_student_resume(payload: ResumeBuildBody, request: Request, user=Depends(get_session_user)):
    if user["role"] != "student":
        raise HTTPException(403, "Forbidden")
        
    student_id = user.get("student_id") or user["user_id"]
    token = uuid.uuid4().hex[:10]
    sections = payload.sections or {}
    skills = sections.get("skills") or []
    score_basis = 58 + min(18, len(skills) * 2) + (8 if sections.get("projects") else 0) + (6 if sections.get("experience") else 0)
    version_doc = {
        "resume_id": f"res_{token}",
        "version_id": f"ver_{token}",
        "student_id": student_id,
        "user_id": user["user_id"],
        "institution_id": user.get("institution_id"),
        "template": payload.template,
        "sections": sections,
        "ats_score": min(94, score_basis),
        "keyword_score": min(96, 60 + len(skills) * 3),
        "format_score": 86,
        "missing_keywords": ["system design", "cloud", "testing"][: max(0, 3 - min(3, len(skills) // 3))],
        "recruiter_match_score": min(94, score_basis + 4),
        "improvement_suggestions": ["Add quantified outcomes to projects", "Tailor summary to the target role", "Mention deployment and testing evidence"],
        "download_token": token,
        "pdf_url": f"/api/me/resume/download/{token}.pdf",
        "download_url": f"/api/me/resume/download/{token}.pdf",
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.resume_versions.insert_one(version_doc)
    await _audit_log("resume.build", user=user, metadata={"version_id": version_doc["version_id"]}, request=request)
    if "_id" in version_doc:
        del version_doc["_id"]
    return version_doc


@app.get("/api/me/resume/download/{token}.pdf")
async def download_built_resume(token: str, user=Depends(get_session_user)):
    query = {"download_token": token}
    if user.get("role") == "student":
        query["user_id"] = user["user_id"]
    doc = await db.resume_versions.find_one(query, {"_id": 0})
    if not doc:
        raise HTTPException(404, "resume not found")

    sections = doc.get("sections") or {}
    student = await db.students.find_one({"student_id": doc.get("student_id")}, {"_id": 0}) or {}
    buffer = io.BytesIO()
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch

    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch
    name = student.get("name") or user.get("name") or "CareerOS Student"
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, y, name)
    y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(inch, y, f"{student.get('department', 'Engineering')} | ATS {doc.get('ats_score', 0)}/100 | CareerOS Resume")
    y -= 28

    def draw_section(title: str, lines: list[str]):
        nonlocal y
        if y < inch:
            c.showPage()
            y = height - inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inch, y, title.upper())
        y -= 14
        c.setFont("Helvetica", 9)
        for line in lines:
            for chunk in [line[i:i + 95] for i in range(0, len(line), 95)] or [""]:
                if y < inch:
                    c.showPage()
                    y = height - inch
                    c.setFont("Helvetica", 9)
                c.drawString(inch, y, chunk)
                y -= 12
        y -= 8

    edu = sections.get("education") or {}
    draw_section("Summary", [sections.get("summary") or "Placement-ready candidate with strong fundamentals, project experience, and active CareerOS preparation history."])
    draw_section("Education", [f"{edu.get('degree', 'B.Tech')} - {edu.get('institution', student.get('institution_name', 'Institution'))} ({edu.get('year', '2026')}) CGPA {edu.get('cgpa', student.get('cgpa', ''))}"])
    draw_section("Skills", [", ".join(sections.get("skills") or ["Python", "Java", "SQL", "DSA"])])
    draw_section("Projects", [f"{p.get('name', 'Project')}: {p.get('description', '')} [{p.get('tech_stack', '')}]" for p in sections.get("projects", [])])
    draw_section("Experience", [f"{e.get('role', 'Role')} at {e.get('company', 'Company')} ({e.get('duration', '')}): {e.get('description', '')}" for e in sections.get("experience", [])])
    c.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CareerOS-{name.replace(' ', '-')}-Resume.pdf"},
    )


@app.get("/api/me/career/recommendations")
async def get_career_recommendations(user=Depends(get_session_user)):
    if user["role"] != "student":
        raise HTTPException(403, "Forbidden")
        
    student = await db.students.find_one({"student_id": user.get("student_id")}, {"_id": 0})
    dept = student.get("department", "CSE") if student else "CSE"
    
    recs = [
        {
            "role": "Software Development Engineer",
            "fit_percentage": 90 if dept in ("CSE", "IT") else 60,
            "reason": "Strong logical skills and solid performance in the DSA module.",
            "actions": ["Solve 50 more medium DSA questions", "Build a React + FastAPI project"]
        },
        {
            "role": "Data Engineer / Analyst",
            "fit_percentage": 85 if dept in ("CSE", "IT", "ECE") else 50,
            "reason": "Good aptitude scores and logical thinking.",
            "actions": ["Practice SQL queries", "Complete the data analysis workshop"]
        },
        {
            "role": "System Engineer / DevOps",
            "fit_percentage": 75 if dept in ("CSE", "ECE", "EEE") else 40,
            "reason": "Compatible with department and basic networking understanding.",
            "actions": ["Learn Docker basics", "Understand CI/CD pipelines"]
        }
    ]
    return {"recommendations": recs}


# ============== JOB DISCOVERY & SAVED OPPORTUNITIES ==============
class SavedJobBody(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: str
    jobType: str
    logo: str
    url: str

async def fetch_jooble_jobs(keywords: str = "developer", location: str = "India", page: int = 1):
    jooble_key = os.environ.get("JOOBLE_API_KEY")
    url = f"https://jooble.org/api/{jooble_key}"
    payload = {
        "keywords": keywords,
        "location": location,
        "page": page
    }
    def clean_html(value: str, fallback: str = "") -> str:
        return re.sub(r"<[^>]+>", " ", value or fallback).strip()

    def fallback_jobs() -> list[dict]:
        city = location if location and location.lower() != "india" else "Hyderabad"
        companies = [
            ("Google", "Software Engineering Intern", "https://www.svgrepo.com/show/475656/google-color.svg"),
            ("Microsoft", "Associate Software Engineer", "https://www.svgrepo.com/show/452062/microsoft.svg"),
            ("Amazon", "SDE I", "https://www.svgrepo.com/show/475634/amazon-color.svg"),
            ("Adobe", "Frontend Engineer", "https://www.svgrepo.com/show/452148/adobe.svg"),
            ("Oracle", "Backend Developer", "https://www.svgrepo.com/show/303229/oracle-6-logo.svg"),
            ("Deloitte", "Analyst Trainee", "https://www.svgrepo.com/show/331339/deloitte.svg"),
        ]
        normalized = []
        for idx, (company, title, logo) in enumerate(companies):
            normalized.append({
                "id": f"fallback-{city.lower()}-{idx}",
                "title": title if keywords.lower() in {"developer", "software", "react", "python"} else f"{keywords.title()} {title}",
                "company": company,
                "location": city,
                "salary": f"{8 + idx * 3}-{14 + idx * 4} LPA",
                "jobType": "Full-time",
                "type": "Full-time",
                "applyLink": "https://www.linkedin.com/jobs/",
                "link": "https://www.linkedin.com/jobs/",
                "url": "https://www.linkedin.com/jobs/",
                "logo": logo,
                "snippet": f"{company} hiring for {title} in {city}. Strong DSA, projects, communication, and role-specific skills improve shortlist probability.",
                "skills": ["DSA", "Python", "Java", "SQL", "Communication"],
                "badges": ["CareerOS fallback", "Verified role"],
                "updated": datetime.now(timezone.utc).isoformat(),
                "source": "CareerOS",
            })
        return normalized

    if not jooble_key:
        return {"success": True, "source": "CareerOS fallback", "totalCount": 6, "jobs": fallback_jobs(), "warning": "Jooble API key not configured"}

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10.0)
            if res.status_code != 200:
                return {"success": True, "source": "CareerOS fallback", "totalCount": 6, "jobs": fallback_jobs(), "warning": f"Jooble returned {res.status_code}"}
            data = res.json()
            raw_jobs = data.get("jobs", [])
            normalized = []
            skill_keywords = [
                'javascript', 'typescript', 'react', 'node', 'express', 'python', 'java',
                'spring', 'sql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
                'machine learning', 'data analysis', 'figma', 'ui', 'ux', 'html', 'css'
            ]
            for idx, job in enumerate(raw_jobs):
                job_title = clean_html(job.get("title"), "Career Opportunity")
                snippet = clean_html(job.get("snippet") or job.get("description"), "Live opportunity")
                # infer skills
                text = f"{job_title} {snippet}".lower()
                inferred = [sk for sk in skill_keywords if sk in text]
                if not inferred:
                    inferred = ["Communication", "Problem Solving"]
                else:
                    inferred = inferred[:6]
                
                normalized.append({
                    "id": job.get("id") or f"jooble-{page}-{idx}",
                    "title": job_title,
                    "company": clean_html(job.get("company"), "Hiring Company"),
                    "location": clean_html(job.get("location"), "India"),
                    "salary": clean_html(job.get("salary"), "Salary not disclosed"),
                    "jobType": job.get("type") or job.get("jobType") or "Full-time",
                    "type": job.get("type") or job.get("jobType") or "Full-time",
                    "applyLink": job.get("link") or job.get("url") or "#",
                    "link": job.get("link") or job.get("url") or "#",
                    "url": job.get("link") or job.get("url") or "#",
                    "logo": job.get("logo") or "https://www.svgrepo.com/show/530661/briefcase.svg",
                    "snippet": snippet[:300] + "..." if len(snippet) > 300 else snippet,
                    "skills": inferred,
                    "badges": [job.get("type") or "Full-time"],
                    "updated": job.get("updated") or job.get("date"),
                    "source": "Jooble"
                })
            return {
                "success": True,
                "source": "jooble",
                "totalCount": data.get("totalCount") or len(normalized),
                "jobs": normalized or fallback_jobs()
            }
        except Exception as e:
            log.warning("Jooble fetch failed: %s", e)
            return {"success": True, "source": "CareerOS fallback", "totalCount": 6, "jobs": fallback_jobs(), "warning": "Live job feed temporarily unavailable"}

@app.get("/api/jobs/discover")
async def discover_jobs(keywords: str = "developer", location: str = "India", page: int = 1, user=Depends(get_session_user)):
    res = await fetch_jooble_jobs(keywords, location, page)
    return res

@app.get("/api/saved-jobs")
async def get_saved_jobs(user=Depends(get_session_user)):
    items = await db.saved_jobs.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return {"items": items}

@app.post("/api/saved-jobs")
async def save_job(payload: SavedJobBody, user=Depends(get_session_user)):
    doc = {
        "user_id": user["user_id"],
        "job_id": payload.id,
        "title": payload.title,
        "company": payload.company,
        "location": payload.location,
        "salary": payload.salary,
        "jobType": payload.jobType,
        "logo": payload.logo,
        "url": payload.url,
        "saved_at": datetime.now(timezone.utc).isoformat()
    }
    await db.saved_jobs.update_one(
        {"user_id": user["user_id"], "job_id": payload.id},
        {"$set": doc},
        upsert=True
    )
    return {"success": True, "saved": True}

@app.delete("/api/saved-jobs/{job_id}")
async def delete_saved_job(job_id: str, user=Depends(get_session_user)):
    await db.saved_jobs.delete_one({"user_id": user["user_id"], "job_id": job_id})
    return {"success": True}


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="not found")
    index = FRONTEND_BUILD / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return HTMLResponse(index.read_text(encoding="utf-8"), headers=SPA_HEADERS)
