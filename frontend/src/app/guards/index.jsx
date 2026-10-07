import React from 'react';
import { Navigate } from 'react-router-dom';

export const AuthGuard = ({ children, isAuthenticated }) => {
    return isAuthenticated ? children : <Navigate to="/auth" replace />;
};

export const RoleGuard = ({ children, userRole, requiredRole }) => {
    return userRole === requiredRole || userRole === 'admin' ? children : <Navigate to="/" replace />;
};
