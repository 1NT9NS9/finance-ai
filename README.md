# Financial consultant based on AI

- the user gets the opportunity to create an individual
financial portfolio based on his preferences;
- the user gets the opportunity to see the portfolio transactions
of the project;
- the user gets the opportunity to communicate with the financial
assistant based on AI;
- the user gets the opportunity to copy the transactions of profitable portfolios by subscription

<img width="817" height="677" alt="image" src="https://github.com/user-attachments/assets/875ca084-2852-434a-8d8a-13d042bd865d" />

<img width="1333" height="640" alt="image" src="https://github.com/user-attachments/assets/b932d95a-5eab-4e5d-afa5-a36963b1bb06" />


Full-stack system for collecting, analyzing, and serving financial market data (MOEX, Yahoo Finance) with technical indicators and a static JS frontend.

## What’s inside
- Backend Flask API (`backend/api`) plus data collectors, indicators, and storage orchestrated by `backend/main.py`.
- Static frontend served by Flask from `frontend/` (vanilla JS modules for dashboards, chat/AI helpers, setup page).
- Docker support via `Dockerfile` and `docker-compose.yml`; deployment notes in `deploy/README.md`.
- Local artifacts (`backend/data`, `backend/logs`, `backend/venv`) are cleaned and ignored for GitHub.

## Quick start (local Python)
1. `pip install -r backend/requirements.txt`
2. Copy `.env.example` to `.env` and fill values (API keys, `API_SECRET_KEY`, optional Gemini settings).
3. Collect data: `python backend/main.py`
4. Run API + frontend: `python -m backend.api.app` (serves `http://localhost:5000`)

## Quick start (Docker)
1. Copy `.env.example` to `.env` and set values.
2. `docker compose up --build`
3. Health check: `curl http://localhost:5000/health`

## Environment variables
- `APP_ENV` (`production`|`development`)
- `API_SECRET_KEY`, `API_KEYS`, `ADMIN_API_KEYS`
- `CORS_ORIGINS` (comma-separated, optional)
- `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BASE_URL` (optional for AI proxy)
See `.env.example` and `backend/config/settings.py` for defaults and parsing.

## Project structure
- `backend/` – collectors, indicators, storage, Flask API (`backend/README.md` has full docs)
- `frontend/` – static assets and environment helpers (`frontend/SETUP.md`, `frontend/README-Environment.md`)
- `deploy/` – Docker runbook
- `docker-compose*.yml` – multi-service config serving API + static frontend

## Notes for publishing
- Data, logs, and local virtualenv have been removed; runtime will recreate `backend/data` and `backend/logs` (placeholders tracked via `.gitkeep`).
- Do not commit real secrets. Keep `.env` local; share only `.env.example`.
- For development tips, troubleshooting, and endpoint list, see `backend/README.md`.

## The rest of the code for deployment and front-end is ready to be provided upon request.


# Deployment with Docker

1) Create a .env file (do not commit secrets)

Create `.env` in the repository root (next to `docker-compose.yml`) and set values:

```
APP_ENV=production
API_SECRET_KEY=
API_KEYS=
ADMIN_API_KEYS=
CORS_ORIGINS=
GEMINI_API_KEY=
```

2) Build and run

```
docker compose up -d --build
```

3) Verify service

```
# Health
curl -s http://localhost:5000/health

```

Notes
- Uses `Dockerfile` and `docker-compose.yml` at repo root.
- Data and logs persist via bind mounts under `backend/data` and `backend/logs`.
- Static frontend is served by Flask at `http://localhost:5000/` (e.g. `/setup.html`, `/chat.html`).
- CORS is disabled unless `CORS_ORIGINS` is set.
- Error details are hidden when `APP_ENV=production`.


