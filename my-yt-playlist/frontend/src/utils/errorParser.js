/**
 * Normalizes backend error responses into a consistent shape:
 * { code: string, message: string, details: object }
 */
export function parseApiError(error) {
  if (!error.response) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your network connection.',
      details: {},
    };
  }

  const { status, data } = error.response;

  if (data && data.error) {
    return {
      code: data.error.code || 'UNKNOWN_ERROR',
      message: data.error.message || 'An error occurred.',
      details: data.error.details || {},
    };
  }

  // Fallback for standard HTTP errors if backend error envelope is missing
  switch (status) {
    case 401:
      return { code: 'UNAUTHORIZED', message: 'Authentication required. Please log in.', details: {} };
    case 403:
      return { code: 'FORBIDDEN', message: 'You do not have permission to access this resource.', details: {} };
    case 404:
      return { code: 'NOT_FOUND', message: 'The requested resource was not found.', details: {} };
    case 409:
      return { code: 'CONFLICT', message: 'Resource already exists.', details: {} };
    case 422:
      return { code: 'VALIDATION_ERROR', message: 'Invalid payload provided.', details: {} };
    default:
      return { code: 'SERVER_ERROR', message: 'An unexpected server error occurred.', details: {} };
  }
}
