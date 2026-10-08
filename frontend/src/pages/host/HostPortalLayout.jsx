import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  PlusCircle,
  CalendarCheck,
  CalendarDays,
  Radio,
  ShieldCheck,
  Key,
  ClipboardCheck,
  Vault,
  TrendingUp,
  Activity,
  Bell,
  Settings,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const NAV_GROUPS = [
  {
    title: 'Core Management',
    items: [
      { path: '/host', label: 'Overview', icon: LayoutDashboard, end: true },
      { path: '/host/notifications', label: 'Notifications', icon: Bell },
    ],
  },
  {
    title: 'Physical Properties',
    items: [
      { path: '/host/spaces', label: 'My Spaces', icon: Building2 },
      { path: '/host/spaces/new', label: 'List New Space', icon: PlusCircle },
    ],
  },
  {
    title: 'Operations & Sessions',
    items: [
      { path: '/host/bookings', label: 'Reservations', icon: CalendarCheck },
      { path: '/host/calendar', label: 'Calendar', icon: CalendarDays },
      { path: '/host/live-sessions', label: 'Live Radar', icon: Radio, pulse: true },
    ],
  },
  {
    title: 'Security & Trust',
    items: [
      { path: '/host/verification', label: 'Discom CA Verification', icon: ShieldCheck },
      { path: '/host/access', label: 'Access & Door Passes', icon: Key },
    ],
  },
  {
    title: 'Settlement & Micro-Escrow',
    items: [
      { path: '/host/condition-reports', label: 'Condition Audits', icon: ClipboardCheck },
      { path: '/host/escrow', label: 'Escrow Ledger', icon: Vault },
    ],
  },
  {
    title: 'Intelligence & Controls',
    items: [
      { path: '/host/analytics', label: 'Analytics & Yield', icon: TrendingUp },
      { path: '/host/activity', label: 'Audit Trail', icon: Activity },
      { path: '/host/settings', label: 'Host Settings', icon: Settings },
    ],
  },
];

export const HostPortalLayout = () => {
  const { user } = useAuth();
  const location = useLocation();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Mobile Horizontal Subnav Strip */}
      <div className="lg:hidden mb-6 overflow-x-auto pb-2 scrollbar-none">
        <div className="flex items-center gap-1.5 min-w-max">
          {NAV_GROUPS.flatMap((g) => g.items).map((item) => {
            const Icon = item.icon;
            const isActive = item.end
              ? location.pathname === item.path || location.pathname === `${item.path}/` || location.pathname === '/host/overview'
              : location.pathname.startsWith(item.path);
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                  isActive
                    ? 'bg-primary text-white shadow-xs'
                    : 'bg-surface border border-border text-text-muted hover:text-text-primary'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      <div className="flex gap-8 items-start">
        {/* Desktop Sidebar Navigation */}
        <aside className="hidden lg:flex flex-col w-64 rounded-3xl bg-surface border border-border p-4 shrink-0 shadow-xs space-y-6 sticky top-24">
          <div className="px-3 pt-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-primary">
              Section 52 Host Console
            </span>
            <h3 className="text-base font-extrabold text-text-primary">Host Management</h3>
          </div>

          <div className="space-y-5">
            {NAV_GROUPS.map((group, gIdx) => (
              <div key={gIdx} className="space-y-1">
                <span className="px-3 text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  {group.title}
                </span>
                <div className="space-y-0.5 pt-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.end}
                        className={({ isActive }) =>
                          `w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition ${
                            isActive
                              ? 'bg-primary/10 text-primary font-bold'
                              : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                          }`
                        }
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className={`w-4 h-4 ${item.pulse ? 'text-emerald-500 animate-pulse' : ''}`} />
                          <span>{item.label}</span>
                        </div>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Content Outlet View */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default HostPortalLayout;
