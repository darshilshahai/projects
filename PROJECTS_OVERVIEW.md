# AI & Full-Stack Engineering Projects — Master Overview & Resume Guide

This document provides a comprehensive technical overview of all 7 repositories in the `ai-engineering-projects` workspace, detailing their architecture, technology stack, data pipelines, key features, engineering decisions, and resume-ready summaries.

---

## 📋 Table of Contents

1. [QueryMint — AI Data Analyst (`ai-data-analyst`)](#1-querymint--ai-data-analyst-ai-data-analyst)
2. [AI Engineer Editorial Portfolio (`ai-engineer-portfolio`)](#2-ai-engineer-editorial-portfolio-ai-engineer-portfolio)
3. [Cricket Intelligence (`ai_cric_scoring`)](#3-cricket-intelligence-ai_cric_scoring)
4. [BeforeYouBuild (`before_you_build`)](#4-beforeyoubuild-before_you_build)
5. [Healthcare Fraud RAG API (`fraud-detection-rag`)](#5-healthcare-fraud-rag-api-fraud-detection-rag)
6. [Habit Tracker (`habit-tracker`)](#6-habit-tracker-habit-tracker)
7. [Northwind RAG — Smart Document Assistant (`northwind-rag`)](#7-northwind-rag--smart-document-assistant-northwind-rag)
8. [🎯 Resume Summaries & Impact Bullets](#-resume-summaries--impact-bullets)

---

## 1. QueryMint — AI Data Analyst (`ai-data-analyst`)

### Overview & Purpose
**QueryMint** is an AI-powered data analytics and business intelligence platform. It allows users to upload CSV datasets, inspect data schemas, execute natural-language queries translated into high-performance SQL via OpenAI function calling, and generate interactive data visualizations.

### Tech Stack
- **Backend Framework:** FastAPI (Python 3.12+), Pydantic v2, Uvicorn
- **Data & Query Engine:** DuckDB (in-memory & file-based high-performance analytical engine), pandas
- **AI / LLM:** OpenAI API (`gpt-4o`, `gpt-4o-mini`) with strict JSON tool calling
- **Frontend Framework:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React
- **Data Visualization:** Plotly.js / Plotly React for interactive charting
- **Testing & Evaluation:** Pytest, custom benchmarking suite (`evaluation/benchmark.json`), Playwright

### Architecture & Workflows
```text
CSV Upload → Validation & Schema Profiling → DuckDB Storage & Type Inspection
     ↓
User Query → FastAPI → OpenAI Function Calling → DuckDB SQL Execution → Dynamic Plotly Visualization
     ↓
Evaluation Harness → Accuracy, Latency & Failure Analysis Reports
```

### Key Technical Features
1. **Automated Dataset Profiling:** Inspects column data types, null percentages, row counts, and summary statistics using DuckDB native functions.
2. **AI Tool Calling & Text-to-SQL:** Generates dialect-correct SQL queries targeting DuckDB without manual SQL writing.
3. **Interactive Plotly Visualization:** Returns dynamic, responsive chart specifications (bar, line, scatter, pie) rendered seamlessly on the Next.js client.
4. **Evaluation Benchmark Suite:** Built-in benchmarking pipeline (`scripts/run_evaluation.py`) that evaluates LLM accuracy, SQL syntax execution success, latency breakdown, and failure modes across sample test cases (`evaluation/sales_eval.csv`).

---

## 2. AI Engineer Editorial Portfolio (`ai-engineer-portfolio`)

### Overview & Purpose
An editorial, brutalist dark portfolio site engineered specifically for an **AI Engineer**. It showcases technical projects, full interactive system-flow case studies, live architectural node animations, article writing, and contact integration.

### Tech Stack
- **Framework:** Next.js 15 (App Router with React Server Components by default)
- **Language:** TypeScript (strict mode)
- **Styling & Design System:** Tailwind CSS v4 + custom CSS token design system (`--bg`, `--ink`, `--acid`, `--muted`, `--line`)
- **Animation & Motion:** Framer Motion (nav slide-in, masked title reveal, live system map pipeline simulation, scroll reveals)
- **Typography:** Geist Mono (`next/font`), Helvetica display, Georgia accent italics
- **Validation & Email:** Zod schema validation (shared between client and API), Resend API for email delivery

### Architecture & Key Features
- **Editorial Brutalist Aesthetics:** Near-black (`#0a0a0a`) canvas with acid-lime accent (`#c8ff32`), paper-toned interactive Project section, and film-grain overlay.
- **Data-Driven Architecture:** All project details, experience records, article lists, and system flow diagrams are driven dynamically from structured TypeScript schemas in `src/data/`.
- **Interactive System Map Pipeline:** Animated visual pipeline simulating step-by-step data flows through AI nodes with travelling pulses and real-time status indicators.
- **Dynamic Case-Study Pages:** Individual routes (`/projects/[slug]`) rendering system flow diagrams, architecture specs, code snippets, and key technical challenges.
- **Production-Grade API & SEO:** Robust contact endpoint with rate-limiting and honeypot spam protection; automated sitemap (`sitemap.xml`), robots (`robots.txt`), Open Graph images, and JSON-LD structured metadata (`Person` & `SoftwareApplication`).

---

## 3. Cricket Intelligence (`ai_cric_scoring`)

### Overview & Purpose
**Cricket Intelligence** is an enterprise-grade full-stack cricket scoring, event auditing, and match analytics platform. It combines a pure deterministic event-sourcing scoring engine with LLM-powered match analysis and conversational historical intelligence.

### Tech Stack
- **Backend:** FastAPI (Python 3.13), SQLAlchemy, PostgreSQL, Alembic migrations, Docker
- **Frontend:** Flutter 3.38+ (Dart 3.10+), Riverpod state management, Dio HTTP client, Flutter Secure Storage
- **Authentication:** OAuth2 JWT access tokens (~15 mins) with SHA-256 hashed opaque refresh tokens (~30 days) and single-flight token rotation
- **AI / LLM:** OpenAI API (`gpt-4o-mini`) with custom factual grounding validators
- **Package Managers:** `uv` (Python), `flutter pub` (Dart)

### Architecture & System Workflows
```text
Flutter App (Scorer) → FastAPI API → Deterministic Event Engine → Postgres (scoring_events)
                                                                       ↓
                                                      Scorecards & Projections (Read Models)
                                                                       ↓
                                                Fact Package Builder → OpenAI LLM → Grounding Validator → AI Analysis
```

### Key Technical Features
1. **Event-Sourced Scoring Engine:** Pure, deterministic state machine decoupled from DB and time. `scoring_events` acts as the single source of truth; deliveries, stats, and snapshots are projections rebuilt during undo operations.
2. **Optimistic Revision Locking:** Multi-user conflict prevention using `client_event_id` idempotency keys and `base_revision` check-and-set semantics (`409 SCORE_CONFLICT`).
3. **100% Grounded AI Match Analysis:** Post-match commentary generated from deterministic fact packages. A custom grounding validator rejects any response introducing ungrounded stats or unknown entity IDs, guaranteeing zero hallucination.
4. **Context-Aware Match AI Chat & Historical Analytics:** In-match and cross-match chat routing that resolves entity names (players/teams) against snapshot data, executes SQL aggregations, and uses LLM strictly for natural-language explanations.

---

## 4. BeforeYouBuild (`before_you_build`)

### Overview & Purpose
**BeforeYouBuild** is an AI startup idea validation platform available as a cross-platform mobile application. Founders submit an app concept, and the system performs live market web research, challenges weak positioning, and returns an unvarnished verdict (`BUILD` | `MODIFY` | `KILL`).

### Tech Stack
- **Mobile Frontend:** Flutter (Dart), Custom UI with `CustomPainter` dark engineering grid layout
- **Backend API:** FastAPI (Python 3.14+), Uvicorn
- **AI Engine:** OpenAI Responses API with live `web_search` tooling + Pydantic v2 structured outputs
- **Package Management & Deployment:** `uv` (Python), Docker, Render deployment configuration (`render.yaml`)

### Technical Pipeline
```text
Founder Idea + Context → FastAPI Endpoint → OpenAI Web Search (Competitor Discovery)
                                                    ↓
                                  Verified Real URL Source Extraction
                                                    ↓
                                 Pydantic Structured Startup Analysis
                                                    ↓
                                  BUILD / MODIFY / KILL Verdict + MVP Plan
```

### Key Technical Features
1. **Live Competitor Discovery:** Conducts real-time web searches to identify existing competitors and extracts verified source URLs directly from metadata.
2. **Strict Verdict Engine:** Evaluates problem clarity, market saturation, and differentiation to categorize ideas into `BUILD`, `MODIFY` (recommending a narrower positioning wedge), or `KILL` (identifying commodity AI wrappers).
3. **Smallest Viable MVP Blueprint:** Outlines core problem, mandatory primary feature, and explicit "features to avoid".
4. **Dark Technical Mobile UI:** Near-black aesthetic (`#0D0E0E`), acid lime accents (`#B8FF1A`), multi-stage animated analysis pipeline loader, and IP-based rate limiting (5 req/min).

---

## 5. Healthcare Fraud RAG API (`fraud-detection-rag`)

### Overview & Purpose
A production-ready **Retrieval-Augmented Generation (RAG)** engine and API tailored for healthcare fraud investigation over complex medical claims, policy guidelines, and audit reports.

### Tech Stack
- **Backend:** FastAPI, Python 3.12+, Pydantic v2
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`, 384-dimensional vector space)
- **Vector Database:** ChromaDB (persistent local/embedded vector store)
- **LLM & Streaming:** OpenAI API (`gpt-4o-mini`), Server-Sent Events (SSE) streaming (`EventSource`)
- **Frontend & Verification:** Next.js (App Router), TypeScript, Tailwind CSS, Playwright benchmarking scripts

### Pipeline Architecture
```text
Document Ingestion:
  Raw Doc → TextNormalizer → Paragraph/Recursive Chunker → OverlapProcessor → SHA-256 ChunkBuilder → SentenceTransformers → ChromaDB

Question Answering:
  Question → Vector Search → Score Thresholding → Jaccard Deduplication → Context Limiter → OpenAILLM → SSE Token Stream + Citations
```

### Key Technical Features
1. **Provider-Independent Interfaces:** Decoupled base classes (`BaseEmbedder`, `BaseVectorStore`, `BaseRetriever`, `BaseLLM`) enabling effortless swapping of vector stores (Chroma, Qdrant, pgvector) or model providers.
2. **Deterministic Chunking & Idempotency:** SHA-256 chunk hashing calculated from source, strategy, content, and namespace, allowing idempotent ChromaDB upserts without duplicate records.
3. **Advanced Semantic Retrieval:** Incorporates exact whitespace/case normalization deduplication and Jaccard word-set similarity filtering to purge near-duplicate chunks before LLM context injection.
4. **Real-Time Token Streaming & Profiling:** SSE streaming endpoint delivering token-by-token answer generation alongside citation mappings, token counts, and microsecond-level latency breakdown.

---

## 6. Habit Tracker (`habit-tracker`)

### Overview & Purpose
A full-stack habit tracking and daily consistency app engineered to help users form habits using daily check-ins, monthly completion matrices, GitHub-style contribution heatmaps, and AI-driven daily mindset inspiration.

### Tech Stack
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide Icons
- **Backend API:** FastAPI (Python 3.10+), Pydantic v2
- **Database & Auth:** Supabase PostgreSQL, Supabase Auth (JWT), PL/pgSQL triggers, Row Level Security (RLS)
- **AI Integration:** OpenAI API (`gpt-4o-mini`) for attributed quote and manifestation fallback generation

### Database & System Architecture
```text
Next.js Client → REST API (FastAPI) → Supabase PostgreSQL (RLS Enforced)
                                           ├── habits
                                           ├── habit_entries (Strict 7-day edit constraint)
                                           ├── manifestations (Max 5 via DB trigger)
                                           └── daily_quotes / ai_cache (Cached OpenAI quotes)
```

### Key Technical Features
1. **Database Row Level Security (RLS):** Security enforced directly at PostgreSQL database level, isolating user habits, check-ins, and affirmations.
2. **Strict 7-Day Edit Constraint Window:** Business logic at both API and UI levels preventing historical data manipulation past a 7-day rolling window.
3. **PL/pgSQL Trigger Enforcement:** Custom database trigger (`enforce_manifestation_limit`) strictly capping personal user manifestation lines to a maximum of 5.
4. **Interactive Analytics & Heatmaps:** GitHub-style daily consistency contribution heatmaps and monthly performance grid matrix with instant optimistic status toggles (`done` | `not_done` | `cleared`).

---

## 7. Northwind RAG — Smart Document Assistant (`northwind-rag`)

### Overview & Purpose
An enterprise RAG system designed for internal company document question-answering. It features a two-gate answerability refusal architecture, cross-encoder reranking, runtime document ingestion, and full transparency over chunk scores, distances, latency, and token consumption.

### Tech Stack
- **Backend API:** FastAPI (Python 3.13+), Pydantic v2
- **Vector Engine & Reranker:** ChromaDB, `all-MiniLM-L6-v2` embeddings, `ms-marco-MiniLM-L-6-v2` Cross-Encoder reranker
- **LLM:** OpenAI API (`gpt-4o-mini`)
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **Evaluation:** Custom 14-question evaluation test suite (`eval/evaluate.py`)

### Two-Gate Refusal Architecture
```text
Question → Embed → Retrieve Top-10 Chunks
                         ↓
Gate 1: Cosine Distance Threshold (Distance > 0.65?) ──[YES]──> Instant Refusal (Zero Token Cost)
                         ↓ [NO]
             Cross-Encoder Reranking (Top 3)
                         ↓
Gate 2: System Prompt Grounding Rule ("Answer ONLY from context") ──[UNGROUNDED]──> Refusal Answer
                         ↓ [GROUNDED]
             Grounded Response + Inline Citations + Full Retrieval Diagnostics
```

### Key Technical Features
1. **Two-Gate Answerability Refusal:** Pre-LLM Gate 1 filters out-of-domain questions based on vector distance (`> 0.65`) saving API tokens, while Gate 2 system prompt rules halt hallucinated answers when facts are missing.
2. **Cross-Encoder Reranking:** Re-scores initial vector similarity results using a cross-encoder model (`ms-marco-MiniLM-L-6-v2`) to optimize context relevance.
3. **Runtime Multi-Format Document Ingestion:** Supports dynamic UI uploads of `.txt`, `.md`, and `.pdf` files (parsed via `pypdf`), instantly chunking, embedding, and indexing into ChromaDB.
4. **Comprehensive Evaluation Harness:** Built-in test script evaluating retrieval precision, gate refusal accuracy, and semantic wording sensitivity.

---

## 🎯 Resume Summaries & Impact Bullets

Use these resume-ready descriptions and impact-driven bullet points for your resume, portfolio, or LinkedIn profile.

---

### Project 1: QueryMint (`ai-data-analyst`)
**Target Roles:** AI Engineer, Full-Stack Developer, Data Engineer  
**One-Line Summary:** An AI-powered business intelligence web app converting natural language into optimized SQL queries over DuckDB with dynamic interactive visualizations.

#### Resume Bullets:
- **Architected** an AI-driven data analytics application using FastAPI, DuckDB, Next.js 15, and OpenAI tool calling, enabling non-technical users to query CSV datasets using natural language.
- **Engineered** an in-memory SQL execution pipeline leveraging DuckDB for instant schema profiling, type inspection, and sub-second analytical query performance.
- **Developed** an automated evaluation benchmark suite (`evaluation/benchmark.json`) measuring Text-to-SQL accuracy, query execution success, and response latency across sample datasets.
- **Implemented** dynamic client-side Plotly visualization rendering, automatically transforming structured LLM query results into interactive charts.

**Core Tech Stack:** FastAPI, Python, DuckDB, OpenAI API, Text-to-SQL, Next.js 15, TypeScript, Tailwind CSS, Plotly.js, Pydantic.

---

### Project 2: AI Engineer Portfolio (`ai-engineer-portfolio`)
**Target Roles:** Full-Stack AI Engineer, Frontend Engineer  
**One-Line Summary:** An editorial, high-performance portfolio application showcasing complex AI architectures via dynamic interactive system flow map simulations.

#### Resume Bullets:
- **Built** a modern editorial portfolio with Next.js 15 App Router, TypeScript, Framer Motion, and Tailwind CSS v4, featuring a custom CSS token design system and server components.
- **Created** an interactive system map visualizer animating real-time data flows through AI nodes with travelling pulses and state feedback.
- **Designed** a modular, data-driven architecture separating layout logic from content, supporting server-rendered case study pages, dynamic sitemaps, and OpenGraph metadata generation.
- **Integrated** a secure contact API endpoint using Zod schema validation, honeypot spam protection, and Resend email service integration.

**Core Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS v4, Framer Motion, Resend API, Zod, SEO Optimization.

---

### Project 3: Cricket Intelligence (`ai_cric_scoring`)
**Target Roles:** Senior AI Engineer, Full-Stack Python/Flutter Developer, Backend Engineer  
**One-Line Summary:** An enterprise full-stack cricket scoring and match analytics platform combining an event-sourced audit engine with factual LLM commentary.

#### Resume Bullets:
- **Designed** a full-stack match intelligence platform using FastAPI, PostgreSQL, Flutter (Riverpod), and OpenAI, handling real-time match scoring and historical analytics.
- **Built** a pure deterministic event-sourcing engine in Python storing an auditable log of scoring events with optimistic concurrency locking (`base_revision` & idempotency keys) to eliminate race conditions.
- **Developed** a factual LLM commentary generator with a strict grounding validation pipeline that verifies 100% of facts against raw score data, eliminating model hallucinations.
- **Implemented** OAuth2 authentication with JWT access tokens, SHA-256 hashed refresh token rotation, and single-flight refresh interceptors in Flutter.

**Core Tech Stack:** FastAPI, Python, Flutter, Dart, Riverpod, PostgreSQL, Alembic, Docker, Event Sourcing, OpenAI API, JWT Auth.

---

### Project 4: BeforeYouBuild (`before_you_build`)
**Target Roles:** Mobile AI Developer, Full-Stack Product Engineer  
**One-Line Summary:** A mobile startup validation tool leveraging live web search research and structured LLM outputs to evaluate app ideas with actionable verdicts.

#### Resume Bullets:
- **Developed** a cross-platform Flutter and FastAPI startup validation application that analyzes startup ideas against live market data.
- **Integrated** OpenAI Responses API with live web search capabilities to discover existing competitors, extracting verified source URLs directly from web metadata.
- **Enforced** strict response structure using Pydantic v2 schemas to generate `BUILD | MODIFY | KILL` verdicts, market saturation scores, and minimal viable product (MVP) blueprints.
- **Designed** a dark technical UI with custom engineering grid canvas animations, multi-step pipeline loading visuals, and IP-based rate limiting.

**Core Tech Stack:** Flutter, Dart, FastAPI, Python 3.14, OpenAI API, Live Web Search, Pydantic v2, Docker, Render.

---

### Project 5: Healthcare Fraud RAG API (`fraud-detection-rag`)
**Target Roles:** AI/RAG Engineer, Backend LLM Systems Developer  
**One-Line Summary:** An enterprise RAG API for healthcare fraud investigation featuring Sentence Transformers, ChromaDB, deduplication, and SSE token streaming.

#### Resume Bullets:
- **Architected** a production-style Healthcare Fraud RAG API using FastAPI, ChromaDB, Sentence Transformers (`all-MiniLM-L6-v2`), and OpenAI GPT-4o.
- **Engineered** provider-independent abstract interfaces (`BaseEmbedder`, `BaseVectorStore`, `BaseRetriever`, `BaseLLM`) allowing seamless swapping of AI infrastructure providers.
- **Implemented** deterministic SHA-256 chunk hashing and Jaccard similarity near-duplicate filtering, reducing redundant LLM context overhead.
- **Built** a Server-Sent Events (SSE) streaming pipeline delivering real-time answer tokens, source citation mappings, and stage-by-stage latency breakdowns.

**Core Tech Stack:** FastAPI, Python, RAG, ChromaDB, Sentence Transformers, OpenAI API, SSE Streaming, Pydantic v2, Vector Search.

---

### Project 6: Habit Tracker (`habit-tracker`)
**Target Roles:** Full-Stack Developer, Web Application Engineer  
**One-Line Summary:** A dark-mode habit tracking web app built with Next.js 16, FastAPI, Supabase PostgreSQL with RLS, and AI mindset inspiration.

#### Resume Bullets:
- **Engineered** a full-stack habit tracking application with Next.js 16 (App Router), React 19, FastAPI, and Supabase PostgreSQL.
- **Implemented** Row Level Security (RLS) policies and PL/pgSQL database triggers directly in PostgreSQL to strictly enforce data isolation and business rules.
- **Built** an interactive analytics dashboard featuring GitHub-style contribution heatmaps, monthly performance matrices, and custom weekday scheduling.
- **Integrated** OpenAI API to fetch and daily-cache attributed motivational quotes and personalized mindset affirmations.

**Core Tech Stack:** Next.js 16, React 19, TypeScript, FastAPI, Python, Supabase, PostgreSQL, Row Level Security (RLS), OpenAI API.

---

### Project 7: Northwind RAG (`northwind-rag`)
**Target Roles:** AI Research/Systems Engineer, RAG Developer  
**One-Line Summary:** A document Q&A RAG engine featuring a two-gate refusal architecture, cross-encoder reranking, and runtime multi-format document ingestion.

#### Resume Bullets:
- **Created** a retrieval-augmented document assistant using FastAPI, ChromaDB, Cross-Encoder rerankers (`ms-marco-MiniLM-L-6-v2`), and Next.js.
- **Designed** a Two-Gate Refusal Architecture combining vector distance thresholding (Gate 1) and LLM grounding rules (Gate 2) to eliminate out-of-domain hallucinations and save API tokens.
- **Implemented** runtime document ingestion for `.txt`, `.md`, and `.pdf` files with sentence-aware paragraph chunking and instant vector re-indexing.
- **Built** a 14-question automated evaluation harness measuring retrieval precision, gate refusal rates, and semantic wording sensitivity.

**Core Tech Stack:** FastAPI, Python, ChromaDB, Reranking (Cross-Encoder), RAG, OpenAI API, Next.js, TypeScript, Evaluation Harness.
