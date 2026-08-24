# Cricket Intelligence API

FastAPI backend for the Cricket Intelligence app.

## Setup

```bash
cd backend
uv sync
cp .env.example .env
```

PostgreSQL must be running (from the repository root):

```bash
docker compose up -d postgres
```

Postgres is published on host port **5433** to avoid clashing with a local PostgreSQL on 5432.

## Database migrations

```bash
uv run alembic upgrade head
uv run alembic current
```

This applies the core domain schema (`users`, `teams`, `players`, `team_players`, `matches`, `match_teams`, `match_players`), `refresh_tokens`, scoring tables (`innings`, `scoring_events`, `deliveries`, `dismissals`, `score_snapshots`, batting/bowling stats), `match_analyses`, `ai_conversations`, `ai_messages`, and historical analytics indexes. There is no `player_career_stats` table.

Tests use a separate database, `cricket_test_db`. Create it once if the Compose volume already existed before the init script was added:

```bash
docker exec cricket-postgres psql -U cricket -d cricket_db -c "CREATE DATABASE cricket_test_db;"
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

Auth:

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Protected routes expect `Authorization: Bearer <access_token>`. Use a real `JWT_SECRET_KEY` outside local development.

Scoring (owner-only, MatchPlayer IDs):

```http
POST /api/v1/matches/{match_id}/start
GET  /api/v1/matches/{match_id}/live
POST /api/v1/matches/{match_id}/scoring/events
POST /api/v1/matches/{match_id}/scoring/select-batter
POST /api/v1/matches/{match_id}/scoring/select-bowler
POST /api/v1/matches/{match_id}/scoring/undo
POST /api/v1/matches/{match_id}/innings/{innings_id}/start
GET  /api/v1/matches/{match_id}/scoring/events
GET  /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis/regenerate
GET  /api/v1/matches/{match_id}/chat/messages
POST /api/v1/matches/{match_id}/chat/messages
GET  /api/v1/analytics/overview
GET  /api/v1/analytics/players/{player_id}
GET  /api/v1/analytics/teams/{team_id}
GET  /api/v1/analytics/leaderboards
POST /api/v1/analytics/compare/players
POST /api/v1/analytics/compare/teams
POST /api/v1/analytics/query
```

AI analysis and match chat are owner-only and completed-match-only. Direct statistical chat answers do not call OpenAI. Historical analytics (`/api/v1/analytics`) aggregate completed matches for the current user; `POST /query` calls OpenAI only for interpretation after SQL facts are computed. Tests mock `AIProvider`.

## Tests

```bash
uv run pytest
```

## Lint and types

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```
