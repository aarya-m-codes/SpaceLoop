import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, verifyApi } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('spaceloop_token'));
  const [activeRole, setActiveRole] = useState(() => localStorage.getItem('spaceloop_active_role') || 'seeker');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const normalizeRole = (role) => {
    if (!role) return 'seeker';
    const r = String(role).toLowerCase().trim();
    if (r === 'guest') return 'seeker';
    return r;
  };

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
      const res = await authApi.me();
      const payload = res?.data || res;
      const userData = payload?.user || (payload?.id ? payload : null);

      if (userData && userData.id) {
        setUser(userData);
        const backendRole =
          payload?.active_role ||
          userData.active_context_role ||
          userData.active_role ||
          userData.role ||
          'seeker';
        const resolvedRole = normalizeRole(backendRole);
        setActiveRole(resolvedRole);
        localStorage.setItem('spaceloop_active_role', resolvedRole);
      } else {
        localStorage.removeItem('spaceloop_token');
        localStorage.removeItem('spaceloop_active_role');
        setUser(null);
        setToken(null);
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
      const payload = response?.data || response;

      if (payload?.mfa_required) {
        return {
          mfaRequired: true,
          mfaToken: payload.mfa_token,
          message: payload.message || 'Two-factor authentication required.',
        };
      }

      const authToken = payload?.access_token || payload?.token || response?.access_token || response?.token;
      const userData = payload?.user || (payload?.id ? payload : null);
      const backendRole =
        payload?.active_role ||
        userData?.active_context_role ||
        userData?.active_role ||
        userData?.role ||
        'seeker';
      const currentRole = normalizeRole(backendRole);

      if (authToken) {
        localStorage.setItem('spaceloop_token', authToken);
        setToken(authToken);
      }
      localStorage.setItem('spaceloop_active_role', currentRole);
      setActiveRole(currentRole);
      if (userData) {
        setUser(userData);
      }
      return { success: true, user: userData, activeRole: currentRole, token: authToken };
    } catch (err) {
      const msg =
        typeof err === 'string'
          ? err
          : err?.message && err.message !== '[object Object]'
          ? err.message
          : 'Authentication failed.';
      setError(msg);
      throw err;
    }
  };

  // MFA Challenge Verification handler
  const verifyMfaLogin = async ({ mfaToken, code, recoveryCode }) => {
    setError(null);
    try {
      const res = await authApi.verifyMfa({
        mfa_token: mfaToken,
        code: code ? code.trim() : undefined,
        recovery_code: recoveryCode ? recoveryCode.trim() : undefined,
      });
      const payload = res?.data || res;
      const authToken = payload?.access_token || payload?.token || res?.access_token || res?.token;
      const userData = payload?.user || (payload?.id ? payload : null);
      const backendRole =
        payload?.active_role ||
        userData?.active_context_role ||
        userData?.active_role ||
        userData?.role ||
        'seeker';
      const currentRole = normalizeRole(backendRole);

      if (authToken) {
        localStorage.setItem('spaceloop_token', authToken);
        setToken(authToken);
      }
      localStorage.setItem('spaceloop_active_role', currentRole);
      setActiveRole(currentRole);
      if (userData) {
        setUser(userData);
      }
      return { success: true, user: userData, activeRole: currentRole, token: authToken };
    } catch (err) {
      setError(err.message || 'MFA verification failed');
      throw err;
    }
  };

  // Register handler
  const register = async (formData) => {
    setError(null);
    try {
      const response = await authApi.register(formData);
      const payload = response?.data || response;
      const authToken = payload?.access_token || payload?.token || response?.access_token || response?.token;
      const userData = payload?.user || (payload?.id ? payload : null);
      const backendRole =
        payload?.active_role ||
        userData?.active_context_role ||
        userData?.active_role ||
        userData?.role ||
        formData.role ||
        'seeker';
      const currentRole = normalizeRole(backendRole);

      if (authToken) {
        localStorage.setItem('spaceloop_token', authToken);
        setToken(authToken);
      }
      localStorage.setItem('spaceloop_active_role', currentRole);
      setActiveRole(currentRole);
      if (userData) {
        setUser(userData);
      }
      return { success: true, user: userData, activeRole: currentRole, token: authToken };
    } catch (err) {
      const msg =
        typeof err === 'string'
          ? err
          : err?.message && err.message !== '[object Object]'
          ? err.message
          : 'Registration failed.';
      setError(msg);
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
      const payload = response?.data || response;
      const newRole = normalizeRole(payload?.active_role || targetRole);
      const newToken = payload?.access_token || response?.access_token;
      if (newToken) {
        localStorage.setItem('spaceloop_token', newToken);
        setToken(newToken);
      }
      localStorage.setItem('spaceloop_active_role', newRole);
      setActiveRole(newRole);
      if (user) {
        setUser((prev) => ({ ...prev, active_role: newRole, active_context_role: newRole }));
      }
      return { success: true, activeRole: newRole };
    } catch (err) {
      const msg =
        typeof err === 'string'
          ? err
          : err?.message && err.message !== '[object Object]'
          ? err.message
          : 'Could not switch context';
      setError(msg);
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

  const uRole = (user?.role || activeRole || '').toLowerCase();
  const isSeeker = activeRole === 'seeker' || uRole === 'guest' || uRole === 'seeker';
  const isHost = activeRole === 'host' || Boolean(user?.is_host) || uRole === 'host';
  const isAdmin = activeRole === 'admin' || Boolean(user?.is_admin) || uRole === 'admin';

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
    verifyMfaLogin,
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
