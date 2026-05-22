import { API_BASE_URL } from '../constants';

// build request headers with user id
function buildHeaders(userId, extra = {}) {
  return {
    'Content-Type': 'application/json',
    ...(userId ? { 'x-user-id': userId } : {}),
    ...extra,
  };
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    ...options,
    headers: buildHeaders(options.userId, options.headers),
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${url}]:`, error.message);
    throw error;
  }
}

// streams response chunks
async function stream(endpoint, body, userId) {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`STREAM REQUEST to: ${url}`, body);

  const response = await fetch(url, {
    method: 'POST',
    headers: buildHeaders(userId),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Stream failed: ${response.status}`);
  }

  console.log('STREAM: Connection established, returning reader...');
  return response;
}

// handles multipart form data for file uploads
async function uploadDocument(endpoint, file, chatId, userId) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const formData = new FormData();
  formData.append('file', file);
  if (chatId) {
    formData.append('chat_id', chatId);
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      ...(userId ? { 'x-user-id': userId } : {}),
      // Do NOT set Content-Type for FormData, browser sets it with boundary
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Upload failed');
  }

  return await response.json();
}

export const apiClient = {
  get:    (endpoint, options)       => request(endpoint, { ...options, method: 'GET' }),
  post:   (endpoint, body, options) => request(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),
  stream: (endpoint, body, userId)  => stream(endpoint, body, userId),
  delete: (endpoint, options)       => request(endpoint, { ...options, method: 'DELETE' }),
  uploadDocument: (endpoint, file, chatId, userId) => uploadDocument(endpoint, file, chatId, userId)
};
