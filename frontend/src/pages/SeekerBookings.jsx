import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  MapPin,
  KeyRound,
  QrCode,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  ExternalLink,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { bookingsApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import { ErrorState } from '../components/common/ErrorState';

export const SeekerBookings = () => {
  const { isAuthenticated } = useAuth();
  const { success, error: toastError } = useToast();

  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [cancelModalBooking, setCancelModalBooking] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelling, setCancelling] = useState(false);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const res = await bookingsApi.getMyBookings();
      const list =
        res?.data?.items ||
        res?.data?.bookings ||
        res?.bookings ||
        res?.items ||
        (Array.isArray(res?.data) ? res.data : []) ||
        (Array.isArray(res) ? res : []);
      setBookings(Array.isArray(list) ? list : []);
    } catch (err) {
      toastError(err.message || 'Could not fetch your reservations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchBookings();
    }
  }, [isAuthenticated]);

  const handleCancel = async () => {
    if (!cancelModalBooking) return;
    setCancelling(true);
    try {
      // Connect to real backend endpoint POST /api/bookings/<id>/cancel
      const res = await bookingsApi.cancelBooking(cancelModalBooking.id, cancelReason);
      success(
        `Booking cancelled. Refund of ₹${res.refunded_amount || res.refund_amount || 'all eligible funds'} processed to your account.`
      );
      setCancelModalBooking(null);
      setCancelReason('');
      await fetchBookings();
    } catch (err) {
      toastError(err.message || 'Failed to cancel booking.');
    } finally {
      setCancelling(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="py-24 px-4">
        <ErrorState
          type="unauthorized"
          title="Sign in to View Bookings"
          description="Please log in with your SpaceLoop account to access your reservation history and digital access PINs."
          actionText="Sign In"
          actionFn={() => (window.location.href = '/auth')}
        />
      </div>
    );
  }

  const filteredBookings = bookings.filter((b) => {
    const status = (b.status || '').toLowerCase();
    const session = (b.session_state || '').toLowerCase();
    if (activeTab === 'active') return session === 'checked_in' || status === 'active';
    if (activeTab === 'upcoming') return status === 'confirmed' || status === 'pending';
    if (activeTab === 'completed') return status === 'completed' || session === 'checked_out';
    if (activeTab === 'cancelled') return status === 'cancelled' || status === 'rejected' || status === 'disputed';
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-text-primary tracking-tight">
            My Space Reservations
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Track arrival PINs, micro-escrow status, and digital passes for all reserved physical spaces.
          </p>
        </div>
        <Link to="/explore">
          <Button variant="primary" size="sm">
            Book Another Space
          </Button>
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-border text-xs font-semibold">
        {[
          { id: 'all', label: 'All Reservations' },
          { id: 'upcoming', label: 'Upcoming' },
          { id: 'active', label: 'Active Session' },
          { id: 'completed', label: 'Completed' },
          { id: 'cancelled', label: 'Cancelled / Disputed' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-primary text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Bookings List */}
      {loading ? (
        <div className="py-20 text-center">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-xs text-text-secondary">Retrieving your ledger reservations...</p>
        </div>
      ) : filteredBookings.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredBookings.map((b) => {
            const spaceTitle = b.space?.title || 'Physical Architectural Space';
            const location = b.space?.location || b.space?.city || 'India';
            const price = b.total_price || b.total_amount || 0;
            const arrivalPin = b.arrival_pin || b.access_code || '1234';
            const startTimeStr = b.start_time
              ? new Date(b.start_time).toLocaleString('en-IN', {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })
              : 'Upcoming Slot';
            const status = (b.status || 'pending').toLowerCase();
            const escrow = (b.escrow_status || 'held').toLowerCase();

            return (
              <div
                key={b.id}
                className="rounded-3xl bg-surface border border-border p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-5"
              >
                <div className="space-y-3">
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-mono font-bold text-text-muted">
                      #{b.id}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          status === 'confirmed' || status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                            : status === 'cancelled'
                            ? 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
                            : 'bg-primary/10 text-primary border border-primary/20'
                        }`}
                      >
                        {status}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          escrow === 'released'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : escrow === 'refunded'
                            ? 'bg-blue-500/10 text-blue-600'
                            : 'bg-amber-500/10 text-amber-600'
                        }`}
                      >
                        Escrow: {escrow}
                      </span>
                    </div>
                  </div>

                  {/* Title & Location */}
                  <div>
                    <h3 className="text-base font-bold text-text-primary line-clamp-1">
                      {spaceTitle}
                    </h3>
                    <p className="text-xs text-text-secondary flex items-center gap-1 mt-1">
                      <MapPin className="w-3.5 h-3.5 text-text-muted shrink-0" />
                      <span>{location}</span>
                    </p>
                  </div>

                  {/* Schedule & PIN Card */}
                  <div className="grid grid-cols-2 gap-3 p-3.5 rounded-2xl bg-surface-elevated border border-border text-xs">
                    <div>
                      <span className="text-[10px] text-text-muted block">Scheduled Arrival</span>
                      <strong className="text-text-primary block text-[11px] leading-tight mt-0.5">
                        {startTimeStr}
                      </strong>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] text-text-muted block">Arrival PIN</span>
                      <strong className="text-primary font-mono text-base tracking-widest block">
                        {arrivalPin}
                      </strong>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-text-secondary pt-1">
                    <span>
                      Total Paid (Escrow Held): <strong>₹{price}</strong>
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Deposit: ₹{b.escrow_deposit ?? 100}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-border flex items-center justify-between gap-2">
                  <Link to={`/booking/${b.id}/access`} className="flex-1">
                    <Button variant="primary" size="sm" className="w-full flex items-center justify-center gap-1.5">
                      <QrCode className="w-3.5 h-3.5" />
                      <span>Digital Pass</span>
                    </Button>
                  </Link>

                  {status !== 'cancelled' && status !== 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCancelModalBooking(b)}
                      className="text-xs text-rose-500 hover:text-rose-600 hover:border-rose-500/40"
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center rounded-3xl bg-surface border border-border space-y-3">
          <Calendar className="w-10 h-10 text-text-muted mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Reservations Found</h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            You don't have any bookings matching this filter. Explore thousands of verified spaces across India.
          </p>
          <Link to="/explore">
            <Button variant="primary" size="sm" className="mt-2">
              Browse Workspaces
            </Button>
          </Link>
        </div>
      )}

      {/* Cancellation Rule Dialog */}
      {cancelModalBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="max-w-md w-full bg-surface border border-border rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2 text-rose-500 font-bold">
              <AlertTriangle className="w-5 h-5" />
              <span>Confirm Reservation Cancellation</span>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              SpaceLoop calculates cancellations strictly according to our transparent micro-escrow formula:
            </p>

            <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border text-xs space-y-1.5">
              <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-semibold">
                <span>100% Rental Refund</span>
                <span>Refunded</span>
              </div>
              <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-semibold">
                <span>100% Escrow Deposit (₹100)</span>
                <span>Refunded</span>
              </div>
              <div className="flex justify-between text-text-muted text-[11px] pt-1 border-t border-border">
                <span>5% Platform Fee</span>
                <span>Retained by SpaceLoop</span>
              </div>
            </div>

            <textarea
              rows={2}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Reason for cancellation (optional)..."
              className="w-full p-3 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-rose-500"
            />

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCancelModalBooking(null)}
                className="flex-1"
              >
                Keep Booking
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCancel}
                disabled={cancelling}
                className="flex-1 bg-rose-600 hover:bg-rose-700 text-white"
              >
                {cancelling ? 'Refunding...' : 'Confirm Cancel'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SeekerBookings;
