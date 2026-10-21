import axios from 'axios';

export const resolveApiBaseUrl = (apiBaseUrl, environment = process.env.NODE_ENV) => (
  apiBaseUrl || (
    environment === 'development'
      ? 'http://localhost:8000/api'
      : 'https://fintech-tax-ai.onrender.com/api'
  )
);
const API_BASE_URL = resolveApiBaseUrl(process.env.REACT_APP_API_URL);
export const resolveHealthUrl = (apiBaseUrl) => new URL('/health', apiBaseUrl).toString();
const HEALTH_URL = resolveHealthUrl(API_BASE_URL);
const MAX_GET_ATTEMPTS = 3;
const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);
const AUTH_ROUTES = [
  'auth/login',
  'auth/google',
  'auth/refresh',
  'auth/register',
  'auth/me',
  'auth/verify-otp',
  'auth/resend-otp',
  'auth/send-registration-otp',
  'auth/verify-registration-otp',
  'auth/password-reset',
  'auth/registration/profile-photo',
];
const RETRY_BASE_DELAY_MS = 500;
let authInitializationInProgress = true;
let refreshPromise = null;
let healthCheckPromise = null;

const finishWarmOperation = (available) => {
  window.dispatchEvent(new CustomEvent('taxmate:api-warming-finished', { detail: { available } }));
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable automatic cookie sending (HttpOnly cookies)
});

export const healthApi = axios.create({ timeout: 20000 });

healthApi.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    const isSafeGet = originalRequest?.method?.toLowerCase() === 'get';
    const isNetworkError = !error.response && (error.code === 'ERR_NETWORK' || Boolean(error.request && !['ECONNABORTED', 'ETIMEDOUT', 'ERR_CANCELED'].includes(error.code)));
    const isRetryableFailure = isNetworkError || RETRYABLE_STATUS_CODES.has(error.response?.status);
    const attempt = originalRequest?._safeGetAttempt || 1;

    if (!isSafeGet || !isRetryableFailure || attempt >= MAX_GET_ATTEMPTS) {
      return Promise.reject(error);
    }

    originalRequest._safeGetAttempt = attempt + 1;
    await new Promise(resolve => window.setTimeout(resolve, RETRY_BASE_DELAY_MS * (2 ** (attempt - 1))));
    return healthApi(originalRequest);
  }
);

export const setAuthInitialization = (inProgress) => {
  authInitializationInProgress = inProgress;
};

export const warmBackend = () => {
  if (healthCheckPromise) return healthCheckPromise;

  window.dispatchEvent(new Event('taxmate:api-warming'));
  healthCheckPromise = healthApi.get(HEALTH_URL)
    .then(
      () => {
        finishWarmOperation(true);
        return true;
      },
      () => {
        window.dispatchEvent(new Event('taxmate:api-unavailable'));
        finishWarmOperation(false);
        return false;
      }
    )
    .finally(() => {
      healthCheckPromise = null;
    });

  return healthCheckPromise;
};

const refreshAccessToken = () => {
  if (!refreshPromise) {
    refreshPromise = api.post('auth/refresh').finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
};

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => {
    window.dispatchEvent(new Event('taxmate:api-available'));
    // Capture and store access token from login/register responses
    if (response.data.access_token) {
      sessionStorage.setItem('access_token', response.data.access_token);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const isSafeGet = originalRequest?.method?.toLowerCase() === 'get';
    const isNetworkError = !error.response && (error.code === 'ERR_NETWORK' || Boolean(error.request && !['ECONNABORTED', 'ETIMEDOUT', 'ERR_CANCELED'].includes(error.code)));
    const isRetryableFailure = isNetworkError || RETRYABLE_STATUS_CODES.has(error.response?.status);
    const attempt = originalRequest?._safeGetAttempt || 1;

    if (isSafeGet && isRetryableFailure && attempt < MAX_GET_ATTEMPTS) {
      const isFirstRetry = !originalRequest._safeGetRetryInProgress;
      if (isFirstRetry) {
        originalRequest._safeGetRetryInProgress = true;
        window.dispatchEvent(new Event('taxmate:api-warming'));
      }
      originalRequest._safeGetAttempt = attempt + 1;
      await new Promise(resolve => window.setTimeout(resolve, RETRY_BASE_DELAY_MS * (2 ** (attempt - 1))));
      const retryRequest = api(originalRequest);
      if (!isFirstRetry) return retryRequest;
      return retryRequest.then(
        response => {
          finishWarmOperation(true);
          return response;
        },
        retryError => {
          finishWarmOperation(false);
          throw retryError;
        }
      );
    }

    if ((!error.response || (isSafeGet && RETRYABLE_STATUS_CODES.has(error.response.status))) && !originalRequest?._safeGetRetryInProgress) {
      window.dispatchEvent(new Event('taxmate:api-unavailable'));
    }

    const requestUrl = originalRequest?.url || '';
    const isAuthRoute = AUTH_ROUTES.some(route => requestUrl.includes(route));

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthRoute) {
      if (authInitializationInProgress) return Promise.reject(error);
      originalRequest._retry = true;

      try {
        const refreshResponse = await refreshAccessToken();
        if (refreshResponse.data.access_token) {
          sessionStorage.setItem('access_token', refreshResponse.data.access_token);
        }

        // Retry original request with new token
        return api(originalRequest);
      } catch (refreshError) {
        // Both the original request and the shared refresh request failed.
        sessionStorage.removeItem('access_token');
        window.dispatchEvent(new Event('taxmate:session-expired'));
        if (window.location.pathname !== '/') {
            window.location.href = '/';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
