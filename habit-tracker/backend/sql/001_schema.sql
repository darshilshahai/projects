-- Habit Tracker schema for Supabase Postgres
-- Run this in the Supabase SQL Editor (Dashboard → SQL → New query)

-- Extensions
create extension if not exists "pgcrypto";

-- Habits
create table if not exists public.habits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null check (char_length(trim(name)) > 0),
  days_of_week int[] not null default array[0,1,2,3,4,5,6],
  archived boolean not null default false,
  created_at timestamptz not null default now(),
  constraint habits_days_of_week_valid check (
    days_of_week <@ array[0,1,2,3,4,5,6]
    and cardinality(days_of_week) >= 1
  )
);

create index if not exists habits_user_id_idx on public.habits (user_id);

-- Habit entries (daily check-ins)
create table if not exists public.habit_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  habit_id uuid not null references public.habits (id) on delete cascade,
  date date not null,
  status text not null check (status in ('done', 'not_done')),
  created_at timestamptz not null default now(),
  unique (habit_id, date)
);

create index if not exists habit_entries_user_date_idx
  on public.habit_entries (user_id, date);
create index if not exists habit_entries_habit_id_idx
  on public.habit_entries (habit_id);

-- User manifestation lines (max 5 enforced in API + trigger)
create table if not exists public.manifestations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  text text not null check (char_length(trim(text)) > 0 and char_length(text) <= 160),
  created_at timestamptz not null default now()
);

create index if not exists manifestations_user_id_idx
  on public.manifestations (user_id);

create or replace function public.enforce_manifestation_limit()
returns trigger
language plpgsql
as $$
begin
  if (
    select count(*) from public.manifestations where user_id = new.user_id
  ) >= 5 then
    raise exception 'Maximum of 5 manifestation lines allowed';
  end if;
  return new;
end;
$$;

drop trigger if exists manifestations_max_five on public.manifestations;
create trigger manifestations_max_five
  before insert on public.manifestations
  for each row
  execute function public.enforce_manifestation_limit();

-- Global daily quote cache (shared across users)
create table if not exists public.daily_quotes (
  date date primary key,
  quote text not null,
  author text not null,
  created_at timestamptz not null default now()
);

-- AI fallback manifestation lines (not counted toward user limit)
create table if not exists public.ai_manifestation_cache (
  user_id uuid not null references auth.users (id) on delete cascade,
  date date not null,
  lines jsonb not null,
  created_at timestamptz not null default now(),
  primary key (user_id, date)
);

-- RLS
alter table public.habits enable row level security;
alter table public.habit_entries enable row level security;
alter table public.manifestations enable row level security;
alter table public.daily_quotes enable row level security;
alter table public.ai_manifestation_cache enable row level security;

-- Habits policies
drop policy if exists "habits_select_own" on public.habits;
create policy "habits_select_own" on public.habits
  for select using (auth.uid() = user_id);

drop policy if exists "habits_insert_own" on public.habits;
create policy "habits_insert_own" on public.habits
  for insert with check (auth.uid() = user_id);

drop policy if exists "habits_update_own" on public.habits;
create policy "habits_update_own" on public.habits
  for update using (auth.uid() = user_id);

drop policy if exists "habits_delete_own" on public.habits;
create policy "habits_delete_own" on public.habits
  for delete using (auth.uid() = user_id);

-- Entries policies
drop policy if exists "entries_select_own" on public.habit_entries;
create policy "entries_select_own" on public.habit_entries
  for select using (auth.uid() = user_id);

drop policy if exists "entries_insert_own" on public.habit_entries;
create policy "entries_insert_own" on public.habit_entries
  for insert with check (auth.uid() = user_id);

drop policy if exists "entries_update_own" on public.habit_entries;
create policy "entries_update_own" on public.habit_entries
  for update using (auth.uid() = user_id);

drop policy if exists "entries_delete_own" on public.habit_entries;
create policy "entries_delete_own" on public.habit_entries
  for delete using (auth.uid() = user_id);

-- Manifestations policies
drop policy if exists "manifestations_select_own" on public.manifestations;
create policy "manifestations_select_own" on public.manifestations
  for select using (auth.uid() = user_id);

drop policy if exists "manifestations_insert_own" on public.manifestations;
create policy "manifestations_insert_own" on public.manifestations
  for insert with check (auth.uid() = user_id);

drop policy if exists "manifestations_update_own" on public.manifestations;
create policy "manifestations_update_own" on public.manifestations
  for update using (auth.uid() = user_id);

drop policy if exists "manifestations_delete_own" on public.manifestations;
create policy "manifestations_delete_own" on public.manifestations
  for delete using (auth.uid() = user_id);

-- Daily quotes: authenticated users can read; writes via service role
drop policy if exists "daily_quotes_select_auth" on public.daily_quotes;
create policy "daily_quotes_select_auth" on public.daily_quotes
  for select to authenticated using (true);

-- AI cache: users can read/write their own rows (API also uses service role)
drop policy if exists "ai_cache_select_own" on public.ai_manifestation_cache;
create policy "ai_cache_select_own" on public.ai_manifestation_cache
  for select using (auth.uid() = user_id);

drop policy if exists "ai_cache_insert_own" on public.ai_manifestation_cache;
create policy "ai_cache_insert_own" on public.ai_manifestation_cache
  for insert with check (auth.uid() = user_id);

drop policy if exists "ai_cache_update_own" on public.ai_manifestation_cache;
create policy "ai_cache_update_own" on public.ai_manifestation_cache
  for update using (auth.uid() = user_id);
