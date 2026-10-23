# How to run CareerOS (Pacio) on Windows

You do **not** need MongoDB. With no `MONGO_URL` set, the backend uses a built-in in-memory database that seeds itself with demo data (13 colleges, ~2,010 students, KMIT fully populated) every time it starts.

---

## Prerequisites (install once)

1. **Python 3.10+** — https://www.python.org/downloads/
   During install, tick **"Add python.exe to PATH"**.
2. **Node.js 18+ (LTS)** — https://nodejs.org/

To check they're installed, open **Command Prompt** and run:

```
python --version
npm --version
```

Both should print a version number. If "not recognized," reinstall and make sure PATH is ticked.

---

## Easiest way — one click (recommended)

1. In File Explorer, open the `Pacio-Merged` folder.
2. Double-click **`start-careeros.bat`**.
3. The first run installs everything and builds the UI (2–5 minutes — this is normal). Later runs are instant.
4. When you see `Uvicorn running on http://0.0.0.0:8000`, open your browser at:

   **http://localhost:8000**

5. Log in (see demo accounts below). Press **Ctrl+C** in the black window to stop.

> The backend serves the built React app, so everything runs from the single address `http://localhost:8000`. One window, one URL — no extra setup.

---

## Manual way (if you prefer typing commands)

Open **two** Command Prompt windows.

**Window 1 — backend:**
```
cd "C:\Users\NIKHIL\OneDrive\ドキュメント\Claude Projects\Career Guidance\Pacio-Merged\backend"
python -m pip install -r requirements.txt
python -m uvicorn server:app --port 8000
```

**Window 2 — frontend (build once, then it's served by the backend):**
```
cd "C:\Users\NIKHIL\OneDrive\ドキュメント\Claude Projects\Career Guidance\Pacio-Merged\frontend"
npm install
npm run build
```

Then open **http://localhost:8000**.

---

## Developer mode (live reload while editing) — optional

Use this only if you want the UI to refresh as you edit code. It runs the UI on port 3000 and talks to the backend on 8000 (the included `frontend/.env.local` already points it there).

**Window 1 — backend:**
```
cd ...\Pacio-Merged\backend
python -m uvicorn server:app --reload --port 8000
```

**Window 2 — frontend dev server:**
```
cd ...\Pacio-Merged\frontend
npm install
npx react-scripts start
```

Then open **http://localhost:3000**.

> ⚠️ Do **not** use `npm start` on Windows — its script contains `BROWSER=none`, which is Unix-only and errors in Command Prompt. Use **`npx react-scripts start`** instead (that's the fix for the setup problem you hit).

---

## Demo logins (password is the same for all)

| Role | Email | Password |
| :--- | :--- | :--- |
| Super admin | `admin@careeros.app` | `${DEFAULT_DEMO_PASSWORD}` |
| Institution admin | `institution@kmit.in` | `${DEFAULT_DEMO_PASSWORD}` |
| TPO (placement officer) | `tpo@kmit.in` | `${DEFAULT_DEMO_PASSWORD}` |
| Faculty | `faculty@kmit.in` | `${DEFAULT_DEMO_PASSWORD}` |
| Student | `student@kmit.in` | `${DEFAULT_DEMO_PASSWORD}` |
| Recruiter | `recruiter@amazon.com` | `${DEFAULT_DEMO_PASSWORD}` |

> Use **these** accounts to demo — they're bound to KMIT, which is fully populated. If you sign up a brand-new college through the signup form, it will (correctly) start empty.

---

## Troubleshooting

- **`'python' is not recognized`** → reinstall Python with "Add to PATH" ticked, then reopen Command Prompt.
- **`npm start` errors with `'BROWSER' is not recognized`** → that's the Unix-only script. Use `npx react-scripts start` (dev mode) or just open `http://localhost:8000` after `npm run build`.
- **Browser shows "frontend build not found"** → you opened `:8000` before building. Run `npm run build` in the `frontend` folder, then refresh.
- **API calls fail / everything is blank in dev mode** → confirm the backend window says `Uvicorn running on ... :8000`, and that `frontend/.env.local` exists with `REACT_APP_BACKEND_URL=http://localhost:8000`.
- **`pip install` is slow or fails** → run `python -m pip install --upgrade pip` first, then retry. A corporate proxy/VPN can block it; try a normal network.
- **Port 8000 already in use** → run on another port: `python -m uvicorn server:app --port 8010` and open `http://localhost:8010` (in dev mode also update `.env.local`).
- **Data looks empty** → restart the backend (it re-seeds on startup) and log in with a demo account above, not a self-registered one.
