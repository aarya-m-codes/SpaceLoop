import React from 'react';
import { useLocation, useOutlet } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Navbar } from '../components/common/Navbar';
import { Footer } from '../components/common/Footer';
import { MobileNav } from '../components/common/MobileNav';
import { PageTransition } from '../components/common/PageTransition';
import { LoopBot } from '../components/ai/LoopBot';

export const MainLayout = () => {
  const location = useLocation();
  const currentOutlet = useOutlet();
  const isLanding = location.pathname === '/';

  return (
    <div className="min-h-screen flex flex-col bg-background text-text-primary overflow-x-hidden transition-colors duration-250 pb-16 md:pb-0">
      <Navbar />
      <main className={`flex-grow flex flex-col w-full relative ${!isLanding ? 'pt-16' : ''}`}>
        <AnimatePresence mode="wait" initial={false}>
          <PageTransition key={location.pathname}>
            {currentOutlet}
          </PageTransition>
        </AnimatePresence>
      </main>
      <Footer />

      {/* Sticky Mobile App Bar */}
      <MobileNav />

      {/* Persistent SpaceLoop Concierge AI */}
      <LoopBot />
    </div>
  );
};

export default MainLayout;
