import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, verifyApi } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('spaceloop_token'));
  const [activeRole, setActiveRole] = useState(() => localStorage.getItem('spaceloop_active_role') || 'seeker');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Synchronize user profile on mount if token exists
  const fetchCurrentUser = useCallback(async () => {
    const storedToken = localStorage.getItem('spaceloop_token');
    if (!storedToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await authApi.me();
      if (data && (data.user || data.id)) {
        const userData = data.user || data;
        setUser(userData);
        const resolvedRole = localStorage.getItem('spaceloop_active_role') || userData.active_role || userData.role || 'seeker';
        setActiveRole(resolvedRole);
      }
    } catch (err) {
      console.warn('Failed to restore user session:', err);
      // If token expired or invalid, reset
      if (err.status === 401 || err.status === 403) {
        localStorage.removeItem('spaceloop_token');
        localStorage.removeItem('spaceloop_active_role');
        setUser(null);
        setToken(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Login handler
  const login = async (email, password) => {
    setError(null);
    try {
      const response = await authApi.login({ email, password });
      const authToken = response.access_token || response.token;
      const userData = response.user || response;
      const currentRole = response.active_role || userData.active_role || userData.role || 'seeker';

      if (authToken) {
        localStorage.setItem('spaceloop_token', authToken);
        setToken(authToken);
      }
      localStorage.setItem('spaceloop_active_role', currentRole);
      setActiveRole(currentRole);
      setUser(userData);
      return { success: true, user: userData, activeRole: currentRole };
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  // Register handler
  const register = async (formData) => {
    setError(null);
    try {
      const response = await authApi.register(formData);
      const authToken = response.access_token || response.token;
      const userData = response.user || response;
      const currentRole = formData.role || 'seeker';

      if (authToken) {
        localStorage.setItem('spaceloop_token', authToken);
        setToken(authToken);
        localStorage.setItem('spaceloop_active_role', currentRole);
        setActiveRole(currentRole);
        setUser(userData);
      }
      return { success: true, user: userData };
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    }
  };

  // Logout handler
  const logout = async () => {
    try {
      if (token) {
        await authApi.logout().catch(() => {});
      }
    } finally {
      localStorage.removeItem('spaceloop_token');
      localStorage.removeItem('spaceloop_active_role');
      setUser(null);
      setToken(null);
      setActiveRole('seeker');
    }
  };

  // Switch context between Seeker, Host, and Admin
  const switchContext = async (targetRole) => {
    setError(null);
    try {
      const response = await authApi.switchContext(targetRole);
      const newRole = response.active_role || targetRole;
      if (response.access_token) {
        localStorage.setItem('spaceloop_token', response.access_token);
        setToken(response.access_token);
      }
      localStorage.setItem('spaceloop_active_role', newRole);
      setActiveRole(newRole);
      if (user) {
        setUser((prev) => ({ ...prev, active_role: newRole }));
      }
      return { success: true, activeRole: newRole };
    } catch (err) {
      setError(err.message || 'Could not switch context');
      throw err;
    }
  };

  // Verification actions
  const verifyStudent = async (studentId, universityEmail) => {
    const res = await verifyApi.verifyStudent({
      student_id: studentId,
      university_email: universityEmail,
    });
    await fetchCurrentUser();
    return res;
  };

  const verifyAadhaar = async (aadhaarNumber) => {
    const res = await verifyApi.verifyAadhaar({
      aadhaar_number: aadhaarNumber,
    });
    await fetchCurrentUser();
    return res;
  };

  const verifyHost = async (consumerNumber, discomProvider, upiVpa) => {
    const res = await verifyApi.verifyHost({
      consumer_number: consumerNumber,
      discom_provider: discomProvider,
      upi_vpa: upiVpa,
    });
    await fetchCurrentUser();
    return res;
  };

  const isSeeker = activeRole === 'seeker';
  const isHost = activeRole === 'host' || user?.is_host || user?.role === 'host';
  const isAdmin = activeRole === 'admin' || user?.is_admin || user?.role === 'admin';

  const value = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    activeRole,
    loading,
    error,
    isSeeker,
    isHost,
    isAdmin,
    login,
    register,
    logout,
    switchContext,
    refreshUser: fetchCurrentUser,
    verifyStudent,
    verifyAadhaar,
    verifyHost,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
