import apiClient from './client';

/**
 * Retrieves all user tags with usage_count aggregation.
 * GET /tags
 */
export async function getTagsApi() {
  const response = await apiClient.get('/tags');
  return response.data;
}

/**
 * Creates a new tag (normalized lowercase by backend).
 * POST /tags
 */
export async function createTagApi({ name }) {
  const response = await apiClient.post('/tags', { name });
  return response.data;
}

/**
 * Deletes a tag.
 * DELETE /tags/{id}
 */
export async function deleteTagApi(id) {
  await apiClient.delete(`/tags/${id}`);
  return true;
}

/**
 * Attaches a tag to a video.
 * POST /tags/videos/{uv_id}/tags/{tag_id}
 */
export async function attachTagToVideoApi(userVideoId, tagId) {
  const response = await apiClient.post(`/tags/videos/${userVideoId}/tags/${tagId}`);
  return response.data;
}

/**
 * Detaches a tag from a video.
 * DELETE /tags/videos/{uv_id}/tags/{tag_id}
 */
export async function detachTagFromVideoApi(userVideoId, tagId) {
  await apiClient.delete(`/tags/videos/${userVideoId}/tags/${tagId}`);
  return true;
}
