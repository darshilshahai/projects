import apiClient from './client';

/**
 * Ingests a new video into user library by YouTube URL.
 * POST /videos
 */
export async function ingestVideoApi(url) {
  const response = await apiClient.post('/videos', { url });
  return response.data;
}

/**
 * Queries user video library with search, filtering, sorting, and pagination.
 * GET /videos
 */
export async function getVideosApi(params = {}) {
  const response = await apiClient.get('/videos', { params });
  return response.data;
}

/**
 * Retrieves unwatched videos matching a maximum duration.
 * GET /videos/quick-queue
 */
export async function getQuickQueueApi(maxDurationSeconds = 900, limit = 10) {
  const response = await apiClient.get('/videos/quick-queue', {
    params: { max_duration_seconds: maxDurationSeconds, limit },
  });
  return response.data;
}

/**
 * Retrieves single video details with embedded metadata & notes.
 * GET /videos/{id}
 */
export async function getVideoByIdApi(userVideoId) {
  const response = await apiClient.get(`/videos/${userVideoId}`);
  return response.data;
}

/**
 * Updates video state (status, favourite, watch_later, category, notes).
 * PATCH /videos/{id}
 */
export async function updateVideoApi(userVideoId, data) {
  const response = await apiClient.patch(`/videos/${userVideoId}`, data);
  return response.data;
}

/**
 * Removes video from user library.
 * DELETE /videos/{id}
 */
export async function deleteVideoApi(userVideoId) {
  await apiClient.delete(`/videos/${userVideoId}`);
  return true;
}

/**
 * Attaches a time-linked note to a video.
 * POST /videos/{id}/notes
 */
export async function createNoteApi(userVideoId, { timestamp_seconds, note_text }) {
  const response = await apiClient.post(`/videos/${userVideoId}/notes`, {
    timestamp_seconds,
    note_text,
  });
  return response.data;
}

/**
 * Deletes a timestamp note from a video.
 * DELETE /videos/{id}/notes/{note_id}
 */
export async function deleteNoteApi(userVideoId, noteId) {
  await apiClient.delete(`/videos/${userVideoId}/notes/${noteId}`);
  return true;
}
