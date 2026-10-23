"""Rebuild DSA progress for the students that already exist in a database.

Needed after a curriculum migration (or any partial reseed) because progress must be
generated from *live* student IDs, never from a freshly invented seed payload.

This writes demo progress (deterministic per student) and is intended for demo/staging
databases only. It backs up the two progress collections, removes rows whose student no
longer exists, and fills progress for engineering students who have none.

Usage:
  .venv/Scripts/python.exe scripts/rebuild_dsa_progress.py \
      --uri mongodb://127.0.0.1:27017 --db pacio_dev_verify --yes
"""
from __future__ import annotations

import argparse
import gzip
import random
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

COLLECTIONS = ["dsa_progress", "dsa_question_progress"]


def backup(db, out_dir: Path, db_name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"dsa-progress-{db_name}-{stamp}.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for name in COLLECTIONS:
            fh.write(json_util.dumps({"__meta__": "collection", "name": name}) + "\n")
            for doc in db[name].find({}):
                fh.write(json_util.dumps(doc) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--force-any", action="store_true")
    parser.add_argument("--backup-dir", default="backups")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("refusing to rewrite progress without --yes")
    if not (args.db.startswith("pacio_") or args.force_any):
        raise SystemExit(f"'{args.db}' does not look like a Pacio demo database (use --force-any)")

    from dsa_catalog import CURRICULUM_VERSION, DSA_TOPICS  # noqa: E402

    client = MongoClient(args.uri, serverSelectionTimeoutMS=10000)
    db = client[args.db]
    questions = list(db.dsa_questions.find({}, {"_id": 0}))
    if not questions:
        raise SystemExit("no questions in this database; start the API once so the catalogue seeds")

    by_topic = defaultdict(list)
    for q in sorted(questions, key=lambda row: row.get("global_order", 0)):
        by_topic[q["topic_code"]].append(q)
    if len(by_topic) != len(DSA_TOPICS):
        raise SystemExit(f"catalogue mismatch: {len(by_topic)} topics in DB, {len(DSA_TOPICS)} in code")

    eng_ids = [i["institution_id"] for i in db.institutions.find({"type": "Engineering"}, {"_id": 0, "institution_id": 1})]
    students = list(db.students.find({"institution_id": {"$in": eng_ids}}, {"_id": 0}))
    if not students:
        students = list(db.students.find({}, {"_id": 0}))
    student_ids = {s["student_id"] for s in students}
    print(f"students={len(students)} engineering_institutions={len(eng_ids)} questions={len(questions)}")

    path = backup(db, Path(args.backup_dir), args.db)
    print(f"backup written: {path} ({path.stat().st_size / 1048576:.1f} MB)")

    # Remove orphan progress whose student row no longer exists.
    orphan_ids = [sid for sid in db.dsa_progress.distinct("student_id") if sid not in student_ids]
    if orphan_ids:
        db.dsa_progress.delete_many({"student_id": {"$in": orphan_ids}})
        db.dsa_question_progress.delete_many({"student_id": {"$in": orphan_ids}})
        print(f"removed progress for {len(orphan_ids)} non-existent students")

    # Completeness is defined by question-level rows: a student can have stale topic
    # aggregates with no question rows (this is how the demo account was skipped), and
    # those aggregates must be regenerated rather than trusted.
    already = set(db.dsa_question_progress.distinct("student_id"))
    todo = [s for s in students if s["student_id"] not in already]
    todo_ids = [s["student_id"] for s in todo]
    if todo_ids:
        db.dsa_progress.delete_many({"student_id": {"$in": todo_ids}})
    print(f"students needing progress: {len(todo)}")

    now = datetime.now(timezone.utc).isoformat()
    topic_rows, question_rows = [], []
    for student in todo:
        rng = random.Random(f"{student['student_id']}:{CURRICULUM_VERSION}")
        try:
            cgpa = float(student.get("cgpa") or 6.8)
        except (TypeError, ValueError):
            cgpa = 6.8
        skill = min(0.95, max(0.05, (cgpa - 6.0) / 4.0))
        for topic in DSA_TOPICS:
            bank = by_topic[topic["code"]]
            total = len(bank)
            solved = max(0, min(total, int(total * (skill + rng.uniform(-0.15, 0.15)))))
            attempted = max(solved, min(total, solved + rng.randint(0, 3)))
            topic_rows.append({
                "progress_id": f"dsa_{uuid.uuid4().hex[:10]}",
                "student_id": student["student_id"],
                "institution_id": student["institution_id"],
                "topic_code": topic["code"],
                "topic_name": topic["name"],
                "topic_order": topic["order"],
                "total": total,
                "solved": solved,
                "attempted": attempted,
                "last_solved_at": now,
                "curriculum_version": CURRICULUM_VERSION,
            })
            for index, question in enumerate(bank[:attempted], start=1):
                is_solved = index <= solved
                mastery = rng.randint(74, 96) if is_solved else rng.randint(18, 50)
                question_rows.append({
                    "progress_id": f"dsqp_{uuid.uuid4().hex[:10]}",
                    "student_id": student["student_id"],
                    "institution_id": student["institution_id"],
                    "question_id": question["question_id"],
                    "topic_code": question["topic_code"],
                    "subtopic_code": question["subtopic_code"],
                    "solved": is_solved,
                    "attempted": True,
                    "mastery": mastery,
                    "revision_count": rng.randint(1, 3) if is_solved else 0,
                    "notes": "",
                    "faculty_comments": [],
                    "difficulty": question["difficulty"],
                    "last_solved_at": now if is_solved else None,
                    "updated_at": now,
                })
        if len(topic_rows) >= 20000:
            db.dsa_progress.insert_many(topic_rows); topic_rows = []
        if len(question_rows) >= 50000:
            db.dsa_question_progress.insert_many(question_rows); question_rows = []
    if topic_rows:
        db.dsa_progress.insert_many(topic_rows)
    if question_rows:
        db.dsa_question_progress.insert_many(question_rows)

    print(f"inserted topic rows={db.dsa_progress.count_documents({})} question rows={db.dsa_question_progress.count_documents({})}")
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
