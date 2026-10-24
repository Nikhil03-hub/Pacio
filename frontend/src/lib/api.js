import axios from "axios";

const configuredBase = process.env.REACT_APP_BACKEND_URL || "";

// A local build can bake a loopback API URL in from .env.local. If that bundle is then served
// from a real host, every request would go to the visitor's own machine, so fall back to
// same-origin - which is what the single-function deployment expects anyway.
const isLoopback = (url) => /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i.test(url || "");
const servedFromLoopback = typeof window !== "undefined"
  && /^(localhost|127\.0\.0\.1)$/i.test(window.location.hostname);
const BASE = isLoopback(configuredBase) && !servedFromLoopback ? "" : configuredBase;
const TOKEN_KEY = "careeros_access_token";

export const api = axios.create({
  baseURL: `${BASE}/api`,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

export const getAuthToken = () => {
  try { return window.localStorage.getItem(TOKEN_KEY); }
  catch { return null; }
};

export const setAuthToken = (token) => {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore storage failures; cookie auth still works.
  }
};

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (error?.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${BASE}/api/auth/refresh`, {}, { withCredentials: true });
        const newToken = data.access_token;
        setAuthToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setAuthToken(null);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  },
);

export const apiUrl = (path) => `${BASE}/api${path}`;
