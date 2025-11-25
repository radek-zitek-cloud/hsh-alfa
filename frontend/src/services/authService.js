import api from './api';

const TOKEN_KEY = 'auth_token';

export const authService = {
  /**
   * Get Google OAuth2 authorization URL
   * @returns {Promise<string>} Authorization URL
   */
  async getGoogleAuthUrl() {
    const response = await api.get('/auth/google/url');
    return response.data.auth_url;
  },

  /**
   * Handle OAuth2 callback with authorization code
   * @param {string} code - Authorization code from Google
   * @param {string} state - State token for CSRF protection
   * @returns {Promise<Object>} Token response with user data
   */
  async handleCallback(code, state) {
    const response = await api.post('/auth/callback', { code, state });
    return response.data;
  },

  /**
   * Get current authenticated user
   * @returns {Promise<Object>} User data
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Logout current user
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout request failed:', error);
      // Continue with local logout even if server request fails
    }
  },

  /**
   * Check if user is authenticated
   * @returns {Promise<Object>} Authentication status
   */
  async checkAuth() {
    const response = await api.get('/auth/check');
    return response.data;
  },

  /**
   * Store authentication token in localStorage
   * @param {string} token - JWT token
   */
  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  /**
   * Get authentication token from localStorage
   * @returns {string|null} JWT token or null if not found
   */
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Remove authentication token from localStorage
   */
  removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  /**
   * Check if user has a valid token (doesn't verify with server)
   * @returns {boolean} True if token exists
   */
  hasToken() {
    return !!this.getToken();
  },
};
