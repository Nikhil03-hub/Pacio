# Git Report — both repositories

Recorded 2026-10-23 after the continuation pass. Nothing was pushed, deployed, merged,
rebased, stashed or reset. Working trees are preserved.

## Pacio-Merged (main product)

| | |
| --- | --- |
| Absolute path | `C:\Users\NIKHIL\OneDrive\ドキュメント\Claude Projects\Career Guidance\Pacio-Merged` |
| Remote (fetch/push) | `https://github.com/Nikhil03-hub/pacio-intelligence.git` (public) |
| Branch | `main`, tracking `origin/main` |
| State | **8 commits ahead of origin, not pushed**, working tree clean |
| Baseline before this work | `6aa0f44` ("Auth redesign…") — clean tree except untracked `pacio-audit-findings.md` |
| Cumulative diff vs origin | run `git diff --stat origin/main..HEAD` for the authoritative count; the table below lists every checkpoint |

### Local checkpoints, oldest first

| Commit | Purpose | Scope |
| --- | --- | --- |
| `a2d445e` | Close P0 auth, tenant and session defects; unify seeding rules; harden uploads and exports | `backend/server.py`, `backend/auth.py`, legacy tests, new `test_hardening.py` |
| `58d6dc5` | Make the design system actually render; remove fabricated benchmark/customer claims; real certificate verification; login capability discovery; delete dead pages | frontend (24 files) + `backend/server.py` |
| `c72e29f` | Remove published credentials; add proprietary `LICENSE`, `.env.example`, README and the full docs set; strip third-party attribution from DSA identifiers | docs, `LICENSE`, `README.md`, `backend/dsa_catalog.py`, `backend/seed_data.py` |
| `6eb2a73` | Correct documented test counts to the verified run | docs |
| `0736e5c` | Repair the MongoDB path (full seed, aptitude/resume backfills, health), add fail-closed production, shared-store rate limiting, central approval gate, staff-only exports; Tenant B matrix + real-Mongo integration tests; release readiness + provenance registry | backend, tests, docs |
| `efa1359` | Fix the partial unique index on resume tokens (E11000 on nulls broke every ATS endpoint on Mongo); decouple derived backfills; record F-10..F-16; remove remaining password literals | backend, tests, docs |
| `e87c536` | Record the final verified legacy run (73/73 on the previous catalogue) | docs |
| `b5a4754` | Replace the third-party DSA sheet with the original 12-topic / 108-problem curriculum; fix orphaned seeding; stop fabricated Jooble listings; add backup/restore + migration scripts, DATABASE_RECOVERY and CREDENTIAL_REMEDIATION; track `.env.example`; ignore backups | backend, frontend strings, tests, scripts, docs |

### Files that exist but are deliberately NOT in git
`backend/.env` (local secrets, git-ignored), `frontend/.env.local` (dev API URL,
git-ignored), `frontend/build/`, `.venv/`, `node_modules/`.

### Recovery points
Every commit is an independent, reversible checkpoint. To discard the last one:
`git reset --soft HEAD~1`. No branch was force-moved and no history was rewritten.

## skill-tank-partner-platform (sub-product)

| | |
| --- | --- |
| Absolute path | `...\Career Guidance\skill-tank-partner-platform` |
| Remote | `https://github.com/Nikhil03-hub/CareerOS-Partner-Intelligence.git` |
| Branch | `main` (no upstream configured) |
| State | **1 local commit ahead of `origin/main` (`885f52b`)**, not pushed, clean tree |
| Commit | `83ed1cb` "wip: preserve the in-progress UI migration so it cannot be lost" — 30 files, +556 / -242 |

What that commit preserves, and why it had to be committed as one unit:

- 24 tracked files were modified **and** they import files that were untracked
  (`src/components/ui/{button,card,input,label}.tsx`). A `git clean -fd` or a bare
  checkout would have left tracked code importing missing modules.
- It is a **half-applied** migration, and the unfinished parts were left exactly as found
  rather than guessed at:
  - `src/app/globals.css` (new palette) is imported by nothing; `src/app/layout.tsx` still
    imports `@/styles/globals.css`.
  - `src/components/ui/badge.tsx` has no importers.
- `tsc --noEmit` passes with the change set applied.
- Undo with `git reset --soft HEAD~1`, which restores the previous uncommitted state.

Environment files: `.env.local` exists on disk and is git-ignored; `.env.example` contains
placeholders only. No Supabase key is committed.

Housekeeping: a stale, zero-byte `.git/index.lock` dated 2026-09-27 was blocking any git
write. No git process was running; it was moved to `.git/index.lock.stale-20261023`
rather than deleted, then the recovery commit was made.

## CareerOS AI (separate project) — untouched

The workspace root (`README.md`, `10th/`) belongs to a different project. A scan for files
modified today outside the two repositories above returned nothing, and the root README's
modification time is unchanged (May 16). No file, dataset, design token or remote was
shared between the projects.

## Divergence between the two products

They remain separate stacks (React/FastAPI/Mongo vs Next.js/Supabase) and were not merged.
Pacio-Merged absorbed the partner-intelligence feature set earlier; the sub-product's
uncommitted UI work is its own design direction and was **not** ported into Pacio. The
Pacio visual identity (ink/bone/accent/rust/moss/ochre) was preserved deliberately.

## Owner actions that remain

1. Push is **not** done. Review the five commits, then push or reset as you prefer.
2. Rotate the demo password and the Jooble key; decide history rewrite vs private repo.
3. Confirm Vercel environment variables; the new build fails closed without `MONGO_URL`.
4. Decide the product name and the DSA curriculum rights path.
