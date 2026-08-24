# Habit Tracker — Frontend

Minimal dark-mode habit tracker built with **Next.js 16**, **React 19**, **TypeScript**, and **Tailwind CSS 4**.

Data and auth are served by the FastAPI + Supabase backend in [`../backend`](../backend).

---

## Prerequisites

1. Backend running at `http://localhost:8000` (see [`../backend/README.md`](../backend/README.md))
2. Supabase schema applied and email confirmation disabled for local signup

---

## Quick start

```bash
cd frontend
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

| Script          | Description              |
|-----------------|--------------------------|
| `npm run dev`   | Development server       |
| `npm run build` | Production build         |
| `npm run start` | Run production server    |
| `npm run lint`  | ESLint                   |

---

## Environment

| Variable               | Default                   | Purpose            |
|------------------------|---------------------------|--------------------|
| `NEXT_PUBLIC_API_URL`  | `http://localhost:8000`   | FastAPI base URL   |

Only the auth token is stored in the browser (`localStorage` key `habit-tracker:auth`). Habits, entries, and manifestations live on the server.

---

## Features (API-backed)

| Screen | Behavior |
|--------|----------|
| Sign in / Sign up | `POST /auth/signin`, `/auth/signup` — password min 6 chars |
| Today | Check-in via `PUT /entries` |
| Dashboard | Matrix + contribution grids from `GET /habits` + `GET /entries` |
| Habits | CRUD via `/habits` |
| Manifestations | Max **5** lines via `/manifestations` |
| Today's focus banner | `GET /inspiration/today` (real quotes + AI fallback lines) |

Edit window for entries: **today + past 7 days** (enforced by API).

---

## Project structure

```
frontend/
├── app/                    # Routes (today, dashboard, habits, manifestations, auth)
├── components/             # UI
├── context/habit-store.tsx # Client store over API
├── lib/
│   ├── api/                # FastAPI client modules
│   ├── auth-token.ts       # Token persistence
│   ├── dates.ts / habits.ts / stats.ts
│   └── types.ts
├── .env.local.example
└── package.json
```

---

## Auth flow

1. User signs up / signs in → backend returns `accessToken`
2. Token saved in `localStorage`
3. All API calls send `Authorization: Bearer <token>`
4. On 401, session is cleared and user is redirected to `/sign-in`
5. On reload, `GET /auth/me` validates the stored token before loading data

---

## Run full stack locally

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate   # or: uv run
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```
