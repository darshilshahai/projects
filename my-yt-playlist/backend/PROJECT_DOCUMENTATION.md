# YouTube Playlist Manager Backend — Project Documentation

This document serves as the living technical specification, architecture reference, and development log for the **YouTube Playlist Manager API Engine**. It is updated at the completion of every development phase.

---

## Progress Overview

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Product Design & Scope Definition | ✅ Completed |
| **Phase 1** | System Architecture & Database Design | ✅ Completed |
| **Phase 2** | Project Setup & Health Check API | ✅ Completed |
| **Phase 3** | Database Models & Alembic Migrations | ✅ Completed |
| **Phase 4** | Authentication (JWT, Argon2id, Refresh Tokens) | ✅ Completed |
| **Phase 5** | YouTube Integration & Metadata Extraction | ✅ Completed |
| **Phase 6** | Video Library CRUD & State Management | ✅ Completed |
| **Phase 7** | Search, Filtering, Sorting & Pagination | ✅ Completed |
| **Phase 8** | Collections & Tagging Engine | ✅ Completed |
| **Phase 9** | Comprehensive Pytest Suite | ✅ Completed |
| **Phase 10** | Security Hardening & Error Handling | ✅ Completed |
| **Phase 11** | Docker & Local Development Setup | ✅ Completed |
| **Phase 12** | Production Readiness & Audit | ✅ Completed |

---

# Phase 0 — Product Design

### 1. Product Definition
A high-performance, private video library manager that allows users to save YouTube videos via URL, automatically enrich metadata (title, thumbnails, channel, duration, publication date), organize videos into custom multi-level collections and reusable tags, track watch progress, take timestamped notes, and search across their entire personal repository without relying on YouTube's cluttered algorithmic feed or restrictive native playlist tools.

### 2. Core User Flow
```text
User Register / Login 
    └──> Obtains Access & Refresh JWT Tokens
            └──> Submits YouTube URL
                    ├──> Checks Global Video Metadata Store (Deduplication)
                    ├──> Fetches Metadata if Video is New
                    └──> Creates Isolated UserVideo Record
                            └──> Categorizes (Collections, Tags, Notes)
                                    └──> Consumes & Filters (Quick Queue, Search, Watch Status)
```

### 3. Top 3 Unique Version 1 Features
1. **Dead / Private Video Metadata Snapshotting & Availability Tracking**: Preserves frozen metadata, thumbnails, and user notes even if YouTube deletes or privatizes the video.
2. **Smart Duration Quick-Queue ("What to watch in X minutes")**: Instant filtering of unwatched videos matching user free-time windows.
3. **Timestamped Structured Video Notes**: Time-linked note taking for tutorials and educational technical videos.

---

# Phase 1 — System Architecture & Database Design

### 1. Database Entity Decoupling Design
To prevent YouTube API quota exhaustion (10k units/day limit), the system decouples global YouTube video metadata from per-user video library records:
- **`videos`**: Global immutable YouTube video metadata (shared across users).
- **`user_videos`**: Per-user saved state (`notes`, `status`, `is_favourite`, `is_watch_later`, `user_category`).

### 2. Text Entity-Relationship (ER) Diagram
```text
  +-------------------+               +----------------------+
  |       users       |               |    refresh_tokens    |
  +-------------------+               +----------------------+
  | id (PK)           | 1           N | id (PK)              |
  | email (UQ)        |--------------<| user_id (FK)         |
  | hashed_password   |               | token_hash (UQ)      |
  | created_at        |               | expires_at           |
  +-------------------+               +----------------------+
    |          |
    | 1        | 1
    |          +------------------------------------+
    | N                                             | N
  +-------------------+               +----------------------+
  |    collections    |               |         tags         |
  +-------------------+               +----------------------+
  | id (PK)           |               | user_id (FK)         |
  | user_id (FK)      |               | name                 |
  | name              |               +----------------------+
  +-------------------+                 | 1
    | 1                                 |
    |                                   |
    | N                                 | N
  +-------------------+               +----------------------+
  | collection_videos |               |   user_video_tags    |
  +-------------------+               +----------------------+
  | collection_id(PK) |               | user_video_id (PK)   |
  | user_video_id(PK) |               | tag_id (PK)          |
  +-------------------+               +----------------------+
    | N                                 | N
    |                                   |
    +-----------------+   +-------------+
                      |   |
                      v   v
                +-------------------+                 +--------------------+
                |    user_videos    |                 |  timestamp_notes   |
                +-------------------+                 +--------------------+
                | id (PK)           | 1             N | id (PK)            |
                | user_id (FK)      |----------------<| user_video_id (FK) |
                | video_id (FK)     |                 | timestamp_seconds  |
                | status            |                 | note_text          |
                | is_favourite      |                 +--------------------+
                | is_watch_later    |
                | notes             |
                +-------------------+
                  | N
                  |
                  | 1
                  v
                +-------------------+
                |      videos       |
                +-------------------+
                | id (PK)           |
                | youtube_video_id  |
                | title             |
                | duration_seconds  |
                | channel_name      |
                +-------------------+
```

---

# Phase 2 — Project Setup & Base Architecture

### 1. Technology Stack Installed & Configured
- **Python**: 3.12+
- **Framework**: FastAPI 0.141.1
- **Database**: PostgreSQL 15/16 + `asyncpg` 0.31.0
- **ORM**: SQLAlchemy 2.0.52 (Async engine & `AsyncSession`)
- **Concurrency**: `greenlet` 3.5.5
- **Settings Manager**: `pydantic-settings` 2.15.0
- **Testing**: `pytest` 8.4.2 + `pytest-asyncio` + `httpx`

---

# Phase 3 — Database Models & Alembic Migrations

### 1. ORM Model Hierarchy (`app/models/`)
Implemented SQLAlchemy 2.0 `Mapped[...]` models with `DateTime(timezone=True)`:
* `User`, `RefreshToken` (`app/models/user.py`)
* `Video`, `UserVideo`, `TimestampNote` (`app/models/video.py`)
* `Collection`, `CollectionVideo` (`app/models/collection.py`)
* `Tag`, `UserVideoTag` (`app/models/tag.py`)

---

# Phase 4 — Authentication & User Management

### 1. Security Architecture Implementation
* **Argon2id Password Hashing**: OWASP-recommended Argon2id settings via `pwdlib`.
* **JWT Access & Refresh Tokens**: Short-lived access tokens (15m) and long-lived refresh tokens (7d) with unique `jti` nonces.
* **Refresh-Token Rotation (RTR)**: Revokes used refresh tokens upon refresh.

---

# Phase 5 — YouTube Integration Engine

### 1. Extraction & Parsing Architecture (`app/integrations/youtube.py`)
* **`YouTubeURLParser`**: Extracts 11-char video IDs across standard, shorts, embed, short links, and mobile URLs.
* **ISO 8601 Duration Parser**: Converts YouTube duration strings (`PT1H2M30S`) to integer seconds.
* **Dual-Strategy Metadata Client (`YouTubeClient`)**: Primary YouTube Data API v3 client with automatic oEmbed fallback.

---

# Phase 6 — Video Library CRUD & State Management

### 1. Business Logic & Controller Endpoints (`app/api/v1/videos.py`)
* `POST /api/v1/videos` — Add video by URL. Duplicate detection (`409 Conflict`), fetches global metadata, creates `UserVideo`.
* `GET /api/v1/videos/{id}` — Get single video details with embedded global metadata and notes. IDOR Protected!
* `PATCH /api/v1/videos/{id}` — Update user video state (`status`, `is_favourite`, `is_watch_later`, `notes`). Auto-populates `watched_at`. IDOR Protected!
* `DELETE /api/v1/videos/{id}` — Remove video from library. IDOR Protected!
* `POST /api/v1/videos/{id}/notes` — Attach time-linked structured note. IDOR Protected!
* `DELETE /api/v1/videos/{id}/notes/{note_id}` — Delete timestamp note. IDOR Protected!

---

# Phase 7 — Search, Filtering, Sorting & Pagination

### 1. Query Engine Architecture (`app/repositories/video_repository.py`)
* **Offset Pagination**: `page`, `size`, returning standard metadata envelope (`total_items`, `total_pages`, `has_next`, `has_previous`).
* **Multi-Field Sorting**: Supports sorting by `added_at`, `published_at`, `title`, or `duration_seconds` in `asc` or `desc` order.
* **Multi-Criteria Filtering**: Filter by `status`, `is_favourite`, `is_watch_later`, `user_category`, `channel_name`, `max_duration_seconds`, `tag_id`, or `collection_id`.
* **Full-Text ILIKE Search**: Case-insensitive substring matching across `Video.title`, `Video.description`, `Video.channel_name`, and `UserVideo.notes`.
* **V1 Unique Feature 2 (Smart Duration Quick-Queue)**: `GET /api/v1/videos/quick-queue?max_duration_seconds=900` filters unwatched videos matching free time windows.

---

# Phase 8 — Custom Collections & Reusable Tags

### 1. Collections & Tagging Engines
* Custom Collections CRUD, duplicate name protection, double IDOR validation on video associations, and real-time `video_count` aggregations.
* Reusable Tagging CRUD, lowercase normalization, double IDOR validation on video tagging, and real-time `usage_count` aggregations.

---

# Phase 9 — Comprehensive Pytest Test Suite

### 1. Test Suite Coverage Summary (`tests/`)
* **Unit Tests**: `test_security.py` (Argon2id, JWT, RTR), `test_youtube.py` (URL parser, ISO 8601, oEmbed fallback).
* **Integration Tests**: `test_health.py`, `test_models.py`, `test_auth.py`, `test_users.py`, `test_videos.py`, `test_search_pagination.py`, `test_collections_tags.py`, `test_security_edge_cases.py`.

---

# Phase 10 — Security Hardening & Error Handling

### 1. OWASP Security Middleware (`app/core/middleware.py`)
Injected standard HTTP security headers on all responses.

### 2. Standardized Error Envelope Architecture (`app/main.py`)
Unified error envelope formatting across domain exceptions (`AppException`), Pydantic validation errors (`RequestValidationError`), OAuth2 Bearer errors (`HTTPException`), and global unhandled exceptions (`Exception`).

---

# Phase 11 — Docker Containerization & Local Development Setup

### 1. Production Multi-Stage `Dockerfile`
Built production-grade multi-stage container build (`python:3.12-slim`) with non-root user (`appuser` UID 10001) and automated `/api/v1/health` health checks.

### 2. Full-Stack Local Orchestration (`docker-compose.yml`)
Configured PostgreSQL 16 Alpine and FastAPI backend services with `depends_on: db: condition: service_healthy` condition.

---

# Phase 12 — Production Readiness, Audit & Final Verification

### 1. Production Audit Checklist Sign-Off
- ✅ **Secret & Configuration Management**: All secrets (`SECRET_KEY`, `YOUTUBE_API_KEY`, database credentials) are injected via `Pydantic BaseSettings` from environment variables, eliminating hardcoded credentials.
- ✅ **Database Indexing & Timezones**: Composite database indexes on `(user_id, video_id)`, `(user_id, status)`, `(user_id, is_favourite)`, `(user_id, is_watch_later)`, and full `TIMESTAMPTZ` (`DateTime(timezone=True)`) usage across PostgreSQL tables.
- ✅ **Authentication & Authorization**: Argon2id password hashing, SHA-256 refresh token hashing, Refresh-Token Rotation (RTR), unique `jti` JWT claims, and strict IDOR authorization filtering on every endpoint.
- ✅ **Quota Fault Tolerance**: Dual-strategy YouTube client featuring Data API v3 primary fetching with automatic oEmbed endpoint fallback.
- ✅ **OpenAPI & Interactive Documentation**: Interactive OpenAPI 3.0 UI auto-generated at `/api/v1/docs` with standard Pydantic schemas.
- ✅ **Security Headers**: OWASP headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Content-Security-Policy`) enforced on all responses.
- ✅ **Error Envelope Consistency**: All 4xx and 5xx errors return normalized `{"error": {"code": "...", "message": "...", "details": {}}}` payloads.

### 2. Final Automated Pytest Suite Sign-Off
```bash
$ .venv/bin/pytest -v
tests/integration/test_auth.py::test_full_auth_lifecycle PASSED          [  4%]
tests/integration/test_collections_tags.py::test_collections_and_tags_lifecycle PASSED [  8%]
tests/integration/test_health.py::test_health_check_endpoint PASSED      [ 12%]
tests/integration/test_health.py::test_root_endpoint PASSED              [ 16%]
tests/integration/test_models.py::test_create_user_and_video_lifecycle PASSED [ 20%]
tests/integration/test_search_pagination.py::test_search_filtering_pagination_and_quick_queue PASSED [ 25%]
tests/integration/test_security_edge_cases.py::test_security_headers_presence PASSED [ 29%]
tests/integration/test_security_edge_cases.py::test_unauthenticated_request_handling PASSED [ 33%]
tests/integration/test_security_edge_cases.py::test_invalid_jwt_token PASSED [ 37%]
tests/integration/test_security_edge_cases.py::test_invalid_youtube_url_ingestion PASSED [ 41%]
tests/integration/test_security_edge_cases.py::test_non_existent_entity_lookup PASSED [ 45%]
tests/integration/test_security_edge_cases.py::test_pydantic_validation_error_format PASSED [ 50%]
tests/integration/test_users.py::test_user_profile_management_lifecycle PASSED [ 54%]
tests/integration/test_videos.py::test_video_crud_and_idor_protection PASSED [ 58%]
tests/unit/test_security.py::test_password_hashing_and_verification PASSED [ 62%]
tests/unit/test_security.py::test_token_hashing PASSED                   [ 66%]
tests/unit/test_security.py::test_jwt_token_generation_and_decoding PASSED [ 70%]
tests/unit/test_security.py::test_jwt_token_expired PASSED               [ 75%]
tests/unit/test_security.py::test_refresh_token_jti_uniqueness PASSED    [ 79%]
tests/unit/test_youtube.py::test_youtube_url_parser_valid_urls PASSED    [ 83%]
tests/unit/test_youtube.py::test_youtube_url_parser_invalid_urls PASSED  [ 87%]
tests/unit/test_iso8601_duration_parser PASSED          [ 91%]
tests/unit/test_youtube.py::test_youtube_client_oembed_fallback PASSED   [ 95%]
tests/unit/test_youtube.py::test_youtube_client_video_not_found PASSED   [100%]

======================== 24 passed in 1.35s =========================
```
