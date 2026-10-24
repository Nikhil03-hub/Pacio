"""Execute the import pipeline against a disposable database and print evidence.

No real dataset is imported. Records are clearly labelled synthetic fixtures used to prove
approval gating, provenance checks, PII refusal, idempotency and rollback.

Run (in-memory store):      .venv/Scripts/python.exe scripts/import_dry_run.py
Run (real MongoDB):         .venv/Scripts/python.exe scripts/import_dry_run.py \
                              --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_import
The real-MongoDB mode refuses to touch any database whose name does not start with
'pacio_dryrun_', so it can never point at the development or production database.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import data_import  # noqa: E402
from memory_db import MemoryDB  # noqa: E402

SOURCE = {"source_id": "SRC-FIXTURE", "name": "Pipeline fixture (not a real source)",
          "commercial_verdict": "APPROVED_WITH_LIMITATIONS", "licence": "n/a", "url": "https://example.org"}


def institution(suffix: str, name: str) -> dict:
    return {"official_id": f"AICTE-FIXTURE-{suffix}", "name": name, "state": "Telangana",
            "source_url": f"https://example.org/institutions/{suffix}",
            "retrieved_at": "2026-10-24T00:00:00Z", "data_status": "synthetic"}


async def _open(args):
    if not args.mongo_url:
        return MemoryDB(), None, "memory"
    if not args.db_name.startswith("pacio_dryrun_"):
        raise SystemExit(f"--db-name must start with 'pacio_dryrun_' (got {args.db_name!r})")
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
    client = AsyncIOMotorClient(args.mongo_url, serverSelectionTimeoutMS=5000)
    await client.admin.command("ping")
    return client[args.db_name], client, f"mongodb (disposable db '{args.db_name}')"


async def run_case(db) -> dict:
    await data_import.register_source(db, SOURCE)

    records = [institution("1", "Fixture Institute One"),
               institution("2", "Fixture Institute Two"),
               institution("3", "Fixture Institute Three")]

    report = {"source": SOURCE["source_id"], "domain": "institutions", "fixtures": len(records)}
    report["dry_run"] = await data_import.dry_run(db, "institutions", records, SOURCE["source_id"])
    report["dry_run_wrote_documents"] = await db.institutions_public.count_documents({})

    batch_a = await data_import.import_records(db, "institutions", records, SOURCE["source_id"], "dry-run-script")
    report["first_import"] = batch_a["counts"]
    report["stored_after_first"] = await db.institutions_public.count_documents({})

    batch_b = await data_import.import_records(db, "institutions", records, SOURCE["source_id"], "dry-run-script")
    report["second_import"] = batch_b["counts"]

    changed = [records[0], institution("2", "Fixture Institute Two (renamed)"), records[2]]
    batch_c = await data_import.import_records(db, "institutions", changed, SOURCE["source_id"], "dry-run-script")
    report["changed_import"] = batch_c["counts"]

    await data_import.register_source(db, {**SOURCE, "source_id": "SRC-REJECTED", "commercial_verdict": "REJECTED"})
    try:
        await data_import.import_records(db, "institutions", records, "SRC-REJECTED", "dry-run-script")
        report["rejected_source_blocked"] = False
    except PermissionError:
        report["rejected_source_blocked"] = True

    pii_record = {**institution("9", "PII Fixture"), "email": "student@example.org"}
    pii = await data_import.dry_run(db, "institutions", [pii_record], SOURCE["source_id"])
    report["pii_rejected"] = bool(pii["invalid"])

    # A later batch rewrote fixture-2, so rolling back the creating batch must refuse rather
    # than silently discard that newer change.
    report["rollback_blocked_by_conflict"] = await data_import.rollback_batch(db, batch_a["batch_id"])

    restore_c = await data_import.rollback_batch(db, batch_c["batch_id"])
    after_restore = await db.institutions_public.find_one(
        {"stable_key": f"{SOURCE['source_id']}:AICTE-FIXTURE-2"}, {"_id": 0})
    report["rollback_of_update_restores_previous_value"] = {
        "result": restore_c, "name_after_restore": (after_restore or {}).get("name")}

    rollback_a = await data_import.rollback_batch(db, batch_a["batch_id"])
    report["rollback"] = rollback_a
    report["stored_after_rollback"] = await db.institutions_public.count_documents({})
    report["remaining_keys"] = sorted(
        row["stable_key"] for row in await db.institutions_public.find({}, {"_id": 0, "stable_key": 1}).to_list(10)
    )
    report["audit_rows"] = {
        "import_runs": await db.import_runs.count_documents({}),
        "undo_items": await db.import_batch_items.count_documents({}),
        "sources_registered": await db.source_registry.count_documents({}),
    }
    return report


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default="", help="run against a disposable MongoDB instead of memory")
    parser.add_argument("--db-name", default="pacio_dryrun_import")
    parser.add_argument("--keep", action="store_true", help="do not drop the disposable database afterwards")
    args = parser.parse_args()

    db, client, engine = await _open(args)
    report = {"engine": engine, "ran_at": data_import._now()}
    report.update(await run_case(db))
    if client is not None:
        report["cleanup"] = "kept" if args.keep else "dropped"
        if not args.keep:
            await client.drop_database(args.db_name)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
