# RF Checker Frontend (Next.js)

Simple Next.js (pages router) UI for your FastAPI backend.

## Dev setup

```powershell
# From repo root
cd frontend

# Install deps
npm install

# Run dev server on http://localhost:3000
npm run dev
```

Backend dev server should run at http://localhost:8000. This frontend proxies requests via Next.js rewrites:
- `/api/*` -> `http://localhost:8000/api/*`
- `/health` -> `http://localhost:8000/health`

If you disable rewrites, add `http://localhost:3000` to `SecurityConfig.ALLOWED_ORIGINS` in the backend.

## Features
- Register, login, regenerate API key
- Manage API key in localStorage
- Submit URLs and optional Steam game name for checking

## Build & start
```powershell
npm run build; npm run start
```
