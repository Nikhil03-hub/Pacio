"""Employer-hosted job board adapters for the Workstream D pilot.

A "board" here is a company's own public recruiting feed on Greenhouse, Lever or Ashby. These are
the employer's listing of the employer's own openings, and this module deliberately keeps only the
metadata a placement cell needs to send a student there:

    title, company, location, when it was posted, the canonical application link, attribution

It never stores the job description, the application questions, or any candidate data: every
adapter passes through `_clean`, which raises if any `FORBIDDEN_KEYS` field survives, and the test
suite asserts it, so a future edit cannot quietly start retaining employer text. Every feed is also
checked against the host's robots.txt before a single byte is requested.

Nothing here writes to the application database; `scripts/job_feed_pilot.py` owns that, and it
writes only to a disposable database behind `data_import`'s approval gate.
"""
from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import data_import

USER_AGENT = "PacioJobFeedPilot/0.1 (research pilot for a college placement-cell product)"
REQUEST_TIMEOUT_SECONDS = 15

# Greenhouse, Lever and Ashby all return the full posting text in their open feeds. We read it and
# discard it. If one of these keys ever reaches the database the pilot contract is broken.
FORBIDDEN_KEYS = {
    "description", "descriptionPlain", "descriptionHtml", "descriptionBody",
    "descriptionBodyPlain", "additional", "additionalPlain", "opening", "openingPlain",
    "lists", "content", "text_html", "sections", "questions", "office",
}

# board_id -> (provider, feed url template, company display name, careers page for attribution)
BOARDS: list[dict[str, str]] = [
    {"board_id": "groww", "provider": "greenhouse", "company": "Groww",
     "careers_url": "https://groww.careers/", "feed_url": "https://boards-api.greenhouse.io/v1/boards/groww/jobs"},
    {"board_id": "cred", "provider": "lever", "company": "CRED",
     "careers_url": "https://cred.ai/careers", "feed_url": "https://api.lever.co/v0/postings/cred?mode=json"},
    {"board_id": "openai", "provider": "ashby", "company": "OpenAI",
     "careers_url": "https://openai.com/careers", "feed_url": "https://api.ashbyhq.com/posting-api/job-board/openai"},
]


def _date_only(value: Any) -> str:
    """Reduce a provider timestamp to a date string; feeds disagree on precision and zone."""
    text = str(value or "").strip()
    if not text:
        return ""
    if text.isdigit():  # Lever sends epoch milliseconds
        return datetime.fromtimestamp(int(text) / 1000, timezone.utc).date().isoformat()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text[:10]


def _clean(record: dict, board: dict, retrieved_at: str) -> dict:
    """Attach the provenance every stored row must carry, then assert no body text survived."""
    row = {key: value for key, value in record.items() if value not in (None, "")}
    row.update({
        "board_id": board["board_id"], "provider": board["provider"], "company": board["company"],
        "source_url": board["feed_url"], "retrieved_at": retrieved_at,
        "attribution": f"{board['company']} careers ({board['provider']}, board {board['board_id']})",
        "careers_url": board["careers_url"], "data_status": "published",
    })
    leaked = FORBIDDEN_KEYS & set(row)
    if leaked:
        raise ValueError(f"feed adapter leaked posting body text: {sorted(leaked)}")
    return row


def normalize_greenhouse(board: dict, payload: Any, retrieved_at: str) -> list[dict]:
    rows = []
    for job in payload.get("jobs", []):
        rows.append(_clean({
            "external_id": str(job.get("id", "")),
            "title": job.get("title"),
            "location": (job.get("location") or {}).get("name"),
            "apply_url": job.get("absolute_url"),
            "posting_url": job.get("absolute_url"),
            "posted_at": _date_only(job.get("first_published") or job.get("updated_at")),
            "updated_at_provider": _date_only(job.get("updated_at")),
            "requisition_id": job.get("requisition_id"),
            "is_active": True,
        }, board, retrieved_at))
    return rows


def normalize_lever(board: dict, payload: Any, retrieved_at: str) -> list[dict]:
    rows = []
    for job in payload:
        categories = job.get("categories") or {}
        # Lever's `text` field is the posting title, lower-cased by their API. Stored verbatim:
        # re-casing here would silently rewrite employer-provided text.
        rows.append(_clean({
            "external_id": str(job.get("id", "")),
            "title": job.get("text"),
            "title_is_provider_lowercased": True,
            "location": categories.get("location") or job.get("country"),
            "department": categories.get("department"),
            "team": categories.get("team"),
            "workplace_type": job.get("workplaceType"),
            "apply_url": job.get("hostedUrl"),
            "posting_url": job.get("hostedUrl"),
            "posted_at": _date_only(job.get("createdAt")),
            "is_active": True,
        }, board, retrieved_at))
    return rows


def normalize_ashby(board: dict, payload: Any, retrieved_at: str) -> list[dict]:
    rows = []
    for job in payload.get("jobs", []):
        if not job.get("isListed", True):
            continue  # Ashby keeps unlisted postings in the feed; they are not open roles
        address = ((job.get("address") or {}).get("postalAddress") or {})
        rows.append(_clean({
            "external_id": str(job.get("id", "")),
            "title": job.get("title"),
            "location": job.get("location") or address.get("addressLocality"),
            "department": job.get("department"),
            "team": job.get("team"),
            "employment_type": job.get("employmentType"),
            "workplace_type": job.get("workplaceType"),
            "is_remote": job.get("isRemote"),
            "apply_url": job.get("applyUrl") or job.get("jobUrl"),
            "posting_url": job.get("jobUrl"),
            "posted_at": _date_only(job.get("publishedAt")),
            "is_active": True,
        }, board, retrieved_at))
    return rows


ADAPTERS: dict[str, Callable[[dict, Any, str], list[dict]]] = {
    "greenhouse": normalize_greenhouse,
    "lever": normalize_lever,
    "ashby": normalize_ashby,
}


def count_body_fields(payload: Any) -> int:
    """How many posting-body fields the provider sent us that we are choosing not to store."""
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        return 0
    return sum(len(FORBIDDEN_KEYS & set(job)) for job in jobs if isinstance(job, dict))


def fetch_board(board: dict) -> dict:
    """One polite GET. Returns {ok, records} or {ok: False, error, http_status} - never raises."""
    result = {"board_id": board["board_id"], "provider": board["provider"],
              "company": board["company"], "feed_url": board["feed_url"], "ok": False,
              "records": [], "error": "", "http_status": None}
    adapter = ADAPTERS.get(board["provider"])
    if adapter is None:
        # Checked before the request: a board we cannot parse should not spend a network call.
        result["error"] = f"no adapter for provider {board['provider']!r}"
        return result
    policy = robots_policy(board["feed_url"])
    result["robots"] = policy
    if not policy["allowed"]:
        result["error"] = (f"robots.txt on {policy['origin']} does not permit this feed "
                           f"({policy['state']}: {policy['detail']})")
        return result
    request = urllib.request.Request(
        board["feed_url"], headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                    "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            result["http_status"] = response.status
            body = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                body = gzip.decompress(body)
    except urllib.error.HTTPError as exc:
        result["error"] = f"HTTP {exc.code} - board not found or feed withdrawn"
        result["http_status"] = exc.code
        return result
    except urllib.error.URLError as exc:
        result["error"] = f"network failure: {exc.reason}"
        return result
    except Exception as exc:  # noqa: BLE001 - a poll must never crash the pilot
        result["error"] = f"unexpected: {type(exc).__name__}: {exc}"
        return result

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["error"] = f"feed is not valid JSON: {exc}"
        return result
    try:
        result["records"] = adapter(board, payload, _now_iso())
    except ValueError as exc:  # adapter leaked body text: refuse the whole board
        result["error"] = str(exc)
        return result
    result["ok"] = True
    result["body_fields_discarded"] = count_body_fields(payload)
    return result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


ROBOTS_TIMEOUT_SECONDS = 10
_robots_cache: dict[str, dict] = {}


def parse_robots(text: str) -> dict:
    """Directives for the `User-agent: *` group only."""
    rules = {"disallow": [], "allow": [], "crawl_delay": None}
    in_star = False
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            in_star = value.strip().lower() == "*"
            continue
        if not in_star:
            continue
        if field == "disallow" and value:
            rules["disallow"].append(value)
        elif field == "allow" and value:
            rules["allow"].append(value)
        elif field == "crawl-delay":
            try:
                rules["crawl_delay"] = float(value)
            except ValueError:
                pass
    return rules


def path_allowed(rules: dict, path: str) -> bool:
    """Longest matching prefix wins, per the usual robots convention."""
    best_prefix, best_kind = "", None
    for kind in ("allow", "disallow"):
        for prefix in rules[kind]:
            if path.startswith(prefix) and len(prefix) > len(best_prefix):
                best_prefix, best_kind = prefix, kind
    return True if best_kind is None else best_kind == "allow"


def robots_policy(feed_url: str) -> dict:
    """Read the host's robots.txt once per run and decide whether this feed may be polled.

    States: `published` (directives parsed), `not_published` (404 - no directive exists, so the
    path is not excluded), `unreadable` (401/403/5xx/timeout - unknown, and unknown is treated as
    a refusal because we are the guest on someone else's API).
    """
    parts = urllib.parse.urlsplit(feed_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin in _robots_cache:
        return _robots_cache[origin]
    policy = {"origin": origin, "state": "unreadable", "allowed": False,
              "crawl_delay": None, "detail": ""}
    try:
        request = urllib.request.Request(f"{origin}/robots.txt",
                                         headers={"User-Agent": USER_AGENT,
                                                  "Accept": "text/plain",
                                                  "Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=ROBOTS_TIMEOUT_SECONDS) as response:
            policy["state"] = "published"
            rules = parse_robots(response.read().decode("utf-8", "replace"))
            policy["crawl_delay"] = rules["crawl_delay"]
            policy["allowed"] = path_allowed(rules, parts.path or "/")
            policy["detail"] = f"disallow={rules['disallow']} allow={rules['allow']}"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            policy.update({"state": "not_published", "allowed": True,
                           "detail": "no robots.txt published for this host"})
        else:
            policy["detail"] = f"robots.txt returned HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - never let a policy probe raise
        policy["detail"] = f"robots.txt fetch failed: {type(exc).__name__}: {exc}"
    _robots_cache[origin] = policy
    return policy


def reset_robots_cache() -> None:
    _robots_cache.clear()


def deduplicate(records: list[dict]) -> tuple[list[dict], int]:
    """Collapse repeated (board, external_id) rows inside one poll, keeping the first seen."""
    seen: set[str] = set()
    kept = []
    for record in records:
        key = f"{record['board_id']}:{record['external_id']}"
        if key in seen:
            continue
        seen.add(key)
        kept.append(record)
    return kept, len(records) - len(kept)


async def import_board_snapshot(db, source_id: str, board_id: str, records: list[dict],
                                operator: str) -> dict:
    """Push one board's poll through `data_import`'s approval gate as a reversible batch.

    The board id is re-checked here so a caller cannot hand a batch to the wrong board's import.
    """
    mismatched = {row.get("board_id") for row in records} - {board_id}
    if mismatched:
        raise ValueError(f"records belong to another board: {sorted(mismatched)}")
    kept, dropped = deduplicate(records)
    result = await data_import.import_records(db, "jobs", kept, source_id, operator)
    result["duplicates_dropped"] = dropped
    return result
async def reconcile_visibility(db, board_ids: list[str], seen_by_board: dict[str, set[str]],
                               expire_after_days: int = 14, now: str | None = None) -> dict:
    """Track which postings the last poll actually saw, and retire the ones it stopped seeing.

    A posting absent from the feed has been filled or withdrawn by the employer. It is marked
    `absent` immediately and `expired` once it has been absent for `expire_after_days`, so the
    product can never advertise a role the employer no longer lists as open.
    """
    now = now or _now_iso()
    cutoff = (datetime.fromisoformat(now) - timedelta(days=expire_after_days)).isoformat()
    summary = {"touched": 0, "reappeared": 0, "newly_absent": 0, "expired": 0, "still_active": 0}
    for board_id in board_ids:
        seen = seen_by_board.get(board_id, set())
        rows = await db.job_postings.find({"board_id": board_id}, {"_id": 0}).to_list(None)
        for row in rows:
            stable = row.get("stable_key", "")
            external_id = row.get("external_id") or stable.rsplit(":", 1)[-1]
            collection = db.job_postings
            if external_id in seen:
                update = {"last_seen_at": now}
                if row.get("absent_since") or row.get("expired"):
                    update.update({"absent_since": None, "is_active": True,
                                   "expired": False, "expired_at": None})
                    summary["reappeared"] += 1
                else:
                    summary["still_active"] += 1
                await collection.update_one({"stable_key": stable}, {"$set": update})
                summary["touched"] += 1
            else:
                absent_since = row.get("absent_since") or now
                update = {"absent_since": absent_since, "is_active": False}
                if absent_since <= cutoff:
                    update["expired"] = True
                    update["expired_at"] = now
                    summary["expired"] += 1
                elif not row.get("absent_since"):
                    summary["newly_absent"] += 1
                await collection.update_one({"stable_key": stable}, {"$set": update})
                summary["touched"] += 1
    return summary
