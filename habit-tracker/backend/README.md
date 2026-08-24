# Habit Tracker API — FastAPI + Supabase + OpenAI

Backend for the Habit Tracker app. Uses **Supabase Auth** (email/password JWT), **Supabase Postgres** (via [supabase-py](https://supabase.com/docs/reference/python/introduction)), and **OpenAI** for daily real-person quotes and AI fallback manifestations.

The Next.js frontend is **not** wired yet — this API is ready for a follow-up integration pass.

---

## Features

| Area | Behavior |
|------|----------|
| Auth | Sign up / sign in / me / sign out (Supabase JWT) |
| Habits | CRUD with weekday schedule (`daysOfWeek` 0=Sun…6=Sat) |
| Entries | Upsert/clear daily status; **edit window = today + past 7 days** |
| Manifestations | User lines, **max 5**; enforced in API + DB trigger |
| Inspiration | Daily quote (real attributed quotes via OpenAI, cached) + user lines or AI-generated lines |

---

## Setup

### 1. Create a Supabase project

1. Create a project at [supabase.com](https://supabase.com).
2. **Required:** Open **SQL Editor** → paste and run the full contents of [`sql/001_schema.sql`](sql/001_schema.sql). Until this runs, habit/entry/manifestation writes will fail (tables do not exist yet).
3. **Auth → Providers → Email**: for local/dev, turn **off** “Confirm email”.
4. Copy keys from **Project Settings → API**:
   - Project URL → `SUPABASE_URL` (must be `https://….supabase.co`, not a `postgresql://` string)
   - `anon` `public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`
5. `SUPABASE_JWT_SECRET` is optional on modern Supabase projects (tokens are ES256 and verified via JWKS automatically).

### 2. Configure environment

```bash
cd backend
cp .env.example .env
```

Edit `.env`:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
```

### 3. Install & run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

---

## API overview

All protected routes require:

```
Authorization: Bearer <access_token>
```

### Auth

| Method | Path | Body |
|--------|------|------|
| POST | `/auth/signup` | `{ "email", "password" }` |
| POST | `/auth/signin` | `{ "email", "password" }` |
| POST | `/auth/signout` | — |
| GET | `/auth/me` | — |

Response (signup/signin):

```json
{
  "accessToken": "...",
  "refreshToken": "...",
  "expiresIn": 3600,
  "tokenType": "bearer",
  "user": { "id": "...", "email": "..." }
}
```

### Habits

| Method | Path | Notes |
|--------|------|-------|
| GET | `/habits?archived=false` | List |
| POST | `/habits` | `{ "name", "daysOfWeek": [0,1,2,3,4,5,6] }` |
| PATCH | `/habits/{id}` | name / daysOfWeek / archived |
| DELETE | `/habits/{id}` | Cascades entries |

### Entries

| Method | Path | Notes |
|--------|------|-------|
| GET | `/entries?from=YYYY-MM-DD&to=YYYY-MM-DD` | Range |
| PUT | `/entries` | `{ "habitId", "date", "status": "done" \| "not_done" \| null }` |

`status: null` clears the entry. Outside the edit window → `400`.

### Manifestations

| Method | Path | Notes |
|--------|------|-------|
| GET | `/manifestations` | User lines only |
| POST | `/manifestations` | `{ "text" }` — max 5 |
| PATCH | `/manifestations/{id}` | |
| DELETE | `/manifestations/{id}` | |

### Inspiration

| Method | Path | Notes |
|--------|------|-------|
| GET | `/inspiration/today` | Quote + lines |

```json
{
  "quote": { "quote": "...", "author": "...", "date": "2026-07-21" },
  "manifestations": ["...", "...", "..."],
  "source": "user" | "ai"
}
```

- **Quote:** cached in `daily_quotes` (one per calendar day, UTC). OpenAI is instructed to return a **real, attributed** quote — never invent. Hardcoded classics used if OpenAI fails.
- **Lines:** if the user has ≥1 manifestation → those (`source: "user"`). Else AI generates 3 lines, cached in `ai_manifestation_cache` for that user+day (`source: "ai"`). AI lines are **not** stored in `manifestations` and do not count toward the 5-limit.

---

## Smoke test (curl)

```bash
# Sign up
curl -s -X POST http://localhost:8000/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"secret12"}'

# Save accessToken from the response, then:
export TOKEN=eyJ...

# Create a habit
curl -s -X POST http://localhost:8000/habits \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Exercise","daysOfWeek":[0,1,2,3,4,5,6]}'

# Inspiration (uses OpenAI on first call of the day)
curl -s http://localhost:8000/inspiration/today \
  -H "Authorization: Bearer $TOKEN"
```

---

## Project structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── deps.py
│   ├── db/supabase.py
│   ├── routers/
│   ├── schemas/
│   └── services/openai_service.py
├── sql/001_schema.sql
├── requirements.txt
├── .env.example
└── README.md
```

---

## Notes for production

- Never expose `SUPABASE_SERVICE_ROLE_KEY` to the browser.
- Prefer confirming emails in production; keep confirmation off only for local testing.
- Rotate OpenAI keys if leaked; set spend limits in the OpenAI dashboard.
