import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { RoleRoute } from './RoleRoute';

// Public & Marketplace Pages
import { LandingPage } from '../pages/LandingPage';
import { ExploreSpaces } from '../pages/ExploreSpaces';
import { SpaceDetails } from '../pages/SpaceDetails';
import { BookingCheckout } from '../pages/BookingCheckout';
import { BookingAccess } from '../pages/BookingAccess';
import { AuthPage } from '../pages/AuthPage';
import { NotFound } from '../pages/NotFound';

// Role-Based Portals
import { SeekerPortal } from '../pages/seeker/SeekerPortal';
import { HostPortal } from '../pages/host/HostPortal';
import { HostListingForm } from '../pages/host/HostListingForm';
import { AdminPortal } from '../pages/admin/AdminPortal';

export const AppRoutes = () => {
  return (
    <Routes>
      {/* =========================================================================
          1. SEEKER PORTAL (Role-Protected: Seeker Entry Point -> /seeker)
         ========================================================================= */}
      <Route
        path="/seeker"
        element={
          <RoleRoute role="seeker">
            <SeekerPortal />
          </RoleRoute>
        }
      />
      <Route
        path="/seeker/*"
        element={
          <RoleRoute role="seeker">
            <SeekerPortal />
          </RoleRoute>
        }
      />
      <Route
        path="/bookings"
        element={
          <RoleRoute role="seeker">
            <SeekerPortal initialTab="bookings" />
          </RoleRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <RoleRoute role="seeker">
            <SeekerPortal initialTab="profile" />
          </RoleRoute>
        }
      />

      {/* =========================================================================
          2. HOST PORTAL (Role-Protected: Host Entry Point -> /host)
         ========================================================================= */}
      <Route
        path="/host"
        element={
          <RoleRoute role="host">
            <HostPortal />
          </RoleRoute>
        }
      />
      <Route
        path="/host/*"
        element={
          <RoleRoute role="host">
            <HostPortal />
          </RoleRoute>
        }
      />
      <Route
        path="/host/spaces/new"
        element={
          <RoleRoute role="host">
            <HostPortal initialTab="new-space" />
          </RoleRoute>
        }
      />
      <Route
        path="/host/spaces/:id/edit"
        element={
          <RoleRoute role="host">
            <HostListingForm />
          </RoleRoute>
        }
      />
      <Route
        path="/host/earnings"
        element={
          <RoleRoute role="host">
            <HostPortal initialTab="earnings" />
          </RoleRoute>
        }
      />
      <Route
        path="/host/reservations"
        element={
          <RoleRoute role="host">
            <HostPortal initialTab="bookings" />
          </RoleRoute>
        }
      />

      {/* =========================================================================
          3. ADMIN PORTAL (Strictly Restricted: Admin Entry Point -> /admin)
         ========================================================================= */}
      <Route
        path="/admin"
        element={
          <RoleRoute role="admin">
            <AdminPortal />
          </RoleRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <RoleRoute role="admin">
            <AdminPortal />
          </RoleRoute>
        }
      />

      {/* =========================================================================
          4. PUBLIC MARKETPLACE & SHARED EXPERIENCE (Wrapped in MainLayout)
         ========================================================================= */}
      <Route element={<MainLayout />}>
        {/* Landing Page & Discovery */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/explore" element={<ExploreSpaces />} />
        <Route path="/spaces/:id" element={<SpaceDetails />} />

        {/* Checkout & Physical Access */}
        <Route path="/checkout/:spaceId" element={<BookingCheckout />} />
        <Route path="/booking/:id/access" element={<BookingAccess />} />
        <Route path="/access/:id" element={<BookingAccess />} />

        {/* Authentication */}
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/login" element={<Navigate to="/auth" replace />} />
        <Route path="/register" element={<Navigate to="/auth" replace />} />

        {/* 404 Catch-All */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
