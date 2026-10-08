import React, { useState, useEffect, useRef } from 'react';
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
  Infinity,
  ArrowRight,
  User,
  Shield,
  Layers,
  LogOut,
  ChevronDown,
  Building2,
  DollarSign,
} from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from './Button';

export const Navbar = () => {
  const { theme, toggleTheme, isDark } = useTheme();
  const { user, isAuthenticated, activeRole, switchContext, logout } = useAuth();
  const { success, error: toastError } = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [roleSwitching, setRoleSwitching] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const menuRef = useRef(null);

  const isLanding = location.pathname === '/';

  // Close dropdown on click outside or Escape key
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setMenuOpen(false);
        setProfileDropdownOpen(false);
      }
    };
    if (menuOpen || profileDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [menuOpen, profileDropdownOpen]);

  // Close menus on route change
  useEffect(() => {
    setMenuOpen(false);
    setProfileDropdownOpen(false);
  }, [location.pathname]);

  const handleRoleSwitch = async (targetRole) => {
    if (roleSwitching || targetRole === activeRole) return;
    setRoleSwitching(true);
    try {
      await switchContext(targetRole);
      success(`Switched to ${targetRole.toUpperCase()} mode`);
      setProfileDropdownOpen(false);
      setMenuOpen(false);
      if (targetRole === 'host') {
        navigate('/host');
      } else if (targetRole === 'seeker') {
        navigate('/seeker');
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

  const handleHowItWorksClick = (e) => {
    setMenuOpen(false);
    if (isLanding) {
      e.preventDefault();
      const el = document.getElementById('how-it-works');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
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
        { name: 'Admin Console', path: '/admin', icon: Shield },
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
    } else if (path === '/#how-it-works') {
      handleHowItWorksClick(e);
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 w-full glass-panel border-b border-border transition-colors duration-250 ${
        isLanding ? 'landing-header-enter' : ''
      }`}
    >
      <div className="w-full px-3 sm:px-4 lg:px-6">
        <div className="flex items-center justify-between h-16 w-full">
          
          {/* ==========================================================================
              LEFT GROUP: Hamburger Menu beside the Infinity Logo & SpaceLoop Brand
             ========================================================================== */}
          <div className="flex items-center gap-2.5 sm:gap-3" ref={menuRef}>
            
            {/* Hamburger Button */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen(!menuOpen)}
                aria-expanded={menuOpen}
                aria-label="Toggle navigation menu"
                className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary flex items-center justify-center cursor-pointer"
              >
                {menuOpen ? (
                  <X className="w-5 h-5 text-text-primary transition-transform duration-150 rotate-90" />
                ) : (
                  <Menu className="w-5 h-5 text-text-primary transition-transform duration-150" />
                )}
              </button>

              {/* Hamburger Dropdown Menu containing How It Works, List a Space, Bookings */}
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 6, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 6, scale: 0.96 }}
                    transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
                    className="absolute top-full left-0 mt-2.5 w-72 sm:w-80 rounded-2xl glass-panel shadow-2xl border border-border p-2.5 z-50 overflow-hidden"
                  >
                    <div className="px-3 pt-1.5 pb-2 text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center justify-between">
                      <span>Menu</span>
                      <span className="text-[10px] lowercase font-normal opacity-70">esc to close</span>
                    </div>

                    <div className="space-y-1">
                      {/* How It Works */}
                      <Link
                        to="/how-it-works"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-primary group-hover:bg-primary-light transition-colors shrink-0">
                          <Compass className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">How It Works</span>
                          <span className="text-[10px] text-text-muted truncate">The SpaceLoop protocol</span>
                        </div>
                      </Link>

                      {/* Calculator */}
                      <Link
                        to="/calculator"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500/10 transition-colors shrink-0">
                          <DollarSign className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">Earnings Calculator</span>
                          <span className="text-[10px] text-text-muted truncate">Estimate host revenue</span>
                        </div>
                      </Link>

                      {/* Trust & Safety */}
                      <Link
                        to="/trust-safety"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-amber-400 group-hover:bg-amber-500/10 transition-colors shrink-0">
                          <Shield className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">Trust & Safety</span>
                          <span className="text-[10px] text-text-muted truncate">Zero-trust telemetry & OTI</span>
                        </div>
                      </Link>

                      {/* Architecture */}
                      <Link
                        to="/architecture"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-purple-400 group-hover:bg-purple-500/10 transition-colors shrink-0">
                          <Layers className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">System Architecture</span>
                          <span className="text-[10px] text-text-muted truncate">Team LogicLoop blueprint</span>
                        </div>
                      </Link>

                      {/* List a Space */}
                      <Link
                        to="/host"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-primary group-hover:bg-primary-light transition-colors shrink-0">
                          <PlusCircle className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">List a Space</span>
                          <span className="text-[10px] text-text-muted truncate">Monetize your unused space</span>
                        </div>
                      </Link>

                      {/* Bookings */}
                      <Link
                        to="/bookings"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors group"
                      >
                        <div className="w-7 h-7 rounded-lg bg-surface border border-border flex items-center justify-center text-primary group-hover:bg-primary-light transition-colors shrink-0">
                          <Calendar className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-text-primary text-xs">My Bookings</span>
                          <span className="text-[10px] text-text-muted truncate">Manage reservations & passes</span>
                        </div>
                      </Link>
                    </div>

                    <div className="pt-2 mt-2 border-t border-border flex flex-col gap-1.5">
                      <Link
                        to="/explore"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold text-primary hover:bg-primary-light transition-colors"
                      >
                        <span>Explore All Spaces</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Brand Logo with Infinity Symbol */}
            <Link
              to="/"
              className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg"
            >
              <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
                <Infinity className="w-5 h-5 text-white stroke-[2.5]" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg tracking-tight text-text-primary group-hover:text-primary transition-colors duration-200">
                  SpaceLoop
                </span>
              </div>
            </Link>

          </div>

          {/* ==========================================================================
              RIGHT GROUP: Role Switcher, Actions, Profile & Theme Toggle at Extreme Right
             ========================================================================== */}
          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* Role Context Pill (Seeker / Host / Admin) */}
            {isAuthenticated && (
              <div className="hidden sm:flex items-center bg-surface-elevated p-1 rounded-xl border border-border text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => handleRoleSwitch('seeker')}
                  disabled={roleSwitching}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
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
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
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
                    className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
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

            {/* Profile Dropdown or Sign In */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 pl-2.5 rounded-xl border border-border bg-surface-elevated hover:bg-surface transition-colors cursor-pointer"
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
                        to={activeRole === 'host' ? '/host' : (activeRole === 'admin' ? '/admin' : '/seeker')}
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors font-medium"
                      >
                        <Layers className="w-4 h-4 text-primary" />
                        <span>{activeRole === 'host' ? 'Host Dashboard' : (activeRole === 'admin' ? 'Admin Dashboard' : 'Seeker Dashboard')}</span>
                      </Link>

                      <Link
                        to="/seeker?tab=profile"
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
                      >
                        <User className="w-4 h-4 text-primary" />
                        <span>Profile & Verification</span>
                      </Link>

                      <Link
                        to="/seeker?tab=bookings"
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
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-left cursor-pointer"
                        >
                          <Compass className="w-4 h-4 text-emerald-500" />
                          <span>Switch to Seeker View</span>
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleRoleSwitch('host')}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors text-left cursor-pointer"
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
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors text-left cursor-pointer"
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

            {/* Theme Toggle Button at Extreme Right */}
            <motion.button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
              whileTap={{ scale: 0.92, rotate: 15 }}
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.15 }}
              className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary cursor-pointer shrink-0"
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
          </div>

        </div>
      </div>
    </header>
  );
};

export default Navbar;
