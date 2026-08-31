export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'yt_playlist_access_token',
  REFRESH_TOKEN: 'yt_playlist_refresh_token',
  USER_DATA: 'yt_playlist_user_data',
};

export const VIDEO_STATUS = {
  UNWATCHED: 'unwatched',
  WATCHING: 'watching',
  WATCHED: 'watched',
};

export const SORT_OPTIONS = [
  { label: 'Recently Added', value: 'added_at', order: 'desc' },
  { label: 'Oldest Added', value: 'added_at', order: 'asc' },
  { label: 'Newest Published', value: 'published_at', order: 'desc' },
  { label: 'Oldest Published', value: 'published_at', order: 'asc' },
  { label: 'Title (A-Z)', value: 'title', order: 'asc' },
  { label: 'Title (Z-A)', value: 'title', order: 'desc' },
  { label: 'Duration (Longest)', value: 'duration_seconds', order: 'desc' },
  { label: 'Duration (Shortest)', value: 'duration_seconds', order: 'asc' },
];
