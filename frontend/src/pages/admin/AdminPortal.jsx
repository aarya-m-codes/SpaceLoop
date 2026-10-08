import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  Calendar,
  DollarSign,
  AlertOctagon,
  ShieldAlert,
  Star,
  ShieldCheck,
  Bell,
  Activity,
  Sliders,
  LogOut,
  FileText,
  UserCheck,
  CheckCircle2,
} from 'lucide-react';
import { PortalLayout } from '../../layouts/PortalLayout';
import { AdminDashboard } from './AdminDashboard';
import { useAuth } from '../../context/AuthContext';
import { ErrorState } from '../../components/common/ErrorState';

export const AdminPortal = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab') || 'dashboard';
  const [activeTab, setActiveTab] = useState(tabParam);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
  };

  // 1. Strict Security Guard: Only Admins permitted
  if (!isAdmin && !(user?.is_admin || user?.role === 'admin')) {
    return (
      <div className="min-h-screen py-24 px-4 flex items-center justify-center bg-background">
        <div className="max-w-md w-full">
          <ErrorState
            type="unauthorized"
            title="Admin Access Denied"
            description="You do not have administrative credentials to enter the SpaceLoop Governance Portal. All unauthorized administrative access attempts are audited."
            actionText="Go to Seeker Portal"
            actionFn={() => navigate('/seeker')}
          />
        </div>
      </div>
    );
  }

  // Exact navigation items required for Admin Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'seekers', label: 'Seekers', icon: UserCheck },
    { id: 'hosts', label: 'Hosts', icon: Building2 },
    { id: 'spaces', label: 'Spaces', icon: Building2 },
    { id: 'approvals', label: 'Space Approvals', icon: CheckCircle2 },
    { id: 'bookings', label: 'Bookings', icon: Calendar },
    { id: 'payments', label: 'Payments', icon: DollarSign },
    { id: 'disputes', label: 'Disputes', icon: AlertOctagon },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'fraud', label: 'Fraud / Risk', icon: ShieldAlert },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'audit', label: 'Activity / Audit', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Sliders },
    {
      id: 'logout',
      label: 'Logout',
      icon: LogOut,
      action: async () => {
        await logout();
        navigate('/');
      },
    },
  ];

  // Map admin portal tabs to AdminDashboard internal tab and pre-filters
  const getTabConfig = () => {
    switch (activeTab) {
      case 'dashboard':
        return { tab: 'overview', roleFilter: '', statusFilter: '' };
      case 'users':
        return { tab: 'users', roleFilter: '', statusFilter: '' };
      case 'seekers':
        return { tab: 'users', roleFilter: 'seeker', statusFilter: '' };
      case 'hosts':
        return { tab: 'users', roleFilter: 'host', statusFilter: '' };
      case 'spaces':
        return { tab: 'spaces', roleFilter: '', statusFilter: '' };
      case 'approvals':
        return { tab: 'spaces', roleFilter: '', statusFilter: 'pending' };
      case 'bookings':
        return { tab: 'bookings', roleFilter: '', statusFilter: '' };
      case 'payments':
        return { tab: 'financials', roleFilter: '', statusFilter: '' };
      case 'disputes':
        return { tab: 'disputes', roleFilter: '', statusFilter: '' };
      case 'fraud':
        return { tab: 'fraud', roleFilter: '', statusFilter: '' };
      case 'verification':
        return { tab: 'trust', roleFilter: '', statusFilter: '' };
      case 'reports':
      case 'audit':
      case 'activity':
        return { tab: 'audit', roleFilter: '', statusFilter: '' };
      case 'reviews':
        return { tab: 'spaces', roleFilter: '', statusFilter: '' };
      case 'notifications':
        return { tab: 'audit', roleFilter: '', statusFilter: '' };
      case 'settings':
        return { tab: 'overview', roleFilter: '', statusFilter: '' };
      default:
        return { tab: 'overview', roleFilter: '', statusFilter: '' };
    }
  };

  const config = getTabConfig();

  return (
    <PortalLayout
      portalName="Admin Portal"
      role="admin"
      navItems={navItems}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      <div className="space-y-6">
        {/* Render AdminDashboard with active view and filters */}
        <AdminDashboard
          initialTab={config.tab}
          initialRoleFilter={config.roleFilter}
          initialSpaceStatusFilter={config.statusFilter}
        />
      </div>
    </PortalLayout>
  );
};

export default AdminPortal;
