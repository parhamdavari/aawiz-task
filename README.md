# Evaluations API

FastAPI service that proxies SnapAuth (FusionAuth) for authentication and provides CRUD endpoints for employee evaluations with cursor-based pagination and role-aware access control.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make run   # or python -m uvicorn app.main:app --reload
```

Environment variables (optional):

- `DATABASE_URL` (default `sqlite:///./app.db`)
- `SNAPAUTH_BASE_URL` (default `http://localhost:8080`)
- `SNAPAUTH_API_KEY` (used for `/auth/register` proxy)
- `SNAPAUTH_JWKS_URL`, `JWT_AUDIENCE`, `JWT_ISSUER` if your tokens require them

### Start SnapAuth locally (needed before hitting `/auth/*`)

SnapAuth has its own repo and docker-compose stack. Run it first:

```bash
git clone https://github.com/parhamdavari/snapauth-platform
cd snapauth-platform
make up   # boots Postgres + FusionAuth + SnapAuth; waits for health
```

This exposes SnapAuth on `http://localhost:8080`. Leave it running, then start this API (with `SNAPAUTH_BASE_URL` pointing to that URL if you changed the port).

### Run the server

- Because of network constraints, prefer `make run` so the API can reach SnapAuth on `localhost:8080` directly.
- If you use `make docker`, the target already injects `SNAPAUTH_BASE_URL=http://host.docker.internal:8080` and adds the host entry so the container can reach SnapAuth without extra steps (assuming SnapAuth is running on the host). For alternative setups, adjust the env var and host mapping as needed.

## Endpoints

- `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`, `/auth/logout` (proxied to SnapAuth)
- `/evaluations` CRUD with cursor pagination: `GET /evaluations?cursor=<base64_id>&limit=20`

Docs are available at `/docs` and `/redoc`.

## Docker

```bash
docker build -t evaluations-api .
docker run -p 8000:8000 --env SNAPAUTH_BASE_URL=http://localhost:8080 evaluations-api
```
