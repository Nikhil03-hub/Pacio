# DSA Grading Security Design

Phase 3 deliverable. Written 2026-10-24. Status: **design only — NOT IMPLEMENTED, NOT RUN.**

This document exists so that the fabricated judge cannot return, and so that if a real judge is
built it is built with the limits that make it safe. It records what the product does today, what a
real judge must defend against, and the exact conditions that must be met before any learner code is
executed.

## 1. Current state (VERIFIED)

| Claim | Evidence |
|---|---|
| Learner code is **not** executed anywhere | `backend/server.py::_static_code_review` returns `executed: false`, `graded: false`; `backend/tests/test_dsa_grading_honesty.py` pins it |
| A submission cannot set `solved` or `mastery` | `submit_my_dsa_code` keeps previous values; pinned by `test_submitting_code_does_not_mark_the_problem_solved` |
| The authoring harness is **not** a sandbox | `test_restricted_exec_is_a_guardrail_not_a_sandbox`: a `__mro__` walk escapes the builtins restriction (245 classes reachable); `import os` is blocked. Measured, not assumed. |
| The reference/mutant harness runs only committed, trusted artefacts | `scripts/validate_dsa_specs.py`, run offline by developers and CI |
| 30 of 108 problems have validated specifications | `docs/data/DSA_SPECIFICATION_COMPLETION.csv`, `validate_dsa_specs.py --stamp` |

The static review may say what the source *looks like* (language tokens, an algorithmic construct,
line count). It must never say the code is correct, never produce a runtime or memory figure, and
never gate progress. Those are product rules, not preferences.

## 2. What must never be reintroduced

A verdict derived from heuristics. Specifically, none of the following may ever be computed from
source text: `Accepted`, a pass/total test count, `runtime_ms`, `memory_kb`, a `solved` flag, a
mastery score, a "best submission" pointer. Any of these values must originate from an actual
execution with a recorded artefact, or not exist.

## 3. Threat model

Asset: the API host, its database, other tenants' data, and the integrity of the score a placement
cell may act on.

| # | Threat | Example | Consequence if unmitigated |
|---|---|---|---|
| T1 | Arbitrary code execution on the API host | `os.system`, `subprocess`, a native extension | Full host compromise; database read/write |
| T2 | Secret exfiltration | reading env vars, `.env`, mounted credentials | Tenant data, JWT signing key, provider keys |
| T3 | Network egress | POSTing stolen data to an attacker, mining, scanning the internal network | Data loss, abuse of our IP |
| T4 | Resource exhaustion | infinite loop, 10 GB allocation, fork bomb, output flooding | Denial of service for every tenant |
| T5 | Filesystem abuse | writing to disk until full, reading other submissions | Cross-tenant disclosure |
| T6 | Grader manipulation | monkeypatching the checker, shadowing builtins, exiting with code 0 | False "solved", corrupt analytics |
| T7 | Timing/oracle abuse | using error timing to infer hidden test inputs | Test leakage |
| T8 | Abuse at scale | thousands of submissions to occupy workers | Cost and availability |

The authoring harness is vulnerable to T1, T2, T3, T5 and T6 **by design** — it runs code the
repository trusts. That is acceptable for `dsa_specs.json` and unacceptable for a learner.

## 4. Required architecture

```
browser → API (FastAPI) → submissions queue (durable) → judge orchestrator (separate service)
                                                              ↓
                                                ephemeral sandbox per submission
                                                (container or microVM, no network)
                                                              ↓
                                          result artefact → API → student
```

Non-negotiable properties of the sandbox:

1. **Process isolation stronger than a process.** A container with a hardened runtime (gVisor) or a
   microVM (Firecracker). Never `exec()` inside the API process, never `subprocess` on the API host.
2. **No network.** `--network none`; DNS absent; loopback only if the harness needs it.
3. **Read-only root filesystem**, one writable `tmpfs` (64 MB) mounted at a scratch path.
4. **Non-root user**, no capabilities, `no-new-privileges`, seccomp profile, no host mounts.
5. **Empty environment.** No `MONGO_URL`, no `JWT_SECRET`, no provider keys, no proxy variables.
6. **Hard limits per test and per submission**: wall clock 5 s/submission (1 s/test), CPU 1 s, memory
   256 MB, 64 processes/threads, stdout+stderr 64 KB combined, output truncated with an explicit
   marker rather than silently.
7. **Kill and reap.** A watchdog kills the whole cgroup/VM, not just the parent process; the
   orchestrator cleans up regardless of exit path, and a reaper sweeps orphans.
8. **Test bundle integrity.** Tests and expected outputs are fetched into the sandbox from a signed,
   versioned artefact produced by the spec pipeline; the learner's process never controls the
   comparison. Comparison happens outside the sandbox, on the orchestrator, from a structured
   result the sandbox cannot forge (exit code + files written to a dedicated result path).
9. **Timeouts are enforced outside the sandbox.** A process that ignores SIGTERM is killed.
10. **Audit and quotas.** Every run records submitter, question, spec version, image digest, limits,
    exit reason and duration; per-student and per-tenant rate limits plus a global concurrency cap.

Threat coverage: T1/T2/T3/T5 by isolation and empty env; T4 by limits and watchdog; T6 by
out-of-sandbox comparison and immutable test bundles; T7 by fixed, non-adaptive test ordering and
uniform error messages; T8 by quotas.

## 5. Phased plan

| Phase | Scope | Precondition |
|---|---|---|
| 0 (today) | Static review only; no execution; no grading claims | — |
| 1 | Trusted-only local runner for staff to sanity-check a spec, still on committed artefacts | none (this is what `validate_dsa_specs.py` does) |
| 2 | Sandboxed judge for **opted-in** questions whose specs are validated, behind a feature flag, one tenant at a time | all acceptance tests in §6 green on staging |
| 3 | Default grading for validated questions | Phase 2 stable for two weeks; cost per submission measured |

Phase 2 must not start before a **cost model** exists: container start-up dominates a 1-second
problem, so expect warm pools per language. Measure before promising a UX.

## 6. Acceptance tests required before any learner code runs

1. `os.system("id")`, `subprocess.run`, `open("/etc/passwd")` → the submission fails, host unaffected.
2. Reading every environment variable yields nothing sensitive (assert the env is empty).
3. An outbound HTTP request fails; DNS resolution fails.
4. `while True: pass` is killed at the wall-clock limit; the API stays responsive.
5. `[0] * 10**9` fails with a clean memory error, not a host OOM.
6. Fork bomb is contained by the pid limit.
7. A 10 MB print is truncated at 64 KB and reported as truncated.
8. A submission that writes to `/` fails; writing to the scratch path works.
9. A submission that defines `__eq__`/monkeypatches builtins cannot influence the verdict.
10. Two tenants' submissions never share a container or a filesystem path.
11. The orchestrator survives a sandbox that never exits (kill + reap within N seconds).
12. Every result row carries the spec version and image digest.

## 7. What this design deliberately does **not** claim

- It does not claim the current product can grade learner code. It cannot.
- It does not claim a container alone is sufficient; the isolation choice, limits, and
  out-of-sandbox comparison are all required together.
- It does not authorise running the authoring harness on untrusted input under any configuration.
- It does not promise a timeline. The prerequisite is engineering capacity plus a cost model.

## 8. Product copy implications

Until Phase 2 lands, every surface must keep saying: submitted code is **not executed and not
graded**, and a submission records an attempt plus a static review. That sentence is enforced by
tests, not convention.
