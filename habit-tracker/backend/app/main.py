from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, entries, habits, inspiration, manifestations


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Habit Tracker API",
        description=(
            "FastAPI backend with Supabase Auth/Postgres and OpenAI inspiration"
        ),
        version="1.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth.router)
    application.include_router(habits.router)
    application.include_router(entries.router)
    application.include_router(manifestations.router)
    application.include_router(inspiration.router)

    @application.get("/health")
    def health():
        return {"status": "ok"}

    return application


app = create_app()
