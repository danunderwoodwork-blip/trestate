---
name: Python backend in pnpm workspace
description: How the FastAPI backend is structured and run inside the Replit pnpm workspace environment
---

The TREstate backend is Python FastAPI, not Node.js. It lives at `backend/` in the workspace root.

**Run command** (in api-server artifact.toml):
- **Development** (workflow CWD = `artifacts/api-server/`): `cd ../../backend && python3 -m uvicorn ...`
- **Production** (container CWD = workspace root): `cd backend && python3 -m uvicorn ...`

These differ — the two artifact.toml entries must use different paths. Using `../../backend` in production causes `bash: cd: ../../backend: No such file or directory` and the health probe never passes.

**Why:** In dev, Replit starts each artifact workflow from inside its own artifact directory. In production autoscale containers, the CWD is the workspace root.

**Python packages:** Installed via `installLanguagePackages({ language: "python", packages: [...] })` — do NOT use `pip install` or `pip3 install` directly (NixOS blocks system-level pip installs). Packages land in `.pythonlibs/bin/`.

**Database:** SQLite by default (`sqlite:///./trestate.db` relative to `backend/`). Tables are created on startup via `Base.metadata.create_all(bind=engine)` in `backend/app/main.py`.

**Why:** The original Vercel project used FastAPI+SQLAlchemy which is too complex to rewrite in Express. The api-server artifact.toml was repurposed to run uvicorn instead of Node.js.

**How to apply:** When touching the Python backend, run from `backend/` directory. To add Python packages, use `installLanguagePackages`. To restart the backend, use `WorkflowsRestart({ name: "artifacts/api-server: API Server" })`.
