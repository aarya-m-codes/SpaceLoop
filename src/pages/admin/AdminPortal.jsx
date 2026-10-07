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
            actionFn={() => (window.location.href = '/seeker')}
          />
        </div>
      </div>
    );
  }

  // Navigation Items required for Admin Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'hosts', label: 'Hosts', icon: Building2 },
    { id: 'seekers', label: 'Seekers', icon: UserCheck },
    { id: 'spaces', label: 'Spaces', icon: Building2 },
    { id: 'approvals', label: 'Space Approvals', icon: CheckCircle2 },
    { id: 'bookings', label: 'Bookings', icon: Calendar },
    { id: 'payments', label: 'Payments', icon: DollarSign },
    { id: 'disputes', label: 'Disputes', icon: AlertOctagon },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'fraud', label: 'Fraud / Risk', icon: ShieldAlert },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
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

  // Map admin portal tabs to AdminDashboard internal tab
  const getInternalTab = () => {
    switch (activeTab) {
      case 'dashboard':
        return 'overview';
      case 'users':
      case 'hosts':
      case 'seekers':
        return 'users';
      case 'spaces':
      case 'approvals':
        return 'spaces';
      case 'bookings':
        return 'bookings';
      case 'payments':
        return 'financials';
      case 'disputes':
        return 'disputes';
      case 'fraud':
        return 'fraud';
      case 'audit':
      case 'activity':
        return 'audit';
      default:
        return 'overview';
    }
  };

  return (
    <PortalLayout
      portalName="Admin Portal"
      role="admin"
      navItems={navItems}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      <div className="space-y-6">
        {/* Render AdminDashboard with active view */}
        <AdminDashboard initialTab={getInternalTab()} />
      </div>
    </PortalLayout>
  );
};

export default AdminPortal;
