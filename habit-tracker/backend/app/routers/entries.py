from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.deps import (
    CurrentUser,
    get_current_user,
    get_db,
    parse_date,
    require_editable_date,
)
from app.schemas.entries import EntryOut, EntryUpsert

router = APIRouter(prefix="/entries", tags=["entries"])


def _row_to_entry(row: dict[str, Any]) -> EntryOut:
    created = row.get("created_at")
    created_at = None
    if isinstance(created, str):
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    elif created is not None:
        created_at = created

    entry_date = row["date"]
    if isinstance(entry_date, str):
        entry_date = parse_date(entry_date)

    return EntryOut(
        id=row["id"],
        habitId=row["habit_id"],
        date=entry_date,
        status=row["status"],
        createdAt=created_at,
    )


@router.get("", response_model=list[EntryOut])
def list_entries(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date: Optional[str] = Query(default=None, alias="to"),
):
    query = (
        db.table("habit_entries")
        .select("*")
        .eq("user_id", str(user.id))
        .order("date")
    )
    if from_date:
        query = query.gte("date", parse_date(from_date).isoformat())
    if to_date:
        query = query.lte("date", parse_date(to_date).isoformat())

    result = query.execute()
    return [_row_to_entry(r) for r in (result.data or [])]


@router.put("", response_model=Optional[EntryOut])
def upsert_entry(
    body: EntryUpsert,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
) -> Optional[EntryOut]:
    require_editable_date(body.date)

    habit = (
        db.table("habits")
        .select("id")
        .eq("id", str(body.habitId))
        .eq("user_id", str(user.id))
        .limit(1)
        .execute()
    )
    if not habit.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )

    date_str = body.date.isoformat()

    if body.status is None:
        db.table("habit_entries").delete().eq(
            "habit_id", str(body.habitId)
        ).eq("date", date_str).eq("user_id", str(user.id)).execute()
        return None

    payload = {
        "user_id": str(user.id),
        "habit_id": str(body.habitId),
        "date": date_str,
        "status": body.status,
    }
    result = (
        db.table("habit_entries")
        .upsert(payload, on_conflict="habit_id,date")
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upsert entry",
        )
    return _row_to_entry(result.data[0])
