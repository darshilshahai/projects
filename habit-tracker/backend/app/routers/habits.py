from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.deps import CurrentUser, get_current_user, get_db
from app.db.errors import raise_supabase_error
from app.schemas.habits import HabitCreate, HabitOut, HabitUpdate

router = APIRouter(prefix="/habits", tags=["habits"])

ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]


def _validate_days(days: list[int]) -> list[int]:
    cleaned = sorted(set(days))
    if not cleaned or any(d < 0 or d > 6 for d in cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="daysOfWeek must be integers 0–6 with at least one day",
        )
    return cleaned


def _row_to_habit(row: dict[str, Any]) -> HabitOut:
    created = row.get("created_at")
    if isinstance(created, str):
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    else:
        created_at = created
    return HabitOut(
        id=row["id"],
        name=row["name"],
        daysOfWeek=row.get("days_of_week") or ALL_DAYS,
        archived=bool(row.get("archived", False)),
        createdAt=created_at,
    )


@router.get("", response_model=list[HabitOut])
def list_habits(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
    archived: Optional[bool] = Query(default=False),
):
    query = db.table("habits").select("*").eq("user_id", str(user.id))
    if archived is not None:
        query = query.eq("archived", archived)
    try:
        result = query.order("created_at").execute()
    except Exception as exc:
        raise_supabase_error(exc)
    return [_row_to_habit(r) for r in (result.data or [])]


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(
    body: HabitCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    days = _validate_days(body.daysOfWeek or ALL_DAYS)
    payload = {
        "user_id": str(user.id),
        "name": body.name.strip(),
        "days_of_week": days,
        "archived": False,
    }
    try:
        result = db.table("habits").insert(payload).execute()
    except Exception as exc:
        raise_supabase_error(exc)
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create habit",
        )
    return _row_to_habit(result.data[0])


@router.patch("/{habit_id}", response_model=HabitOut)
def update_habit(
    habit_id: UUID,
    body: HabitUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    updates: dict[str, Any] = {}
    if body.name is not None:
        updates["name"] = body.name.strip()
    if body.daysOfWeek is not None:
        updates["days_of_week"] = _validate_days(body.daysOfWeek)
    if body.archived is not None:
        updates["archived"] = body.archived

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = (
        db.table("habits")
        .update(updates)
        .eq("id", str(habit_id))
        .eq("user_id", str(user.id))
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return _row_to_habit(result.data[0])


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit_id: UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    result = (
        db.table("habits")
        .delete()
        .eq("id", str(habit_id))
        .eq("user_id", str(user.id))
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return None
