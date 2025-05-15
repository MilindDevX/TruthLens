/**
 * API endpoint functions.
 * Thin wrappers around the Axios client — all return response.data.
 */

import client from './client';

// ─── Auth ───
export const authAPI = {
  login: (email, password) =>
    client.post('/auth/login', { email, password }).then((r) => r.data),

  register: (email, password, full_name) =>
    client.post('/auth/register', { email, password, full_name }).then((r) => r.data),

  refresh: (refresh_token) =>
    client.post('/auth/refresh', { refresh_token }).then((r) => r.data),

  googleAuthUrl: () =>
    client.get('/auth/google').then((r) => r.data),
};

// ─── Content Analysis ───
export const analyzeAPI = {
  text: (text) =>
    client.post('/analyze/text', { text }).then((r) => r.data),
};

// ─── History ───
export const historyAPI = {
  list: (page = 1, limit = 10) =>
    client.get('/history', { params: { page, limit } }).then((r) => r.data),

  get: (id) =>
    client.get(`/history/${id}`).then((r) => r.data),
};

// ─── System ───
export const systemAPI = {
  health: () =>
    client.get('/health').then((r) => r.data),
};
