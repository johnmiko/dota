# Dota Backend (FastAPI + Postgres)

This backend fetches recent Dota games, scores them, and lets you rate matches. Persistence uses SQLAlchemy with Postgres (Railway) or falls back to local SQLite.

## Setup
- Python 3.13 (virtualenv recommended)
- Install deps:
	- `pip install -r requirements.txt`

## Local Development
- Option A: Postgres (recommended)
	1. Create `.env` with `DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>` (append `?sslmode=require` if needed).
	2. Run:
		 - `python -m venv .venv`
		 - `.\.venv\Scripts\Activate.ps1`
		 - `pip install -r requirements.txt`
		 - `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`
	3. Health: http://localhost:8000/api/health

- Option B: SQLite fallback
	- Unset `DATABASE_URL` so the app uses `sqlite:///./dota_ratings.db`.
		- PowerShell: `Remove-Item Env:DATABASE_URL`

- Quick DB check
	- `python db_ping.py` — initializes tables and runs `SELECT 1`.

## Railway Deployment (Postgres)
1. In Railway, add a **PostgreSQL** service.
2. Add a **FastAPI** service (from this repo).
3. In FastAPI Service → Variables:
	 - Set `DATABASE_URL` to reference the DB: `${{PostgreSQL.DATABASE_URL}}`
	 - If the DB exposes `POSTGRESQL_URL` instead, use that.
	 - If SSL errors occur, add `?sslmode=require` or set `PGSSLMODE=require`.
4. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. (Optional) Set `NIXPACKS_PYTHON_VERSION=3.13`.
6. Verify:
	 - Service health: `/api/health`
	 - Logs show DB connected; DB shell via `railway connect` then `SELECT 1;` and `\dt` for tables.

## Notes
- The app normalizes `postgres://` to `postgresql://` automatically.
- Uses connection pooling with `pool_pre_ping=True` for resiliency.