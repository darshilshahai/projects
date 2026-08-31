import apiClient from './client';

/**
 * Retrieves all user collections with video_count aggregation.
 * GET /collections
 */
export async function getCollectionsApi() {
  const response = await apiClient.get('/collections');
  return response.data;
}

/**
 * Creates a new custom collection.
 * POST /collections
 */
export async function createCollectionApi({ name, description }) {
  const response = await apiClient.post('/collections', { name, description });
  return response.data;
}

/**
 * Retrieves single collection details.
 * GET /collections/{id}
 */
export async function getCollectionByIdApi(id) {
  const response = await apiClient.get(`/collections/${id}`);
  return response.data;
}

/**
 * Updates collection name or description.
 * PATCH /collections/{id}
 */
export async function updateCollectionApi(id, { name, description }) {
  const response = await apiClient.patch(`/collections/${id}`, { name, description });
  return response.data;
}

/**
 * Deletes a collection.
 * DELETE /collections/{id}
 */
export async function deleteCollectionApi(id) {
  await apiClient.delete(`/collections/${id}`);
  return true;
}

/**
 * Adds a video to a collection.
 * POST /collections/{id}/videos/{uv_id}
 */
export async function addVideoToCollectionApi(collectionId, userVideoId) {
  const response = await apiClient.post(`/collections/${collectionId}/videos/${userVideoId}`);
  return response.data;
}

/**
 * Removes a video from a collection.
 * DELETE /collections/{id}/videos/{uv_id}
 */
export async function removeVideoFromCollectionApi(collectionId, userVideoId) {
  await apiClient.delete(`/collections/${collectionId}/videos/${userVideoId}`);
  return true;
}
