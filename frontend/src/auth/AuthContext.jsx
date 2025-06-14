/**
 * Auth React Context.
 *
 * Provides: user, isAuthenticated, login, register, logout
 * Listens for forced logout events from the Axios interceptor.
 * Attempts session restore on mount via refresh token.
 */

import { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { authAPI } from '../api/endpoints';
import { setTokens, clearTokens, getRefreshToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Forced logout (refresh token rejected)
  useEffect(() => {
    const handleForceLogout = () => {
      setUser(null);
      clearTokens();
    };
    window.addEventListener('auth:logout', handleForceLogout);
    return () => window.removeEventListener('auth:logout', handleForceLogout);
  }, []);

  // Try restore session on mount
  useEffect(() => {
    setLoading(false); // Memory tokens don't survive reload — no restore possible
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authAPI.login(email, password);
    setTokens(data.access_token, data.refresh_token);
    setUser({ email, authenticated: true });
    return data;
  }, []);

  const register = useCallback(async (email, password, fullName) => {
    const data = await authAPI.register(email, password, fullName);
    setTokens(data.access_token, data.refresh_token);
    setUser({ email, full_name: fullName, authenticated: true });
    return data;
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthContext;
