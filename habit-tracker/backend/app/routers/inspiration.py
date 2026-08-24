from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from supabase import Client

from app.db.supabase import get_service_client
from app.deps import CurrentUser, get_current_user, get_db, today_utc
from app.schemas.inspiration import InspirationOut, QuoteOut
from app.services.openai_service import (
    generate_manifestation_lines,
    generate_real_quote,
)

router = APIRouter(prefix="/inspiration", tags=["inspiration"])


def _get_or_create_daily_quote() -> QuoteOut:
    today = today_utc()
    date_str = today.isoformat()
    service = get_service_client()

    existing = (
        service.table("daily_quotes")
        .select("*")
        .eq("date", date_str)
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        return QuoteOut(
            quote=row["quote"],
            author=row["author"],
            date=date_str,
        )

    day_of_year = today.timetuple().tm_yday
    generated = generate_real_quote(day_of_year)
    service.table("daily_quotes").upsert(
        {
            "date": date_str,
            "quote": generated["quote"],
            "author": generated["author"],
        }
    ).execute()

    return QuoteOut(
        quote=generated["quote"],
        author=generated["author"],
        date=date_str,
    )


def _get_ai_manifestations(user: CurrentUser) -> list[str]:
    today = today_utc().isoformat()
    service = get_service_client()

    cached = (
        service.table("ai_manifestation_cache")
        .select("lines")
        .eq("user_id", str(user.id))
        .eq("date", today)
        .limit(1)
        .execute()
    )
    if cached.data:
        lines = cached.data[0].get("lines") or []
        if isinstance(lines, list) and lines:
            return [str(x) for x in lines]

    lines = generate_manifestation_lines()
    service.table("ai_manifestation_cache").upsert(
        {
            "user_id": str(user.id),
            "date": today,
            "lines": lines,
        }
    ).execute()
    return lines


@router.get("/today", response_model=InspirationOut)
def inspiration_today(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    quote = _get_or_create_daily_quote()

    user_lines = (
        db.table("manifestations")
        .select("text")
        .eq("user_id", str(user.id))
        .order("created_at")
        .execute()
    )
    texts = [r["text"] for r in (user_lines.data or []) if r.get("text")]

    if texts:
        return InspirationOut(
            quote=quote,
            manifestations=texts,
            source="user",
        )

    ai_lines = _get_ai_manifestations(user)
    return InspirationOut(
        quote=quote,
        manifestations=ai_lines,
        source="ai",
    )
