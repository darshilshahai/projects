from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.deps import CurrentUser, get_current_user, get_db
from app.db.errors import raise_supabase_error
from app.schemas.manifestations import (
    ManifestationCreate,
    ManifestationOut,
    ManifestationUpdate,
)

router = APIRouter(prefix="/manifestations", tags=["manifestations"])

MAX_MANIFESTATIONS = 5


def _row_to_manifestation(row: dict[str, Any]) -> ManifestationOut:
    created = row.get("created_at")
    if isinstance(created, str):
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    else:
        created_at = created
    return ManifestationOut(
        id=row["id"],
        text=row["text"],
        createdAt=created_at,
    )


@router.get("", response_model=list[ManifestationOut])
def list_manifestations(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    try:
        result = (
            db.table("manifestations")
            .select("*")
            .eq("user_id", str(user.id))
            .order("created_at")
            .execute()
        )
    except Exception as exc:
        raise_supabase_error(exc)
    return [_row_to_manifestation(r) for r in (result.data or [])]


@router.post(
    "",
    response_model=ManifestationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_manifestation(
    body: ManifestationCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    try:
        count_result = (
            db.table("manifestations")
            .select("id", count="exact")
            .eq("user_id", str(user.id))
            .execute()
        )
    except Exception as exc:
        raise_supabase_error(exc)

    count = count_result.count if count_result.count is not None else len(
        count_result.data or []
    )
    if count >= MAX_MANIFESTATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_MANIFESTATIONS} manifestation lines allowed",
        )

    payload = {
        "user_id": str(user.id),
        "text": body.text.strip(),
    }
    try:
        result = db.table("manifestations").insert(payload).execute()
    except Exception as exc:
        message = str(exc)
        if "Maximum of 5" in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum of {MAX_MANIFESTATIONS} manifestation lines allowed",
            ) from exc
        raise_supabase_error(exc)

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create manifestation",
        )
    return _row_to_manifestation(result.data[0])


@router.patch("/{manifestation_id}", response_model=ManifestationOut)
def update_manifestation(
    manifestation_id: UUID,
    body: ManifestationUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    try:
        result = (
            db.table("manifestations")
            .update({"text": body.text.strip()})
            .eq("id", str(manifestation_id))
            .eq("user_id", str(user.id))
            .execute()
        )
    except Exception as exc:
        raise_supabase_error(exc)
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manifestation not found",
        )
    return _row_to_manifestation(result.data[0])


@router.delete("/{manifestation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manifestation(
    manifestation_id: UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    try:
        result = (
            db.table("manifestations")
            .delete()
            .eq("id", str(manifestation_id))
            .eq("user_id", str(user.id))
            .execute()
        )
    except Exception as exc:
        raise_supabase_error(exc)
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manifestation not found",
        )
    return None
