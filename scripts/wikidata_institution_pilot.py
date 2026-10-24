"""Import a bounded, filtered Wikidata CC0 slice of Indian institutions into a disposable database.

Phase 3 Workstream D pilot. Wikidata's structured data is CC0, so the rights question is settled;
the open question is fitness, and `docs/data/WIKIDATA_FEASIBILITY.md` measured it as noisy:
9.3% K-12 contamination, ~half of the website links dead or hijacked, state coverage skewed.

So this script does not "import Wikidata". It applies the filters that report prescribes, records
why each row was excluded, health-checks the website links it keeps, labels every surviving row
`unverified` (community-maintained, not confirmed with the institution), and writes only to a
disposable database that it then rolls back.

Run:
  .venv/Scripts/python.exe scripts/wikidata_institution_pilot.py --check-links
  .venv/Scripts/python.exe scripts/wikidata_institution_pilot.py \
      --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_wikidata --check-links
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import data_import  # noqa: E402
from memory_db import MemoryDB  # noqa: E402

SAMPLE = ROOT / "docs" / "data" / "wikidata_institutions_sample.json"
USER_AGENT = "PacioInstitutionPilot/0.1 (catalogue hygiene check; one request per site)"

SOURCE = {
    "source_id": "SRC-WIKIDATA",
    "name": "Wikidata structured data (CC0) - Indian higher-education institutions",
    "commercial_verdict": "APPROVED_WITH_LIMITATIONS",
    "licence": "CC0 1.0 Universal (public domain dedication) - https://www.wikidata.org/wiki/Wikidata:Licensing",
    "limitations": (
        "CC0 clears commercial reuse and redistribution. Fitness is limited: community-maintained and "
        "not confirmed with any institution; measured 9.3% K-12 contamination, roughly half of website "
        "URLs dead or hijacked, skewed state coverage, no AICTE/UGC code for most rows. Rows are stored "
        "with data_status='unverified' and must be shown as community-sourced, never as a partnership or "
        "an official AICTE directory. Website links require a liveness check before display."),
}

# K-12 and non-institution types seen in the sample that must never reach a directory.
K12_TYPES = {
    "girls' school", "primary school", "secondary school", "higher secondary school",
    "upper primary school", "urban school", "rural school", "school", "high school",
    "middle school", "elementary school", "public school",
}
NON_INSTITUTION_TYPES = {"open-access publisher", "person", "company", "disambiguation page",
                         "business", "enterprise"}
K12_LABEL = re.compile(r"high school|higher secondary|primary sch|vidyalaya|convent|"
                       r"\bpublic school\b|\bu\.? ?primary\b", re.I)
# Word boundaries matter: "Biotechnology" must not match "technology".

ENGINEERING_WORDS = {"engineering", "polytechnic", "technical", "technology"}


def in_engineering_scope(label: str) -> bool:
    """Word-based, so 'Biotechnology' does not count as 'technology'."""
    words = set(re.findall(r"[a-z]+", label.lower()))
    return bool(words & ENGINEERING_WORDS) or "institute of tech" in label.lower()


DEPARTMENT_PREFIXES = ("department", "dept", "faculty", "centre for", "center for", "school of")


def is_department(label: str) -> bool:
    return label.strip().lower().startswith(DEPARTMENT_PREFIXES)

def _labels(row: dict, field: str) -> list[str]:
    return [item.get("label", "") for item in (row.get(field) or []) if isinstance(item, dict)]


def from_sparql_bindings(payload: dict) -> list[dict]:
    """Accept a raw SPARQL JSON response so a targeted query is a first-class input."""
    rows = []
    for binding in payload["results"]["bindings"]:
        def value(key):
            return binding.get(key, {}).get("value")

        qid_uri = value("item")
        if not qid_uri:
            continue
        qid = qid_uri.rsplit("/", 1)[-1]
        rows.append({
            "qid": qid,
            "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
            "label_en": value("itemLabel"),
            "description_en": None,
            "instance_of": [{"id": "", "label": part} for part in (value("types") or "").split("|") if part],
            "official_website": [value("website")] if value("website") else [],
            "located_in_admin": ([{"id": "", "label": value("adminLabel")}] if value("adminLabel") else []),
            "country": [{"id": "Q668", "label": "India"}],
            "inception": [value("inception")] if value("inception") else [],
            "aishe_code": [value("aishe")] if value("aishe") else [],
            "aicte_permanent_id": [value("aictePerm")] if value("aictePerm") else [],
            "aicte_application_id": [value("aicteApp")] if value("aicteApp") else [],
            "state_resolved": value("stateLabel"),
        })
    return rows


def classify(row: dict) -> tuple[str, str]:
    """Return (decision, reason). Decision is keep | exclude."""
    types = {label.lower() for label in _labels(row, "instance_of")}
    label = (row.get("label_en") or "").strip()

    if not row.get("qid") or not label:
        return "exclude", "missing qid or label"
    if types & NON_INSTITUTION_TYPES:
        return "exclude", "not an educational institution"
    if types & K12_TYPES or K12_LABEL.search(label):
        return "exclude", "K-12 school, not higher education"
    if is_department(label):
        return "exclude", "department, not a standalone institution"

    has_identifier = bool(row.get("aishe_code") or row.get("aicte_permanent_id")
                          or row.get("aicte_application_id"))
    has_aicte = bool(row.get("aicte_permanent_id") or row.get("aicte_application_id"))
    has_website = bool(row.get("official_website"))
    if not (has_identifier or has_website):
        return "exclude", "no website and no education identifier"
    # Scope follows WIKIDATA_FEASIBILITY.md 7.1: engineering label, engineering type, or an AICTE id.
    # An AISHE code alone is not a scope signal - it is present on law and education colleges too.
    if not (in_engineering_scope(label) or has_aicte
            or types & {"engineering school", "university of technology",
                        "institute of technology", "technical university"}):
        return "exclude", "outside engineering/technical scope"
    return "keep", ""


def to_record(row: dict, retrieved_at: str) -> dict:
    admin = _labels(row, "located_in_admin")
    return {
        "official_id": row["qid"],
        "name": row["label_en"].strip(),
        "city": admin[0] if admin else "",
        "state": row.get("state_resolved") or "",
        "website": (row.get("official_website") or [""])[0],
        "aishe_code": (row.get("aishe_code") or [""])[0],
        "aicte_id": (row.get("aicte_permanent_id") or [""])[0],
        "institution_type": ", ".join(_labels(row, "instance_of"))[:120],
        "wikidata_url": row["wikidata_url"],
        "source_url": row["wikidata_url"],
        "retrieved_at": retrieved_at,
        # Published on Wikidata, but not verified against the institution: `unverified` is the honest
        # value in the pipeline's enum, and the UI must treat it as community-sourced.
        "data_status": "unverified",
        "trust_level": "community-maintained",
        "website_status": "not_checked",
    }


def dedupe(records: list[dict]) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    seen_qid, seen_code, seen_domain = set(), {}, {}
    for record in records:
        qid = record["official_id"]
        code = record.get("aishe_code")
        domain = re.sub(r"^www\.", "", re.sub(r"^https?://", "", record.get("website") or "")).split("/")[0].lower()
        if qid in seen_qid:
            dropped.append({**record, "reason": "duplicate qid"})
            continue
        if code and code in seen_code:
            dropped.append({**record, "reason": f"same AISHE code as {seen_code[code]}"})
            continue
        if domain and domain in seen_domain:
            dropped.append({**record, "reason": f"same domain as {seen_domain[domain]}"})
            continue
        seen_qid.add(qid)
        if code:
            seen_code[code] = qid
        if domain:
            seen_domain[domain] = qid
        kept.append(record)
    return kept, dropped


def check_link(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return "ok" if 200 <= response.status < 400 else f"http_{response.status}"
    except urllib.error.HTTPError as exc:
        return f"http_{exc.code}"
    except urllib.error.URLError as exc:
        return "dns_or_connection" if "getaddrinfo" in str(exc.reason) else "connection_failed"
    except Exception:  # noqa: BLE001 - a dead link must never break the pilot
        return "unreachable"


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default="")
    parser.add_argument("--db-name", default="pacio_dryrun_wikidata")
    parser.add_argument("--check-links", action="store_true")
    parser.add_argument("--link-delay", type=float, default=0.4)
    parser.add_argument("--source-file", default=str(SAMPLE),
                        help="Wikidata sample JSON or a raw SPARQL JSON response")
    parser.add_argument("--max-rows", type=int, default=0,
                        help="cap the slice (deterministic by qid) to sample a large population")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.source_file).read_text(encoding="utf-8"))
    rows = (from_sparql_bindings(payload) if "results" in payload
            else payload["institutions"])
    retrieved_at = datetime.now(timezone.utc).isoformat()

    decisions = {"keep": [], "exclude": []}
    for row in rows:
        decision, reason = classify(row)
        decisions[decision].append((row, reason))
    records = [to_record(row, retrieved_at) for row, _ in decisions["keep"]]
    kept, duplicates = dedupe(records)

    if args.max_rows and len(kept) > args.max_rows:
        # Deterministic sample: same input, same subset, so two runs are comparable.
        kept = sorted(kept, key=lambda r: r["official_id"])[:args.max_rows]

    if args.check_links:
        checked = 0
        for record in kept:
            if record.get("website"):
                record["website_status"] = check_link(record["website"])
                checked += 1
                if checked % 25 == 0:
                    print(f"  link-checked {checked}", file=sys.stderr)
                time.sleep(args.link_delay)

    client = None
    if args.mongo_url:
        if not args.db_name.startswith("pacio_dryrun_"):
            raise SystemExit("--db-name must start with 'pacio_dryrun_'")
        from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
        client = AsyncIOMotorClient(args.mongo_url, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        db = client[args.db_name]
        engine = f"mongodb (disposable db '{args.db_name}')"
    else:
        db = MemoryDB()
        engine = "memory"

    await data_import.register_source(db, SOURCE)
    dry = await data_import.dry_run(db, "institutions", kept, SOURCE["source_id"])
    batch = await data_import.import_records(db, "institutions", kept, SOURCE["source_id"],
                                             "wikidata-pilot")
    again = await data_import.import_records(db, "institutions", kept, SOURCE["source_id"],
                                             "wikidata-pilot")
    stored = await db.institutions_public.find({}, {"_id": 0}).to_list(None)
    rollback = await data_import.rollback_batch(db, batch["batch_id"])
    remaining = await db.institutions_public.count_documents({})

    link_states: dict[str, int] = {}
    for record in kept:
        link_states[record["website_status"]] = link_states.get(record["website_status"], 0) + 1

    report = {
        "engine": engine,
        "source": SOURCE["source_id"],
        "sampled_rows": len(rows),
        "kept_after_filters": len(decisions["keep"]),
        "excluded": len(decisions["exclude"]),
        "exclusion_reasons": {},
        "dedupe_dropped": len(duplicates),
        "final_rows": len(kept),
        "dry_run": dry,
        "first_import": batch["counts"],
        "second_import": again["counts"],
        "stored_before_rollback": len(stored),
        "website_states": link_states,
        "rows_with_aishe_code": sum(1 for r in kept if r.get("aishe_code")),
        "rows_with_website": sum(1 for r in kept if r.get("website")),
        "states_covered": len({r["state"] for r in kept if r.get("state")}),
        "sample_rows": [{k: r.get(k) for k in ("name", "city", "state", "website_status",
                                               "data_status", "trust_level")}
                        for r in stored[:8]],
        "rollback": rollback,
        "rows_after_rollback": remaining,
    }
    for _, reason in decisions["exclude"]:
        report["exclusion_reasons"][reason] = report["exclusion_reasons"].get(reason, 0) + 1

    if client is not None:
        report["cleanup"] = "kept" if args.keep else "dropped"
        if not args.keep:
            await client.drop_database(args.db_name)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
