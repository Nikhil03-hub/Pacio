# Demo and seeded accounts

No password is written down in this repository. Earlier revisions of these docs
published the demo password in plain text while the repository was public, which is
why the accounts are now opt-in.

## How accounts come to exist

| Path | Enabled by | Result |
| --- | --- | --- |
| Google sign-in | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | First sign-in creates a pending account; a platform admin assigns role and institution at approval. |
| Institution self-registration | always (`/register`) | Creates a pending institution plus a pending `tpo` account. |
| Invitation | staff role on `/api/invite` | Creates the account with role + institution and **no password**; it activates when that email first signs in with Google. |
| Platform admin bootstrap | `ADMIN_EMAIL` + `ADMIN_PASSWORD` | Ensures exactly one super_admin exists, with that password. |
| Role demo accounts | `SEED_DEMO_USERS=true` **and** `DEFAULT_DEMO_PASSWORD` | The six KMIT demo logins used during judging. Never enable on a deployment holding real institution data. |

## Local development

Copy `.env.example` to `backend/.env` (git-ignored) and set at minimum:

```
JWT_SECRET=<any long random string>
SEED_DEMO_DATA=true
SEED_DEMO_USERS=true
DEFAULT_DEMO_PASSWORD=<something you choose locally>
ADMIN_EMAIL=<your address>
ADMIN_PASSWORD=<something you choose locally>
```

Sign in through the "Sign in with email" option on `/login`; the demo emails are
`tpo@kmit.in`, `institution@kmit.in`, `faculty@kmit.in`, `student@kmit.in`,
`recruiter@amazon.com` and `tpo@vasavi.ac.in` (deliberately left unapproved, for the
approval-flow walkthrough). Passwords are the value you set above.

## Production

- `SEED_DEMO_USERS` stays unset (it defaults to false).
- `JWT_SECRET` is required; the app refuses to start without it.
- `MONGO_URL` is required for real data. Without it the app runs on the in-memory
  fallback and **every cold start erases all users, sessions and uploads**.
- The demo password that appeared in the public git history should be treated as
  compromised: rotate it and remove any surviving demo accounts from the database.
