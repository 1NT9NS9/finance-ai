Deployment with Docker

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


