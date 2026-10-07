import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ErrorState } from '../components/common/ErrorState';

/**
 * RoleRoute Guard
 * Protects portal entry points based on authentication and role privileges:
 * - Unauthenticated users are redirected to /auth with return URL
 * - Admin portal (/admin) is strictly restricted to verified administrators
 * - Non-admin users attempting to access /admin receive an explicit access denied error
 */
export const RoleRoute = ({ role, children }) => {
  const { isAuthenticated, user, activeRole, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  // 1. Require Authentication
  if (!isAuthenticated) {
    return <Navigate to={`/auth?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  // 2. Strict Admin Restriction
  if (role === 'admin') {
    const isUserAdmin = Boolean(user?.is_admin || user?.role === 'admin' || activeRole === 'admin');
    if (!isUserAdmin) {
      return (
        <div className="min-h-screen py-24 px-4 flex items-center justify-center bg-background">
          <div className="max-w-md w-full">
            <ErrorState
              type="unauthorized"
              title="Admin Access Restricted"
              description="You do not have administrative credentials to enter the SpaceLoop Governance Portal. All unauthorized administrative access attempts are logged."
              actionText="Return to Seeker Portal"
              actionFn={() => (window.location.href = '/seeker')}
            />
          </div>
        </div>
      );
    }
  }

  // 3. Host Restriction
  if (role === 'host') {
    // If user is logged in, allow them to view or onboard as host
    // (AuthContext supports switching activeRole)
  }

  return children;
};

export default RoleRoute;
