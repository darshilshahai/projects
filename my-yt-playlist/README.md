# 📺 YouTube Playlist Manager — Full-Stack Web Application

A modern, high-performance full-stack web application designed for saving, organizing, searching, and managing YouTube video playlists. Built with a production **FastAPI (Python 3.12)** backend and a **React 19 + Vite 8 + Tailwind CSS v4** frontend.

---

## 🌟 Key Features

* ⚡ **Automated YouTube Metadata Ingestion**: Paste any YouTube link (standard watch URL, short link `youtu.be`, Shorts `/shorts/`, or embed link) to automatically extract title, channel name, video duration, and 16:9 thumbnail via YouTube's oEmbed API.
* ⏱️ **Smart Quick Queue ("What to watch in X minutes?")**: Filter unwatched saved videos based on available free time (5 Mins, 15 Mins, 30 Mins).
* 📌 **Timestamped Video Notes**: Take educational notes attached to specific video timestamps (e.g. `04:15 - Key architectural pattern`).
* 📁 **Custom Collections (Playlists)**: Group videos into topic-specific folders with real-time video count badges.
* 🏷️ **Tag Cloud & Filtering**: Categorize videos using normalized, lightweight hashtags (`#fastapi`, `#tutorial`, `#react`).
* 🔍 **Debounced Full-Text Search & Pagination**: Search across video titles, channel names, and custom notes with server-side offset pagination.
* 🔐 **Secure JWT Authentication with RTR**: Argon2id password hashing, short-lived JWT Access Tokens (15 mins), and long-lived Refresh Tokens (7 days) with automatic Refresh Token Rotation (RTR).
* 📱 **Touch-First Mobile Ergonomics**: Built with 44px minimum tap targets, CSS safe area inset padding (`safe-area-inset-bottom`), and mobile navigation drawers.
* 🚀 **High Performance & Accessibility**: `React.lazy()` route code splitting (-22% bundle footprint), WAI-ARIA modal roles, and global keyboard shortcuts (`Cmd+K` / `Ctrl+K` / `Cmd+N`).

---

## 🛠️ Technology Stack

### Backend
* **Language & Framework**: Python 3.12, FastAPI 0.115+
* **Database & ORM**: PostgreSQL 16, AsyncPG, SQLAlchemy 2.0 (Async ORM)
* **Database Migrations**: Alembic
* **Security & Auth**: Argon2id (`pwdlib`), PyJWT (Access + Refresh Token Rotation)
* **Testing**: Pytest (24/24 passing unit & integration tests)
* **Containerization**: Multi-stage `Dockerfile`, `docker-compose.yml`

### Frontend
* **Core & Build Tool**: React 19, Vite 8, JavaScript (ES6+)
* **Styling**: Tailwind CSS v4 (`@tailwindcss/vite`), HSL design tokens
* **State & Data Fetching**: TanStack Query (`@tanstack/react-query` v5), Axios
* **Routing**: React Router v6 with `React.lazy()` route code splitting
* **Icons**: Lucide React

---

## 📁 Repository Structure

```text
my-yt-playlist/
├── README.md                      # Top-level repository documentation
├── backend/                       # FastAPI Python Backend Service
│   ├── app/
│   │   ├── api/                   # API Routers (auth, users, videos, collections, tags)
│   │   ├── core/                  # Security, JWT tokens, config, database session
│   │   ├── models/                # SQLAlchemy 2.0 Async DB Models
│   │   ├── schemas/               # Pydantic V2 Request & Response schemas
│   │   └── services/              # YouTube metadata extraction service
│   ├── alembic/                   # Database async migrations
│   ├── tests/                     # 24/24 Passing Pytest Unit & Integration tests
│   ├── Dockerfile                 # Multi-stage Docker build file
│   ├── docker-compose.yml         # Container orchestrator linking FastAPI & PostgreSQL
│   ├── pyproject.toml             # Python dependencies & tool configs
│   └── PROJECT_DOCUMENTATION.md   # Detailed backend technical specifications
└── frontend/                      # React 19 + Vite 8 Frontend Application
    ├── src/
    │   ├── api/                   # Axios API modules (auth, videos, collections, tags)
    │   ├── components/            # Reusable UI components (VideoCard, QuickQueue, FilterBar, Modals)
    │   ├── contexts/              # AuthContext session state & token management
    │   ├── layouts/               # Header, Sidebar, MobileNav app shell layout
    │   ├── pages/                 # Lazy-loaded page views (Dashboard, Library, Favourites, etc.)
    │   └── routes/                # Protected/Guest Route guarding & Code-split router
    ├── index.html                 # Main HTML entrypoint
    ├── vite.config.ts             # Vite 8 config with Tailwind v4 & proxy rules
    └── package.json               # Node.js dependencies
```

---

## 🚀 Quick Start & Local Setup

### Prerequisites
* **Python**: 3.12 or higher
* **Node.js**: 18.0 or higher
* **PostgreSQL**: 16.0 or Docker

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/my-yt-playlist.git
cd my-yt-playlist
```

---

### Step 2: Backend Setup (FastAPI)

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment configuration:
   ```bash
   cp .env.example .env
   ```
5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
6. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   * **Backend API Base**: `http://localhost:8000/api/v1`
   * **Swagger Interactive Docs**: `http://localhost:8000/docs`

---

### Step 3: Frontend Setup (React + Vite)

1. Open a new terminal tab and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   * **Frontend Web Application**: `http://localhost:5173`

---

### Step 4: Run via Docker Compose (Optional)

To launch both FastAPI and PostgreSQL 16 in isolated containers:
```bash
cd backend
docker-compose up --build
```

---

## 🧪 Testing & Build Verification

### Running Backend Unit & Integration Tests
```bash
cd backend
source .venv/bin/activate
pytest
```
* **Result**: **24/24 passing unit & integration tests** in 1.77s.

### Verifying Frontend Production Build
```bash
cd frontend
npm run build
```
* **Result**: `dist/` production assets generated cleanly in 190ms with zero errors.

---

## 🔗 Key API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user account | ❌ No |
| `POST` | `/api/v1/auth/login` | Login and receive JWT access + refresh tokens | ❌ No |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token for a new access token | ❌ No |
| `GET` | `/api/v1/users/me` | Fetch authenticated user profile | ✅ Yes |
| `POST` | `/api/v1/videos` | Save YouTube URL & auto-extract metadata | ✅ Yes |
| `GET` | `/api/v1/videos` | List saved videos with search, filter, and pagination | ✅ Yes |
| `GET` | `/api/v1/videos/quick-queue` | Smart Quick Queue by max duration seconds | ✅ Yes |
| `PATCH` | `/api/v1/videos/{id}` | Update video status, favourite, or watch later | ✅ Yes |
| `POST` | `/api/v1/videos/{id}/notes` | Add timestamped video note | ✅ Yes |
| `GET` | `/api/v1/collections` | List custom video collections | ✅ Yes |
| `GET` | `/api/v1/tags` | List tag cloud keywords | ✅ Yes |

---

## 📄 License & Attribution

This project is open-source and available under the **MIT License**.
