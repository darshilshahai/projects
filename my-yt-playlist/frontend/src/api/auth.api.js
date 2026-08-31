import apiClient from './client';

/**
 * Authenticates user credentials and retrieves JWT token pair.
 * POST /auth/login
 */
export async function loginApi({ email, password }) {
  const response = await apiClient.post('/auth/login', { email, password });
  return response.data;
}

/**
 * Registers new user account and retrieves JWT token pair.
 * POST /auth/register
 */
export async function registerApi({ email, password, full_name }) {
  const response = await apiClient.post('/auth/register', { email, password, full_name });
  return response.data;
}

/**
 * Rotates refresh token and returns fresh token pair.
 * POST /auth/refresh
 */
export async function refreshTokenApi(refresh_token) {
  const response = await apiClient.post('/auth/refresh', { refresh_token });
  return response.data;
}

/**
 * Revokes refresh token on backend.
 * POST /auth/logout
 */
export async function logoutApi(refresh_token) {
  const response = await apiClient.post('/auth/logout', { refresh_token });
  return response.data;
}

/**
 * Fetches authenticated user profile.
 * GET /users/me
 */
export async function getCurrentUserApi() {
  const response = await apiClient.get('/users/me');
  return response.data;
}

/**
 * Updates profile fields (e.g. full_name).
 * PATCH /users/me
 */
export async function updateProfileApi({ full_name }) {
  const response = await apiClient.patch('/users/me', { full_name });
  return response.data;
}

/**
 * Changes user password.
 * POST /users/me/change-password
 */
export async function changePasswordApi({ current_password, new_password }) {
  const response = await apiClient.post('/users/me/change-password', {
    current_password,
    new_password,
  });
  return response.data;
}
