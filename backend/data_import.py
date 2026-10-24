"""Source registry and idempotent, reversible dataset import.

Design goals (Phase 2, Workstream B):
  - refuse to import from a source that is not approved,
  - require provenance on every record,
  - reject personal data outright,
  - dry-run before writing,
  - stable keys and content hashes so re-imports are idempotent,
  - every write is tagged with an import_batch_id that can be rolled back,
  - an audit record per run.

This module never deletes or rewrites synthetic collections. Targets are separate
collections (institutions_public, placement_stats, job_postings).

Usage from tests or scripts:
    from data_import import register_source, dry_run, import_records, rollback_batch
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

APPROVED_STATUSES = {"APPROVED", "APPROVED_WITH_LIMITATIONS"}
DATA_STATUSES = {"published", "synthetic", "unverified", "draft"}
PII_KEYS = {"student_name", "student_email", "student_phone", "email", "phone", "mobile", "contact"}

# Domain contract: required fields, stable-key builder, extra validation.
DOMAINS: dict[str, dict[str, Any]] = {
    "institutions": {
        "collection": "institutions_public",
        "required": ["source_id", "source_url", "retrieved_at", "official_id", "name", "data_status"],
        "stable_key": lambda r: f"{r['source_id']}:{r['official_id']}",
        "validate": lambda r: [] if str(r.get("name", "")).strip() else ["name is empty"],
    },
    "placement_stats": {
        "collection": "placement_stats",
        "required": ["source_id", "source_url", "retrieved_at", "published_on",
                     "institution_id", "academic_year", "metric", "value", "definition", "data_status"],
        "stable_key": lambda r: f"{r['source_id']}:{r['institution_id']}:{r['academic_year']}:{r['metric']}",
        "validate": lambda r: [] if str(r.get("definition", "")).strip() else ["definition is required"],
    },
    "jobs": {
        "collection": "job_postings",
        "required": ["source_id", "source_url", "retrieved_at", "board_id", "external_id",
                     "title", "company", "apply_url", "posted_at", "data_status"],
        "stable_key": lambda r: f"{r['source_id']}:{r['board_id']}:{r['external_id']}",
        "validate": lambda r: [] if str(r.get("apply_url", "")).startswith("http") else ["apply_url must be an http(s) URL"],
        # Liveness bookkeeping is written by the feed reconciler, not by the content hash, so that
        # polling the same unchanged posting every day does not look like a data change.
        "hash_exclude": ("retrieved_at", "last_seen_at", "first_seen_at", "is_active", "absent_since"),
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


NON_HASHED_FIELDS = {"import_batch_id", "first_import_batch_id", "content_hash", "updated_at"}


def _hash(record: dict, exclude: Iterable[str] = ()) -> str:
    """Content hash of the fields that define the record's substance.

    `exclude` lets a domain declare volatile provenance (when we last saw a live job posting,
    for example) that must not make an otherwise identical record look like a change.
    """
    skip = NON_HASHED_FIELDS | set(exclude)
    payload = {k: v for k, v in record.items() if k not in skip}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _hash_for(spec: dict, record: dict) -> str:
    return _hash(record, spec.get("hash_exclude", ()))


def validate_record(domain: str, record: dict) -> list[str]:
    spec = DOMAINS.get(domain)
    if not spec:
        return [f"unknown domain '{domain}'"]
    errors = []
    for field in spec["required"]:
        if record.get(field) in (None, ""):
            errors.append(f"missing {field}")
    if record.get("data_status") not in DATA_STATUSES:
        errors.append("data_status must be published|synthetic|unverified|draft")
    for key in record:
        if key.lower() in PII_KEYS:
            errors.append(f"personal-data field not allowed: {key}")
    if record.get("source_url") and not str(record["source_url"]).startswith("http"):
        errors.append("source_url must be http(s)")
    errors.extend(spec["validate"](record))
    return errors


async def register_source(db, source: dict) -> dict:
    """Create/update a source registry entry. Status must be explicit."""
    if not source.get("source_id") or not source.get("name"):
        raise ValueError("source_id and name are required")
    if source.get("commercial_verdict") not in APPROVED_STATUSES | {
        "BLOCKED", "BLOCKED (commercial)", "BLOCKED (consent)", "BLOCKED (redistribution)",
        "REJECTED", "RESEARCH_ONLY", "NEEDS_REVIEW", "APPROVED (not India)",
    }:
        raise ValueError("commercial_verdict must be an explicit verdict")
    doc = {**source, "updated_at": _now()}
    existing = await db.source_registry.find_one({"source_id": source["source_id"]}, {"_id": 0})
    doc["created_at"] = (existing or {}).get("created_at", doc["updated_at"])
    await db.source_registry.update_one({"source_id": source["source_id"]}, {"$set": doc}, upsert=True)
    return doc


async def _approved_source(db, source_id: str) -> dict:
    source = await db.source_registry.find_one({"source_id": source_id}, {"_id": 0})
    if not source:
        raise PermissionError(f"source '{source_id}' is not registered")
    if source.get("commercial_verdict") not in APPROVED_STATUSES:
        raise PermissionError(f"source '{source_id}' is not approved ({source.get('commercial_verdict')})")
    return source


async def dry_run(db, domain: str, records: Iterable[dict], source_id: str) -> dict:
    """Validate and diff without writing anything."""
    await _approved_source(db, source_id)
    spec = DOMAINS[domain]
    seen: set[str] = set()
    report = {"new": 0, "updated": 0, "unchanged": 0, "invalid": [], "total": 0}
    for record in records:
        report["total"] += 1
        record = {**record, "source_id": source_id}
        errors = validate_record(domain, record)
        if errors:
            report["invalid"].append({"stable_key": None, "errors": errors})
            continue
        key = spec["stable_key"](record)
        if key in seen:
            report["invalid"].append({"stable_key": key, "errors": ["duplicate stable key in batch"]})
            continue
        seen.add(key)
        existing = await db[spec["collection"]].find_one({"stable_key": key}, {"_id": 0})
        if not existing:
            report["new"] += 1
        elif existing.get("content_hash") == _hash_for(spec, record):
            report["unchanged"] += 1
        else:
            report["updated"] += 1
    return report


async def import_records(db, domain: str, records: Iterable[dict], source_id: str,
                         operator: str, backup_path: str | None = None) -> dict:
    """Validate everything first, then write idempotently. Raises on any invalid record."""
    source = await _approved_source(db, source_id)
    spec = DOMAINS[domain]
    batch_id = f"imp_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{source_id}_{uuid.uuid4().hex[:6]}"
    started = _now()
    prepared: list[tuple[str, dict]] = []
    seen: set[str] = set()
    invalid: list[dict] = []
    for record in records:
        record = {**record, "source_id": source_id}
        errors = validate_record(domain, record)
        if errors:
            invalid.append({"errors": errors, "record": {k: record.get(k) for k in ("external_id", "official_id", "institution_id")}})
            continue
        key = spec["stable_key"](record)
        if key in seen:
            invalid.append({"errors": ["duplicate stable key in batch"], "stable_key": key})
            continue
        seen.add(key)
        prepared.append((key, record))
    if invalid:
        raise ValueError(f"{len(invalid)} invalid record(s); nothing imported: {invalid[:3]}")

    counts = {"new": 0, "updated": 0, "unchanged": 0}
    collection = db[spec["collection"]]
    undo: list[dict] = []
    for seq, (key, record) in enumerate(prepared):
        content_hash = _hash_for(spec, record)
        existing = await collection.find_one({"stable_key": key}, {"_id": 0})
        if existing and existing.get("content_hash") == content_hash:
            counts["unchanged"] += 1
            continue
        doc = {**record, "stable_key": key, "content_hash": content_hash,
               "import_batch_id": batch_id, "updated_at": _now()}
        if existing:
            counts["updated"] += 1
            doc["first_import_batch_id"] = existing.get("first_import_batch_id", existing["import_batch_id"])
        else:
            counts["new"] += 1
            doc["created_at"] = doc["updated_at"]
            doc["first_import_batch_id"] = batch_id
        await collection.update_one({"stable_key": key}, {"$set": doc}, upsert=True)
        undo.append({"batch_id": batch_id, "seq": seq, "stable_key": key,
                     "collection": spec["collection"], "domain": domain,
                     "action": "update" if existing else "insert",
                     "before": existing, "after_hash": content_hash, "recorded_at": _now()})
    if undo:
        await db.import_batch_items.insert_many(undo)

    run = {
        "batch_id": batch_id, "domain": domain, "source_id": source_id,
        "source_name": source.get("name"), "operator": operator,
        "backup_path": backup_path, "counts": counts, "total": len(prepared),
        "undo_items": len(undo), "status": "completed",
        "started_at": started, "finished_at": _now(),
    }
    await db.import_runs.insert_one(run)
    return run


async def rollback_batch(db, batch_id: str, force: bool = False) -> dict:
    """Undo exactly what one import batch wrote, newest change first.

    Every write stores a pre-image, so a record the batch only *updated* is restored to its
    previous content instead of being deleted, and a record it *created* is removed. If the
    live content no longer matches what this batch wrote, another batch or an out-of-band edit
    has touched it: rollback refuses unless `force` is set, because silently overwriting that
    work is worse than an aborted rollback.
    """
    run = await db.import_runs.find_one({"batch_id": batch_id}, {"_id": 0})
    if not run:
        raise ValueError(f"unknown batch '{batch_id}'")
    if run.get("status") == "rolled_back":
        return {"batch_id": batch_id, "status": "already_rolled_back", "deleted": 0, "restored": 0}

    items = await db.import_batch_items.find({"batch_id": batch_id, "consumed_at": None}) \
        .sort("seq", -1).to_list(None)
    conflicts = []
    for item in items:
        collection = db[item["collection"]]
        current = await collection.find_one({"stable_key": item["stable_key"]}, {"_id": 0})
        if current is None:
            conflicts.append({"stable_key": item["stable_key"], "reason": "record missing from collection"})
        elif current.get("content_hash") != item["after_hash"]:
            conflicts.append({"stable_key": item["stable_key"],
                              "reason": "modified after this batch; refusing to overwrite"})
    if conflicts and not force:
        return {"batch_id": batch_id, "status": "blocked_conflict", "conflicts": conflicts,
                "deleted": 0, "restored": 0}

    deleted = restored = 0
    for item in items:
        collection = db[item["collection"]]
        if item["action"] == "insert":
            await collection.delete_many({"stable_key": item["stable_key"]})
            deleted += 1
        else:
            await collection.delete_many({"stable_key": item["stable_key"]})
            if item["before"]:
                # The pre-image was read with an _id-excluding projection, so the store mints a
                # fresh id; `stable_key`, not the id, is the identity the pipeline depends on.
                await collection.insert_one(item["before"])
                restored += 1
        await db.import_batch_items.update_one(
            {"batch_id": batch_id, "seq": item["seq"]}, {"$set": {"consumed_at": _now()}})

    await db.import_runs.update_one({"batch_id": batch_id},
                                    {"$set": {"status": "rolled_back", "rolled_back_at": _now(),
                                              "rollback_forced": bool(force)}})
    return {"batch_id": batch_id, "collection": DOMAINS[run["domain"]]["collection"],
            "status": "rolled_back", "forced": bool(force), "deleted": deleted,
            "restored": restored, "undo_items": len(items)}
