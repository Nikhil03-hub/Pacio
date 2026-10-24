"""Validate DSA problem specs and emit a completion report.

A problem is COMPLETE only if:
  - every required field is present and well-typed,
  - its reference solution passes every example and hidden test,
  - its mutant fails at least one hidden test (proves the tests have teeth),
  - the checker is one of the supported kinds.

Reference solutions are trusted repository artefacts, not learner code. They are executed
with a restricted builtin set and an import allowlist. Learner submissions are NOT executed
here; a real sandbox is required before grading untrusted code (see docs/data/DSA_COVERAGE_AND_VALIDATION.md).

Usage:
  .venv/Scripts/python.exe scripts/validate_dsa_specs.py
  .venv/Scripts/python.exe scripts/validate_dsa_specs.py --specs backend/dsa_specs.json --csv docs/data/DSA_SPECIFICATION_COMPLETION.csv
"""
from __future__ import annotations

import argparse
import builtins
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dsa_catalog import DSA_HARNESS_VERSION, build_dsa_question_bank  # noqa: E402

REQUIRED_FIELDS = {
    "question_id", "statement", "signature", "constraints", "examples",
    "hidden_tests", "checker", "reference", "mutant", "complexity",
}
CHECKERS = {"exact", "unordered", "nested_unordered", "float"}
SAFE_MODULES = {"heapq", "collections", "bisect", "math", "itertools", "functools"}
SAFE_BUILTINS = {
    "len": len, "range": range, "enumerate": enumerate, "zip": zip, "sorted": sorted,
    "min": min, "max": max, "sum": sum, "abs": abs, "any": any, "all": all,
    "list": list, "dict": dict, "set": set, "tuple": tuple, "int": int, "float": float,
    "str": str, "bool": bool, "isinstance": isinstance, "reversed": reversed,
    "map": map, "filter": filter, "next": next, "iter": iter, "ord": ord, "chr": chr,
    "divmod": divmod, "pow": pow, "round": round, "True": True, "False": False, "None": None,
}


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] not in SAFE_MODULES:
        raise ImportError(f"import of '{name}' is not allowed in DSA specs")
    return builtins.__import__(name, globals, locals, fromlist, level)


def load_function(source: str, name: str, label: str):
    namespace = {"__builtins__": {**SAFE_BUILTINS, "__import__": _safe_import}}
    exec(compile(source, f"<{label}>", "exec"), namespace)  # noqa: S102 - trusted artefact
    fn = namespace.get(name)
    if not callable(fn):
        raise ValueError(f"{label} does not define callable '{name}'")
    return fn


def _sequence(value) -> bool:
    # str must be excluded: sorted("ab") == sorted(["a", "b"]) would let a learner answer a
    # list-of-strings question with a bare string and still be graded correct.
    return isinstance(value, (list, tuple))


def check(kind: str, actual, expected) -> bool:
    if kind == "exact":
        return actual == expected
    if kind == "unordered":
        if not (_sequence(actual) and _sequence(expected)):
            return False
        try:
            return sorted(actual) == sorted(expected)
        except TypeError:
            return False
    if kind == "nested_unordered":
        if not (_sequence(actual) and _sequence(expected)):
            return False
        try:
            return sorted(sorted(x) for x in actual) == sorted(sorted(x) for x in expected)
        except TypeError:
            return False
    if kind == "float":
        return abs(float(actual) - float(expected)) <= 1e-6
    raise ValueError(f"unknown checker {kind!r}")


def call(fn, case: dict):
    args = case["in"]
    if isinstance(args, dict):
        return fn(**args)
    if isinstance(args, list):
        return fn(*args)
    return fn(args)


def validate_spec(spec: dict, catalog_row: dict) -> dict:
    errors = []
    missing = sorted(REQUIRED_FIELDS - set(spec))
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if spec.get("question_id") != catalog_row["question_id"]:
        errors.append("question_id does not match the catalogue")
    if spec.get("checker") not in CHECKERS:
        errors.append(f"invalid checker {spec.get('checker')!r}")
    for field in ("constraints", "examples", "hidden_tests", "edge_cases"):
        if field in spec and not isinstance(spec[field], list):
            errors.append(f"{field} must be a list")
    if len(spec.get("examples") or []) < 1:
        errors.append("at least one example is required")
    if len(spec.get("hidden_tests") or []) < 3:
        errors.append("at least 3 hidden tests are required")

    signature = spec.get("signature") or {}
    fn_name = signature.get("name")
    if not fn_name:
        errors.append("signature.name is required")

    reference_ok = mutant_rejected = False
    failed_cases = []
    if not errors and fn_name:
        try:
            ref = load_function(spec["reference"], fn_name, f"{spec['question_id']}:ref")
            cases = (spec.get("examples") or []) + (spec.get("hidden_tests") or [])
            for index, case in enumerate(cases):
                got = call(ref, case)
                if not check(spec["checker"], got, case["out"]):
                    failed_cases.append(f"case {index}: got {got!r}, expected {case['out']!r}")
            reference_ok = not failed_cases
        except Exception as exc:  # noqa: BLE001
            failed_cases.append(f"reference error: {exc}")

        try:
            mutant = load_function(spec["mutant"], fn_name, f"{spec['question_id']}:mutant")
            mutant_rejected = any(
                not check(spec["checker"], call(mutant, case), case["out"])
                for case in (spec.get("examples") or []) + (spec.get("hidden_tests") or [])
            )
            if not mutant_rejected:
                failed_cases.append("mutant passed every test (tests are too weak)")
        except Exception as exc:  # noqa: BLE001
            failed_cases.append(f"mutant error: {exc}")

    status = "COMPLETE" if (reference_ok and mutant_rejected and not errors) else "INVALID"
    return {
        "question_id": spec.get("question_id"),
        "title": catalog_row["title"],
        "topic": catalog_row["topic_code"],
        "difficulty": catalog_row["difficulty"],
        "checker": spec.get("checker"),
        "cases": len((spec.get("examples") or []) + (spec.get("hidden_tests") or [])),
        "reference_pass": reference_ok,
        "mutant_rejected": mutant_rejected,
        "status": status,
        "errors": "; ".join(errors + failed_cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs", default="backend/dsa_specs.json")
    parser.add_argument("--csv", default="docs/data/DSA_SPECIFICATION_COMPLETION.csv")
    parser.add_argument("--stamp", action="store_true", help="write the harness result into every passing spec; that stamp is what makes it gradable")
    args = parser.parse_args()

    catalog = build_dsa_question_bank()
    by_id = {row["question_id"]: row for row in catalog}
    specs_path = Path(args.specs)
    if not specs_path.exists():
        print(f"spec file not found: {specs_path}")
        return 2
    specs = json.loads(specs_path.read_text(encoding="utf-8"))
    if not isinstance(specs, list):
        print("spec file must contain a JSON array")
        return 2

    seen = set()
    results = []
    duplicates = []
    for spec in specs:
        qid = spec.get("question_id")
        if qid in seen:
            duplicates.append(qid)
            continue
        seen.add(qid)
        row = by_id.get(qid)
        if not row:
            results.append({"question_id": qid, "title": "?", "topic": "?", "difficulty": "?",
                            "checker": spec.get("checker"), "cases": 0, "reference_pass": False,
                            "mutant_rejected": False, "status": "INVALID",
                            "errors": "question_id not in catalogue"})
            continue
        results.append(validate_spec(spec, row))

    for row in catalog:
        if row["question_id"] not in seen:
            results.append({"question_id": row["question_id"], "title": row["title"],
                            "topic": row["topic_code"], "difficulty": row["difficulty"],
                            "checker": "", "cases": 0, "reference_pass": False,
                            "mutant_rejected": False, "status": "DRAFT",
                            "errors": "no validated specification yet"})

    results.sort(key=lambda r: (r["status"] != "COMPLETE", r["topic"], r["question_id"]))
    out = Path(args.csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    if args.stamp:
        by_qid = {res["question_id"]: res for res in results}
        validated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        stamped = 0
        for spec in specs:
            res = by_qid.get(spec.get("question_id"))
            if res and res["status"] == "COMPLETE":
                spec["verification"] = {"harness": DSA_HARNESS_VERSION, "result": "pass",
                                        "validated_at": validated_at, "cases": res["cases"],
                                        "reference_pass": True, "mutant_rejected": True}
                stamped += 1
        specs_path.write_text(json.dumps(specs, indent=2, ensure_ascii=False) + chr(10), encoding="utf-8")
        print(f"stamped {stamped}/{len(specs)} specs with harness {DSA_HARNESS_VERSION}")

    complete = [r for r in results if r["status"] == "COMPLETE"]
    invalid = [r for r in results if r["status"] == "INVALID"]
    drafts = [r for r in results if r["status"] == "DRAFT"]
    print(f"specs supplied: {len(specs)} | COMPLETE: {len(complete)} | INVALID: {len(invalid)} | DRAFT: {len(drafts)}")
    if duplicates:
        print(f"duplicate ids: {duplicates}")
    for row in invalid:
        print(f"INVALID {row['question_id']}: {row['errors']}")
    print(f"report: {out}")
    return 0 if not invalid and not duplicates else 1


if __name__ == "__main__":
    raise SystemExit(main())
