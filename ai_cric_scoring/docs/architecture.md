# Architecture

Cricket Intelligence is a monorepo with a Flutter client and a FastAPI backend.

## Request flow

**Flutter:** UI → Riverpod controller → use case → repository → local / remote data source

**Backend:** Router → service → repository → database

Widgets must not call APIs or databases directly. Route handlers must not run SQL.

## Boundaries reserved for later phases

- `backend/app/cricket/` — deterministic scoring engine (implemented; not FastAPI)
- `backend/app/ai/` — provider-abstracted match intelligence (OpenAI first)
- `frontend/lib/core/sync/` — offline event queue and synchronization
- `frontend/lib/core/storage/` — Drift/SQLite and secure storage

## Domain schema (Phase 2)

```text
User
 ├── Team
 │    └── TeamPlayer ── Player
 │
 └── Match
      ├── MatchTeam ── Team
      └── MatchPlayer ── Player
```

`TeamPlayer` is current roster membership. `MatchPlayer` / `MatchTeam` are historical snapshots for a specific match. A player can change teams without rewriting old scorecards.

## Phase 2 decisions

- **IDs:** UUID v4 primary keys (`uuid.uuid4` + PostgreSQL `gen_random_uuid()`).
- **Ownership:** `teams.owner_user_id`, `players.owner_user_id`, `matches.created_by_user_id`. Private user workspace, not organizations.
- **Transactions:** repositories and services `flush` only; they never commit. `get_db` commits at the request boundary after a successful handler. Tests override `get_db` and roll back an outer transaction.
- **Snapshots:** `match_teams.team_name_snapshot` and `match_players.display_name_snapshot` preserve names if a team or player is renamed.
- **Enums:** native PostgreSQL enums for stable cricket vocabulary (role, styles, match format/status/side). Format is descriptive; `overs_per_innings` and `balls_per_over` are authoritative.
- **Deletion:** `is_active` on users, teams, players, and roster rows. No generic soft-delete. Foreign keys to history use `RESTRICT`; match children use `CASCADE`.
- **Email uniqueness:** unique index on `lower(email)` (no CITEXT).
- **Player identity:** a single `name` field (community cricket names do not fit first/last splits).
- **Test database:** `cricket_test_db` on the same Postgres instance. Never run destructive tests against `cricket_db`.

## Phase 3 — Flutter foundation

The Flutter client now has a reusable Material 3 design system and a persistent navigation shell. Placeholder screens prove theme, layout, and routing. They do not implement product features.

### Theme tokens

Semantic tokens live in `frontend/lib/core/theme/`:

- `AppColors` — graphite/off-white surfaces and electric lime (`#B7FF1A`)
- `AppSurfaces` / `CricketColors` — `ThemeExtension`s with light and dark variants, including grid, muted text, and scoring accents
- `AppTypography` — Space Grotesk, Instrument Serif (identity italic), IBM Plex Mono (technical labels), tabular scores
- `AppSpacing` — 4 / 8 / 12 / 16 / 24 / 32 / 48
- `AppRadius` — 4 / 8 / 12 / pill
- `AppShadows` — lime glow on dark CTAs only; light mode stays crisp
- `AppBreakpoints` — compact `< 600`, medium `600–1024`, expanded `> 1024`
- `AppMotion` — 150 / 200 / 250 ms

Widgets consume `Theme.of(context)` and extensions, not scattered hex values.

### Material 3

`useMaterial3: true`. Light and dark `ColorScheme`s are authored (not inverted). Dark mode layers `background → surface → surfaceElevated`. Theme mode is a Riverpod `Notifier` (`system` / `light` / `dark`) and is not persisted yet.

### Navigation

`GoRouter` `StatefulShellRoute.indexedStack` preserves tab state:

```text
/home  /matches  /ai  /stats  /profile
```

Compact widths use `NavigationBar`. Medium and expanded widths use `NavigationRail`. Content is centered with a max width on tablet/desktop.

Future `/matches/:id/scoring` stays **outside** this shell.

Auth routes `/splash`, `/login`, `/register`, `/forgot-password` are also outside the shell. GoRouter redirects:

```text
initializing or restore failure  → /splash
unauthenticated + protected      → /login
authenticated + auth/splash      → /home
authenticated + protected        → allowed
```

Initializing is not treated as logged out, so Login does not flash during session restore.

### Reusable UI

`frontend/lib/core/widgets/` includes page layout, cards, stats, status badges, buttons, text fields, empty/error/loading states, and responsive helpers. Team/player list tiles and role badges are shared here for later match selection.

## Phase 4 — Authentication

```text
Flutter widget
  → AuthController (Riverpod)
  → AuthRepository
  → AuthRemoteDataSource / AuthLocalDataSource
  → Dio + AuthInterceptor
  → FastAPI Auth router
  → AuthService
  → UserRepository / RefreshTokenRepository
  → PostgreSQL
```

### Password hashing

Argon2id via `pwdlib[argon2]` (`PasswordHash.recommended()`). Passwords are never logged or returned. Policy: 8–128 characters. Email is trimmed and lowercased; uniqueness remains `lower(email)` in PostgreSQL.

### Access tokens

Short-lived JWT (`HS256`). Claims: `sub` (user UUID), `type=access`, `iat`, `exp`, `jti`. Default lifetime 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`). Protected routes use `get_current_user()` which verifies signature, expiry, `type=access`, and `user.is_active`.

### Refresh tokens

Opaque `secrets.token_urlsafe(48)` values. PostgreSQL stores **SHA-256 hex**, never the raw token. Table `refresh_tokens`: `id`, `user_id`, `token_hash` (unique), `expires_at`, `revoked_at`, `created_at`, `last_used_at`, `user_agent`. Indexes on `user_id` and `expires_at`. Default lifetime 30 days.

### Rotation and reuse

Each refresh revokes the presented session and inserts a replacement in one transaction. Reusing a rotated/revoked token returns `SESSION_REVOKED` (401). Logout sets `revoked_at`.

### Flutter session

`flutter_secure_storage` holds access and refresh tokens. Startup: no refresh token → unauthenticated; otherwise `/me`, then refresh on 401. Network errors during restore do **not** clear credentials; splash shows retry. Invalid refresh clears tokens and shows login.

The Dio interceptor attaches `Authorization`, skips `/login` `/register` `/refresh`, and **single-flights** refresh so concurrent 401s share one rotation. Refresh recursion is impossible because those paths are skipped and retried requests set `retried`.

### Rate limiting

Not implemented in-process. In-memory limiters are not enough for horizontally scaled production. Production rate limiting is deferred to Phase 17.

## Phase 5 — Teams & Players

```text
User
 ├── Teams          (owner_user_id)
 └── Players        (owner_user_id)
      └── TeamPlayer  (roster membership: team_id + player_id)
```

Player remains independent of Team. There is no `players.team_id`. A player can exist before assignment, appear on multiple teams over time, and keep historical match snapshots later without rewriting the player row.

### TeamPlayer ≠ MatchPlayer

- **TeamPlayer** — current/general roster. Add/remove is activation (`is_active`) plus optional `left_at`. Unique `(team_id, player_id)`. Re-adding reactivates the same row.
- **MatchPlayer** — historical participation in a specific match. Do not use TeamPlayer as Playing XI history.

### Ownership

Every list/get/update/roster call is `WHERE id = … AND owner_user_id = current_user.id` (repository methods such as `get_by_id_for_owner`). Another user's UUID returns **404** (`TEAM_NOT_FOUND` / `PLAYER_NOT_FOUND`). Adding a player to a roster requires both the team and the player to belong to the current user.

### Deactivation

Teams, players, and roster rows use `is_active`. Phase 5 does not hard-delete these records. Deactivating a team does not deactivate its players. An inactive player cannot be newly added to a roster until reactivated.

### Flutter

`features/teams/` and `features/players/` follow Screen → Riverpod → Repository → Remote Data Source → Dio. Shared tiles live in `core/widgets/` for later match selectors. Routes sit outside the bottom shell so Home/Matches/AI/Stats/Profile stay unchanged.

## Phase 6 — Match creation & configuration

Phase 6 configures a match. It does not score it.

### Lifecycle

```text
DRAFT  →  READY
```

DRAFT allows incomplete setup (teams without an XI, no toss, etc.). READY requires:

- two distinct owned active teams
- valid format, overs (1–50), balls per over
- `players_per_team` (2–11, default 11)
- equal Playing XI sizes matching that count
- one captain and one wicketkeeper per side, both in the XI
- toss winner (a match team) and decision (`BAT` / `BOWL`)

Editing a READY match that becomes incomplete returns it to DRAFT. LIVE / COMPLETED / ABANDONED / CANCELLED configuration is rejected (`MATCH_NOT_EDITABLE`). LIVE is not created in this phase.

### Two-team model

Exactly two sides: `TEAM_A` and `TEAM_B`. Same team twice is rejected. Changing a side drops that side’s MatchPlayers. Toss is cleared when teams change.

### Snapshots

- **MatchTeam** stores `team_name_snapshot` and `team_short_name_snapshot` at selection time.
- **MatchPlayer** stores `display_name_snapshot`, captain/keeper flags, and `batting_position`.

Canonical Team/Player rows may change later; historical match display uses snapshots. Before READY, selected players must still be on the current active roster.

**TeamPlayer ≠ MatchPlayer.** TeamPlayer is roster membership. MatchPlayer is this match’s XI.

### Toss

Stored on `Match` as `toss_winner_match_team_id` + `toss_decision`. First batting side is derived later from winner + decision. No innings rows are created here.

### Formats

UI: T10 / T20 / ODI / Custom. Named formats lock default overs (10 / 20 / 50); stored `overs_per_innings` and `balls_per_over` remain authoritative. TEST is stored in the enum but not offered in the creation UI.

### Flutter

`features/matches/` uses a single `MatchSetupController` for wizard state. The backend draft is canonical: each step persists, and Continue setup reloads `GET /matches/{id}`. List lives in the shell; `/matches/new`, `/matches/:id`, and `/matches/:id/setup` are outside the shell.

## Phase 7 — Cricket scoring engine

Scoring is a pure deterministic function. FastAPI, SQLAlchemy, PostgreSQL, Flutter, OpenAI, the system clock, and randomness are outside the engine.

```text
ScoreCommand → Pure Cricket Engine → Domain Result → ScoringService → Event + Projections → PostgreSQL
```

### Source of truth

- **`scoring_events`**: append-only audit stream (who, when, client event id, payload, void flag). Sequence numbers are per innings, not timestamps.
- **Projections** (same transaction): `deliveries`, `dismissals`, `innings_batting_stats`, `innings_bowling_stats`, `score_snapshots`.
- Live reads use the snapshot. Undo voids the latest user event and **replays** the innings to replace projections. Deliveries are marked `is_voided`, never deleted.

### Identity

Scoring refers to **MatchPlayer** UUIDs (`striker_id` on start is `match_players.id`). Global `Player` rows are not the historical participant identity.

### Idempotency and concurrency

- `UNIQUE (match_id, client_event_id)` where `client_event_id IS NOT NULL`.
- Optimistic `base_revision` vs `score_snapshots.revision`. Mismatch → `409 SCORE_CONFLICT` with `current_revision`.
- `SELECT … FOR UPDATE` on the current innings snapshot (and match row on start) so two writers cannot both accept the same revision.
- One active scorer per match for MVP. No merge algorithm.

### Undo

Append `DELIVERY_VOIDED` targeting the latest non-voided user event (`DELIVERY_RECORDED`, batter/bowler select, retirement). Replay remaining events. Do not edit history in place.

### Rules implemented (limited-overs MVP)

- Team runs = bat + wides + no-balls + byes + leg-byes + penalties.
- Bowler conceded = bat + wides + no-balls. Byes/leg-byes excluded. **Penalties are team-only** (`penalty_runs_charged_to_bowler=False`).
- Legal ball: not wide and not no-ball. Overs stored as integer `legal_balls`; display `completed.remainder`.
- `maximum_wickets = players_per_team - 1`. Configurable `balls_per_over`.
- Bowler over limit: `max(1, ceil(overs_per_innings / 5))`. Consecutive overs forbidden.
- Maidens: completed over with zero **bowler-conceded** runs (byes do not prevent a maiden).
- Strike: odd running runs swap; legal ball completing the over swaps again. Wides use `wides - 1` as running runs. Catch crossing is ignored; the incoming batter takes the dismissed batter’s end (modern/simple MVP).
- No-ball wickets: run out / obstructing / hit the ball twice only. Wide: not bowled/LBW/caught/hit the ball twice.
- Retired hurt is not a team wicket. Retired out is a team wicket, not bowler-credited.
- First innings end creates a `NOT_STARTED` second innings with `target = first_total + 1`. Chase complete immediately when `score >= target`. Tie if scores equal. Win by runs or remaining wickets. No Super Over.

### APIs

Thin router → `ScoringService`. Flutter live scoring (Phase 8) is the only client of these APIs.

```http
POST /api/v1/matches/{id}/start
GET  /api/v1/matches/{id}/live
POST /api/v1/matches/{id}/scoring/events
POST /api/v1/matches/{id}/scoring/select-batter
POST /api/v1/matches/{id}/scoring/select-bowler
POST /api/v1/matches/{id}/scoring/undo
POST /api/v1/matches/{id}/innings/{id}/start
GET  /api/v1/matches/{id}/scoring/events
```

## Phase 8 — Live scoring UI

Flutter does **not** calculate authoritative cricket state. Buttons emit facts (`runs_off_bat`, extras, dismissal). The Phase 7 engine returns `LiveMatchState`; Riverpod replaces local state with that response.

```text
Scoring controls
  → LiveScoringController
  → ScoringRepository
  → FastAPI ScoringService
  → deterministic engine
  → canonical LiveMatchState
  → Flutter
```

### Reliability

- One scoring mutation in flight. Controls lock until the response returns.
- Each logical action gets one `client_event_id`. Timeouts retry the **same** payload and ID. 400/409 are never retried.
- `base_revision` is taken from the last canonical state. The client never increments revision itself.
- `409 SCORE_CONFLICT` reloads `GET /live` and does **not** replay the tap.
- Uncertain network outcomes keep a pending action and offer Retry / Refresh. This is not offline scoring (Phase 14).
- Undo calls the server and replaces the entire live state.

### Navigation

`/matches/:id/start` and `/matches/:id/scoring` are authenticated and **outside** the Home / Matches / AI / Stats / Profile shell.

### Read-model additions

Live state now includes `balls_remaining`, `available_batters`, `available_bowlers`, and `chase_target` so Flutter does not recreate over-limit, batter-availability, or first-innings target rules. Engine behavior is unchanged.

## Phase 9 — Scorecard & match statistics

Scorecard data is derived from deterministic scoring state. It is never authored independently.

```text
scoring_events (audit)
+ deliveries / dismissals / batting / bowling projections
+ innings + score_snapshots.state_json
        ↓
ScorecardService (ownership-safe assembly)
        ↓
structured MatchScorecardResponse
        ↓
Flutter scorecard (presentation only)
```

There are no authoritative `batting_scorecard` / `bowling_scorecard` tables. Historical reconstruction remains possible from scoring events and deliveries.

### Deterministic sources

| Section | Source |
| --- | --- |
| Innings totals, FoW, maidens | Phase 7 projections / `InningsState` |
| Batting / bowling rows | `innings_batting_stats` / `innings_bowling_stats` |
| Names | `MatchPlayer.display_name_snapshot` |
| Dismissal text | `DismissalFormatter` (`app/analytics/dismissals.py`) |
| Extras | `calculate_extras()` from non-voided deliveries |
| Partnerships | `build_partnerships()` from ordered non-voided deliveries |
| Over summaries | `build_over_summaries()` using Phase 7 `over_label` |
| Overs / RR / SR / economy | Phase 7 `format_overs`, `run_rate`, `strike_rate`, `economy` |

Voided deliveries are excluded. Retired hurt is not a wicket and does not appear in FoW. Flutter does not recalculate score, overs, strike rate, economy, or the winner.

### API

```http
GET /api/v1/matches/{match_id}/scorecard
```

Protected. Cross-user access returns `404`. READY matches return `innings: []`.

### Flutter

`/matches/:id/scorecard` sits outside the bottom-nav shell. `matchScorecardProvider` is `autoDispose`, so returning from live scoring always reloads.

## Phase 10 — Match completion & history

Completed matches are historically stable. Phase 10 does not recalculate results.

```text
Scoring Engine
→ innings / match complete
→ Match.result_* + completed_at
→ paginated history query
→ Flutter Active | History
```

### Immutability

`LIVE`, `COMPLETED`, `ABANDONED`, and `CANCELLED` cannot change teams, Playing XI, toss, or format. Scoring after `COMPLETED` returns `409 MATCH_COMPLETE`. There is no completed-match delete and no historical editing.

`CANCELLED` / `ABANDONED` exist on the status enum but have no dedicated API in this phase.

### Result identity

Structured fields on `matches` are authoritative:

- `result_type`: `WON` | `TIED`
- `winner_match_team_id` → `MatchTeam` (historical snapshot), null on a tie
- `margin_runs` / `margin_wickets`
- `completed_at` set once

Display text is derived by `format_result()` (`Weekend Warriors won by 12 runs`, `Match tied`). Flutter does not invent a winner.

Wicket margins use `players_per_team - 1`, not a hard-coded 10.

### History query

`GET /api/v1/matches` is the history endpoint. `scope=history` is `status=COMPLETED`. `scope=active` is `LIVE`, `READY`, `DRAFT` (LIVE first).

Search is PostgreSQL `ILIKE` on match name, venue, and `MatchTeam.team_name_snapshot`. `team_id` filters through `MatchTeam`. Completed date filters use `completed_at`. Pagination is `limit`/`offset` (default 20, max 100) with `total` from `COUNT(*)`. Order: `completed_at DESC NULLS LAST, id DESC`.

List rows use innings `ScoreSnapshot` totals in one batched query. They do not include Playing XI, deliveries, or scoring events.

Index added: `ix_matches_created_by_status_completed_at`.

Every query is scoped to `created_by_user_id`. Other users receive empty lists or `404`.

### Flutter

History lives in `features/matches/`. `MatchHistoryController` owns pagination, debounced search (400ms), generation-token races, and filter reset. Completed Match Detail reuses `/matches/:id` and opens the Phase 9 scorecard. Career stats, vector search, and Redis are out of scope.

## Phase 11 — AI match analysis

The LLM explains facts. It does not calculate official cricket statistics.

```text
Deterministic Match Data
→ Analytics (scorecard, phases, key events)
→ Fact Package
→ Context Builder
→ Prompt Builder
→ AIProvider
→ OpenAI
→ Structured Analysis
→ Grounding Validator
→ Persistence (match_analyses)
→ Flutter
```

### ADRs

- **LLM never calculates official stats.** Numbers come from Phases 7–10 (`ScorecardService`, partnerships, FoW, over summaries, analytical phases, key-event heuristics).
- **OpenAI behind `AIProvider`.** Only `OpenAIProvider` imports the OpenAI SDK. Services depend on the protocol.
- **Structured AI output.** Pydantic `StructuredMatchAnalysis` with `fact_ids`, `match_player_id`, and `match_team_id`. No free-form markdown API.
- **Fact package.** Compact JSON context: metadata, result, batting/bowling tables, partnerships, FoW, over summaries, analytical phases, key-event candidates, POTM candidates. Not the full ball stream.
- **Prompt versioning.** `prompt_version = match_analysis_v1`, `analysis_version = v1`, `facts_version = scorecard_v1`.
- **Grounding validation.** Unknown fact IDs, foreign player/team IDs, impossible winners, and ungrounded numbers are rejected. Invalid output is not persisted.
- **Persisted analysis.** `match_analyses` stores JSONB commentary plus token/latency metadata. Multiple generations are kept; GET returns the latest.
- **No RAG / vector DB / agents / LangChain.** One structured provider call is enough.
- **Explicit generation.** Opening a completed match does not call OpenAI. The user generates or regenerates on purpose.

### Analytical phases

Application-level segments, not official playing conditions:

- Standard T20 (20 overs): Powerplay / Middle / Death (labelled analytical)
- Standard ODI (50): Opening 1–10 / Middle 11–40 / Closing 41–50
- Standard T10 (10): Opening 1–3 / Middle 4–7 / Closing 8–10
- Custom and other lengths: first 30% / middle 40% / last 30% as Opening / Middle / Closing Phase — never official Powerplay

### Key-event heuristics

- Wicket cluster: 2+ wickets within 12 legal balls
- Collapse: 3 wickets for ≤ 20 runs in a consecutive FoW sequence
- Top 3 scoring overs and top wicket overs
- Top 3 partnerships
- Chase acceleration / stall from later vs earlier RR

### API

```http
GET  /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis
POST /api/v1/matches/{match_id}/analysis/regenerate
```

Owner-only. Completed matches only. GET never calls the provider.

### Flutter

`features/ai_analysis/` is separate from `features/ai_chat/`. `/matches/:id/analysis` sits outside the shell. Completed Match Detail shows Generate / View AI analysis. Player of the Match is labelled an AI recommendation.

## Phase 12 — Match AI chat

Match chat answers natural-language questions about **one completed match**. The LLM does not know the match; the backend retrieves deterministic facts.

```text
User Question
→ Question Router
→ Entity Resolution
→ Deterministic Fact Retrieval
→ Direct Answer OR AI Context
→ AIProvider
→ Grounding Validation
→ Persistence
→ Flutter
```

### ADRs

- **One-match scope.** Conversations belong to one user + one completed match. No cross-match, career, or live chat.
- **Deterministic answers when possible.** Who won, top scorer, extras, largest partnership, over-range totals, and named batting figures do not call OpenAI.
- **AI only for interpretation.** Why-result, turning points, "how did they bat", subjective best spell, and extras impact use `AIProvider` with compact context.
- **Question routing.** `MatchQuestionRouter` uses lightweight rules. No LLM classifier and no text-to-SQL.
- **Entity resolution.** Players and teams resolve against MatchPlayer/MatchTeam snapshots. Ambiguous names clarify; pronouns use last resolved entity.
- **Bounded conversation context.** Prompts include at most the last 8 messages plus the current question facts. Pending clarification is stored on the conversation.
- **Fact references.** Analytical answers cite `fact_ids`. `ChatGroundingValidator` rejects unknown facts, players, teams, and ungrounded numbers.
- **No RAG / vector DB / agents / LangChain / text-to-SQL.** Predefined query functions only.
- **Retry-safe `client_message_id`.** Unique per conversation. Timeouts do not duplicate the user message. User questions persist if generation fails.
- **Explicit generation / one request at a time.** Flutter disables send while a response is in flight. No streaming, so grounding can run before display.

### API

```http
GET  /api/v1/matches/{match_id}/chat/messages
POST /api/v1/matches/{match_id}/chat/messages
```

Owner-only. Completed matches only. One conversation per user/match, created on first question.

### Flutter

`/matches/:id/chat` is outside the shell. Completed Match Detail has **Ask about this match**. Empty chat shows suggested questions. Clarifications are tappable. Analytical answers show evidence rows.

## Phase 13 — Historical intelligence

Cross-match stats for completed matches owned by the current user. The LLM never calculates official statistics.

```text
User Question
→ Historical Question Router
→ Entity + Scope Resolution
→ PostgreSQL / deterministic analytics
→ Historical Fact Package
→ Direct answer OR grounded LLM explanation
→ Flutter Stats
```

### Statistical definitions

- Aggregate by `players.id` and `teams.id`. `innings_batting_stats.player_id` / `innings_bowling_stats.player_id` are `match_players.id`; always join `match_players.player_id`.
- Player matches: Playing XI appearances (`MatchPlayer.is_playing`).
- Batting innings: rows in `innings_batting_stats` only. DNB is not an innings.
- Dismissals: `OUT`, `RETIRED_OUT`. Not dismissals: `BATTING`, `NOT_OUT`, `RETIRED_HURT`.
- Batting average: `SUM(runs) / dismissals`. Zero dismissals → `null`.
- Strike rate: `SUM(runs) / SUM(balls_faced) * 100`.
- Highest score: max innings runs; `*` when that innings is not a dismissal.
- Bowling wickets: `innings_bowling_stats.wickets` (run-outs excluded).
- Bowling average: `SUM(runs_conceded) / wickets` when wickets > 0, else `null`.
- Economy: conventional formula only when every match in scope shares `balls_per_over`. Mixed rules → `economy = null`, expose `runs_per_legal_ball`.
- Best bowling: most wickets, then fewest runs conceded.
- Win %: `wins / completed_matches * 100` including ties in the denominator. Ties are neither wins nor losses.
- Last N (player): last N completed appearances, `completed_at DESC`, after format/date/team filters. `last_n` clamped 1–50.
- Recent: last 5 appearances. Copy says “in the last 5 matches…”.
- This season: clarification; no season model.
- Leaderboard qualification: batting average ≥ 3 dismissals; economy ≥ 12 legal balls. Detail screens still show raw sample size.
- Compare last N: each player’s own last N appearances (possibly different match sets).
- Chase/defend: innings 1 = defending, innings 2 = chasing.
- Team innings totals: `score_snapshots.total_runs` (includes extras).

### ADRs

- **SQL is the source of truth.** Averages, totals, economy, win %, and rankings are calculated in PostgreSQL/Python. OpenAI only explains supplied facts.
- **Player/Team IDs for aggregation.** Stats screens display current names. Snapshots are for per-match form rows only.
- **Owner-scoped completed matches.** DRAFT/READY/LIVE are excluded. Inactive players/teams remain in history. Foreign IDs return safe 404s.
- **Direct vs AI.** Totals, averages, highest, win %, last-N form, and head-to-head skip OpenAI. Form change, chasing, and death-over interpretation use `historical_intelligence_v1` after backend deltas.
- **No RAG / vector DB / agents / LangChain / text-to-SQL / career tables.** No `player_career_stats` materialization.
- **Historical chat is not match chat.** Do not persist into `ai_conversations`. Do not route through `MatchQuestionRouter`.
- **Grounding.** `HistoricalGroundingValidator` rejects unknown `fact_ids` and IDs outside the current scope.

### API

```http
GET  /api/v1/analytics/overview
GET  /api/v1/analytics/players/{player_id}
GET  /api/v1/analytics/teams/{team_id}
GET  /api/v1/analytics/leaderboards?metric=runs|wickets|batting_average|strike_rate|economy
POST /api/v1/analytics/compare/players
POST /api/v1/analytics/compare/teams
POST /api/v1/analytics/query
```

### Flutter

`/stats` is the shell hub. Player, team, compare, and ask routes are full-screen. Flutter formats repository values; it does not compute averages, economy, or win %. Unavailable values render as `—`. Ask AI is not a ChatGPT transcript: suggestions, evidence, and clarification chips.



