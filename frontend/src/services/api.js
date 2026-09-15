import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
let authInitializationInProgress = true;
let refreshPromise = null;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable automatic cookie sending (HttpOnly cookies)
});

export const setAuthInitialization = (inProgress) => {
  authInitializationInProgress = inProgress;
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
    // Capture and store access token from login/register responses
    if (response.data.access_token) {
      sessionStorage.setItem('access_token', response.data.access_token);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';
    const isAuthRoute = requestUrl.includes('auth/login') || requestUrl.includes('auth/refresh') || requestUrl.includes('auth/register') || requestUrl.includes('auth/me') || requestUrl.includes('auth/verify-otp') || requestUrl.includes('auth/resend-otp') || requestUrl.includes('auth/send-registration-otp') || requestUrl.includes('auth/verify-registration-otp');

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
