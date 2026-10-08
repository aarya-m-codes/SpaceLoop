import React from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        <p className="text-xs text-text-muted font-medium">Checking session...</p>
      </div>
    );
  }

  // 1. Require Authentication
  if (!isAuthenticated) {
    return <Navigate to={`/auth?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  const uRole = (user?.role || activeRole || '').toLowerCase();
  const isUserAdmin = Boolean(user?.is_admin || uRole === 'admin' || activeRole === 'admin');
  const isUserHost = Boolean(user?.is_host || uRole === 'host' || activeRole === 'host');

  // 2. Strict Admin Restriction
  if (role === 'admin' && !isUserAdmin) {
    return (
      <div className="min-h-screen py-24 px-4 flex items-center justify-center bg-background">
        <div className="max-w-md w-full">
          <ErrorState
            type="unauthorized"
            title="Admin Access Restricted"
            description="You do not have administrative credentials to enter the SpaceLoop Governance Portal. All unauthorized administrative access attempts are logged."
            actionText="Return to Seeker Portal"
            actionFn={() => navigate('/seeker')}
          />
        </div>
      </div>
    );
  }

  // 3. Strict Host Restriction
  if (role === 'host' && !isUserHost && !isUserAdmin) {
    return (
      <div className="min-h-screen py-24 px-4 flex items-center justify-center bg-background">
        <div className="max-w-md w-full">
          <ErrorState
            type="unauthorized"
            title="Host Portal Access Restricted"
            description="You are currently signed in with a Seeker account. Switch to Host mode in your account menu or register as a host to list and manage workspaces."
            actionText="Return to Seeker Dashboard"
            actionFn={() => navigate('/seeker')}
          />
        </div>
      </div>
    );
  }

  return children;
};

export default RoleRoute;
