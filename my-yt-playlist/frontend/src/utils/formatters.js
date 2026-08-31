/**
 * Formats seconds into HH:MM:SS or MM:SS (e.g. 1800 -> 30:00, 3665 -> 1:01:05)
 */
export function formatDuration(seconds) {
  if (!seconds || isNaN(seconds) || seconds <= 0) return '0:00';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const formattedSecs = secs.toString().padStart(2, '0');
  if (hrs > 0) {
    const formattedMins = mins.toString().padStart(2, '0');
    return `${hrs}:${formattedMins}:${formattedSecs}`;
  }
  return `${mins}:${formattedSecs}`;
}

/**
 * Formats ISO date string into readable relative date or localized string
 */
export function formatDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
