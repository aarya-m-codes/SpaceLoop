import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Building2,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  PlusCircle,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Radio,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { hostApi, bookingsApi, spacesApi } from '../../../services/api';
import { useAuth } from '../../../context/AuthContext';
import { useToast } from '../../../context/ToastContext';
import { Button } from '../../../components/common/Button';
import { useI18n } from '../../../i18n/I18nContext';

export const OverviewView = () => {
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const { t, formatCurrency } = useI18n();
  const navigate = useNavigate();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getDashboard();
      setDashboardData(res);
    } catch (err) {
      console.warn('Failed to load host dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleAccept = async (bookingId) => {
    try {
      setActionId(bookingId);
      await bookingsApi.acceptBooking(bookingId);
      success(`Booking #${bookingId} accepted! Seeker notified.`);
      await fetchDashboard();
    } catch (err) {
      toastError(err.message || 'Failed to accept booking.');
    } finally {
      setActionId(null);
    }
  };

  const handleReject = async (bookingId) => {
    try {
      setActionId(bookingId);
      await bookingsApi.rejectBooking(bookingId, 'Host unavailable');
      success(`Booking #${bookingId} rejected.`);
      await fetchDashboard();
    } catch (err) {
      toastError(err.message || 'Failed to reject booking.');
    } finally {
      setActionId(null);
    }
  };

  const metrics = dashboardData?.host_metrics || {
    gross_revenue: 6850,
    net_earnings: 6507,
    platform_fee: 343,
    total_hours: 24,
    active_spaces_count: 2,
    total_spaces_count: 2,
    upcoming_count: 1,
    completed_count: 8,
  };

  const spaces = dashboardData?.host_spaces || [];
  const bookings = dashboardData?.host_bookings || [];
  const pendingRequests = bookings.filter((b) => (b.status || '').toLowerCase() === 'pending');
  const activeBookings = bookings.filter(
    (b) => (b.status || '').toLowerCase() === 'confirmed' || (b.session_state || '').toLowerCase() === 'checked_in'
  );

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              Host Operations Command
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
              Host Mode
            </span>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Real-time management for physical listings, pending reservation handshakes, and micro-escrow releases.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/host/spaces/new">
            <Button variant="primary" size="sm" className="flex items-center gap-1.5 shadow-sm">
              <PlusCircle className="w-4 h-4" />
              <span>List New Space</span>
            </Button>
          </Link>
          <Link to="/host/live-sessions">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <Radio className="w-4 h-4 text-emerald-500 animate-pulse" />
              <span>Live Radar</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-surface border border-border space-y-1 shadow-xs">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Active Spaces
          </span>
          <div className="text-2xl font-black text-text-primary">
            {metrics.active_spaces_count || spaces.length || 0}
          </div>
          <span className="text-[10px] text-text-secondary">
            {metrics.total_spaces_count || spaces.length} Registered Premise(s)
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border space-y-1 shadow-xs">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Pending Requests
          </span>
          <div className="text-2xl font-black text-amber-500">
            {pendingRequests.length}
          </div>
          <span className="text-[10px] text-text-secondary">Awaiting Approval</span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border space-y-1 shadow-xs">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Net Payout (95%)
          </span>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {formatCurrency(metrics.net_earnings || 6507)}
          </div>
          <span className="text-[10px] text-text-secondary">5% SpaceLoop Fee Deducted</span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border space-y-1 shadow-xs">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Trust Score (OTI)
          </span>
          <div className="text-2xl font-black text-primary flex items-center gap-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <span>98.4%</span>
          </div>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400">Discom CA Verified</span>
        </div>
      </div>

      {/* Pending Approvals */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <span>Pending Booking Requests</span>
            {pendingRequests.length > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/15 text-amber-600">
                {pendingRequests.length} Action Needed
              </span>
            )}
          </h2>
          <Link to="/host/bookings" className="text-xs font-semibold text-primary hover:underline">
            View All ({bookings.length})
          </Link>
        </div>

        {pendingRequests.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingRequests.map((req) => (
              <div
                key={req.id}
                className="p-5 rounded-2xl bg-surface border border-border shadow-xs space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-text-muted">
                      Request #{req.id}
                    </span>
                    <span className="text-xs font-black text-primary font-mono">
                      {formatCurrency(req.total_amount || req.total_price || 300)}
                    </span>
                  </div>

                  <h3 className="font-bold text-base text-text-primary">
                    {req.space?.title || `Space #${req.space_id}`}
                  </h3>

                  <div className="text-xs text-text-secondary space-y-1">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-text-muted" />
                      <span>
                        {req.start_time
                          ? new Date(req.start_time).toLocaleString('en-IN', {
                              dateStyle: 'medium',
                              timeStyle: 'short',
                            })
                          : 'Upcoming slot'}
                        {' '}({req.duration_hours || req.hours_booked || 2} hrs)
                      </span>
                    </div>
                    <div className="text-text-muted text-[11px]">
                      Seeker: {req.user?.full_name || req.seeker_name || 'Verified Student / Seeker'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-border">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    disabled={actionId === req.id}
                    onClick={() => handleAccept(req.id)}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    <span>Accept</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-rose-600 border-rose-500/20 hover:bg-rose-500/10"
                    disabled={actionId === req.id}
                    onClick={() => handleReject(req.id)}
                  >
                    <XCircle className="w-3.5 h-3.5 mr-1" />
                    <span>Decline</span>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-surface border border-border text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <h4 className="text-sm font-bold text-text-primary">No Pending Approvals</h4>
            <p className="text-xs text-text-secondary">
              All incoming bookings are either accepted or instant-booked via OTI automation.
            </p>
          </div>
        )}
      </div>

      {/* Quick Access Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          to="/host/verification"
          className="p-5 rounded-2xl bg-surface border border-border hover:border-primary/40 transition group space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
          </div>
          <h4 className="text-sm font-bold text-text-primary">Discom CA Verification</h4>
          <p className="text-xs text-text-secondary">
            Authenticate premise ownership via official electricity utility meters.
          </p>
        </Link>

        <Link
          to="/host/calendar"
          className="p-5 rounded-2xl bg-surface border border-border hover:border-primary/40 transition group space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
              <Calendar className="w-4 h-4" />
            </div>
            <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
          </div>
          <h4 className="text-sm font-bold text-text-primary">Operational Calendar</h4>
          <p className="text-xs text-text-secondary">
            View booking overlaps, buffer turnaround windows, and availability.
          </p>
        </Link>

        <Link
          to="/host/access"
          className="p-5 rounded-2xl bg-surface border border-border hover:border-primary/40 transition group space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <Radio className="w-4 h-4" />
            </div>
            <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
          </div>
          <h4 className="text-sm font-bold text-text-primary">Access & Door Passes</h4>
          <p className="text-xs text-text-secondary">
            Print door QR signage and configure 50-meter Haversine GPS perimeters.
          </p>
        </Link>
      </div>
    </div>
  );
};

export default OverviewView;
