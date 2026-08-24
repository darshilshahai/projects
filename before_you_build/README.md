# BeforeYouBuild

**BeforeYouBuild** helps founders decide whether a startup or app idea is worth building.

You describe an idea (and optional context). The product researches what already exists in the market, challenges weak assumptions, and returns a structured verdict:

```text
BUILD  |  MODIFY  |  KILL
```

The product is intentionally direct. It does not flatter founders — it attacks weak ideas and recommends a narrower wedge when the problem is real but positioning is too broad.

This repository is a full-stack MVP:

| Layer | Stack |
|-------|-------|
| Mobile app | Flutter (Dart) |
| Backend | Python, FastAPI, OpenAI Responses API |
| AI | Web search + structured outputs (Pydantic) |
| Package managers | `flutter pub`, `uv` |

There is **no database**, **no authentication**, and **no saved history** in the current MVP.

---

## Product flow

```text
Startup idea + optional context
        ↓
Live competitor research (OpenAI web search)
        ↓
AI startup analysis (structured output)
        ↓
BUILD / MODIFY / KILL verdict
        ↓
Recommended wedge + smallest useful MVP
```

The UI metaphor is **idea → analysis → decision**, not a chatbot.

---

## Repository structure

```text
before_you_build/
│
├── lib/                          # Flutter mobile app
│   ├── main.dart
│   ├── core/
│   │   ├── api_config.dart
│   │   ├── app_colors.dart
│   │   └── app_theme.dart
│   ├── models/
│   │   ├── analysis.dart
│   │   └── mock_analysis.dart    # dev-only sample data (not used in production flow)
│   ├── services/
│   │   └── api_service.dart
│   ├── screens/
│   │   └── analyze_screen.dart
│   └── widgets/
│       ├── app_header.dart
│       ├── technical_grid.dart
│       ├── section_header.dart
│       ├── idea_form.dart
│       ├── loading_analysis.dart
│       ├── verdict_header.dart
│       ├── weakness_section.dart
│       ├── wedge_section.dart
│       ├── score_section.dart
│       ├── competitor_section.dart
│       ├── differentiation_section.dart
│       ├── mvp_section.dart
│       └── idea_summary_section.dart
│
├── backend/                      # FastAPI + OpenAI pipeline
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/analyze.py
│   │   ├── core/config.py
│   │   ├── models/
│   │   │   ├── request.py
│   │   │   └── response.py
│   │   ├── prompts/
│   │   │   ├── research_prompt.py
│   │   │   └── analysis_prompt.py
│   │   └── services/
│   │       ├── competitor_research.py
│   │       └── idea_analyzer.py
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
│
├── android/                      # Flutter Android target
├── ios/                          # Flutter iOS target
├── pubspec.yaml
└── README.md
```

---

## Development phases

The project was built incrementally across six phases. Each phase added a focused slice of functionality without over-engineering.

---

### Phase 1 — Project initialization

**Goal:** Stand up the monorepo skeleton.

**What was done:**

- Created the Flutter project at the repo root (`lib/`, `pubspec.yaml`, platform folders)
- Created the Python backend under `backend/` using `uv init`
- Established the split layout: Flutter frontend + FastAPI backend in one repository

**Outcome:** Empty but runnable Flutter and Python project shells.

---

### Phase 2 — Backend scaffolding

**Goal:** Define the backend folder architecture before AI logic.

**What was done:**

- Created the FastAPI app structure:

  ```text
  app/
  ├── api/routes/analyze.py
  ├── core/config.py
  ├── models/request.py, response.py
  ├── prompts/research_prompt.py, analysis_prompt.py
  └── services/competitor_research.py, idea_analyzer.py
  ```

- Added `.env`, `.env.example`, and `.gitignore`
- Added a health endpoint stub in `app/main.py`

**Outcome:** Clean backend layout ready for implementation.

---

### Phase 3 — Backend dependencies and environment

**Goal:** Install and configure backend tooling.

**What was done:**

- Installed dependencies with `uv`:

  ```bash
  uv add "fastapi[standard]" openai python-dotenv
  ```

- Configured environment variables:

  ```env
  OPENAI_API_KEY=
  RESEARCH_MODEL=gpt-5.6-luna
  ANALYSIS_MODEL=gpt-5.6
  ```

- Pointed the IDE Python interpreter at `backend/.venv`

**Outcome:** Backend virtual environment and dependency lockfile (`uv.lock`) in place.

---

### Phase 4 — FastAPI + OpenAI backend (complete AI pipeline)

**Goal:** Build the full backend and AI pipeline — no database, no auth, no agent frameworks.

**What was done:**

#### Architecture

Two deterministic OpenAI calls (not an autonomous agent):

1. **Competitor research** — `RESEARCH_MODEL` + Responses API + `web_search`
2. **Startup analysis** — `ANALYSIS_MODEL` + structured output (Pydantic)

```text
POST /api/v1/analyze
        ↓
Validate request
        ↓
Competitor research (web search)
        ↓
Idea analysis (structured output)
        ↓
Merge verified competitor URLs
        ↓
JSON response
```

#### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/analyze` | Analyze a startup idea |

#### Request body

```json
{
  "idea": "An app that estimates calories from a meal photo.",
  "context": "Optional: target users, niche, insight..."
}
```

- `idea`: required, 10–3000 characters (trimmed)
- `context`: optional, max 3000 characters

#### Response (high level)

```json
{
  "idea_summary": "...",
  "target_user": "...",
  "problem": "...",
  "market_saturation": "LOW | MEDIUM | HIGH",
  "competitors": [
    { "name": "...", "description": "...", "url": "https://..." }
  ],
  "biggest_problem": "...",
  "differentiation": {
    "description": "...",
    "strength": "WEAK | MODERATE | STRONG"
  },
  "recommended_wedge": "...",
  "mvp": {
    "target_user": "...",
    "core_problem": "...",
    "core_feature": "...",
    "avoid_features": ["...", "..."]
  },
  "scores": {
    "problem_clarity": 0,
    "differentiation": 0,
    "opportunity": 0
  },
  "verdict": "BUILD | MODIFY | KILL",
  "confidence": 0,
  "reason": "..."
}
```

Competitor URLs come from **real web-search source metadata** — never fabricated by the analysis model.

#### Verdict rules (summary)

| Verdict | Meaning |
|---------|---------|
| `BUILD` | Worth testing with a small MVP — clear user, real problem, meaningful differentiation |
| `MODIFY` | Problem is real but positioning is too broad; a narrower wedge is recommended |
| `KILL` | Weak value, commodity AI wrapper, or existing tools already solve it well |

#### Error handling

| Status | When |
|--------|------|
| `422` | Validation failure |
| `502` | Research or OpenAI failure |
| `500` | Unexpected server error |

#### Explicitly not included

- LangChain, LangGraph, agents, vector DBs, Redis, Celery, SQLAlchemy
- Authentication, database, tests (manual testing via Swagger/curl)

**Outcome:** Production-clean backend runnable with:

```bash
cd backend
uv run fastapi dev app/main.py
```

Swagger: http://127.0.0.1:8000/docs

---

### Phase 5 — Flutter frontend (mock-driven UI)

**Goal:** Build the complete mobile UI using mocked analysis data — no live backend yet.

**What was done:**

#### Architecture

- Simple `setState()` state machine — no Bloc, Riverpod, or routing libraries
- States: `input` → `loading` → `result` → `error`

#### Folder structure

```text
lib/
├── core/api_config.dart
├── models/analysis.dart
├── services/api_service.dart      # contract prepared, not wired
├── screens/analyze_screen.dart
└── widgets/                       # one widget per result section
```

#### UX flow

```text
Enter idea → optional context → Destroy My Idea → loading → verdict + analysis → Analyze another idea
```

#### UI personality (Phase 5)

- Light, editorial, minimal design
- Strong typography, generous spacing
- Verdict accents: green (BUILD), amber (MODIFY), red (KILL)
- Primary CTA: **Destroy My Idea**
- Loading messages rotated on a timer (UI-only, not backend streaming)
- Mock data in `lib/models/mock_analysis.dart` (MODIFY verdict, Indian meal calorie scenario)

#### Dependencies

```bash
flutter pub add http url_launcher
```

**Outcome:** Polished Flutter UI testable without FastAPI running.

---

### Phase 6 — Flutter + FastAPI integration and premium UI redesign

**Goal:** Connect the app to the live backend and redesign the UI to a premium dark technical aesthetic.

**What was done:**

#### Backend integration

- Removed mock execution from the production path
- `ApiService.analyzeIdea()` calls `POST /api/v1/analyze` with a 60-second timeout
- Typed error handling: validation, research failure, server error, timeout, network
- Configurable base URL via compile-time define:

  ```bash
  flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
  ```

#### Platform networking (local dev)

| Platform | Config |
|----------|--------|
| Android emulator | `API_BASE_URL=http://10.0.2.2:8000` + debug cleartext HTTP |
| iOS simulator | `API_BASE_URL=http://127.0.0.1:8000` + `NSAllowsLocalNetworking` |
| Physical device | Mac LAN IP + `fastapi dev --host 0.0.0.0` |

#### UI redesign

Translated a premium technical / editorial reference into a mobile-native dark theme:

| Element | Implementation |
|---------|----------------|
| Background | Near-black charcoal (`#0D0E0E`) |
| Grid | Subtle engineering grid via `CustomPainter` |
| Accent | Acid lime (`#B8FF1A`) — used sparingly |
| Typography | Large bold headlines + monospace section labels |
| Layout | Report-style sections with thin dividers, not floating cards |
| Loading | 5-step analysis pipeline visual (SEARCH → VERDICT) |
| Result | AI startup teardown report hierarchy |

New shared components: `technical_grid.dart`, `app_header.dart`, `section_header.dart`, `app_colors.dart`

#### End-to-end flow (current)

```text
Flutter AnalyzeScreen
  → ApiService.analyzeIdea()
  → POST /api/v1/analyze
  → FastAPI (web research + structured analysis)
  → Analysis.fromJson()
  → Premium dark result UI
```

**Outcome:** Working end-to-end MVP with real market research and structured verdicts.

---

## Getting started

### Prerequisites

- Flutter SDK (Dart ^3.10)
- Python 3.14+
- [uv](https://github.com/astral-sh/uv) for Python dependency management
- OpenAI API key

### 1. Backend setup

```bash
cd backend

cp .env.example .env
# Edit .env and set OPENAI_API_KEY

uv sync
uv run fastapi dev app/main.py
```

Verify:

- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

For testing from a physical phone on the same Wi‑Fi network:

```bash
uv run fastapi dev app/main.py --host 0.0.0.0
```

### 2. Flutter setup

```bash
flutter pub get
flutter analyze
```

Run against the backend:

```bash
# iOS simulator / macOS
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000

# Android emulator
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Physical device (replace with your machine's LAN IP)
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000
```

---

## API reference

### `GET /health`

```json
{
  "status": "ok",
  "service": "before-you-build-api"
}
```

### `POST /api/v1/analyze`

**Request:**

```json
{
  "idea": "An AI app where users upload PDFs and ask questions about them.",
  "context": null
}
```

**Example curl:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"idea":"An app that estimates calories from a meal photo.","context":"Designed for Indian vegetarian meals and mixed thalis."}'
```

Analysis can take **30–90 seconds** (web search + two LLM calls).

---

## Mobile app states

| State | What the user sees |
|-------|---------------------|
| `input` | Idea + context form, **Destroy My Idea** CTA |
| `loading` | Analysis pipeline steps + rotating status messages |
| `result` | Verdict hero, biggest problem, wedge, scores, competitors, MVP |
| `error` | Designed error screen with **Try Again** |

---

## Design system (Phase 6)

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0D0E0E` | Page background |
| Surface | `#101111` | Input fields |
| Primary text | `#F1F1EC` | Headlines, body |
| Secondary text | `#9A9A95` | Supporting copy |
| Muted text | `#666864` | Placeholders, metadata |
| Border | `#292B29` | Dividers, outlines |
| Lime accent | `#B8FF1A` | CTA, scores, links, status |
| BUILD accent | Lime | Verdict highlight |
| MODIFY accent | `#E5A020` | Verdict highlight |
| KILL accent | `#E04545` | Verdict highlight |

---

## Production deployment

### Backend (Render)

The repo includes `render.yaml` and `backend/Dockerfile` for a single Render web service.

1. Push the repo to GitHub and connect it in [Render](https://render.com).
2. Create the web service from `render.yaml` (service name: `beforeyoubuild-api`).
3. Set the `OPENAI_API_KEY` secret in the Render dashboard (synced from `render.yaml`).
4. Deploy and confirm health:

```bash
curl https://beforeyoubuild-api.onrender.com/health
```

**Production start command** (via Dockerfile):

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key (server-side only) |
| `RESEARCH_MODEL` | Yes | e.g. `gpt-5.6-luna` |
| `ANALYSIS_MODEL` | Yes | e.g. `gpt-5.6` |
| `APP_ENV` | No | `production` in deployed environments |
| `RATE_LIMIT_PER_MINUTE` | No | Default `5` analyses/minute per client IP |

Copy `backend/.env.example` to `backend/.env` for local development. Never commit `.env`.

### Abuse protection

`POST /api/v1/analyze` is rate-limited in application code (`backend/app/middleware/rate_limit.py`):

- Default: **5 requests per minute per client IP**
- Returns **429** with: `"Too many analyses. Please wait a moment and try again."`
- **Limitation:** in-memory, single-instance only — suitable for MVP/demo; resets on restart and does not work across multiple replicas without a shared store.

### Flutter production builds

Release builds **require** an HTTPS production backend URL:

```bash
flutter build apk --release \
  --dart-define=API_BASE_URL=https://beforeyoubuild-api.onrender.com

flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://beforeyoubuild-api.onrender.com
```

On macOS, if Gradle fails with a Java version error, point `JAVA_HOME` at Android Studio's bundled JBR before building:

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
```

Without `--dart-define=API_BASE_URL=...`, release builds throw at runtime when the API is first accessed.

Debug builds fall back to `http://127.0.0.1:8000` when no URL is supplied.

---

## Known MVP limitations

- **Web search reliability** — competitor results vary by query and timing
- **Competitor/source matching** — URLs are validated against search metadata; uncertain matches become `url: null`
- **AI judgment ≠ market proof** — verdicts are model reasoning, not validated demand data
- **Scores are heuristic** — 0–100 values reflect model judgment, not objective metrics
- **No persistence** — each analysis is stateless; no history or saved reports
- **No authentication** — public API with lightweight IP rate limiting only
- **90-second client timeout** — long analyses may time out on very slow networks
- **Single-instance rate limiting** — not distributed across multiple backend replicas

---

## Manual test ideas

Use these against the live backend to sanity-check behavior:

**1. Commodity AI wrapper**

```json
{
  "idea": "An AI app where users upload PDFs and ask questions about them.",
  "context": null
}
```

Expect: strong competition, likely KILL or MODIFY, general-purpose AI tools mentioned.

**2. Crowded idea with a possible wedge**

```json
{
  "idea": "An app that estimates calories from a meal photo.",
  "context": "Designed specifically for Indian vegetarian meals and mixed thalis."
}
```

Expect: crowded market, India-specific wedge, likely MODIFY.

**3. More differentiated workflow**

```json
{
  "idea": "A tool for freelancers that reads client conversations and extracts promises, deadlines and tasks automatically.",
  "context": "Only track commitments the freelancer personally made to clients."
}
```

Expect: narrower positioning, BUILD or MODIFY depending on evidence.

**4. Error handling**

Stop the backend, submit an idea — the app should show a network error, not crash. Restart the backend and retry.

---

## What is intentionally out of scope

The following were explicitly excluded from all phases:

- Authentication and user accounts
- Database and saved analysis history
- Payments and subscriptions
- Firebase, Supabase, analytics
- LangChain, agents, streaming
- Chat UI, onboarding, settings, dark/light toggle
- Push notifications and sharing

---

## License

Private project — not published to pub.dev (`publish_to: 'none'`).
