from __future__ import annotations

from supabase import Client, create_client

from app.config import get_settings


def get_anon_client() -> Client:
    """Client using the anon key (auth + RLS as anonymous / with user JWT)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_service_client() -> Client:
    """Service-role client bypasses RLS — use for shared caches only."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_user_client(access_token: str) -> Client:
    """
    Anon client authenticated as the user so RLS policies apply.
    Sets the PostgREST Authorization header to the user's access token.
    """
    client = get_anon_client()
    client.postgrest.auth(access_token)
    return client
