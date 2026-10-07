import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { LandingPage } from '../pages/LandingPage';
import { ExploreSpaces } from '../pages/ExploreSpaces';
import { SpaceDetails } from '../pages/SpaceDetails';
import { BookingCheckout } from '../pages/BookingCheckout';
import { SeekerBookings } from '../pages/SeekerBookings';
import { BookingAccess } from '../pages/BookingAccess';
import { Profile } from '../pages/Profile';
import { AuthPage } from '../pages/AuthPage';
import { HostDashboard } from '../pages/host/HostDashboard';
import { HostListingForm } from '../pages/host/HostListingForm';
import { HostEarnings } from '../pages/host/HostEarnings';
import { AdminDashboard } from '../pages/admin/AdminDashboard';
import { NotFound } from '../pages/NotFound';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        {/* Marketplace Discovery & Seeker Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/explore" element={<ExploreSpaces />} />
        <Route path="/spaces/:id" element={<SpaceDetails />} />
        <Route path="/checkout/:spaceId" element={<BookingCheckout />} />
        <Route path="/bookings" element={<SeekerBookings />} />
        <Route path="/booking/:id/access" element={<BookingAccess />} />
        <Route path="/profile" element={<Profile />} />

        {/* Authentication */}
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/login" element={<Navigate to="/auth" replace />} />
        <Route path="/register" element={<Navigate to="/auth" replace />} />

        {/* Host Experience Routes */}
        <Route path="/host" element={<HostDashboard />} />
        <Route path="/host/spaces/new" element={<HostListingForm />} />
        <Route path="/host/spaces/:id/edit" element={<HostListingForm />} />
        <Route path="/host/reservations" element={<HostDashboard />} />
        <Route path="/host/earnings" element={<HostEarnings />} />

        {/* Trust & Safety Admin Portal */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* 404 Catch-All */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
