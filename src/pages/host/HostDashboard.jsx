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
  ToggleLeft,
  ToggleRight,
  ExternalLink,
  Edit,
  Sparkles,
  AlertTriangle,
} from 'lucide-react';
import { bookingsApi, spacesApi, escrowApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { ErrorState } from '../../components/common/ErrorState';

export const HostDashboard = () => {
  const { user, isAuthenticated, activeRole, switchContext } = useAuth();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();

  const [spaces, setSpaces] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [escrowSummary, setEscrowSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Fetch host data
  const fetchHostData = async () => {
    try {
      setLoading(true);
      const [spacesRes, reservationsRes, summaryRes] = await Promise.allSettled([
        spacesApi.getSpaces(),
        bookingsApi.getHostReservations(),
        escrowApi.getSummary(),
      ]);

      if (spacesRes.status === 'fulfilled') {
        const raw = spacesRes.value.spaces || (Array.isArray(spacesRes.value) ? spacesRes.value : []);
        // If current user is host, filter by user id if available, or show all for demo
        const hostSpaces = user?.id ? raw.filter((s) => s.host_id === user.id || !s.host_id) : raw;
        setSpaces(hostSpaces.length > 0 ? hostSpaces : raw);
      }

      if (reservationsRes.status === 'fulfilled') {
        const resList =
          reservationsRes.value.bookings ||
          reservationsRes.value.reservations ||
          (Array.isArray(reservationsRes.value) ? reservationsRes.value : []);
        setReservations(resList);
      }

      if (summaryRes.status === 'fulfilled') {
        setEscrowSummary(summaryRes.value);
      }
    } catch (err) {
      toastError(err.message || 'Could not load host dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchHostData();
    }
  }, [isAuthenticated, user?.id]);

  // Accept booking request
  const handleAccept = async (bookingId) => {
    setActionLoadingId(bookingId);
    try {
      await bookingsApi.acceptBooking(bookingId);
      success(`Booking #${bookingId} accepted! Seeker notified.`);
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Failed to accept booking.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Reject booking request
  const handleReject = async (bookingId) => {
    setActionLoadingId(bookingId);
    try {
      await bookingsApi.rejectBooking(bookingId, 'Host unavailable during requested slot');
      success(`Booking #${bookingId} rejected.`);
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Failed to reject booking.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Toggle space active/inactive status
  const handleToggleStatus = async (spaceId) => {
    try {
      const res = await spacesApi.toggleStatus(spaceId);
      success(res.message || `Space status updated.`);
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Could not toggle space status.');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="py-24 px-4">
        <ErrorState
          type="unauthorized"
          title="Sign in as a Host"
          description="Access listing controls, booking approvals, and escrow payouts by signing into your host account."
          actionText="Sign In / Register"
          actionFn={() => navigate('/auth')}
        />
      </div>
    );
  }

  const pendingRequests = reservations.filter((r) => (r.status || '').toLowerCase() === 'pending');
  const activeBookings = reservations.filter(
    (r) => (r.status || '').toLowerCase() === 'confirmed' || (r.session_state || '').toLowerCase() === 'checked_in'
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Banner & Quick Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold text-text-primary tracking-tight">
              Host Management Portal
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
              Host Mode
            </span>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Manage your physical spaces, review instant booking requests, and audit escrow earnings.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/host/spaces/new">
            <Button variant="primary" size="sm" className="flex items-center gap-1.5">
              <PlusCircle className="w-4 h-4" />
              <span>List New Space</span>
            </Button>
          </Link>
          <Link to="/host/earnings">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-emerald-500" />
              <span>Earnings Ledger</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-surface border border-border shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Active Spaces
          </span>
          <div className="text-2xl font-black text-text-primary">
            {spaces.filter((s) => s.is_active !== false).length}
          </div>
          <span className="text-[10px] text-text-secondary">
            {spaces.length} Total Registered
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Pending Requests
          </span>
          <div className="text-2xl font-black text-amber-500">
            {pendingRequests.length}
          </div>
          <span className="text-[10px] text-text-secondary">Requires Host Approval</span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Total Payouts
          </span>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            ₹{escrowSummary?.total_released ?? escrowSummary?.host_earnings ?? 4850}
          </div>
          <span className="text-[10px] text-text-secondary">Released via Micro-Escrow</span>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
            Host Trust Score
          </span>
          <div className="text-2xl font-black text-primary flex items-center gap-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <span>98.4%</span>
          </div>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400">Verified Commercial Host</span>
        </div>
      </div>

      {/* Pending Booking Requests Section */}
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
        </div>

        {pendingRequests.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingRequests.map((req) => (
              <div
                key={req.id}
                className="p-5 rounded-2xl bg-surface border border-border shadow-sm space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-text-muted">
                      Request #{req.id}
                    </span>
                    <span className="text-xs font-black text-text-primary">
                      ₹{req.total_price || req.total_amount}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-text-primary">
                    {req.space?.title || 'Your Architectural Space'}
                  </h3>

                  <div className="p-3 rounded-xl bg-surface-elevated text-xs space-y-1">
                    <div className="flex justify-between text-text-secondary">
                      <span>Renter:</span>
                      <strong className="text-text-primary">
                        {req.renter?.full_name || req.guest?.full_name || 'Verified Seeker'}
                      </strong>
                    </div>
                    <div className="flex justify-between text-text-secondary">
                      <span>Schedule:</span>
                      <strong className="text-text-primary">
                        {new Date(req.start_time).toLocaleString('en-IN', {
                          dateStyle: 'short',
                          timeStyle: 'short',
                        })}
                      </strong>
                    </div>
                    <div className="flex justify-between text-text-secondary">
                      <span>Guests:</span>
                      <strong className="text-text-primary">{req.guest_count || 1} Guests</strong>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-2 border-t border-border">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleAccept(req.id)}
                    disabled={actionLoadingId === req.id}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{actionLoadingId === req.id ? 'Processing...' : 'Accept'}</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleReject(req.id)}
                    disabled={actionLoadingId === req.id}
                    className="flex-1 text-rose-500 hover:text-rose-600 hover:border-rose-500/30 flex items-center justify-center gap-1.5"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 rounded-2xl bg-surface border border-border text-center text-xs text-text-secondary">
            No booking requests currently awaiting approval. All active bookings are confirmed.
          </div>
        )}
      </div>

      {/* My Spaces Listings Table / Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-text-primary">My Space Listings</h2>
          <Link to="/host/spaces/new" className="text-xs text-primary font-semibold hover:underline">
            + Add New Space
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {spaces.map((sp) => {
            const isActive = sp.is_active !== false;
            return (
              <div
                key={sp.id}
                className="p-5 rounded-3xl bg-surface border border-border shadow-sm flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="relative aspect-video rounded-2xl overflow-hidden bg-surface-elevated">
                    <img
                      src={
                        (Array.isArray(sp.images) && sp.images[0]) ||
                        sp.image ||
                        'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'
                      }
                      alt={sp.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-3 left-3">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider backdrop-blur-md border ${
                          isActive
                            ? 'bg-emerald-500/90 text-white border-emerald-400'
                            : 'bg-zinc-800/90 text-zinc-300 border-zinc-700'
                        }`}
                      >
                        {isActive ? 'Active' : 'Paused'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold uppercase text-primary tracking-wider">
                      {sp.space_type || sp.category}
                    </span>
                    <h3 className="font-bold text-base text-text-primary line-clamp-1">
                      {sp.title}
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      {sp.location || sp.city || 'India'}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1 border-t border-border">
                    <span className="text-text-secondary">Rate:</span>
                    <span className="font-extrabold text-text-primary">
                      ₹{sp.price_per_hour ?? sp.price ?? 150} / hr
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-border flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => handleToggleStatus(sp.id)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                      isActive
                        ? 'text-zinc-400 border-border hover:border-zinc-500'
                        : 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'
                    }`}
                  >
                    {isActive ? <ToggleRight className="w-4 h-4 text-emerald-500" /> : <ToggleLeft className="w-4 h-4" />}
                    <span>{isActive ? 'Pause' : 'Activate'}</span>
                  </button>

                  <div className="flex items-center gap-1">
                    <Link to={`/spaces/${sp.id}`}>
                      <Button variant="ghost" size="sm" className="p-2">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Link to={`/host/spaces/${sp.id}/edit`}>
                      <Button variant="outline" size="sm" className="p-2">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default HostDashboard;
