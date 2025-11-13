import axios, { AxiosError } from 'axios';

// Use relative path so Vite proxy works
// Vite proxies /api to http://localhost:8000/api
export const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (for future auth)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('api_token');
    if (token) {
      config.headers['X-API-Key'] = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as any;
      console.error('API Error:', {
        status: error.response.status,
        error: data.error,
        detail: data.detail,
        metadata: data.metadata,
      });
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

