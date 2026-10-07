import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Menu, X, Compass, PlusCircle, Calendar } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { Button } from './Button';
import { mobileMenuVariants } from '../../utils/motion';

export const Navbar = () => {
  const { theme, toggleTheme, isDark } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isLanding = location.pathname === '/';

  const navLinks = [
    { name: 'Explore', path: '/explore', icon: Compass },
    { name: 'How It Works', path: '/#how-it-works' },
    { name: 'List a Space', path: '/host', icon: PlusCircle },
    { name: 'Bookings', path: '/bookings', icon: Calendar },
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <motion.header
      initial={isLanding ? { opacity: 0, y: -48 } : { opacity: 1, y: 0 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: isLanding ? 2.0 : 0,
        duration: 0.5,
        ease: [0.16, 1, 0.3, 1],
      }}
      className="fixed top-0 left-0 right-0 z-50 w-full glass-panel border-b border-border transition-colors duration-250"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link
            to="/"
            className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg"
          >
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
              <span className="font-bold text-lg tracking-tight">SL</span>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg tracking-tight text-text-primary group-hover:text-primary transition-colors duration-200">
                SpaceLoop
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5" aria-label="Main Navigation">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`relative px-3.5 py-2 text-sm font-medium rounded-lg transition-colors duration-150 ${
                    active
                      ? 'text-primary'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                  }`}
                >
                  {link.name}
                  {active && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute bottom-0 left-2 right-2 h-0.5 bg-primary rounded-full"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right Controls: Theme Toggle & Actions */}
          <div className="hidden md:flex items-center gap-3">
            {/* Theme Toggle Button with Motion */}
            <motion.button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
              whileTap={{ scale: 0.92, rotate: 15 }}
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.15 }}
              className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={theme}
                  initial={{ opacity: 0, rotate: -90, scale: 0.8 }}
                  animate={{ opacity: 1, rotate: 0, scale: 1 }}
                  exit={{ opacity: 0, rotate: 90, scale: 0.8 }}
                  transition={{ duration: 0.18 }}
                >
                  {isDark ? <Sun className="w-5 h-5 text-primary" /> : <Moon className="w-5 h-5 text-text-secondary" />}
                </motion.div>
              </AnimatePresence>
            </motion.button>

            {/* Auth / Action Button */}
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/explore">
              <Button variant="primary" size="sm">
                Explore Spaces
              </Button>
            </Link>
          </div>

          {/* Mobile Menu & Theme Buttons */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-2 rounded-xl text-text-secondary hover:bg-surface-elevated transition-colors"
            >
              {isDark ? <Sun className="w-5 h-5 text-primary" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle mobile menu"
              className="p-2 rounded-xl text-text-primary hover:bg-surface-elevated transition-colors"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer with Smooth Animation */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            variants={mobileMenuVariants}
            initial="closed"
            animate="open"
            exit="closed"
            className="md:hidden border-t border-border bg-surface overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const active = isActive(link.path);
                return (
                  <Link
                    key={link.name}
                    to={link.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                      active
                        ? 'bg-primary-light text-primary font-semibold'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                    }`}
                  >
                    {Icon && <Icon className="w-4 h-4 shrink-0" />}
                    <span>{link.name}</span>
                  </Link>
                );
              })}
              <div className="pt-3 border-t border-border flex flex-col gap-2">
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" className="w-full">
                    Sign In
                  </Button>
                </Link>
                <Link to="/explore" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" className="w-full">
                    Explore Spaces
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
};

export default Navbar;
