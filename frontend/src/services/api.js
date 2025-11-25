import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Bookmarks API
export const bookmarksApi = {
  getAll: (category = null, sortBy = null) => {
    const params = {};
    if (category) params.category = category;
    if (sortBy) params.sort_by = sortBy;
    return api.get('/bookmarks/', { params });
  },

  getOne: (id) => api.get(`/bookmarks/${id}`),

  create: (data) => api.post('/bookmarks/', data),

  update: (id, data) => api.put(`/bookmarks/${id}`, data),

  delete: (id) => api.delete(`/bookmarks/${id}`),

  search: (query) => api.get('/bookmarks/search/', { params: { q: query } }),

  trackClick: (id) => api.post(`/bookmarks/${id}/click`),
};

// Widgets API
export const widgetsApi = {
  getAll: () => api.get('/widgets/'),

  getTypes: () => api.get('/widgets/types'),

  getOne: (id) => api.get(`/widgets/${id}`),

  getData: (id, forceRefresh = false) =>
    api.get(`/widgets/${id}/data`, { params: { force_refresh: forceRefresh } }),

  create: (data) => api.post('/widgets/', data),

  update: (id, data) => api.put(`/widgets/${id}`, data),

  delete: (id) => api.delete(`/widgets/${id}`),

  refresh: (id) => api.post(`/widgets/${id}/refresh`),

  reloadConfig: () => api.post('/widgets/reload-config'),
};

// Sections API
export const sectionsApi = {
  getAll: () => api.get('/sections/'),

  getOne: (id) => api.get(`/sections/${id}`),

  create: (data) => api.post('/sections/', data),

  update: (id, data) => api.put(`/sections/${id}`, data),

  reorder: (sections) => api.put('/sections/reorder', { sections }),

  delete: (id) => api.delete(`/sections/${id}`),
};

export default api;
