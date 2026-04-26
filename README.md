# The Forge

AI-powered résumé tailoring. Upload a base `.docx`, paste a job description, and three sequential AI agents produce a tailored résumé — with a programmatic validator enforcing forbidden edits (dates, employer names, job titles).

---

## Prerequisites

- Python 3.12+
- Node.js 22+
- PostgreSQL 15+ (local) or Docker Desktop with WSL2 integration enabled
- `uv` — `pip install uv`

---

## Local development

### 1. Clone and configure environment

```bash
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GEMINI_API_KEY
```

### 2. Set up the database

Start Postgres via Docker (recommended — creates the `forge` user and DB automatically):

```bash
docker compose up postgres -d
```

Or if running Postgres locally without Docker:

```bash
sudo -u postgres psql -c "CREATE USER forge WITH PASSWORD 'forge';"
sudo -u postgres psql -c "CREATE DATABASE forge OWNER forge;"
```

### 3. Install backend dependencies

```bash
uv sync
```

### 4. Run migrations

All commands must be run from the **project root** (where `alembic.ini` lives):

```bash
uv run alembic upgrade head
```

### 5. Install frontend dependencies

```bash
cd frontend && npm install
```

### 6. Start the dev servers

Open two terminals:

```bash
# Terminal 1 — backend
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

- Frontend: http://localhost:5173
- Backend API / Swagger docs: http://localhost:8000/docs

---

## Docker (alternative)

Requires Docker Desktop with WSL2 integration enabled.

```bash
docker compose up
```

Services:

| Service  | URL                        |
| -------- | -------------------------- |
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |
| Swagger  | http://localhost:8000/docs |
| Adminer  | http://localhost:8080      |
| Postgres | localhost:5432             |

Run migrations inside the backend container:

```bash
docker compose exec backend uv run alembic upgrade head
```

---

## Testing

Tests live in `backend/tests/` and run against a dedicated Postgres instance on port 5434 (separate from dev on 5433).

### Start the test database

```bash
make test-db-up
```

### Run the suite

```bash
make test
```

### Stop the test database

```bash
make test-db-down
```

To wipe and restart the test database (e.g. after schema changes):

```bash
make test-db-reset
```

The test suite uses real database queries — no mocks for internal code. Only external HTTP calls (Google OAuth) are intercepted with `respx`. Tables are truncated between tests, so the database persists between runs and only needs to be started once per session.

---

## Production build

Builds the Vue app and serves it as static files from FastAPI:

```bash
docker build -t the-forge .
docker run -p 8000:8000 --env-file .env the-forge
```

---

## Project structure

```
/
├── backend/
│   ├── agents/          # JD, Resume, Diff agent definitions
│   ├── domain/          # State machine, Judge validator
│   ├── database/
│   │   ├── models.py    # SQLModel table definitions
│   │   ├── session.py   # DB engine + session dependency
│   │   ├── repositories/# Repository classes per model
│   │   └── migrations/  # Alembic migrations
│   ├── routers/         # FastAPI route handlers
│   ├── services/        # Mammoth parser, python-docx writer, GCS client
│   ├── tests/           # pytest suite (repositories + routes)
│   ├── config.py        # Settings (pydantic-settings + .env)
│   └── main.py          # FastAPI app entry point
├── frontend/
│   └── src/
│       ├── views/       # Page-level Vue components
│       ├── components/  # Shared UI components
│       ├── stores/      # Pinia stores
│       └── composables/ # Reusable composition functions
├── Dockerfile           # Multi-stage: builds Vue, serves via FastAPI
├── docker-compose.yml   # Local dev stack
└── .env.example         # Required environment variables
```

---

## Environment variables

| Variable               | Default                                         | Description                |
| ---------------------- | ----------------------------------------------- | -------------------------- |
| `DATABASE_URL`         | `postgresql://forge:forge@localhost:5432/forge` | Postgres connection string |
| `SECRET_KEY`           | —                                               | Session signing key        |
| `GOOGLE_CLIENT_ID`     | —                                               | OAuth 2.0 client ID        |
| `GOOGLE_CLIENT_SECRET` | —                                               | OAuth 2.0 client secret    |
| `GOOGLE_REDIRECT_URI`  | `http://localhost:8000/auth/google/callback`    | OAuth callback URL         |
| `GCS_BUCKET`           | `the-forge-files`                               | GCS bucket name            |
| `GEMINI_API_KEY`       | —                                               | Gemini API key             |
| `FRONTEND_URL`         | `http://localhost:5173`                         | Allowed CORS origin        |
