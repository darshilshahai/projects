from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings

FALLBACK_QUOTES = [
    {
        "quote": "We are what we repeatedly do. Excellence, then, is not an act, but a habit.",
        "author": "Aristotle",
    },
    {
        "quote": "Success is the sum of small efforts, repeated day in and day out.",
        "author": "Robert Collier",
    },
    {
        "quote": "Discipline is choosing between what you want now and what you want most.",
        "author": "Abraham Lincoln",
    },
]

FALLBACK_MANIFESTATIONS = [
    "I show up for myself every day.",
    "My habits shape the life I want.",
    "I am becoming who I choose to be.",
]


def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def _extract_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if match:
            return json.loads(match.group(1))
        raise


def generate_real_quote(day_of_year: int) -> dict[str, str]:
    """
    Ask OpenAI to return a well-known quote by a real person.
    Must not invent quotes. Falls back to a curated list on failure.
    """
    settings = get_settings()
    prompt = (
        "Return ONE well-known motivational or habit-related quote that was "
        "actually said or written by a real historical or public figure. "
        "Never invent or paraphrase into a fake quote. Prefer widely attributed classics. "
        'Respond with JSON only: {"quote": "...", "author": "..."}. '
        f"Vary selection using seed number {day_of_year}."
    )
    try:
        response = _client().chat.completions.create(
            model=settings.openai_model,
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You curate famous real quotes only. "
                        "Never fabricate quotes or authors. JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        data = _extract_json(content)
        quote = str(data.get("quote", "")).strip()
        author = str(data.get("author", "")).strip()
        if quote and author:
            return {"quote": quote, "author": author}
    except Exception:
        pass

    return FALLBACK_QUOTES[day_of_year % len(FALLBACK_QUOTES)]


def generate_manifestation_lines() -> list[str]:
    """Generate short first-person habit affirmations when the user has none."""
    settings = get_settings()
    prompt = (
        "Generate exactly 3 short first-person manifestation / affirmation lines "
        "about discipline, habits, and personal growth. "
        'Respond with JSON only: {"lines": ["...", "...", "..."]}.'
    )
    try:
        response = _client().chat.completions.create(
            model=settings.openai_model,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write concise, sincere first-person affirmations. JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        data = _extract_json(content)
        lines = data.get("lines") if isinstance(data, dict) else data
        if isinstance(lines, list):
            cleaned = [str(x).strip() for x in lines if str(x).strip()]
            if len(cleaned) >= 3:
                return cleaned[:3]
            if cleaned:
                return cleaned
    except Exception:
        pass

    return list(FALLBACK_MANIFESTATIONS)
