"""Live job-feed pilot: poll employer-hosted boards into a disposable database.

Workstream D deliverable. This script performs real HTTP GETs against a company's own public
recruiting feed, keeps only metadata plus the canonical application link, and writes into a
disposable database behind data_import's approval gate. It never writes to the application
database, and it drops what it created unless --keep is passed.

Run (memory only, disposable):  .venv/Scripts/python.exe scripts/job_feed_pilot.py
Run (real MongoDB):             .venv/Scripts/python.exe scripts/job_feed_pilot.py \
                                  --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_jobs
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import data_import  # noqa: E402
import job_feeds  # noqa: E402
from memory_db import MemoryDB  # noqa: E402

SOURCE = {
    "source_id": "SRC-ATS-PILOT",
    "name": "Employer-hosted ATS boards (pilot)",
    "commercial_verdict": "APPROVED_WITH_LIMITATIONS",
    "licence": "employer-published public job feed",
    "limitations": (
        "Pilot only. Metadata and the employer's own canonical application link; no job "
        "description text, no candidate data, no bulk crawler, one polite request per board per "
        "poll with attribution recorded on every row. Production rollout and any wider board list "
        "stay gated on the terms findings in docs/data/SOURCE_RIGHTS_EVIDENCE.md."),
}

# A posting link is only canonical if it still belongs to the provider the employer hosts the
# board on. Anything else (an employer intranet, a redirector) needs a human look.
CANONICAL_HOST_SUFFIXES = {"greenhouse": "greenhouse.io", "lever": "lever.co", "ashby": "ashbyhq.com"}


def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def check_links(rows: list[dict]) -> dict:
    off_board, no_link = [], []
    for row in rows:
        if not str(row.get("apply_url", "")).startswith("https://"):
            no_link.append(row.get("external_id"))
            continue
        suffix = CANONICAL_HOST_SUFFIXES.get(row["provider"], "")
        if suffix and not _host(row["apply_url"]).endswith(suffix):
            off_board.append({"external_id": row["external_id"], "host": _host(row["apply_url"])})
    return {"https_apply_links": len(rows) - len(no_link), "missing_apply_link": no_link,
            "off_provider_host": off_board}


async def one_poll(db, boards: list[dict], poll_index: int, seen_by_board: dict) -> dict:
    result = {"poll": poll_index, "started_at": datetime.now(timezone.utc).isoformat(),
              "boards": [], "records": [], "batch_ids": []}
    for index, board in enumerate(boards):
        if index:
            # Polite and sequential; never below the host's own Crawl-delay directive.
            time.sleep(max(PilotArgs.delay, previous_crawl_delay))
        fetched = job_feeds.fetch_board(board)
        robots = fetched.get("robots", {})
        previous_crawl_delay = float(robots.get("crawl_delay") or 0)
        entry = {"robots_state": robots.get("state"), "robots_allowed": robots.get("allowed"),
                 "crawl_delay_directive": previous_crawl_delay,
                 "board_id": board["board_id"], "provider": board["provider"],
                 "company": board["company"], "http_status": fetched["http_status"],
                 "ok": fetched["ok"], "postings_seen": len(fetched["records"]),
                 "body_fields_discarded": fetched.get("body_fields_discarded", 0),
                 "error": fetched["error"]}
        if fetched["ok"]:
            entry["link_check"] = check_links(fetched["records"])
            batch = await job_feeds.import_board_snapshot(db, SOURCE["source_id"], board["board_id"],
                                                          fetched["records"], "job-feed-pilot")
            entry["import_counts"] = batch["counts"]
            entry["batch_id"] = batch["batch_id"]
            result["batch_ids"].append(batch["batch_id"])
            result["records"].extend(fetched["records"])
            seen_by_board[board["board_id"]] = {row["external_id"] for row in fetched["records"]}
        else:
            seen_by_board[board["board_id"]] = None  # unknown state: do not expire anything
        entry["visibility"] = (await job_feeds.reconcile_visibility(
            db, [board["board_id"]], {board["board_id"]: seen_by_board[board["board_id"]] or set()}
        )) if fetched["ok"] else {"skipped": "feed unavailable; last-known state left untouched"}
        result["boards"].append(entry)
    return result


class PilotArgs:
    delay = 1.5


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default="")
    parser.add_argument("--db-name", default="pacio_dryrun_jobs")
    parser.add_argument("--boards", default="", help="comma separated board_id subset")
    parser.add_argument("--polls", type=int, default=2)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--out", default="", help="also write the JSON report to this path")
    args = parser.parse_args()
    PilotArgs.delay = args.delay

    boards = job_feeds.BOARDS
    if args.boards:
        wanted = {part.strip() for part in args.boards.split(",")}
        boards = [board for board in boards if board["board_id"] in wanted]

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
    report: dict = {"engine": engine, "source": SOURCE["source_id"],
                    "verdict": SOURCE["commercial_verdict"], "limitations": SOURCE["limitations"],
                    "user_agent": job_feeds.USER_AGENT, "requested_boards": len(boards),
                    "polls": [], "ran_at": datetime.now(timezone.utc).isoformat()}

    seen_by_board: dict[str, set[str] | None] = {}
    for poll_index in range(1, args.polls + 1):
        report["polls"].append(await one_poll(db, boards, poll_index, seen_by_board))

    all_rows = [row for poll in report["polls"] for row in poll["records"]]
    unique = {(row["board_id"], row["external_id"]) for row in all_rows}
    report["totals"] = {
        "requests_made": sum(1 for poll in report["polls"] for _ in poll["boards"]),
        "successful_polls": sum(1 for poll in report["polls"] for board in poll["boards"] if board["ok"]),
        "failed_polls": sum(1 for poll in report["polls"] for board in poll["boards"] if not board["ok"]),
        "posting_observations": len(all_rows),
        "unique_postings": len(unique),
        "duplicate_observations": len(all_rows) - len(unique),
        "body_fields_discarded": sum(int(board.get("body_fields_discarded", 0))
                                     for poll in report["polls"] for board in poll["boards"]),
        "stored_job_rows": await db.job_postings.count_documents({}),
    }
    report["per_board_stored"] = {
        board["board_id"]: await db.job_postings.count_documents({"board_id": board["board_id"]})
        for board in boards}
    report["stored_row_has_no_body_text"] = not any(
        job_feeds.FORBIDDEN_KEYS & set(row)
        for row in await db.job_postings.find({}, {"_id": 0}).to_list(None))
    uniq = {(row["board_id"], row["external_id"]): row for row in all_rows}.values()
    report["sample_stored_rows"] = [
        {"title": row.get("title"), "company": row.get("company"), "location": row.get("location"),
         "posted_at": row.get("posted_at"), "apply_url_host": _host(row.get("apply_url", "")),
         "attribution": row.get("attribution"), "data_status": row.get("data_status")}
        for row in sorted(uniq, key=lambda item: (item["company"], item.get("title") or ""))[:8]]
    stored_rows = await db.job_postings.find({}, {"_id": 0}).to_list(None)

    def _in_india(row):
        return "india" in str(row.get("location", "")).lower()

    report["location_relevance"] = {
        "rows_with_india_location": sum(1 for row in stored_rows if _in_india(row)),
        "rows_with_other_location": sum(1 for row in stored_rows
                                        if row.get("location") and not _in_india(row)),
        "rows_with_no_location": sum(1 for row in stored_rows if not row.get("location")),
        "distinct_locations": len({str(row.get("location", "")) for row in stored_rows}),
    }
    report["audit_rows"] = {"import_runs": await db.import_runs.count_documents({}),
                            "undo_items": await db.import_batch_items.count_documents({})}

    # Roll back every batch the pilot wrote, newest first, and prove the store is empty again.
    created = [batch_id for poll in report["polls"] for batch_id in poll["batch_ids"]]
    rollback = [await data_import.rollback_batch(db, batch_id) for batch_id in reversed(created)]
    report["batches_created"] = len(created)
    report["rollback_all_batches"] = rollback
    report["stored_after_rollback"] = await db.job_postings.count_documents({})

    if client is not None:
        report["cleanup"] = "kept" if args.keep else "dropped"
        if not args.keep:
            await client.drop_database(args.db_name)
    text = json.dumps(report, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
