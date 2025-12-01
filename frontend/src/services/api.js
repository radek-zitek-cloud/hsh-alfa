import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    // Handle network errors gracefully
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout:', error.message);
      error.message = 'Request timed out. Please check your connection.';
    } else if (error.code === 'ERR_NETWORK' || !error.response) {
      console.error('Network error:', error.message);
      error.message = 'Unable to connect to server. Please check your connection.';
    } else if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      if (status >= 500) {
        console.error('Server error:', error.message);
        error.message = 'Server error. Please try again later.';
      } else if (status === 404) {
        console.error('Resource not found:', error.message);
        error.message = 'Resource not found.';
      }
    }
    return Promise.reject(error);
  }
);

// Bookmarks API
export const bookmarksApi = {
  getAll: (category = null, sortBy = null) => {
    const params = {};
    if (category) params.category = category;
    if (sortBy) params.sort_by = sortBy;
    return api.get('/bookmarks/', { params });
  },

  getOne: id => api.get(`/bookmarks/${id}`),

  create: data => api.post('/bookmarks/', data),

  update: (id, data) => api.put(`/bookmarks/${id}`, data),

  delete: id => api.delete(`/bookmarks/${id}`),

  search: query => api.get('/bookmarks/search/', { params: { q: query } }),

  trackClick: id => api.post(`/bookmarks/${id}/click`),
};

// Widgets API
export const widgetsApi = {
  getAll: () => api.get('/widgets/'),

  getTypes: () => api.get('/widgets/types'),

  getOne: id => api.get(`/widgets/${id}`),

  getData: (id, forceRefresh = false) =>
    api.get(`/widgets/${id}/data`, { params: { force_refresh: forceRefresh } }),

  create: data => api.post('/widgets/', data),

  update: (id, data) => api.put(`/widgets/${id}`, data),

  delete: id => api.delete(`/widgets/${id}`),

  refresh: id => api.post(`/widgets/${id}/refresh`),

  reloadConfig: () => api.post('/widgets/reload-config'),
};

// Sections API
export const sectionsApi = {
  getAll: () => api.get('/sections/'),

  getOne: id => api.get(`/sections/${id}`),

  create: data => api.post('/sections/', data),

  update: (id, data) => api.put(`/sections/${id}`, data),

  reorder: sections => api.put('/sections/reorder', { sections }),

  delete: id => api.delete(`/sections/${id}`),
};

// Preferences API
export const preferencesApi = {
  getAll: () => api.get('/preferences/'),

  get: key => api.get(`/preferences/${key}`),

  set: (key, value) => api.put(`/preferences/${key}`, { value }),
};

// Habits API
export const habitsApi = {
  getAll: () => api.get('/habits/'),

  getOne: id => api.get(`/habits/${id}`),

  create: data => api.post('/habits/', data),

  update: (id, data) => api.put(`/habits/${id}`, data),

  delete: id => api.delete(`/habits/${id}`),

  getCompletions: id => api.get(`/habits/${id}/completions`),

  toggleCompletion: data => api.post('/habits/completions', data),
};

// Export/Import API
export const exportImportApi = {
  exportData: (format = 'json') =>
    api.get('/export', {
      params: { format },
      responseType: 'blob', // Important for file download
    }),

  importData: data => api.post('/import', data),
};

// Admin API
export const adminApi = {
  // Users
  getUsers: () => api.get('/admin/users'),

  getUser: id => api.get(`/admin/users/${id}`),

  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),

  // Bookmarks
  getBookmarks: (userId = null) => {
    const params = {};
    if (userId) params.user_id = userId;
    return api.get('/admin/bookmarks', { params });
  },

  updateBookmark: (id, data) => api.put(`/admin/bookmarks/${id}`, data),

  deleteBookmark: id => api.delete(`/admin/bookmarks/${id}`),

  // Widgets
  getWidgets: (userId = null) => {
    const params = {};
    if (userId) params.user_id = userId;
    return api.get('/admin/widgets', { params });
  },

  updateWidget: (id, data) => api.put(`/admin/widgets/${id}`, data),

  deleteWidget: id => api.delete(`/admin/widgets/${id}`),

  // Preferences
  getPreferences: (userId = null) => {
    const params = {};
    if (userId) params.user_id = userId;
    return api.get('/admin/preferences', { params });
  },

  deletePreference: id => api.delete(`/admin/preferences/${id}`),
};

export default api;
