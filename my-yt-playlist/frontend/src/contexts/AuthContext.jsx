import React, { createContext, useContext, useState, useEffect } from 'react';
import { STORAGE_KEYS } from '../constants';
import { loginApi, registerApi, logoutApi, getCurrentUserApi } from '../api/auth.api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN));
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on mount if token exists
  useEffect(() => {
    async function restoreSession() {
      const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

      if (token || refreshToken) {
        try {
          const userData = await getCurrentUserApi();
          setUser(userData);
          localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
        } catch (error) {
          // Token restoration failed (client.js will handle redirect if refresh fails)
          localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.USER_DATA);
          setUser(null);
          setAccessToken(null);
        }
      }
      setIsLoading(false);
    }

    restoreSession();

    // Event listener for auth:logout dispatched by client.js on token revocation
    const handleGlobalLogout = () => {
      setUser(null);
      setAccessToken(null);
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    };

    window.addEventListener('auth:logout', handleGlobalLogout);
    return () => window.removeEventListener('auth:logout', handleGlobalLogout);
  }, []);

  const login = async (credentials) => {
    const data = await loginApi(credentials);
    const { user: userData, tokens } = data;

    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));

    setAccessToken(tokens.access_token);
    setUser(userData);
    return userData;
  };

  const register = async (payload) => {
    const data = await registerApi(payload);
    const { user: userData, tokens } = data;

    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));

    setAccessToken(tokens.access_token);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (refreshToken) {
      try {
        await logoutApi(refreshToken);
      } catch (e) {
        // Ignore logout API network errors
      }
    }
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(updatedUser));
  };

  const value = {
    user,
    accessToken,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
