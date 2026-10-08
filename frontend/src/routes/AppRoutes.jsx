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
import { SessionPage } from '../pages/SessionPage';
import { CalculatorPage } from '../pages/CalculatorPage';
import { HowItWorksPage } from '../pages/HowItWorksPage';
import { TrustSafetyPage } from '../pages/TrustSafetyPage';
import { ArchitecturePage } from '../pages/ArchitecturePage';
import { VerifyPage } from '../pages/VerifyPage';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import { PrintableDoorPass } from '../pages/PrintableDoorPass';
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
        path="/dashboard"
        element={
          <RoleRoute role="seeker">
            <SeekerPortal initialTab="overview" />
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
        <Route path="/curated" element={<Navigate to="/explore" replace />} />
        <Route path="/explore-view" element={<Navigate to="/explore" replace />} />
        <Route path="/boutique" element={<Navigate to="/explore" replace />} />

        {/* Space Details & Door Signage */}
        <Route path="/spaces/:id" element={<SpaceDetails />} />
        <Route path="/space/:id" element={<SpaceDetails />} />
        <Route path="/spaces/:id/door-pass" element={<PrintableDoorPass />} />
        <Route path="/space/:id/door-pass" element={<PrintableDoorPass />} />
        <Route path="/space/:id/printable-qr" element={<PrintableDoorPass />} />

        {/* Checkout & Physical Access & Real-Time Session Cockpit */}
        <Route path="/checkout/:spaceId" element={<BookingCheckout />} />
        <Route path="/booking/:id/access" element={<BookingAccess />} />
        <Route path="/access/:id" element={<BookingAccess />} />
        <Route path="/session/:id" element={<SessionPage />} />
        <Route path="/booking/:id/session" element={<SessionPage />} />

        {/* Feature & Public Informational Pages */}
        <Route path="/calculator" element={<CalculatorPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/trust-safety" element={<TrustSafetyPage />} />
        <Route path="/admin/trust-safety" element={<TrustSafetyPage />} />
        <Route path="/architecture" element={<ArchitecturePage />} />

        {/* Email Verification Handlers */}
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
        <Route path="/auth/verify-email/:token" element={<VerifyEmailPage />} />

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
