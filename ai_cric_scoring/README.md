# Cricket Intelligence

AI-powered cricket scoring and match intelligence. This repository is a monorepo with a Flutter client and a FastAPI backend.

## Architecture summary

- **Flutter:** UI → Riverpod controller → repository → local / remote data source
- **FastAPI:** Router → service → repository → database
- Scoring uses a pure deterministic cricket engine plus an auditable event stream
- AI match analysis explains deterministic facts; the LLM never calculates official statistics

See [docs/architecture.md](docs/architecture.md) for boundaries.

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Flutter 3.38+ (Dart 3.10+)
- Docker Desktop (for PostgreSQL)

## Repository structure

```text
.
├── backend/          FastAPI application
├── frontend/         Flutter application
├── docker-compose.yml
├── docs/
└── README.md
```

## Environment configuration

Copy the backend example env file and keep real secrets out of git:

```bash
cp backend/.env.example backend/.env
```

Development values (`cricket` / `cricket_db`) are local-only. They are not production credentials.

JWT settings in `backend/.env.example` (placeholders only — never commit real secrets):

```text
JWT_SECRET_KEY=replace-me-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Flutter development API hosts are selected in `frontend/lib/app/environment.dart`:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator / desktop / web: `http://127.0.0.1:8000`

## PostgreSQL setup

From the repository root:

```bash
docker compose up -d postgres
docker compose ps
```

PostgreSQL should report `healthy`.

The Compose service publishes Postgres on host port **5433** (`5433:5432`) so it does not collide with a local PostgreSQL instance on 5432. The backend `DATABASE_URL` in `.env.example` matches that port.

Core tables: `users`, `teams`, `players`, `team_players`, `matches`, `match_teams`, `match_players`, `refresh_tokens`, plus Phase 7 scoring tables (`innings`, `scoring_events`, `deliveries`, `dismissals`, `score_snapshots`, batting/bowling stats). See [docs/architecture.md](docs/architecture.md).

## Backend setup

```bash
cd backend
uv sync
cp .env.example .env
```

### Alembic

```bash
uv run alembic upgrade head
uv run alembic current
```

This creates the Phase 2 core domain tables and the Phase 4 `refresh_tokens` table.

### Test database

Persistence tests use `cricket_test_db`, never `cricket_db`.

Fresh Compose volumes create it automatically via `docker/postgres/init`. If Postgres was already initialized, create it once:

```bash
docker exec cricket-postgres psql -U cricket -d cricket_db -c "CREATE DATABASE cricket_test_db;"
```

`TEST_DATABASE_URL` is in `backend/.env.example`.

### Running backend

```bash
uv run uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Flutter setup

```bash
cd frontend
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

### Running frontend

```bash
flutter run
```

The app shell has five destinations: Home, Matches, AI, Stats, Profile.

- Phone (`< 600` dp): Material 3 `NavigationBar`
- Tablet / wider (`≥ 600` dp): `NavigationRail`
- Appearance: Profile → System / Light / Dark
- Design system preview: Profile → Design system (`/dev/design-system`)
- Phase 1 API check: Profile → Developer → **Check API** (`GET /api/v1/health`)

### Authentication

Public routes: `/splash`, `/login`, `/register`, `/forgot-password`.

Protected shell: `/home`, `/matches`, `/ai`, `/stats`, `/profile`.

Session restore on startup reads tokens from `flutter_secure_storage`, validates with `GET /api/v1/auth/me`, and refreshes if the access token is expired. A Dio interceptor attaches `Authorization` and uses **single-flight** refresh so concurrent 401s share one refresh call. Login/register/refresh paths are never auto-refreshed.

Tokens:

```text
Access JWT     ~15 minutes   (Authorization: Bearer)
Refresh opaque ~30 days      stored hashed (SHA-256) in PostgreSQL
```

Refresh tokens rotate on every refresh. Logout revokes the server session, then clears local credentials. If logout cannot reach the API, local tokens are still cleared; the remote refresh token may remain valid until expiry.

Forgot-password UI exists but does **not** send email.

Authenticated APIs:

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Use `Authorization: Bearer <access_token>` on `/me` and future protected routes. OpenAPI at `/docs` includes the bearer scheme.

## Teams, players, and roster

Every team and player belongs to the authenticated user (`owner_user_id`). Queries are always scoped to the current user. Cross-user IDs return **404**, not 403, so resource existence is not leaked.

A player is **not** owned by a team. Roster membership is a separate `team_players` row:

```text
User
 ├── Teams
 └── Players
      └── TeamPlayer (roster membership)
```

`TeamPlayer` is the current/general roster. It is **not** a historical Playing XI. `MatchPlayer` is the match-specific snapshot.

Deactivation (`is_active = false`) is used instead of hard delete. Re-adding a removed roster member reactivates the existing row.

```http
GET    /api/v1/teams
POST   /api/v1/teams
GET    /api/v1/teams/{team_id}
PATCH  /api/v1/teams/{team_id}
GET    /api/v1/teams/{team_id}/players
POST   /api/v1/teams/{team_id}/players
DELETE /api/v1/teams/{team_id}/players/{player_id}

GET    /api/v1/players
POST   /api/v1/players
GET    /api/v1/players/{player_id}
PATCH  /api/v1/players/{player_id}
```

`DELETE` on a roster membership deactivates it (`is_active = false`, `left_at` set). It does not remove the player from the pool.

Flutter routes (authenticated, outside the bottom shell):

```text
/teams  /teams/new  /teams/:id  /teams/:id/edit  /teams/:id/roster
/players  /players/new  /players/:id  /players/:id/edit
```

Reach them from Home → Manage, or Profile → Teams / Players.

## Matches

A match is a configured contest until it is READY. Scoring starts it LIVE and can complete it.

```text
DRAFT  →  READY  →  LIVE  →  COMPLETED
```

Historical identity uses snapshots:

```text
Match
 ├── MatchTeam   (team_name_snapshot, side)
 └── MatchPlayer (display_name_snapshot, captain, keeper, batting order)
```

`TeamPlayer ≠ MatchPlayer`. Roster membership is the source of Playing XI candidates; the match stores its own XI snapshots.

```http
POST   /api/v1/matches
GET    /api/v1/matches
GET    /api/v1/matches/{match_id}
PATCH  /api/v1/matches/{match_id}
PUT    /api/v1/matches/{match_id}/teams
PUT    /api/v1/matches/{match_id}/playing-xi
PUT    /api/v1/matches/{match_id}/toss
POST   /api/v1/matches/{match_id}/ready
```

Ownership is always `created_by_user_id = current_user.id`. Cross-user access returns **404**. Incomplete drafts can be saved and resumed from Matches → Continue setup. Flutter routes:

```text
/matches  /matches/new  /matches/:id  /matches/:id/setup
```

## Live scoring (Phase 7)

Scoring is a pure function: previous match state + command + rules → new state + domain events. The engine does not touch FastAPI, SQLAlchemy, or the clock.

`scoring_events` is the audit source of truth. Deliveries, batting/bowling stats, and `score_snapshots` are projections rebuilt from events on undo.

Each mutation sends `client_event_id` (unique per match) and `base_revision`. Stale revisions return `409 SCORE_CONFLICT`. Duplicate client IDs are idempotent. The snapshot row is locked `FOR UPDATE` in the scoring transaction.

Undo appends `DELIVERY_VOIDED` and replays the innings. Rows are not deleted.

Opening players and scoring identities are **MatchPlayer** IDs, not global Player IDs. `MatchPlayerPublic` now includes `id` for that purpose.

```http
POST /api/v1/matches/{match_id}/start
GET  /api/v1/matches/{match_id}/live
POST /api/v1/matches/{match_id}/scoring/events
POST /api/v1/matches/{match_id}/scoring/select-batter
POST /api/v1/matches/{match_id}/scoring/select-bowler
POST /api/v1/matches/{match_id}/scoring/undo
POST /api/v1/matches/{match_id}/innings/{innings_id}/start
GET  /api/v1/matches/{match_id}/scoring/events
```

Example (after a READY match exists):

```bash
# Start
curl -X POST "$API/api/v1/matches/$MATCH_ID/start" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"striker_id":"...","non_striker_id":"...","bowler_id":"...","client_event_id":"..."}'

# Delivery
curl -X POST "$API/api/v1/matches/$MATCH_ID/scoring/events" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"client_event_id":"...","base_revision":1,"type":"DELIVERY","delivery":{"runs_off_bat":1}}'

# Select batter / bowler
curl -X POST "$API/api/v1/matches/$MATCH_ID/scoring/select-batter" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"client_event_id":"...","base_revision":2,"player_id":"..."}'

# Undo and live state
curl -X POST "$API/api/v1/matches/$MATCH_ID/scoring/undo" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"client_event_id":"...","base_revision":3}'

curl "$API/api/v1/matches/$MATCH_ID/live" -H "Authorization: Bearer $TOKEN"
```

Scoring tests:

```bash
cd backend
uv run pytest tests/cricket tests/test_scoring_api.py
```

The Flutter live-scoring UI is implemented in Phase 8.

## Live scoring (Phase 8)

The scorer records deliveries from Flutter. The backend engine remains the only authority for score, overs, strike, and result.

```text
/matches/:id/start     opening players (outside bottom nav)
/matches/:id/scoring   live scoring (outside bottom nav)
```

Normal runs are one tap (`0`–`6`). Wide is one tap. No-ball and other extras use compact sheets. Wickets use a dismissal sheet. New batter / new bowler selection blocks the run pad until the server says play can continue.

Each mutation sends one `client_event_id` and the current `base_revision`. Timeouts retry the same ID. `409 SCORE_CONFLICT` reloads canonical live state and does not replay the tap. Undo asks for a quick confirm, then replaces the entire live state from the server.

Phase 8 is not offline-first. A lost request keeps a pending action for retry; it does not queue deliveries locally.

```bash
cd frontend
dart format .
flutter analyze
flutter test
```

## Scorecard (Phase 9)

Scorecards are **read models** derived from Phase 7 scoring events and projections. They are never authored independently and never recalculated in Flutter.

```http
GET /api/v1/matches/{match_id}/scorecard
```

Works for READY (empty innings), LIVE, between innings, and COMPLETED matches. Other users receive `404`.

The response includes match header/result, innings totals, batting and bowling rows, extras, fall of wickets, partnerships, over summaries, and compact match facts (`highest_scorers`, `most_wickets`, boundaries, extras, largest partnerships). Names come from `MatchPlayer` snapshots.

```text
/matches/:id/scorecard   full scorecard (outside bottom nav)
```

Open from Live Scoring (`View scorecard`) or Match Detail. Pull-to-refresh reloads the canonical scorecard. Opening the route always fetches fresh data (`autoDispose`).

Scorecard tests:

```bash
cd backend
uv run pytest tests/analytics tests/test_scorecard_api.py

cd frontend
flutter test test/scorecard
```

## Match history (Phase 10)

Completed-match results are persisted by the Phase 7 scoring engine (`result_type`, `winner_match_team_id`, `margin_runs` / `margin_wickets`, `completed_at`). History never recalculates a winner.

```http
GET /api/v1/matches?scope=history
GET /api/v1/matches?scope=active
GET /api/v1/matches/{match_id}
GET /api/v1/matches/{match_id}/scorecard
```

History filters: `status`, `scope`, `format`, `team_id` (via `MatchTeam`), `search` (ILIKE on match name, venue, and **snapshot** team names), `date_from` / `date_to` (against `completed_at` for completed/history), `limit` (default 20, max 100), `offset`. Ordered by `completed_at DESC, id DESC`.

Team and player names on history and scorecards come from `MatchTeam.team_name_snapshot` and `MatchPlayer.display_name_snapshot`. Completed matches are immutable.

The Matches screen uses **Active | History**. History is server-paginated with debounced search.

```bash
cd backend
uv run pytest tests/test_match_history_api.py tests/analytics/test_result_format.py

cd frontend
flutter test test/matches
```

## AI match analysis (Phase 11)

Post-match analysis is generated only for **completed** matches the current user owns. The backend builds a compact fact package from Phase 7–10 scorecard analytics, then an `AIProvider` (OpenAI) returns structured commentary. A grounding validator rejects unknown fact IDs, players, teams, and ungrounded numbers before anything is persisted.

```text
PostgreSQL → deterministic analytics → fact package → prompt → AIProvider →
structured analysis → grounding → match_analyses → Flutter
```

```http
GET  /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis/regenerate
```

`GET` is read-only and never calls OpenAI. `POST` returns the latest saved analysis if one exists. `POST .../regenerate` creates a new versioned record. Player of the Match is an **AI recommendation**, not an official award.

Environment (placeholders only — do not commit keys):

```env
AI_ENABLED=true
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=1
```

Tests mock `AIProvider`. Optional manual evaluation:

```bash
cd backend
uv run python scripts/evaluate_match_analysis.py
```

```bash
cd backend
uv run pytest tests/ai tests/analytics/test_phases.py tests/analytics/test_key_events.py

cd frontend
flutter test test/ai_analysis
```

## Match AI chat (Phase 12)

Match chat is scoped to **one completed match** the current user owns. A question router classifies the request, resolves MatchPlayer/MatchTeam snapshot names, and answers direct statistics from deterministic facts without calling OpenAI. Analytical questions send a minimal fact context through `AIProvider`, then grounding validation. One conversation is created lazily per user+match. `client_message_id` makes retries safe.

```text
User question → router → entity resolution → deterministic facts
→ direct answer OR compact AI context → grounding → ai_messages → Flutter
```

```http
GET  /api/v1/matches/{match_id}/chat/messages
POST /api/v1/matches/{match_id}/chat/messages
```

`GET` never calls OpenAI. `POST` saves the user message first. If an analytical provider call fails, the question remains and Flutter can retry the same `client_message_id`. Ambiguous players/teams/innings return a clarification instead of guessing. Out-of-scope and missing-data questions stay in match scope and do not call OpenAI.

```bash
cd backend
uv run pytest tests/ai/test_chat_eval.py tests/ai/test_chat_entities.py tests/ai/test_chat_context.py tests/ai/test_chat_grounding.py tests/ai/test_match_chat_api.py

cd frontend
flutter test test/ai_chat
```

## Historical intelligence (Phase 13)

Cross-match stats cover **completed matches owned by the current user**. Identity is `players.id` / `teams.id`. Innings batting/bowling `player_id` columns are `match_players.id`; aggregations always join `match_players.player_id`. SQL and Python calculate official numbers. OpenAI only explains facts already computed. There is no RAG, embeddings, text-to-SQL, agents, or career materialization table.

```text
User question → HistoricalQuestionRouter → owned Player/Team resolve
→ PostgreSQL aggregates → HistoricalFactPackage
→ direct answer OR AIProvider + grounding → Flutter Stats
```

```http
GET  /api/v1/analytics/overview
GET  /api/v1/analytics/players/{player_id}
GET  /api/v1/analytics/teams/{team_id}
GET  /api/v1/analytics/leaderboards?metric=runs|wickets|batting_average|strike_rate|economy
POST /api/v1/analytics/compare/players
POST /api/v1/analytics/compare/teams
POST /api/v1/analytics/query
```

Shared filters: `format`, `date_from`, `date_to`, `team_id`, `last_n` (1–50). Empty history returns zeros, not invented numbers. Unavailable averages are `null` (Flutter shows `—`). Overview load does not call OpenAI.

Locked definitions:

- Batting innings are `innings_batting_stats` rows only (DNB is not an innings).
- Dismissals are `OUT` and `RETIRED_OUT`. `BATTING`, `NOT_OUT`, and `RETIRED_HURT` are not dismissals.
- Batting average is `SUM(runs) / dismissals` (`null` if dismissals = 0). Strike rate is `SUM(runs) / SUM(balls) * 100`.
- Economy uses a shared `balls_per_over`. Mixed 5-ball and 6-ball windows set `mixed_rules` and leave `economy` null.
- Win % is `wins / completed_matches * 100` including ties in the denominator.
- Last N for a player is that player's last N completed appearances, `completed_at DESC`. Recent means last 5 appearances.
- “This season” is a clarification; there is no season model.
- Leaderboard batting average requires ≥ 3 dismissals; economy requires ≥ 12 legal balls.

```bash
cd backend
uv run pytest tests/analytics/test_historical_math.py tests/ai/test_historical_router.py tests/ai/test_historical_entities.py tests/ai/test_historical_grounding.py tests/ai/test_historical_api.py

cd frontend
flutter test test/analytics
```

## Tests

Backend:

```bash
cd backend
uv run pytest
```

Flutter:

```bash
cd frontend
flutter test
```

## Linting

Backend:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

Flutter:

```bash
cd frontend
flutter analyze
dart format .
```

## Phase status

```text
Phase 0 ✅ Product Definition & Architecture
Phase 1 ✅ Project Setup & Development Environment
Phase 2 ✅ Backend Foundation + Database
Phase 3 ✅ Flutter Foundation + Design System
Phase 4 ✅ Authentication & User Management
Phase 5 ✅ Teams & Players
Phase 6 ✅ Match Creation & Match Configuration
Phase 7 ✅ Cricket Scoring Engine
Phase 8 ✅ Live Scoring UI
Phase 9 ✅ Scorecard & Match Statistics
Phase 10 ✅ Match Completion & History
Phase 11 ✅ AI Match Analysis
Phase 12 ✅ Match AI Chat
Phase 13 ✅ Historical Intelligence
```
