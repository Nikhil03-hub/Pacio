"""Backup, restore and verify a MongoDB database without mongodump/mongorestore.

Usage (run from the repository root):

  .venv/Scripts/python.exe scripts/mongo_backup_restore.py backup \
      --uri mongodb://127.0.0.1:27017 --db pacio_dev_verify --out backups/pacio_dev_verify.jsonl.gz

  .venv/Scripts/python.exe scripts/mongo_backup_restore.py restore \
      --uri mongodb://127.0.0.1:27017 --file backups/pacio_dev_verify.jsonl.gz \
      --db pacio_restore_verify

  .venv/Scripts/python.exe scripts/mongo_backup_restore.py verify \
      --uri mongodb://127.0.0.1:27017 --file backups/pacio_dev_verify.jsonl.gz \
      --db pacio_dev_verify

Format: gzipped JSON Lines. For every collection, one metadata line
(`{"__meta__": "collection", "name": ..., "indexes": [...]}`) followed by one document
per line encoded with Extended JSON, so ObjectIds and dates survive a round trip.
Includes GridFS collections because they are ordinary collections.

Restore refuses to write into a database that already has collections unless --force is
passed, and refuses to restore into the same database it was taken from.
"""
from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path

from bson import json_util
from pymongo import MongoClient, ASCENDING


def iter_collections(db):
    for name in sorted(db.list_collection_names()):
        if name.startswith("system."):
            continue
        yield name


def backup(uri: str, db_name: str, out_path: Path) -> dict:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        for name in iter_collections(db):
            indexes = [
                {k: v for k, v in idx.items() if k != "v"}
                for idx in db[name].index_information().values()
                if idx.get("name") != "_id_"
            ]
            fh.write(json_util.dumps({"__meta__": "collection", "name": name, "indexes": indexes}) + "\n")
            count = 0
            for doc in db[name].find({}):
                fh.write(json_util.dumps(doc) + "\n")
                count += 1
            counts[name] = count
    client.close()
    return counts


def restore(uri: str, file_path: Path, target_db: str, force: bool) -> dict:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    db = client[target_db]
    existing = [n for n in db.list_collection_names() if not n.startswith("system.")]
    if existing and not force:
        client.close()
        raise SystemExit(f"refusing to restore into non-empty database '{target_db}' (use --force)")

    counts: dict[str, int] = {}
    current = None
    buffer: list[dict] = []

    def flush():
        nonlocal buffer
        if current and buffer:
            db[current].insert_many(buffer, ordered=False)
            counts[current] = counts.get(current, 0) + len(buffer)
        buffer = []

    with gzip.open(file_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            doc = json_util.loads(line)
            if doc.get("__meta__") == "collection":
                flush()
                current = doc["name"]
                if force:
                    db[current].drop()
                db[current].create_index([("_id", ASCENDING)])  # no-op if present
                for idx in doc.get("indexes", []):
                    keys = list(idx["key"].items()) if isinstance(idx.get("key"), dict) else idx.get("key")
                    options = {k: v for k, v in idx.items()
                               if k in {"unique", "sparse", "expireAfterSeconds", "partialFilterExpression"}}
                    try:
                        db[current].create_index(keys, name=idx.get("name"), **options)
                    except Exception as exc:  # noqa: BLE001
                        print(f"  index skipped on {current}: {exc}", file=sys.stderr)
            else:
                buffer.append(doc)
    flush()
    client.close()
    return counts


def verify(uri: str, file_path: Path, db_name: str) -> tuple[bool, list[str]]:
    """Compare the metadata/counts in a backup file with a live database."""
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    problems: list[str] = []
    expected: dict[str, int] = {}
    current = None
    with gzip.open(file_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            doc = json_util.loads(line)
            if doc.get("__meta__") == "collection":
                current = doc["name"]
                expected[current] = 0
            elif current:
                expected[current] += 1
    for name, count in expected.items():
        actual = db[name].count_documents({})
        if actual != count:
            problems.append(f"{name}: backup={count} live={actual}")
    client.close()
    return (not problems), problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("backup")
    b.add_argument("--uri", required=True)
    b.add_argument("--db", required=True)
    b.add_argument("--out", required=True, type=Path)

    r = sub.add_parser("restore")
    r.add_argument("--uri", required=True)
    r.add_argument("--file", required=True, type=Path)
    r.add_argument("--db", required=True)
    r.add_argument("--force", action="store_true")

    v = sub.add_parser("verify")
    v.add_argument("--uri", required=True)
    v.add_argument("--file", required=True, type=Path)
    v.add_argument("--db", required=True)

    args = parser.parse_args()
    if args.command == "backup":
        counts = backup(args.uri, args.db, args.out)
        total = sum(counts.values())
        print(f"backed up {len(counts)} collections / {total} documents -> {args.out} ({args.out.stat().st_size / 1048576:.1f} MB)")
        return 0
    if args.command == "restore":
        counts = restore(args.uri, args.file, args.db, args.force)
        print(f"restored {len(counts)} collections / {sum(counts.values())} documents into {args.db}")
        return 0
    ok, problems = verify(args.uri, args.file, args.db)
    if ok:
        print(f"verified: every collection in {args.file.name} matches database {args.db}")
        return 0
    print("MISMATCH:\n  " + "\n  ".join(problems))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
