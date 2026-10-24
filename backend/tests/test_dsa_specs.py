"""Every shipped DSA spec must be executable and have tests that reject a wrong solution."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

import pytest  # noqa: E402

import dsa_catalog as C  # noqa: E402
from dsa_catalog import build_dsa_question_bank  # noqa: E402
import validate_dsa_specs as harness  # noqa: E402

SPECS = json.loads((ROOT / "backend" / "dsa_specs.json").read_text(encoding="utf-8"))
CATALOG = {row["question_id"]: row for row in build_dsa_question_bank()}


def test_specs_exist_and_ids_are_valid():
    assert SPECS, "at least one validated spec must ship"
    ids = [spec.get("question_id") for spec in SPECS]
    assert len(ids) == len(set(ids)), "duplicate spec ids"
    for qid in ids:
        assert qid in CATALOG, f"{qid} is not in the catalogue"


@pytest.mark.parametrize("spec", SPECS, ids=[s["question_id"] for s in SPECS])
def test_spec_is_complete_and_tests_have_teeth(spec):
    result = harness.validate_spec(spec, CATALOG[spec["question_id"]])
    assert result["status"] == "COMPLETE", result["errors"]
    assert result["reference_pass"] is True
    assert result["mutant_rejected"] is True
    assert result["cases"] >= 4


def test_restricted_exec_is_a_guardrail_not_a_sandbox():
    """Pin the truth about the harness, so nobody ships learner code onto it by accident.

    Verified 2026-10-24: a `__mro__` walk escapes the builtins restriction, while imports are
    refused. The harness is therefore only for trusted artefacts - reference and mutant
    solutions committed by Pacio - and must never execute a learner submission.
    """
    escape = "def f():" + chr(10) + "    return len(().__class__.__bases__[0].__subclasses__())" + chr(10)
    fn = harness.load_function(escape, "f", "escape-probe")
    assert fn() > 0, "if this ever stops escaping, the docstring must be re-checked, not trusted"

    blocked_import = "def f():" + chr(10) + "    import os" + chr(10) + "    return os.name" + chr(10)
    sneaky = harness.load_function(blocked_import, "f", "import-probe")
    with pytest.raises(ImportError):
        sneaky()


def test_every_shipped_checker_is_exercised():
    """All four checkers are product surface. An untested checker is a silent grading bug."""
    assert harness.check("exact", [1, 2], [1, 2])
    assert not harness.check("exact", [1, 2], [2, 1])
    assert harness.check("unordered", [3, 1, 2], [1, 2, 3])
    assert not harness.check("unordered", [1, 1, 2], [1, 2, 2])
    assert harness.check("nested_unordered", [[3, 1], [2]], [[2], [1, 3]])
    assert not harness.check("nested_unordered", [[1, 2]], [[1, 3]])
    assert harness.check("float", 6.5000001, 6.5)
    assert not harness.check("float", 6.6, 6.5)
    with pytest.raises(ValueError):
        harness.check("almost_right", 1, 1)
    # An uncomparable shape must grade as wrong, never as right and never as a crash.
    assert harness.check("unordered", "ab", ["a", "b"]) is False
    assert harness.check("nested_unordered", 5, [[1]]) is False
    assert harness.check("exact", None, 0) is False


def test_gradability_needs_the_current_harness_stamp(tmp_path):
    """A spec file entry alone must not make a problem auto-gradable."""
    import json as _json

    def state_of(verification):
        spec = {"question_id": "Q", "verification": verification} if verification is not None             else {"question_id": "Q"}
        path = tmp_path / "specs.json"
        path.write_text(_json.dumps([spec]), encoding="utf-8")
        return C._spec_states(path)["Q"]

    current = {"harness": C.DSA_HARNESS_VERSION, "result": "pass"}
    assert state_of(current) == "validated"
    assert state_of({"harness": "ancient-harness-v0", "result": "pass"}) == "specified_unverified"
    assert state_of({"harness": C.DSA_HARNESS_VERSION, "result": "fail"}) == "specified_unverified"
    assert state_of(None) == "specified_unverified"


def test_missing_spec_file_is_drafts_not_a_crash(tmp_path):
    assert C._spec_states(tmp_path / "absent.json") == {}


def test_corrupt_spec_file_fails_loudly_instead_of_demoting_the_bank(tmp_path):
    path = tmp_path / "specs.json"
    path.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(ValueError):
        C._spec_states(path)


def test_shipped_specs_are_all_stamped_and_gradable():
    bank = {row["question_id"]: row for row in C.build_dsa_question_bank()}
    assert len(SPECS) == 20
    for spec in SPECS:
        row = bank[spec["question_id"]]
        assert row["gradable"] is True and row["spec_status"] == "validated"
        assert spec["verification"]["harness"] == C.DSA_HARNESS_VERSION
    ungraded = [qid for qid, row in bank.items() if not row["gradable"]]
    assert len(ungraded) == 88, "the product must not imply the full bank is gradable"


def test_untested_catalogue_entries_remain_drafts():
    tested = {spec["question_id"] for spec in SPECS}
    drafts = [qid for qid in CATALOG if qid not in tested]
    # The product must not imply the full bank is gradable while drafts exist.
    assert len(drafts) == len(CATALOG) - len(SPECS)
