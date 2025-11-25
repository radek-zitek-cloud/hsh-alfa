import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const token = authService.getToken();

      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      // Verify token is still valid by fetching user info
      const userData = await authService.getCurrentUser();
      setUser(userData);
      setError(null);
    } catch (err) {
      console.error('Auth check failed:', err);
      // Token might be expired or invalid
      authService.removeToken();
      setUser(null);
      setError(err?.message || 'Authentication check failed');
    } finally {
      setLoading(false);
    }
  }, []);

  // Check if user is authenticated on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = (token, userData) => {
    authService.setToken(token);
    setUser(userData);
    setError(null);
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      authService.removeToken();
      setUser(null);
      setError(null);
    }
  };

  const getAuthUrl = async () => {
    try {
      return await authService.getGoogleAuthUrl();
    } catch (err) {
      setError(err?.message || 'Failed to get authentication URL');
      throw err;
    }
  };

  const handleCallback = useCallback(async (code, state) => {
    try {
      setLoading(true);
      setError(null);
      const response = await authService.handleCallback(code, state);
      login(response.access_token, response.user);
      return response;
    } catch (err) {
      setError(err?.message || 'Authentication failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [login]);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    logout,
    getAuthUrl,
    handleCallback,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
