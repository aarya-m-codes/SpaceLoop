import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Infinity,
  Menu,
  X,
  Bell,
  Sun,
  Moon,
  LogOut,
  User,
  Compass,
  Building2,
  Shield,
  ChevronRight,
  ExternalLink,
  Search,
  PlusCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../hooks/useTheme';
import { useToast } from '../context/ToastContext';

export const PortalLayout = ({
  portalName,
  role,
  navItems = [],
  activeTab,
  onTabChange,
  children,
}) => {
  const { user, activeRole, switchContext, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  // Portal Badge Colors
  const badgeConfig = {
    seeker: {
      label: 'Seeker Portal',
      bg: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
      dot: 'bg-emerald-500',
    },
    host: {
      label: 'Host Portal',
      bg: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
      dot: 'bg-indigo-500',
    },
    admin: {
      label: 'Admin Portal',
      bg: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
      dot: 'bg-rose-500',
    },
  }[role] || {
    label: portalName,
    bg: 'bg-primary/10 text-primary border-primary/20',
    dot: 'bg-primary',
  };

  const handleRoleSwitch = async (targetRole) => {
    if (switching || targetRole === activeRole) return;
    setSwitching(true);
    try {
      await switchContext(targetRole);
      success(`Switched to ${targetRole.toUpperCase()} mode`);
      if (targetRole === 'host') {
        navigate('/host');
      } else if (targetRole === 'seeker') {
        navigate('/seeker');
      } else if (targetRole === 'admin') {
        navigate('/admin');
      }
    } catch (err) {
      toastError(err.message || 'Could not switch context');
    } finally {
      setSwitching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    success('Logged out successfully');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col transition-colors duration-250">
      
      {/* ==========================================================================
          PORTAL HEADER (Edge-to-Edge with Extreme Left & Extreme Right Alignment)
         ========================================================================== */}
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-border transition-colors duration-200">
        <div className="w-full px-3 sm:px-4 lg:px-6">
          <div className="flex items-center justify-between h-16 w-full">
            
            {/* Left: Mobile Toggle + Logo + Portal Indicator */}
            <div className="flex items-center gap-2.5 sm:gap-3.5">
              {/* Mobile Sidebar Hamburger */}
              <button
                type="button"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors"
                aria-label="Toggle navigation sidebar"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>

              {/* SpaceLoop Brand Logo */}
              <Link to="/" className="flex items-center gap-2 group">
                <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
                  <Infinity className="w-4 h-4 text-white stroke-[2.5]" />
                </div>
                <span className="font-bold text-base sm:text-lg tracking-tight text-text-primary hidden sm:inline-block">
                  SpaceLoop
                </span>
              </Link>

              {/* Portal Identity Badge */}
              <div
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${badgeConfig.bg}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${badgeConfig.dot} animate-pulse`} />
                <span>{badgeConfig.label}</span>
              </div>
            </div>

            {/* Center: Search input for Seeker / + Add Space for Host */}
            {role === 'seeker' && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const q = e.target.searchQuery?.value;
                  if (q) {
                    navigate(`/explore?search=${encodeURIComponent(q)}`);
                  } else {
                    onTabChange?.('explore');
                  }
                }}
                className="hidden md:flex items-center relative max-w-xs w-full mx-4"
              >
                <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  name="searchQuery"
                  type="text"
                  placeholder="Search spaces, cities, amenities..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary transition-colors"
                />
              </form>
            )}

            {role === 'host' && (
              <div className="hidden sm:flex items-center mx-3">
                <button
                  type="button"
                  onClick={() => onTabChange?.('new-space')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold shadow-sm hover:bg-primary-hover transition-colors"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>+ Add Space</span>
                </button>
              </div>
            )}

            {/* Right: Role Switcher, Notifications, Theme Toggle, Profile & Logout */}
            <div className="flex items-center gap-2 sm:gap-2.5">
              
              {/* Portal Switching: Seeker <-> Host (and Admin if admin user) */}
              <div className="hidden sm:flex items-center bg-surface-elevated p-1 rounded-xl border border-border text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => handleRoleSwitch('seeker')}
                  disabled={switching}
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
                  disabled={switching}
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
                    disabled={switching}
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

              {/* Notifications Toggle */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setNotificationsOpen(!notificationsOpen)}
                  aria-label="View notifications"
                  className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors relative"
                >
                  <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary" />
                </button>

                {/* Notifications Popover */}
                <AnimatePresence>
                  {notificationsOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-72 sm:w-80 rounded-2xl bg-surface border border-border shadow-2xl p-3 z-50 text-xs"
                    >
                      <div className="flex items-center justify-between pb-2 border-b border-border/70 font-semibold text-text-primary">
                        <span>Notifications</span>
                        <span className="text-[10px] text-primary font-normal">Mark all read</span>
                      </div>
                      <div className="py-3 space-y-2 text-text-secondary">
                        <div className="p-2 rounded-xl bg-surface-elevated border border-border/50">
                          <p className="font-medium text-text-primary">Escrow Secured</p>
                          <p className="text-[11px] text-text-muted mt-0.5">
                            Booking #SL-8921 micro-escrow confirmed with instant access PIN.
                          </p>
                        </div>
                        <div className="p-2 rounded-xl bg-surface-elevated border border-border/50">
                          <p className="font-medium text-text-primary">System Notification</p>
                          <p className="text-[11px] text-text-muted mt-0.5">
                            Welcome to the {badgeConfig.label}! All activities are verified.
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Theme Toggle */}
              <button
                type="button"
                onClick={toggleTheme}
                aria-label="Toggle theme"
                className="p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-transparent hover:border-border transition-colors shrink-0"
              >
                {isDark ? <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-primary" /> : <Moon className="w-4 h-4 sm:w-5 sm:h-5" />}
              </button>

              {/* User Identity Pill */}
              <div className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-xl bg-surface-elevated border border-border">
                <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                  {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
                </div>
                <span className="text-xs font-semibold text-text-primary hidden md:inline-block max-w-[110px] truncate">
                  {user?.full_name || user?.email?.split('@')[0]}
                </span>
              </div>

              {/* Logout Button */}
              <button
                type="button"
                onClick={handleLogout}
                aria-label="Sign out"
                title="Sign out"
                className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors"
              >
                <LogOut className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>

            </div>
          </div>
        </div>
      </header>

      {/* ==========================================================================
          PORTAL BODY: Responsive Sidebar + Content Area
         ========================================================================== */}
      <div className="flex-1 flex w-full relative">
        
        {/* Backdrop for mobile drawer */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
            />
          )}
        </AnimatePresence>

        {/* Sidebar */}
        <aside
          className={`fixed top-16 bottom-0 left-0 z-40 w-64 bg-surface border-r border-border flex flex-col justify-between py-4 transition-transform duration-250 md:sticky md:top-16 md:h-[calc(100vh-4rem)] md:translate-x-0 ${
            sidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
          }`}
        >
          {/* Top navigation items */}
          <div className="px-3 space-y-1 overflow-y-auto">
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">
              {badgeConfig.label} Navigation
            </div>

            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    if (item.action) {
                      item.action();
                    } else {
                      onTabChange(item.id);
                    }
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-primary text-white shadow-sm font-semibold'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-text-muted'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge !== undefined && (
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                        isActive ? 'bg-white/20 text-white' : 'bg-surface-elevated text-primary'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Bottom Sidebar: Return to Marketplace / Switch */}
          <div className="px-3 pt-3 border-t border-border/60 space-y-1">
            <Link
              to="/"
              className="flex items-center justify-between px-3 py-2 rounded-xl text-xs text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
            >
              <span>Public Marketplace</span>
              <ExternalLink className="w-3.5 h-3.5 text-text-muted" />
            </Link>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 w-full min-w-0 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>

      </div>

    </div>
  );
};

export default PortalLayout;
