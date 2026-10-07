import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sun,
  Moon,
  Menu,
  X,
  Compass,
  PlusCircle,
  Calendar,
  User,
  Shield,
  Layers,
  LogOut,
  ChevronDown,
  Building2,
  DollarSign,
  Sparkles,
} from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from './Button';
import { mobileMenuVariants } from '../../utils/motion';

export const Navbar = () => {
  const { theme, toggleTheme, isDark } = useTheme();
  const { user, isAuthenticated, activeRole, switchContext, logout, isSeeker, isHost, isAdmin } = useAuth();
  const { success, error: toastError } = useToast();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [roleSwitching, setRoleSwitching] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isLanding = location.pathname === '/';

  const handleRoleSwitch = async (targetRole) => {
    if (roleSwitching || targetRole === activeRole) return;
    setRoleSwitching(true);
    try {
      await switchContext(targetRole);
      success(`Switched to ${targetRole.toUpperCase()} mode`);
      setProfileDropdownOpen(false);
      setMobileMenuOpen(false);
      if (targetRole === 'host') {
        navigate('/host');
      } else if (targetRole === 'seeker') {
        navigate('/explore');
      } else if (targetRole === 'admin') {
        navigate('/admin');
      }
    } catch (err) {
      toastError(err.message || 'Failed to switch context');
    } finally {
      setRoleSwitching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    success('Logged out successfully');
    setProfileDropdownOpen(false);
    navigate('/');
  };

  // Dynamic navigation links based on active role context
  const getNavLinks = () => {
    if (activeRole === 'host') {
      return [
        { name: 'Dashboard', path: '/host', icon: Layers },
        { name: 'List a Space', path: '/host/spaces/new', icon: PlusCircle },
        { name: 'Reservations', path: '/host/reservations', icon: Calendar },
        { name: 'Earnings', path: '/host/earnings', icon: DollarSign },
      ];
    }
    if (activeRole === 'admin') {
      return [
        { name: 'Trust & Safety', path: '/admin', icon: Shield },
        { name: 'Explore Spaces', path: '/explore', icon: Compass },
      ];
    }
    // Default Seeker links
    return [
      { name: 'Explore', path: isLanding ? '#spaceloop-content' : '/explore', icon: Compass },
      { name: 'How It Works', path: '/#how-it-works' },
      { name: 'My Bookings', path: '/bookings', icon: Calendar },
      { name: 'List a Space', path: '/host', icon: PlusCircle },
    ];
  };

  const navLinks = getNavLinks();

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const handleNavClick = (e, path) => {
    if (path === '#spaceloop-content') {
      e.preventDefault();
      const el = document.getElementById('spaceloop-content');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 w-full glass-panel border-b border-border transition-colors duration-250 ${
        isLanding ? 'landing-header-enter' : ''
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
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
              const Icon = link.icon;
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={(e) => handleNavClick(e, link.path)}
                  className={`relative px-3.5 py-2 text-sm font-medium rounded-lg transition-colors duration-150 flex items-center gap-1.5 ${
                    active
                      ? 'text-primary'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                  }`}
                >
                  {Icon && <Icon className="w-4 h-4 shrink-0" />}
                  <span>{link.name}</span>
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

          {/* Right Controls: Role Context Switcher, Theme, User Profile */}
          <div className="hidden md:flex items-center gap-3">
            {/* Role Context Pill (Seeker / Host / Admin) */}
            {isAuthenticated && (
              <div className="flex items-center bg-surface-elevated p-1 rounded-xl border border-border text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => handleRoleSwitch('seeker')}
                  disabled={roleSwitching}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    activeRole === 'seeker'
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Seeker
                </button>
                <button
                  type="button"
                  onClick={() => handleRoleSwitch('host')}
                  disabled={roleSwitching}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    activeRole === 'host'
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Host
                </button>
                {(user?.is_admin || user?.role === 'admin') && (
                  <button
                    type="button"
                    onClick={() => handleRoleSwitch('admin')}
                    disabled={roleSwitching}
                    className={`px-2.5 py-1 rounded-lg transition-all ${
                      activeRole === 'admin'
                        ? 'bg-rose-600 text-white shadow-sm'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    Admin
                  </button>
                )}
              </div>
            )}

            {/* Theme Toggle */}
            <motion.button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
              whileTap={{ scale: 0.92, rotate: 15 }}
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.15 }}
              className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors duration-200"
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

            {/* Profile Dropdown or Sign In */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 pl-2.5 rounded-xl border border-border bg-surface-elevated hover:bg-surface transition-colors"
                >
                  <div className="flex flex-col text-right">
                    <span className="text-xs font-bold text-text-primary max-w-[100px] truncate">
                      {user?.full_name || user?.email?.split('@')[0]}
                    </span>
                    <span className="text-[10px] text-primary capitalize font-medium">
                      {activeRole}
                    </span>
                  </div>
                  <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                    {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
                  </div>
                  <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
                </button>

                <AnimatePresence>
                  {profileDropdownOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-56 rounded-2xl bg-surface border border-border shadow-xl p-2 z-50 text-xs"
                    >
                      <div className="px-3 py-2 border-b border-border/60 mb-1">
                        <p className="font-semibold text-text-primary truncate">{user?.full_name}</p>
                        <p className="text-[11px] text-text-muted truncate">{user?.email}</p>
                      </div>

                      <Link
                        to="/profile"
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
                      >
                        <User className="w-4 h-4 text-primary" />
                        <span>Profile & Verification</span>
                      </Link>

                      <Link
                        to="/bookings"
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
                      >
                        <Calendar className="w-4 h-4 text-primary" />
                        <span>My Bookings</span>
                      </Link>

                      {activeRole === 'host' ? (
                        <button
                          type="button"
                          onClick={() => handleRoleSwitch('seeker')}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-left"
                        >
                          <Compass className="w-4 h-4 text-emerald-500" />
                          <span>Switch to Seeker View</span>
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleRoleSwitch('host')}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-left"
                        >
                          <Building2 className="w-4 h-4 text-primary" />
                          <span>Switch to Host View</span>
                        </button>
                      )}

                      {(user?.is_admin || user?.role === 'admin') && (
                        <Link
                          to="/admin"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                        >
                          <Shield className="w-4 h-4" />
                          <span>Trust & Safety Admin</span>
                        </Link>
                      )}

                      <div className="pt-1 border-t border-border/60 mt-1">
                        <button
                          type="button"
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors text-left"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Sign Out</span>
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/auth">
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
            )}
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

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            variants={mobileMenuVariants}
            initial="closed"
            animate="open"
            exit="closed"
            className="md:hidden border-t border-border bg-surface overflow-hidden shadow-2xl"
          >
            <div className="px-4 py-3 space-y-2">
              {/* Context Selector in Mobile */}
              {isAuthenticated && (
                <div className="flex items-center justify-between p-2 rounded-xl bg-surface-elevated border border-border">
                  <span className="text-xs font-semibold text-text-secondary">Mode:</span>
                  <div className="flex gap-1 text-xs">
                    <button
                      type="button"
                      onClick={() => handleRoleSwitch('seeker')}
                      className={`px-3 py-1 rounded-lg ${
                        activeRole === 'seeker' ? 'bg-primary text-white font-bold' : 'text-text-secondary'
                      }`}
                    >
                      Seeker
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRoleSwitch('host')}
                      className={`px-3 py-1 rounded-lg ${
                        activeRole === 'host' ? 'bg-primary text-white font-bold' : 'text-text-secondary'
                      }`}
                    >
                      Host
                    </button>
                    {(user?.is_admin || user?.role === 'admin') && (
                      <button
                        type="button"
                        onClick={() => handleRoleSwitch('admin')}
                        className={`px-3 py-1 rounded-lg ${
                          activeRole === 'admin' ? 'bg-rose-600 text-white font-bold' : 'text-text-secondary'
                        }`}
                      >
                        Admin
                      </button>
                    )}
                  </div>
                </div>
              )}

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
                {isAuthenticated ? (
                  <>
                    <Link to="/profile" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="outline" className="w-full flex items-center justify-center gap-2">
                        <User className="w-4 h-4" />
                        <span>Profile & Verification</span>
                      </Button>
                    </Link>
                    <Button variant="ghost" onClick={handleLogout} className="w-full text-rose-500">
                      Sign Out
                    </Button>
                  </>
                ) : (
                  <>
                    <Link to="/auth" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="outline" className="w-full">
                        Sign In / Register
                      </Button>
                    </Link>
                    <Link to="/explore" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="primary" className="w-full">
                        Explore Spaces
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default Navbar;
