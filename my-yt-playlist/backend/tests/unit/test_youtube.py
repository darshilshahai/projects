import pytest
from app.core.exceptions import InvalidYouTubeURLException, YouTubeVideoNotFoundException
from app.integrations.youtube import (
    YouTubeClient,
    YouTubeURLParser,
    parse_iso8601_duration,
)


def test_youtube_url_parser_valid_urls():
    """Test extracting video ID across various YouTube URL formats."""
    expected_id = "dQw4w9WgXcQ"
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=100s&list=PL12345",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?t=42",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    ]

    for url in valid_urls:
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == expected_id, f"Failed on URL: {url}"


def test_youtube_url_parser_invalid_urls():
    """Test that invalid URLs raise InvalidYouTubeURLException."""
    invalid_urls = [
        "https://google.com",
        "https://vimeo.com/12345678",
        "https://youtube.com/watch?v=short",
        "not_a_url",
        "",
    ]

    for url in invalid_urls:
        with pytest.raises(InvalidYouTubeURLException):
            YouTubeURLParser.extract_video_id(url)


def test_iso8601_duration_parser():
    """Test ISO 8601 duration string parsing into seconds."""
    assert parse_iso8601_duration("PT1H2M30S") == 3750
    assert parse_iso8601_duration("PT15M33S") == 933
    assert parse_iso8601_duration("PT45S") == 45
    assert parse_iso8601_duration("PT1H") == 3600
    assert parse_iso8601_duration("P1DT1H") == 90000
    assert parse_iso8601_duration("") == 0


@pytest.mark.asyncio
async def test_youtube_client_oembed_fallback():
    """Test metadata retrieval via oEmbed fallback endpoint."""
    client = YouTubeClient(api_key="")
    # Use real test video ID (Rick Astley - Never Gonna Give You Up)
    metadata = await client.fetch_video_metadata("dQw4w9WgXcQ")

    assert metadata.youtube_video_id == "dQw4w9WgXcQ"
    assert "Rick Astley" in metadata.title or "Never Gonna Give You Up" in metadata.title
    assert metadata.channel_name is not None
    assert metadata.thumbnail_url is not None


@pytest.mark.asyncio
async def test_youtube_client_video_not_found():
    """Test that requesting a non-existent video ID raises YouTubeVideoNotFoundException."""
    client = YouTubeClient(api_key="")
    with pytest.raises(YouTubeVideoNotFoundException):
        await client.fetch_video_metadata("non_exist_99")
