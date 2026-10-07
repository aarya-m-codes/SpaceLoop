import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { LandingPage } from '../pages/LandingPage';
import { ExploreSpaces } from '../pages/ExploreSpaces';
import { SpaceDetails } from '../pages/SpaceDetails';
import { NotFound } from '../pages/NotFound';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/explore" element={<ExploreSpaces />} />
        <Route path="/spaces/:id" element={<SpaceDetails />} />
        <Route path="/host" element={<ExploreSpaces />} />
        <Route path="/bookings" element={<ExploreSpaces />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
