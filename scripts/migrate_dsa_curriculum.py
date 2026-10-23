"""Replace the DSA catalogue in an existing database with the current curriculum.

The catalogue is code-defined, but existing databases keep the rows they were seeded with.
This script:

1. Refuses to run against a database whose name does not look like a Pacio demo database
   (override with --force-any only if you understand that per-student progress will be lost).
2. Backs up the three DSA collections to backups/dsa-<db>-<timestamp>.jsonl.gz.
3. Drops dsa_questions, dsa_progress and dsa_question_progress.
4. Prints the next step: restart the API so startup reseeds from backend/dsa_catalog.py.

Usage:
  .venv/Scripts/python.exe scripts/migrate_dsa_curriculum.py \
      --uri mongodb://127.0.0.1:27017 --db pacio_dev_verify --yes
"""
from __future__ import annotations

import argparse
import gzip
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

COLLECTIONS = ["dsa_questions", "dsa_progress", "dsa_question_progress"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--force-any", action="store_true")
    parser.add_argument("--backup-dir", default="backups")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("refusing to delete DSA progress without --yes")
    if not (args.db.startswith("pacio_") or args.force_any):
        raise SystemExit(
            f"database '{args.db}' does not look like a Pacio demo database. "
            "Use --force-any only if losing per-student DSA progress is acceptable."
        )

    from dsa_catalog import CURRICULUM_VERSION, DSA_TOTAL  # noqa: E402

    client = MongoClient(args.uri, serverSelectionTimeoutMS=10000)
    db = client[args.db]
    before = {c: db[c].count_documents({}) for c in COLLECTIONS}
    print(f"target {args.db}: " + ", ".join(f"{k}={v}" for k, v in before.items()))
    print(f"replacement curriculum: {CURRICULUM_VERSION} ({DSA_TOTAL} problems)")

    out_dir = Path(args.backup_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = out_dir / f"dsa-{args.db}-{stamp}.jsonl.gz"
    with gzip.open(backup_path, "wt", encoding="utf-8") as fh:
        for name in COLLECTIONS:
            fh.write(json_util.dumps({"__meta__": "collection", "name": name}) + "\n")
            for doc in db[name].find({}):
                fh.write(json_util.dumps(doc) + "\n")
    print(f"backup written: {backup_path} ({backup_path.stat().st_size / 1048576:.1f} MB)")

    for name in COLLECTIONS:
        db[name].drop()
        print(f"dropped {name}")

    client.close()
    print("done. Restart the API so startup reseeds the new curriculum.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
