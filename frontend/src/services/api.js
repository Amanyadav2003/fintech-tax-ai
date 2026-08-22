import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable automatic cookie sending (HttpOnly cookies)
});

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
    const isAuthRoute = originalRequest.url.includes('auth/login') || originalRequest.url.includes('auth/refresh') || originalRequest.url.includes('auth/register') || originalRequest.url.includes('auth/verify-otp') || originalRequest.url.includes('auth/resend-otp') || originalRequest.url.includes('auth/send-registration-otp') || originalRequest.url.includes('auth/verify-registration-otp');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;

      try {
        // Token refresh is automatic - just call the endpoint
        // The new access token will be set as an HttpOnly cookie by the backend
        const refreshResponse = await api.post('auth/refresh');
        if (refreshResponse.data.access_token) {
          sessionStorage.setItem('access_token', refreshResponse.data.access_token);
        }

        // Retry original request with new token
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login if not already there
        sessionStorage.removeItem('access_token');
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
