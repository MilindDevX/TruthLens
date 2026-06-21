/**
 * Axios HTTP client with JWT silent refresh interceptor.
 *
 * Strategy:
 * - Access token stored in memory (closure variable, not localStorage)
 * - Refresh token stored in memory
 * - On 401: automatically refresh, retry original request
 * - On refresh failure: force logout
 * - Queue concurrent requests while refreshing (prevent token stampede)
 */

import axios from 'axios';
import { toast } from '../components/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// ─── Token Storage (memory-only, XSS-safe) ───
let accessToken = null;
let refreshToken = null;
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve(token);
  });
  failedQueue = [];
};

// ─── Axios Instance ───
const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Request Interceptor: Attach Bearer Token ───
client.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: Silent Refresh on 401 + Timeout/Network Toasts ───
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Timeout detection
    if (error.code === 'ECONNABORTED') {
      toast.warn('Request timed out — the server may be busy. Please try again.');
      return Promise.reject(error);
    }

    // Network error (no response at all)
    if (!error.response) {
      toast.error('Network error — please check your connection.');
      return Promise.reject(error);
    }

    // Only retry once, only on 401, only if we have a refresh token
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      !refreshToken ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login')
    ) {
      return Promise.reject(error);
    }

    // Queue concurrent requests while refreshing
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return client(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const response = await axios.post(`${API_BASE}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;
      setTokens(access_token, newRefreshToken);

      processQueue(null, access_token);

      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return client(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearTokens();
      // Dispatch custom event for AuthContext to catch
      window.dispatchEvent(new Event('auth:logout'));
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// ─── Token Management ───
export const setTokens = (access, refresh) => {
  accessToken = access;
  refreshToken = refresh;
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
};

export const getAccessToken = () => accessToken;
export const getRefreshToken = () => refreshToken;

export default client;
