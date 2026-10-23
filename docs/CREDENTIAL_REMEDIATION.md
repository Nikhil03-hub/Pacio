# Credential Remediation

Status as of 2026-10-23. No secret values are reproduced here.

**Overall: BLOCKED on owner/provider action.** The codebase no longer contains the exposed
values and no longer falls back to them, but rotation is the only real remediation and this
machine has no provider access. Deleting a file or making a repository private does **not**
revoke a credential that has already been published.

## What was exposed

| Credential | Where it lived | Current source state | Verified |
| --- | --- | --- | --- |
| Demo account password (`DEFAULT_DEMO_PASSWORD`) | Published in `memory/test_credentials.md`, `auth_testing.md`, `RUN_ON_WINDOWS.md`, two test-report JSONs, the Windows launcher, and two legacy test files. Present in **8 commits** of public history. | Removed forward: 0 literal occurrences in the tracked tree (`git grep` clean); docs reference `${DEFAULT_DEMO_PASSWORD}`; tests require the env var and skip with a message; the launcher echo was deleted. | VERIFIED (tree), history still contains it |
| Jooble API key | Hardcoded fallback in `backend/server.py` in **1 historical commit**; removed from current source by `b170ab0`. | Integration reads `JOOBLE_API_KEY` from the environment only, with no fallback. Missing key now returns `totalCount: 0`, `jobs: []` and a warning instead of fabricated listings. | VERIFIED (missing-key behaviour tested live) |
| Account email list / preview host | Demo emails and a dead `emergentagent.com` preview URL appeared in docs and invite emails. | Docs sanitised; invite emails use `PUBLIC_BASE_URL`; the legacy Emergent login is disabled by default. | VERIFIED (source), not a credential |

No private keys, cloud keys, JWTs or database URIs were found in the current tracked tree.
The sub-product (`skill-tank-partner-platform`) contains only placeholder
`SUPABASE_SERVICE_ROLE_KEY=your-…` lines and a Vercel secret reference; no real key is
committed.

## Required provider-side actions

### 1. Jooble (highest priority)

1. Sign in to the Jooble API account that issued the key.
2. Revoke/regenerate the key. Do not reuse the old value.
3. In Vercel → Project → Settings → Environment Variables, set `JOOBLE_API_KEY` for
   Production **and** Preview. Environment changes apply to new deployments only.
4. Redeploy. Verify `GET /api/jobs/discover?keywords=python` returns `"source": "jooble"`
   with real listings; with the variable removed it must return `"source": "unconfigured"`
   and an empty list (this is the tested behaviour).
5. Record the rotation date and who performed it.

### 2. Demo accounts

1. In Vercel, set `DEFAULT_DEMO_PASSWORD` to a new value (or leave it unset and keep
   `SEED_DEMO_USERS` unset).
2. In MongoDB Atlas, delete or disable the demo accounts that were seeded before this work:
   `admin@careeros.app`, `institution@kmit.in`, `tpo@kmit.in`, `faculty@kmit.in`,
   `student@kmit.in`, `recruiter@amazon.com`, `tpo@vasavi.ac.in`.
3. Confirm `SEED_DEMO_USERS` is not set in Vercel. New deployments no longer create them.
4. Change any real account that reused the old demo password.

### 3. Other credentials to confirm

- `JWT_SECRET`: confirm it is set in Vercel and is not the old fallback value. Rotating it
  signs every user out.
- Google OAuth client secret: confirm it was never committed (no evidence it was).
- MongoDB Atlas user: rotate if the URI ever appeared in a screenshot, chat or commit.

## Git history

The exposed values remain in history and are recoverable by anyone who cloned or forked the
public repository. After rotation:

- **Option A — leave history.** Acceptable once the credentials are dead. Simple, no
  coordination cost.
- **Option B — rewrite history** with `git filter-repo` (BFG alternative), then
  force-push. Consequences: every collaborator/fork must re-clone; open PRs break; commit
  hashes change; Vercel redeploys. Coordinate before doing it.
- Making the repository private reduces future exposure but does not revoke anything and
  does not remove forks.

**Recommendation:** rotate first (A is sufficient if rotation is done), then decide whether
the remaining exposure of old, dead values is worth a rewrite.

## Verification performed in this pass

- Current tree scan for high-confidence secret patterns: **0 files**.
- `git grep` for the demo password: **0** tracked occurrences.
- Jooble without a key: **empty result + warning**, no invented jobs (live request).
- Sub-product scan: placeholders only; **0** JWT-looking literals.
- History: demo password in 8 commits, Jooble key in 1 commit (counts only; values not
  printed).
