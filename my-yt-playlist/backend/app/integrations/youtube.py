import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.core.exceptions import (
    InvalidYouTubeURLException,
    YouTubeVideoNotFoundException,
)

# Regex pattern matching standard, short, embed, mobile, and shorts YouTube URLs
YOUTUBE_URL_REGEX = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?"
    r"(?:youtube\.com/(?:watch\?.*v=|shorts/|embed/|v/)|youtu\.be/)"
    r"([a-zA-Z0-9_-]{11})"
)

# ISO 8601 duration regex (e.g. PT1H2M30S, PT15M, PT45S)
ISO_DURATION_REGEX = re.compile(
    r"P(?:(?P<days>\d+)D)?"
    r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?"
)


def parse_iso8601_duration(duration_str: str) -> int:
    """Converts YouTube ISO 8601 duration format (PT1H2M30S) to total seconds."""
    if not duration_str:
        return 0

    match = ISO_DURATION_REGEX.match(duration_str)
    if not match:
        return 0

    parts = match.groupdict(default="0")
    days = int(parts.get("days") or 0)
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)

    return (days * 86400) + (hours * 3600) + (minutes * 60) + seconds


class YouTubeURLParser:
    """Extractor and validator for YouTube video URLs."""

    @staticmethod
    def extract_video_id(url: str) -> str:
        """
        Parses YouTube URL and extracts 11-character video ID.
        Raises InvalidYouTubeURLException if format is invalid.
        """
        if not url:
            raise InvalidYouTubeURLException("URL string cannot be empty.")

        clean_url = url.strip()
        match = YOUTUBE_URL_REGEX.search(clean_url)
        if not match:
            raise InvalidYouTubeURLException("Invalid YouTube URL format.")

        return match.group(1)

    @staticmethod
    def build_canonical_url(video_id: str) -> str:
        """Build canonical YouTube watch URL from 11-char video ID."""
        return f"https://www.youtube.com/watch?v={video_id}"


@dataclass
class YouTubeVideoMetadata:
    """Immutable data transfer object for fetched YouTube video metadata."""

    youtube_video_id: str
    youtube_url: str
    title: str
    description: Optional[str]
    channel_name: str
    channel_id: str
    thumbnail_url: Optional[str]
    duration_seconds: int
    published_at: Optional[datetime]
    category_id: Optional[str]
    is_unavailable: bool = False


class YouTubeClient:
    """
    Client for interacting with YouTube Data API v3 and fallback oEmbed endpoints.
    Provides automatic fallback to oEmbed + watch page HTML parsing for duration extraction.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY

    async def fetch_video_metadata(self, video_id: str) -> YouTubeVideoMetadata:
        """
        Fetches metadata for a YouTube video ID.
        Uses official Data API v3 if API key exists; otherwise falls back to oEmbed + HTML duration parsing.
        """
        if self.api_key:
            try:
                return await self._fetch_via_data_api(video_id)
            except YouTubeVideoNotFoundException:
                raise
            except Exception:
                # If Data API fails (e.g. quota limit), fallback to oEmbed
                pass

        return await self._fetch_via_oembed(video_id)

    async def _fetch_duration_from_watch_page(self, client: httpx.AsyncClient, canonical_url: str) -> int:
        """Fallback helper to extract exact video duration in seconds from YouTube watch page HTML."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = await client.get(canonical_url, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                html = resp.text

                # Match 1: "lengthSeconds":"359"
                length_match = re.search(r"\"lengthSeconds\":\"(\d+)\"", html)
                if length_match:
                    return int(length_match.group(1))

                # Match 2: "approxDurationMs":"359440"
                approx_match = re.search(r"\"approxDurationMs\":\"(\d+)\"", html)
                if approx_match:
                    return int(approx_match.group(1)) // 1000

                # Match 3: itemprop="duration" content="PT6M0S"
                itemprop_match = re.search(r"itemprop=\"duration\"\s+content=\"([^\"]+)\"", html)
                if itemprop_match:
                    return parse_iso8601_duration(itemprop_match.group(1))
        except Exception:
            pass
        return 0

    async def _fetch_via_data_api(self, video_id: str) -> YouTubeVideoMetadata:
        """Fetch metadata using official YouTube Data API v3 endpoint."""
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": video_id,
            "part": "snippet,contentDetails,status",
            "key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 403:
                # Quota exceeded or invalid key fallback
                raise Exception("YouTube API quota exceeded or unauthorized.")

            if response.status_code != 200:
                raise Exception(f"YouTube API returned HTTP {response.status_code}")

            data = response.json()
            items = data.get("items", [])

            if not items:
                raise YouTubeVideoNotFoundException(
                    f"Video with ID '{video_id}' not found or is private/deleted."
                )

            item = items[0]
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})

            duration_iso = content_details.get("duration", "")
            duration_sec = parse_iso8601_duration(duration_iso)

            # Published at timestamp parsing
            published_str = snippet.get("publishedAt")
            published_at = None
            if published_str:
                try:
                    published_at = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    published_at = datetime.now(timezone.utc)

            # Thumbnail selection (maxres -> high -> medium -> default)
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = None
            for quality in ["maxres", "high", "medium", "default"]:
                if quality in thumbnails:
                    thumb_url = thumbnails[quality].get("url")
                    break

            return YouTubeVideoMetadata(
                youtube_video_id=video_id,
                youtube_url=YouTubeURLParser.build_canonical_url(video_id),
                title=snippet.get("title", "Untitled Video"),
                description=snippet.get("description", ""),
                channel_name=snippet.get("channelTitle", "Unknown Channel"),
                channel_id=snippet.get("channelId", ""),
                thumbnail_url=thumb_url,
                duration_seconds=duration_sec,
                published_at=published_at,
                category_id=snippet.get("categoryId"),
                is_unavailable=False,
            )

    async def _fetch_via_oembed(self, video_id: str) -> YouTubeVideoMetadata:
        """Fallback metadata fetcher using YouTube oEmbed endpoint with HTML duration parsing."""
        canonical_url = YouTubeURLParser.build_canonical_url(video_id)
        oembed_url = "https://www.youtube.com/oembed"
        params = {"url": canonical_url, "format": "json"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(oembed_url, params=params)

            if response.status_code == 404:
                raise YouTubeVideoNotFoundException(
                    f"Video with ID '{video_id}' not found or is private/deleted."
                )

            if response.status_code != 200:
                raise YouTubeVideoNotFoundException(
                    f"Unable to retrieve metadata for video ID '{video_id}'."
                )

            data = response.json()
            duration_sec = await self._fetch_duration_from_watch_page(client, canonical_url)

            return YouTubeVideoMetadata(
                youtube_video_id=video_id,
                youtube_url=canonical_url,
                title=data.get("title", "Untitled Video"),
                description="",  # oEmbed doesn't include full description
                channel_name=data.get("author_name", "Unknown Channel"),
                channel_id=data.get("author_url", "").split("/")[-1] or "channel_id",
                thumbnail_url=data.get("thumbnail_url"),
                duration_seconds=duration_sec,
                published_at=datetime.now(timezone.utc),
                category_id=None,
                is_unavailable=False,
            )
