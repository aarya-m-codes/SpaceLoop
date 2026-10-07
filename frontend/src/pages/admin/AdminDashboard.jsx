import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  Flame,
  Activity,
  Users,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Bot,
  RefreshCw,
  Eye,
  GitBranch,
  Building,
  Calendar,
  DollarSign,
  Gavel,
  FileText,
  Lock,
  Unlock,
  Sliders,
  Check,
  ChevronRight,
  TrendingUp,
  CreditCard,
  UserCheck,
  AlertOctagon,
  ArrowRight,
  HelpCircle,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import { adminApi, trustSafetyApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { ErrorState } from '../../components/common/ErrorState';

export const AdminDashboard = ({
  initialTab = 'overview',
  initialRoleFilter = '',
  initialSpaceStatusFilter = '',
}) => {
  const { user, isAdmin } = useAuth();
  const { success, error: toastError, info } = useToast();

  // Active navigation tab
  const [activeTab, setActiveTab] = useState(initialTab);
  // 'overview' | 'users' | 'spaces' | 'bookings' | 'financials' | 'disputes' | 'trust' | 'fraud' | 'audit'

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Data states
  const [stats, setStats] = useState(null);
  const [usersList, setUsersList] = useState([]);
  const [spacesList, setSpacesList] = useState([]);
  const [bookingsList, setBookingsList] = useState([]);
  const [financials, setFinancials] = useState({ summary: {}, transactions: [] });
  const [disputesList, setDisputesList] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [fraudAlerts, setFraudAlerts] = useState([]);

  // Filters & Searches
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState(initialRoleFilter);
  const [spaceSearch, setSpaceSearch] = useState('');
  const [spaceStatusFilter, setSpaceStatusFilter] = useState(initialSpaceStatusFilter);
  const [bookingFilter, setBookingFilter] = useState('');

  useEffect(() => {
    if (initialRoleFilter !== undefined) {
      setUserRoleFilter(initialRoleFilter);
    }
  }, [initialRoleFilter]);

  useEffect(() => {
    if (initialSpaceStatusFilter !== undefined) {
      setSpaceStatusFilter(initialSpaceStatusFilter);
    }
  }, [initialSpaceStatusFilter]);

  // Dispute Adjudication Modal state
  const [selectedDispute, setSelectedDispute] = useState(null);
  const [disputeResolution, setDisputeResolution] = useState('REFUND_SEEKER');
  const [disputeNotes, setDisputeNotes] = useState('');
  const [adjudicating, setAdjudicating] = useState(false);

  // Trust & Safety On-Demand Evaluator Form
  const [evalEntityType, setEvalEntityType] = useState('user');
  const [evalEntityId, setEvalEntityId] = useState('1');
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);

  // Graph Inspector
  const [graphEntityType, setGraphEntityType] = useState('user');
  const [graphEntityId, setGraphEntityId] = useState('1');
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);

  // Fetch all primary admin data
  const fetchAllAdminData = async () => {
    try {
      setLoading(true);
      const [
        statsRes,
        usersRes,
        spacesRes,
        bookingsRes,
        finRes,
        disputesRes,
        auditRes,
        assessRes,
        alertsRes,
      ] = await Promise.allSettled([
        adminApi.getStats(),
        adminApi.getUsers(),
        adminApi.getSpaces(),
        adminApi.getBookings(),
        adminApi.getFinancials(),
        adminApi.getDisputes(),
        adminApi.getAuditLogs({ limit: 50 }),
        trustSafetyApi.getAssessments(),
        trustSafetyApi.getFraudAlerts(),
      ]);

      if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
        setStats(statsRes.value.data);
      }
      if (usersRes.status === 'fulfilled') {
        setUsersList(usersRes.value.users || []);
      }
      if (spacesRes.status === 'fulfilled') {
        setSpacesList(spacesRes.value.spaces || []);
      }
      if (bookingsRes.status === 'fulfilled') {
        setBookingsList(bookingsRes.value.bookings || []);
      }
      if (finRes.status === 'fulfilled') {
        setFinancials({
          summary: finRes.value.summary || {},
          transactions: finRes.value.transactions || [],
        });
      }
      if (disputesRes.status === 'fulfilled') {
        setDisputesList(disputesRes.value.disputes || []);
      }
      if (auditRes.status === 'fulfilled') {
        setAuditLogs(auditRes.value.audit_logs || []);
      }
      if (assessRes.status === 'fulfilled') {
        setAssessments(
          assessRes.value.assessments ||
            (Array.isArray(assessRes.value) ? assessRes.value : [])
        );
      }
      if (alertsRes.status === 'fulfilled') {
        setFraudAlerts(
          alertsRes.value.alerts ||
            (Array.isArray(alertsRes.value) ? alertsRes.value : [])
        );
      }
    } catch (err) {
      toastError(err.message || 'Could not load administrative telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin || user?.is_admin || user?.role === 'admin') {
      fetchAllAdminData();
    }
  }, [isAdmin, user]);

  // Handle User Suspend / Reactivate
  const handleToggleUserStatus = async (targetUser) => {
    if (targetUser.id === user?.id) {
      toastError('Cannot suspend your own administrator account.');
      return;
    }
    const willSuspend = targetUser.is_active;
    if (
      !window.confirm(
        `Are you sure you want to ${
          willSuspend ? 'suspend' : 'reactivate'
        } user "${targetUser.full_name}" (${targetUser.email})?`
      )
    ) {
      return;
    }

    try {
      setActionLoading(true);
      const res = await adminApi.toggleUserStatus(targetUser.id);
      success(
        res.message ||
          `User account ${willSuspend ? 'suspended' : 'reactivated'} successfully.`
      );
      // Update local state
      setUsersList((prev) =>
        prev.map((u) =>
          u.id === targetUser.id ? { ...u, is_active: !willSuspend } : u
        )
      );
      // Refresh audit logs
      const auditRes = await adminApi.getAuditLogs({ limit: 50 });
      if (auditRes?.audit_logs) setAuditLogs(auditRes.audit_logs);
    } catch (err) {
      toastError(err.message || 'Failed to update user status.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Space Active / Pause
  const handleToggleSpaceStatus = async (targetSpace) => {
    const willPause = targetSpace.is_active;
    if (
      !window.confirm(
        `Are you sure you want to ${willPause ? 'pause' : 'activate'} space "${
          targetSpace.title
        }"?`
      )
    ) {
      return;
    }

    try {
      setActionLoading(true);
      const res = await adminApi.toggleSpaceStatus(targetSpace.id);
      success(
        res.message ||
          `Listing ${willPause ? 'paused' : 'activated'} successfully.`
      );
      // Update local state
      setSpacesList((prev) =>
        prev.map((sp) =>
          sp.id === targetSpace.id ? { ...sp, is_active: !willPause } : sp
        )
      );
      // Refresh audit logs
      const auditRes = await adminApi.getAuditLogs({ limit: 50 });
      if (auditRes?.audit_logs) setAuditLogs(auditRes.audit_logs);
    } catch (err) {
      toastError(err.message || 'Failed to update space status.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Dispute Adjudication
  const handleAdjudicateDispute = async (e) => {
    e.preventDefault();
    if (!selectedDispute) return;

    try {
      setAdjudicating(true);
      const res = await adminApi.adjudicateDispute(selectedDispute.booking_id, {
        resolution: disputeResolution,
        notes: disputeNotes || 'Resolved through Admin Console.',
      });

      success(
        res.message ||
          `Dispute successfully adjudicated: ${disputeResolution}`
      );
      setSelectedDispute(null);
      setDisputeNotes('');

      // Refresh disputes, bookings, and financials
      const [dRes, bRes, fRes, aRes] = await Promise.all([
        adminApi.getDisputes(),
        adminApi.getBookings(),
        adminApi.getFinancials(),
        adminApi.getAuditLogs({ limit: 50 }),
      ]);
      if (dRes?.disputes) setDisputesList(dRes.disputes);
      if (bRes?.bookings) setBookingsList(bRes.bookings);
      if (fRes) {
        setFinancials({
          summary: fRes.summary || {},
          transactions: fRes.transactions || [],
        });
      }
      if (aRes?.audit_logs) setAuditLogs(aRes.audit_logs);
    } catch (err) {
      toastError(err.message || 'Dispute adjudication failed.');
    } finally {
      setAdjudicating(false);
    }
  };

  // Run On-Demand Graph Evaluation
  const handleRunEvaluation = async (e) => {
    e.preventDefault();
    setEvaluating(true);
    setEvaluationResult(null);

    try {
      const res = await trustSafetyApi.evaluate({
        entity_type: evalEntityType,
        entity_id: evalEntityId,
      });
      setEvaluationResult(res.data || res);
      success('Trust & Safety evaluation completed.');
      const assessRes = await trustSafetyApi.getAssessments();
      if (assessRes?.assessments) setAssessments(assessRes.assessments);
    } catch (err) {
      toastError(err.message || 'Risk evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  // Inspect Entity Graph
  const handleInspectGraph = async (e) => {
    e.preventDefault();
    setGraphLoading(true);
    setGraphData(null);

    try {
      const res = await trustSafetyApi.getGraph(graphEntityType, graphEntityId);
      setGraphData(res.data || res);
      info('Bipartite graph topological data retrieved.');
    } catch (err) {
      toastError(err.message || 'Failed to retrieve entity graph.');
    } finally {
      setGraphLoading(false);
    }
  };

  // Authorization Check
  if (!isAdmin && !(user?.is_admin || user?.role === 'admin')) {
    return (
      <div className="py-24 px-4">
        <ErrorState
          type="unauthorized"
          title="Admin Authorization Required"
          description="Access to the SpaceLoop Admin Console and Governance Architecture is restricted to authorized platform administrators."
          actionText="Return to Explore"
          actionFn={() => (window.location.href = '/explore')}
        />
      </div>
    );
  }

  // Filtered Users
  const filteredUsers = usersList.filter((u) => {
    const matchesSearch =
      !userSearch ||
      (u.full_name &&
        u.full_name.toLowerCase().includes(userSearch.toLowerCase())) ||
      (u.email && u.email.toLowerCase().includes(userSearch.toLowerCase()));
    const matchesRole = !userRoleFilter || u.role === userRoleFilter.toLowerCase();
    return matchesSearch && matchesRole;
  });

  // Filtered Spaces
  const filteredSpaces = spacesList.filter((sp) => {
    const matchesSearch =
      !spaceSearch ||
      (sp.title && sp.title.toLowerCase().includes(spaceSearch.toLowerCase())) ||
      (sp.city && sp.city.toLowerCase().includes(spaceSearch.toLowerCase())) ||
      (sp.location && sp.location.toLowerCase().includes(spaceSearch.toLowerCase()));
    const matchesStatus =
      !spaceStatusFilter ||
      (spaceStatusFilter === 'pending'
        ? sp.status === 'pending' || !sp.is_verified
        : sp.status === spaceStatusFilter);
    return matchesSearch && matchesStatus;
  });

  // Filtered Bookings
  const filteredBookings = bookingsList.filter((b) => {
    if (!bookingFilter) return true;
    if (bookingFilter === 'active_sessions')
      return b.session_state === 'checked_in';
    if (bookingFilter === 'disputed')
      return b.status === 'disputed' || b.escrow_status === 'disputed';
    return b.status === bookingFilter.toLowerCase();
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-black text-text-primary tracking-tight">
              Admin & Governance Console
            </h1>
            <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-rose-600 text-white shadow-sm flex items-center gap-1">
              <Shield className="w-3.5 h-3.5" />
              Restricted
            </span>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1.5 max-w-2xl">
            Deterministic Micro-Escrow Ledger • Autonomous ML Fraud Engine • Dual-System Trust & Safety • Full Identity & Listing Governance
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAllAdminData}
            disabled={loading}
            className="flex items-center gap-2 border-border shadow-sm hover:bg-surface-elevated"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh All Telemetry</span>
          </Button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-border text-xs font-semibold scrollbar-none">
        {[
          { id: 'overview', label: 'Overview', icon: TrendingUp },
          { id: 'users', label: `Users (${usersList.length})`, icon: Users },
          { id: 'spaces', label: `Spaces (${spacesList.length})`, icon: Building },
          { id: 'bookings', label: `Bookings (${bookingsList.length})`, icon: Calendar },
          { id: 'financials', label: 'Micro-Escrow', icon: DollarSign },
          {
            id: 'disputes',
            label: `Disputes (${disputesList.length})`,
            icon: Gavel,
            badge: disputesList.length > 0,
          },
          { id: 'trust', label: `Trust & Safety (${assessments.length})`, icon: Shield },
          { id: 'fraud', label: `ML Fraud Alerts (${fraudAlerts.length})`, icon: AlertOctagon },
          { id: 'audit', label: `Audit Trail (${auditLogs.length})`, icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-2.5 rounded-xl whitespace-nowrap flex items-center gap-2 transition-all cursor-pointer ${
                isActive
                  ? 'bg-primary text-white shadow-sm font-bold'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>

      {/* ==================================================== */}
      {/* TAB 1: OVERVIEW & TELEMETRY                          */}
      {/* ==================================================== */}
      {activeTab === 'overview' && (
        <div className="space-y-8 animate-fade-in">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Users Card */}
            <div className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm hover:border-primary/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Community
                </span>
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-black text-text-primary">
                  {stats?.users?.total ?? usersList.length}
                </div>
                <div className="text-[11px] text-text-secondary mt-1 flex items-center gap-2">
                  <span className="text-emerald-500 font-bold">
                    {stats?.users?.active ?? usersList.filter((u) => u.is_active).length} active
                  </span>
                  •
                  <span>
                    {stats?.users?.verified ?? usersList.filter((u) => u.is_verified || u.is_student_verified || u.is_host_verified).length} verified
                  </span>
                </div>
              </div>
            </div>

            {/* Spaces Card */}
            <div className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm hover:border-primary/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Listings
                </span>
                <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-500">
                  <Building className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-black text-text-primary">
                  {stats?.spaces?.total ?? spacesList.length}
                </div>
                <div className="text-[11px] text-text-secondary mt-1 flex items-center gap-2">
                  <span className="text-emerald-500 font-bold">
                    {stats?.spaces?.active ?? spacesList.filter((s) => s.is_active).length} live
                  </span>
                  •
                  <span>
                    {stats?.spaces?.paused ?? spacesList.filter((s) => !s.is_active).length} paused
                  </span>
                </div>
              </div>
            </div>

            {/* Bookings Card */}
            <div className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm hover:border-primary/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Bookings
                </span>
                <div className="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-500">
                  <Calendar className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-black text-text-primary">
                  {stats?.bookings?.total ?? bookingsList.length}
                </div>
                <div className="text-[11px] text-text-secondary mt-1 flex items-center gap-2">
                  <span className="text-blue-500 font-bold">
                    {stats?.bookings?.active_sessions ?? bookingsList.filter((b) => b.session_state === 'checked_in').length} in session
                  </span>
                  •
                  <span>
                    {stats?.bookings?.completed ?? bookingsList.filter((b) => b.status === 'completed').length} completed
                  </span>
                </div>
              </div>
            </div>

            {/* Escrow & Fees Card */}
            <div className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm hover:border-primary/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Micro-Escrow Ledger
                </span>
                <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                  <DollarSign className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-black text-emerald-500">
                  ₹{stats?.financials?.total_held_escrow ?? financials.summary?.total_held ?? 0}
                </div>
                <div className="text-[11px] text-text-secondary mt-1">
                  Platform Fees: ₹
                  {stats?.financials?.total_platform_fees ?? financials.summary?.total_fees ?? 0}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Operations & Architecture Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Action Navigator */}
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
              <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Sliders className="w-4 h-4 text-primary" />
                Administrative Workflows
              </h2>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('disputes')}
                  className="w-full p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between text-left hover:border-primary transition-colors cursor-pointer"
                >
                  <div>
                    <div className="text-xs font-bold text-text-primary">
                      Review Open Disputes ({disputesList.length})
                    </div>
                    <div className="text-[10px] text-text-secondary mt-0.5">
                      Binding adjudication: Refund seeker, release to host, or 50/50 split
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted" />
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('users')}
                  className="w-full p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between text-left hover:border-primary transition-colors cursor-pointer"
                >
                  <div>
                    <div className="text-xs font-bold text-text-primary">
                      Manage Users & Verifications
                    </div>
                    <div className="text-[10px] text-text-secondary mt-0.5">
                      Inspect trust scores, Aadhaar hashes, student status, and account suspension
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted" />
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('trust')}
                  className="w-full p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between text-left hover:border-primary transition-colors cursor-pointer"
                >
                  <div>
                    <div className="text-xs font-bold text-text-primary">
                      System A: Behavioral Graph Risk
                    </div>
                    <div className="text-[10px] text-text-secondary mt-0.5">
                      Analyze collusion rings, velocity spikes, self-bookings, device reuse
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted" />
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('fraud')}
                  className="w-full p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between text-left hover:border-primary transition-colors cursor-pointer"
                >
                  <div>
                    <div className="text-xs font-bold text-text-primary">
                      System B: Autonomous ML Fraud Engine
                    </div>
                    <div className="text-[10px] text-text-secondary mt-0.5">
                      Inspect anomaly score alerts and triggered policy rules
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted" />
                </button>
              </div>
            </div>

            {/* Deterministic Rules & Micro-Escrow Ledger Invariants */}
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-4 lg:col-span-2">
              <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                SpaceLoop Marketplace Governance Invariants
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border space-y-1.5">
                  <div className="font-bold text-text-primary flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Micro-Escrow Formula
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed font-mono">
                    Total Paid = Subtotal + round(Subtotal × 0.05, 2) + ₹100.00 Refundable Deposit.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border space-y-1.5">
                  <div className="font-bold text-text-primary flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Cancellation Rule
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    Seeker receives 100% rental + 100% of ₹100 deposit. SpaceLoop retains strictly the 5% platform fee.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border space-y-1.5">
                  <div className="font-bold text-text-primary flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    ML Decision Thresholds
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed font-mono">
                    Risk ≥ 0.80: BLOCK • Risk ≥ 0.60: REVIEW • Risk ≥ 0.40: CHALLENGE • Risk &lt; 0.40: ALLOW.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border space-y-1.5">
                  <div className="font-bold text-text-primary flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Audit & Identity Guarantee
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    All administrative mutations generate immutable AuditLog records with actor ID and delta. Raw Aadhaar numbers are never stored (SHA-256 tokenized).
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 2: USERS MANAGEMENT & VERIFICATION               */}
      {/* ==================================================== */}
      {activeTab === 'users' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-text-primary">
                User Management & Identity Verification
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Inspect accounts, verification status, trust scores, MFA state, and manage suspensions.
              </p>
            </div>

            {/* Filter Bar */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary focus:outline-none focus:border-primary"
                />
              </div>

              <select
                value={userRoleFilter}
                onChange={(e) => setUserRoleFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="">All Roles</option>
                <option value="seeker">Seeker</option>
                <option value="host">Host</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>

          <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated border-b border-border text-text-muted font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Verification</th>
                    <th className="py-3 px-4">Trust Score</th>
                    <th className="py-3 px-4">MFA</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredUsers.length > 0 ? (
                    filteredUsers.map((u) => {
                      const isCurrentUser = u.id === user?.id;
                      return (
                        <tr key={u.id} className="hover:bg-surface-elevated/40 transition-colors">
                          <td className="py-3.5 px-4">
                            <div className="font-bold text-text-primary">{u.full_name}</div>
                            <div className="text-[11px] text-text-muted font-mono">{u.email}</div>
                            <div className="text-[9px] text-text-muted">ID: #{u.id}</div>
                          </td>
                          <td className="py-3.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                u.role === 'admin'
                                  ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                                  : u.role === 'host'
                                  ? 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20'
                                  : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex flex-wrap gap-1">
                              {u.is_student_verified && (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-500/10 text-purple-600 border border-purple-500/20">
                                  Student (-15%)
                                </span>
                              )}
                              {u.is_host_verified && (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-600 border border-blue-500/20">
                                  Host (Discom)
                                </span>
                              )}
                              {(u.is_aadhaar_verified || u.aadhaar_hash) && (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 font-mono">
                                  Aadhaar SHA-256
                                </span>
                              )}
                              {!u.is_student_verified &&
                                !u.is_host_verified &&
                                !u.is_aadhaar_verified &&
                                !u.aadhaar_hash && (
                                  <span className="text-text-muted text-[10px]">Unverified</span>
                                )}
                            </div>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono font-bold text-text-primary">
                                {u.trust_score ?? 100}%
                              </span>
                              <div className="w-12 h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    (u.trust_score ?? 100) >= 80
                                      ? 'bg-emerald-500'
                                      : (u.trust_score ?? 100) >= 50
                                      ? 'bg-amber-500'
                                      : 'bg-rose-500'
                                  }`}
                                  style={{ width: `${Math.min(u.trust_score ?? 100, 100)}%` }}
                                />
                              </div>
                            </div>
                          </td>
                          <td className="py-3.5 px-4">
                            {u.mfa_enabled ? (
                              <span className="text-emerald-500 flex items-center gap-1 font-semibold text-[11px]">
                                <CheckCircle2 className="w-3 h-3" /> Enabled
                              </span>
                            ) : (
                              <span className="text-text-muted text-[11px]">Disabled</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4">
                            {u.is_active ? (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                                Active
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-600 border border-rose-500/20">
                                Suspended
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            {!isCurrentUser && (
                              <Button
                                size="sm"
                                variant={u.is_active ? 'outline' : 'primary'}
                                disabled={actionLoading}
                                onClick={() => handleToggleUserStatus(u)}
                                className="text-[11px] py-1 px-2.5"
                              >
                                {u.is_active ? (
                                  <span className="text-rose-500 flex items-center gap-1">
                                    <Lock className="w-3 h-3" /> Suspend
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1">
                                    <Unlock className="w-3 h-3" /> Reactivate
                                  </span>
                                )}
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-text-muted text-xs">
                        No users found matching current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 3: SPACES / LISTINGS OVERSIGHT                   */}
      {/* ==================================================== */}
      {activeTab === 'spaces' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-text-primary">
                Physical Spaces & Listing Oversight
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Review listings, location coordinates, host trust scores, and manage pause states.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by title, city, or area..."
                  value={spaceSearch}
                  onChange={(e) => setSpaceSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary focus:outline-none focus:border-primary w-56"
                />
              </div>

              <select
                value={spaceStatusFilter}
                onChange={(e) => setSpaceStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="">All Listings</option>
                <option value="pending">Pending Approvals</option>
                <option value="active">Active / Live</option>
              </select>
            </div>
          </div>

          <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated border-b border-border text-text-muted font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Space Listing</th>
                    <th className="py-3 px-4">Location</th>
                    <th className="py-3 px-4">Host</th>
                    <th className="py-3 px-4">Hourly Rate</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredSpaces.length > 0 ? (
                    filteredSpaces.map((sp) => (
                      <tr key={sp.id} className="hover:bg-surface-elevated/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-bold text-text-primary">{sp.title}</div>
                          <div className="text-[10px] text-text-muted font-mono">Space #{sp.id}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="text-text-primary flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-text-muted" />
                            {sp.city || 'Bengaluru'}
                          </div>
                          <div className="text-[10px] text-text-muted truncate max-w-xs">
                            {sp.location || sp.address_line1}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-text-primary">
                            {sp.host?.full_name || 'Host'}
                          </div>
                          <div className="text-[10px] text-text-muted">
                            Trust: {sp.host?.trust_score ?? 100}%
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-bold text-text-primary">
                          ₹{sp.price_per_hour || sp.hourly_rate || 0}/hr
                        </td>
                        <td className="py-3.5 px-4 capitalize text-text-secondary">
                          {sp.space_type || sp.category || 'desk'}
                        </td>
                        <td className="py-3.5 px-4">
                          {sp.is_active ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                              Active / Live
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20">
                              Paused
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <Button
                            size="sm"
                            variant={sp.is_active ? 'outline' : 'primary'}
                            disabled={actionLoading}
                            onClick={() => handleToggleSpaceStatus(sp)}
                            className="text-[11px] py-1 px-2.5"
                          >
                            {sp.is_active ? 'Pause Listing' : 'Activate'}
                          </Button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-text-muted text-xs">
                        No space listings found matching search criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 4: BOOKINGS & ACTIVE SESSIONS                    */}
      {/* ==================================================== */}
      {activeTab === 'bookings' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-text-primary">
                Bookings & Real-Time Sessions
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Monitor reservation lifecycle, access PINs, physical arrival timestamps, and cancellations.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={bookingFilter}
                onChange={(e) => setBookingFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="">All Bookings</option>
                <option value="active_sessions">Active Sessions (Checked In)</option>
                <option value="disputed">Disputed</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>

          <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated border-b border-border text-text-muted font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Booking ID</th>
                    <th className="py-3 px-4">Space</th>
                    <th className="py-3 px-4">Seeker</th>
                    <th className="py-3 px-4">Session State</th>
                    <th className="py-3 px-4">Escrow & Total</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Arrival PIN</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredBookings.length > 0 ? (
                    filteredBookings.map((b) => (
                      <tr key={b.id} className="hover:bg-surface-elevated/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-bold text-text-primary">
                          #{b.id}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-text-primary">
                            {b.space?.title || `Space #${b.space_id}`}
                          </div>
                          <div className="text-[10px] text-text-muted">
                            {b.total_hours || b.duration_hours || 1} hrs
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-text-primary">
                            {b.guest?.full_name || `Seeker #${b.guest_id}`}
                          </div>
                          <div className="text-[10px] text-text-muted font-mono">
                            {b.guest?.email}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              b.session_state === 'checked_in'
                                ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20 animate-pulse'
                                : b.session_state === 'checked_out'
                                ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                                : 'bg-surface-elevated text-text-muted'
                            }`}
                          >
                            {b.session_state || 'not_started'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono">
                          <div className="font-bold text-text-primary">₹{b.total_amount}</div>
                          <div className="text-[10px] text-text-muted">
                            Deposit: ₹{b.escrow_deposit || 100} • Fee: ₹{b.platform_fee || 0}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              b.status === 'completed'
                                ? 'bg-emerald-500/10 text-emerald-600'
                                : b.status === 'disputed'
                                ? 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
                                : b.status === 'cancelled'
                                ? 'bg-zinc-500/10 text-zinc-600'
                                : 'bg-amber-500/10 text-amber-600'
                            }`}
                          >
                            {b.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-bold text-primary">
                          {b.arrival_pin || '••••'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-text-muted text-xs">
                        No bookings found matching selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 5: FINANCIALS & MICRO-ESCROW                     */}
      {/* ==================================================== */}
      {activeTab === 'financials' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-text-primary">
              Deterministic Micro-Escrow Ledger
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Auditable internal ledger tracking held deposits, host releases, seeker refunds, and 5% platform fees.
            </p>
          </div>

          {/* Ledger Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Total Held Escrow
              </span>
              <div className="text-2xl font-black text-amber-500 font-mono">
                ₹{financials.summary?.total_held || 0}
              </div>
              <p className="text-[10px] text-text-secondary">Securing active bookings & ₹100 deposits</p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Total Released to Hosts
              </span>
              <div className="text-2xl font-black text-emerald-500 font-mono">
                ₹{financials.summary?.total_released || 0}
              </div>
              <p className="text-[10px] text-text-secondary">Settled post-checkout host payouts</p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Total Refunded to Seekers
              </span>
              <div className="text-2xl font-black text-blue-500 font-mono">
                ₹{financials.summary?.total_refunded || 0}
              </div>
              <p className="text-[10px] text-text-secondary">100% security deposits & cancellations</p>
            </div>

            <div className="p-5 rounded-3xl bg-surface border border-border space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Platform Fees Retained (5%)
              </span>
              <div className="text-2xl font-black text-primary font-mono">
                ₹{financials.summary?.total_fees || 0}
              </div>
              <p className="text-[10px] text-text-secondary">SpaceLoop retained facilitation revenue</p>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm">
            <div className="p-4 bg-surface-elevated border-b border-border font-bold text-xs text-text-primary">
              Immutable Escrow Transactions Trail
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated/50 border-b border-border text-text-muted font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Tx ID</th>
                    <th className="py-3 px-4">Booking</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Method & VPA</th>
                    <th className="py-3 px-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {financials.transactions && financials.transactions.length > 0 ? (
                    financials.transactions.map((tx) => (
                      <tr key={tx.id} className="hover:bg-surface-elevated/40 transition-colors font-mono">
                        <td className="py-3 px-4 font-bold text-text-primary">#{tx.id}</td>
                        <td className="py-3 px-4 text-text-secondary">Booking #{tx.booking_id}</td>
                        <td className="py-3 px-4 capitalize font-sans">
                          <span className="px-2 py-0.5 rounded-md bg-surface-elevated border border-border text-[10px] font-bold text-text-primary">
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-sans">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              (tx.status || '').toUpperCase() === 'RELEASED'
                                ? 'bg-emerald-500/10 text-emerald-600'
                                : (tx.status || '').toUpperCase() === 'REFUNDED'
                                ? 'bg-blue-500/10 text-blue-600'
                                : (tx.status || '').toUpperCase() === 'HELD'
                                ? 'bg-amber-500/10 text-amber-600'
                                : 'bg-zinc-500/10 text-zinc-600'
                            }`}
                          >
                            {tx.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-bold text-text-primary">
                          ₹{tx.amount || tx.held_amount}
                        </td>
                        <td className="py-3 px-4 text-[11px] text-text-muted font-sans truncate max-w-xs">
                          {tx.upi_vpa || tx.payment_method || 'UPI Mock Adapter'}
                        </td>
                        <td className="py-3 px-4 text-[10px] text-text-muted">
                          {tx.created_at ? new Date(tx.created_at).toLocaleString() : 'Recent'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-text-muted text-xs">
                        No financial transactions recorded in ledger.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 6: DISPUTES ADJUDICATION WORKFLOW                */}
      {/* ==================================================== */}
      {activeTab === 'disputes' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Gavel className="w-5 h-5 text-primary" />
              Dispute Review & Binding Adjudication
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Review seeker and host claims, inspect held funds, and execute authoritative micro-escrow settlements.
            </p>
          </div>

          {disputesList.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {disputesList.map((d) => (
                <div
                  key={d.booking_id}
                  className="p-6 rounded-3xl bg-surface border border-border space-y-4 shadow-sm"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-base text-text-primary">
                        Dispute on Booking #{d.booking_id}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-600 border border-rose-500/20">
                        {d.status || 'Disputed'}
                      </span>
                    </div>

                    <div className="text-xs font-mono font-bold text-emerald-500">
                      Escrow Held: ₹{d.total_amount} (Deposit: ₹{d.escrow_deposit || 100})
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div>
                      <div className="text-text-muted font-bold text-[10px] uppercase">Space</div>
                      <div className="font-bold text-text-primary mt-0.5">{d.space?.title}</div>
                      <div className="text-[11px] text-text-secondary">{d.space?.location}</div>
                    </div>

                    <div>
                      <div className="text-text-muted font-bold text-[10px] uppercase">Seeker</div>
                      <div className="font-bold text-text-primary mt-0.5">{d.seeker?.name}</div>
                      <div className="text-[11px] text-text-muted font-mono">{d.seeker?.email}</div>
                    </div>

                    <div>
                      <div className="text-text-muted font-bold text-[10px] uppercase">Host</div>
                      <div className="font-bold text-text-primary mt-0.5">{d.host?.name}</div>
                      <div className="text-[11px] text-text-muted">Host ID: #{d.host?.id}</div>
                    </div>
                  </div>

                  {/* Statement */}
                  <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border text-xs space-y-1">
                    <div className="text-[10px] font-bold uppercase text-text-muted">
                      Dispute Claim / Statement
                    </div>
                    <p className="text-text-secondary leading-relaxed">
                      {d.dispute_reason || 'Renter reported physical lock malfunction or access denial.'}
                    </p>
                  </div>

                  {/* Action Button */}
                  <div className="flex justify-end pt-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedDispute(d);
                        setDisputeResolution('REFUND_SEEKER');
                        setDisputeNotes('');
                      }}
                      className="flex items-center gap-1.5"
                    >
                      <Gavel className="w-3.5 h-3.5" />
                      <span>Adjudicate Dispute #{d.booking_id}</span>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 rounded-3xl bg-surface border border-border text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <h3 className="text-sm font-bold text-text-primary">No Active Disputes</h3>
              <p className="text-xs text-text-secondary">
                All bookings and physical micro-escrow transactions are currently resolved or operating normally.
              </p>
            </div>
          )}

          {/* Adjudication Modal */}
          {selectedDispute && (
            <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="w-full max-w-lg rounded-3xl bg-surface border border-border p-6 space-y-5 shadow-2xl animate-scale-up">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                      <Gavel className="w-4 h-4 text-primary" />
                      Adjudicate Dispute #{selectedDispute.booking_id}
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      Binding platform resolution for {selectedDispute.space?.title}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedDispute(null)}
                    className="p-1 rounded-full text-text-muted hover:text-text-primary cursor-pointer"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleAdjudicateDispute} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-text-secondary mb-2">
                      Select Binding Resolution Formula
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-elevated border border-border cursor-pointer hover:border-primary transition-colors">
                        <input
                          type="radio"
                          name="resolution"
                          value="REFUND_SEEKER"
                          checked={disputeResolution === 'REFUND_SEEKER'}
                          onChange={(e) => setDisputeResolution(e.target.value)}
                          className="mt-0.5"
                        />
                        <div className="text-xs">
                          <div className="font-bold text-text-primary">
                            100% Refund to Seeker (REFUND_SEEKER)
                          </div>
                          <div className="text-text-secondary text-[11px] mt-0.5">
                            Rental amount + ₹100 deposit refunded to seeker. Host receives ₹0.
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-elevated border border-border cursor-pointer hover:border-primary transition-colors">
                        <input
                          type="radio"
                          name="resolution"
                          value="RELEASE_TO_HOST"
                          checked={disputeResolution === 'RELEASE_TO_HOST'}
                          onChange={(e) => setDisputeResolution(e.target.value)}
                          className="mt-0.5"
                        />
                        <div className="text-xs">
                          <div className="font-bold text-text-primary">
                            Release to Host (RELEASE_TO_HOST)
                          </div>
                          <div className="text-text-secondary text-[11px] mt-0.5">
                            Rental subtotal payable to host. Seeker deposit refunded if no damages reported.
                          </div>
                        </div>
                      </label>

                      <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-elevated border border-border cursor-pointer hover:border-primary transition-colors">
                        <input
                          type="radio"
                          name="resolution"
                          value="SPLIT_50_50"
                          checked={disputeResolution === 'SPLIT_50_50'}
                          onChange={(e) => setDisputeResolution(e.target.value)}
                          className="mt-0.5"
                        />
                        <div className="text-xs">
                          <div className="font-bold text-text-primary">
                            50 / 50 Equitable Split (SPLIT_50_50)
                          </div>
                          <div className="text-text-secondary text-[11px] mt-0.5">
                            Rental amount divided equally between seeker and host. Security deposit refunded.
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-text-secondary mb-1">
                      Adjudication Notes & Findings
                    </label>
                    <textarea
                      rows="3"
                      required
                      placeholder="Detail reason for decision (logged to immutable audit trail)..."
                      value={disputeNotes}
                      onChange={(e) => setDisputeNotes(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedDispute(null)}
                      disabled={adjudicating}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      disabled={adjudicating}
                    >
                      {adjudicating ? 'Executing Settlement...' : 'Confirm & Execute Settlement'}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 7: TRUST & SAFETY ENGINE (SYSTEM A)              */}
      {/* ==================================================== */}
      {activeTab === 'trust' && (
        <div className="space-y-8 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              System A: Marketplace Trust & Safety Engine
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Behavioral signal extraction, collusion ring graph cycles, forensic narrative explanations.
            </p>
          </div>

          {/* Evaluations List */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider">
              Recorded Assessments ({assessments.length})
            </h3>
            {assessments.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assessments.map((item, idx) => {
                  const riskScore = item.risk_score ?? item.score ?? 0;
                  const signals = item.signals || item.behavioral_signals || [];

                  return (
                    <div
                      key={idx}
                      className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm hover:border-primary/40 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-text-muted">
                          Entity: {item.entity_type || 'USER'} #{item.entity_id}
                        </span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            riskScore >= 0.8
                              ? 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
                              : riskScore >= 0.6
                              ? 'bg-amber-500/10 text-amber-600 border border-amber-500/20'
                              : riskScore >= 0.4
                              ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20'
                              : 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                          }`}
                        >
                          Risk: {(riskScore * 100).toFixed(0)}% •{' '}
                          {riskScore >= 0.8
                            ? 'BLOCK'
                            : riskScore >= 0.6
                            ? 'HOLD/REVIEW'
                            : riskScore >= 0.4
                            ? 'CHALLENGE'
                            : 'ALLOW'}
                        </span>
                      </div>

                      <p className="text-xs text-text-secondary leading-relaxed">
                        {item.forensic_narrative || item.explanation || 'Verified normal activity.'}
                      </p>

                      {signals.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {signals.map((sig, sIdx) => (
                            <span
                              key={sIdx}
                              className="px-2 py-0.5 rounded-md bg-surface-elevated border border-border text-[10px] font-mono text-rose-500"
                            >
                              {sig}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 rounded-3xl bg-surface border border-border text-center text-xs text-text-secondary">
                No active trust assessments logged. Execute an evaluation below to inspect user or listing graph cycles.
              </div>
            )}
          </div>

          {/* Interactive Tools: On-Demand Evaluator & Graph Inspector */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* On-Demand Evaluator Form */}
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Run On-Demand Graph Evaluation
              </h3>
              <form onSubmit={handleRunEvaluation} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                      Entity Type
                    </label>
                    <select
                      value={evalEntityType}
                      onChange={(e) => setEvalEntityType(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                    >
                      <option value="user">User</option>
                      <option value="space">Space</option>
                      <option value="booking">Booking</option>
                      <option value="device">Device</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                      Entity ID
                    </label>
                    <input
                      type="text"
                      required
                      value={evalEntityId}
                      onChange={(e) => setEvalEntityId(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-mono"
                    />
                  </div>
                </div>

                <Button type="submit" variant="primary" size="sm" disabled={evaluating}>
                  {evaluating ? 'Analyzing Graph Cycles...' : 'Execute Forensic Evaluation'}
                </Button>
              </form>

              {evaluationResult && (
                <div className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-text-primary">Evaluation Result</span>
                    <span className="font-mono text-xs font-bold text-primary">
                      {evaluationResult.decision || 'ALLOW'}
                    </span>
                  </div>
                  <p className="text-text-secondary text-[11px]">
                    {evaluationResult.forensic_narrative || evaluationResult.explanation}
                  </p>
                  <pre className="p-3 rounded-xl bg-zinc-950 text-emerald-400 font-mono text-[10px] overflow-x-auto max-h-40">
                    {JSON.stringify(evaluationResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Graph Inspector */}
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-indigo-500" />
                Bipartite Graph Inspector
              </h3>
              <form onSubmit={handleInspectGraph} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                      Entity Type
                    </label>
                    <select
                      value={graphEntityType}
                      onChange={(e) => setGraphEntityType(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                    >
                      <option value="user">User</option>
                      <option value="space">Space</option>
                      <option value="device">Device</option>
                      <option value="ip">IP</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                      Entity ID
                    </label>
                    <input
                      type="text"
                      required
                      value={graphEntityId}
                      onChange={(e) => setGraphEntityId(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-mono"
                    />
                  </div>
                </div>

                <Button type="submit" variant="outline" size="sm" disabled={graphLoading}>
                  {graphLoading ? 'Retrieving Graph...' : 'Inspect Entity Graph'}
                </Button>
              </form>

              {graphData && (
                <div className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-2 text-xs">
                  <div className="font-bold text-text-primary">Topological Graph Data</div>
                  <pre className="p-3 rounded-xl bg-zinc-950 text-emerald-400 font-mono text-[10px] overflow-x-auto max-h-40">
                    {JSON.stringify(graphData, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 8: AUTONOMOUS ML FRAUD ENGINE (SYSTEM B)         */}
      {/* ==================================================== */}
      {activeTab === 'fraud' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-rose-500" />
              System B: Autonomous ML Fraud Engine
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Numerical feature extraction, Isolation Forest anomaly scoring, and triggered deterministic rule alerts.
            </p>
          </div>

          {fraudAlerts.length > 0 ? (
            <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm divide-y divide-border">
              {fraudAlerts.map((al) => {
                const details = al.details || {};
                const score = details.risk_score ?? details.ml_anomaly_score ?? al.anomaly_score ?? 0;
                return (
                  <div key={al.id} className="p-5 space-y-3 hover:bg-surface-elevated/40 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-bold text-text-primary text-xs">{al.title}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-600 border border-rose-500/20">
                          {al.status}
                        </span>
                      </div>

                      <div className="text-xs font-mono font-bold text-rose-500">
                        Risk Score: {(score * 100).toFixed(0)}% [{details.decision || 'REVIEW'}]
                      </div>
                    </div>

                    {/* Features and Triggered Rules */}
                    {details.triggered_rules && details.triggered_rules.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {details.triggered_rules.map((rule, rIdx) => (
                          <span
                            key={rIdx}
                            className="px-2 py-0.5 rounded bg-surface-elevated border border-border text-[10px] font-mono text-amber-500"
                          >
                            Rule: {rule}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[11px] text-text-muted">
                      <span>User ID: #{al.user_id || 'N/A'} • Event ID: #{al.event_id || 'N/A'}</span>
                      <span>{al.created_at ? new Date(al.created_at).toLocaleString() : 'Recent'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-12 rounded-3xl bg-surface border border-border text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <h3 className="text-sm font-bold text-text-primary">No High-Risk Fraud Alerts</h3>
              <p className="text-xs text-text-secondary">
                Autonomous ML feature extraction and anomaly detection indicate normal baseline activity.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ==================================================== */}
      {/* TAB 9: IMMUTABLE AUDIT TRAIL                         */}
      {/* ==================================================== */}
      {activeTab === 'audit' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              Immutable Compliance Audit Trail
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Cryptographically verifiable log of all administrative and financial mutations on SpaceLoop.
            </p>
          </div>

          <div className="rounded-3xl border border-border overflow-hidden bg-surface shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated border-b border-border text-text-muted font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Log ID</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">IP Address</th>
                    <th className="py-3 px-4">Changes</th>
                    <th className="py-3 px-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {auditLogs.length > 0 ? (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-surface-elevated/40 transition-colors">
                        <td className="py-3 px-4 font-bold text-text-primary">#{log.id}</td>
                        <td className="py-3 px-4 font-sans font-bold text-primary">
                          {log.action}
                        </td>
                        <td className="py-3 px-4 text-text-secondary">
                          {log.entity_type} #{log.entity_id}
                        </td>
                        <td className="py-3 px-4 font-sans text-text-primary">
                          {log.admin_name || `User #${log.user_id}`}
                        </td>
                        <td className="py-3 px-4 text-text-muted text-[11px]">
                          {log.ip_address || '127.0.0.1'}
                        </td>
                        <td className="py-3 px-4 text-[10px] text-text-secondary max-w-xs truncate font-mono">
                          {JSON.stringify(log.changes || {})}
                        </td>
                        <td className="py-3 px-4 text-[10px] text-text-muted font-sans">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : 'Recent'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="py-8 text-center text-text-muted text-xs">
                        No audit records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
