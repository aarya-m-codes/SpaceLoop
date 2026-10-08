import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CalendarCheck,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  Radio,
  AlertTriangle,
  Search,
  Filter,
  ShieldCheck,
  User,
  ArrowRight,
} from 'lucide-react';
import { bookingsApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';
import { useI18n } from '../../../i18n/I18nContext';

export const BookingsView = () => {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const { t, formatCurrency } = useI18n();

  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [actionId, setActionId] = useState(null);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const res = await bookingsApi.getHostReservations();
      const list = res.bookings || res.reservations || (Array.isArray(res) ? res : []);
      setBookings(list);
    } catch (err) {
      console.warn('Failed to load host reservations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const handleAccept = async (id) => {
    try {
      setActionId(id);
      await bookingsApi.acceptBooking(id);
      success(`Booking #${id} accepted! Seeker notified.`);
      await fetchBookings();
    } catch (err) {
      toastError(err.message || 'Failed to accept booking.');
    } finally {
      setActionId(null);
    }
  };

  const handleReject = async (id) => {
    try {
      setActionId(id);
      await bookingsApi.rejectBooking(id, 'Unavailable');
      success(`Booking #${id} rejected.`);
      await fetchBookings();
    } catch (err) {
      toastError(err.message || 'Failed to reject booking.');
    } finally {
      setActionId(null);
    }
  };

  const filteredBookings = bookings.filter((b) => {
    if (statusFilter === 'all') return true;
    return (b.status || '').toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-primary tracking-tight">
            Reservation Ledger & Approvals
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Review seeker reservation slots, accept on-demand requests, and monitor check-in arrival handshakes.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {['all', 'pending', 'confirmed', 'checked_in', 'completed', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                statusFilter === st
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-surface border border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {st.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Bookings List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-surface border border-border animate-pulse" />
          ))}
        </div>
      ) : filteredBookings.length === 0 ? (
        <div className="p-12 rounded-2xl bg-surface border border-border text-center space-y-3">
          <CalendarCheck className="w-10 h-10 text-text-muted mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Bookings Found</h3>
          <p className="text-xs text-text-secondary">
            No reservations currently match status "{statusFilter.toUpperCase()}".
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredBookings.map((b) => {
            const status = (b.status || 'confirmed').toLowerCase();
            const isPending = status === 'pending';
            const isActive = status === 'confirmed' || status === 'checked_in';
            return (
              <div
                key={b.id}
                className="p-5 rounded-2xl bg-surface border border-border shadow-xs hover:border-primary/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-text-muted">
                      #{b.id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        isPending
                          ? 'bg-amber-500/15 text-amber-600 border border-amber-500/20'
                          : status === 'completed'
                          ? 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/20'
                          : 'bg-primary/15 text-primary border border-primary/20'
                      }`}
                    >
                      {status.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-black text-text-primary font-mono">
                      {formatCurrency(b.total_amount || b.total_price || 300)}
                    </span>
                  </div>

                  <h3 className="font-bold text-base text-text-primary">
                    {b.space?.title || `Space #${b.space_id}`}
                  </h3>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-text-muted" />
                      <span>
                        {b.start_time
                          ? new Date(b.start_time).toLocaleString('en-IN', {
                              dateStyle: 'medium',
                              timeStyle: 'short',
                            })
                          : 'Upcoming slot'}
                        {' '}({b.duration_hours || 2}h)
                      </span>
                    </span>

                    <span className="flex items-center gap-1 text-text-muted">
                      <User className="w-3.5 h-3.5" />
                      <span>{b.user?.full_name || b.seeker_name || 'Verified Seeker'}</span>
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  {isPending ? (
                    <>
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={actionId === b.id}
                        onClick={() => handleAccept(b.id)}
                        className="bg-emerald-600 hover:bg-emerald-700"
                      >
                        Accept
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={actionId === b.id}
                        onClick={() => handleReject(b.id)}
                        className="text-rose-600 border-rose-500/20 hover:bg-rose-500/10"
                      >
                        Decline
                      </Button>
                    </>
                  ) : isActive ? (
                    <Link to={`/host/live-sessions/${b.id}`}>
                      <Button variant="outline" size="sm" className="flex items-center gap-1.5">
                        <Radio className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
                        <span>Live Radar</span>
                      </Button>
                    </Link>
                  ) : (
                    <Link to={`/session/${b.id}`}>
                      <Button variant="ghost" size="sm" className="text-xs">
                        View Session
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BookingsView;
