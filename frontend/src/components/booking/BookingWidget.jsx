import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Users,
  ShieldCheck,
  Info,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Lock,
  Sparkles,
} from 'lucide-react';
import { bookingsApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../common/Button';

export const BookingWidget = ({ space }) => {
  const { isAuthenticated, user } = useAuth();
  const { error: toastError } = useToast();
  const navigate = useNavigate();

  // Date & Duration state
  const [selectedDate, setSelectedDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [startHour, setStartHour] = useState(10); // 10:00 AM
  const [durationHours, setDurationHours] = useState(2); // 2 hours
  const [guestCount, setGuestCount] = useState(2);

  // Authoritative Backend Price Calculation State
  const [precheckData, setPrecheckData] = useState(null);
  const [loadingPrecheck, setLoadingPrecheck] = useState(false);
  const [precheckError, setPrecheckError] = useState('');
  const [showDepositModal, setShowDepositModal] = useState(false);

  // Call backend precheck whenever parameters change
  useEffect(() => {
    if (!space?.id || !selectedDate) return;

    let isMounted = true;
    const fetchPrecheck = async () => {
      setLoadingPrecheck(true);
      setPrecheckError('');

      try {
        const start = new Date(`${selectedDate}T${String(startHour).padStart(2, '0')}:00:00`);
        const end = new Date(start.getTime() + durationHours * 3600 * 1000);

        // Strict authoritative call to POST /api/bookings/precheck
        const response = await bookingsApi.precheck({
          space_id: space.id,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          guest_count: guestCount,
        });

        if (isMounted) {
          setPrecheckData(response);
          setPrecheckError('');
        }
      } catch (err) {
        if (isMounted) {
          setPrecheckData(null);
          setPrecheckError(err.message || 'Selected time is unavailable or conflicts with existing booking.');
        }
      } finally {
        if (isMounted) {
          setLoadingPrecheck(false);
        }
      }
    };

    fetchPrecheck();
    return () => {
      isMounted = false;
    };
  }, [space?.id, selectedDate, startHour, durationHours, guestCount]);

  const handleProceedToCheckout = () => {
    if (!isAuthenticated) {
      navigate('/auth', { state: { from: `/spaces/${space.id}` } });
      return;
    }

    if (!precheckData) {
      toastError(precheckError || 'Please resolve booking conflict before proceeding.');
      return;
    }

    const start = new Date(`${selectedDate}T${String(startHour).padStart(2, '0')}:00:00`);
    const end = new Date(start.getTime() + durationHours * 3600 * 1000);

    navigate(`/checkout/${space.id}`, {
      state: {
        space,
        precheck: precheckData,
        bookingParams: {
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          duration_hours: durationHours,
          guest_count: guestCount,
        },
      },
    });
  };

  const hourlyRate = space?.price_per_hour ?? space?.price ?? 150;

  return (
    <div className="rounded-3xl bg-surface border border-border p-6 shadow-xl space-y-6 sticky top-24">
      {/* Price Header */}
      <div className="flex items-baseline justify-between border-b border-border pb-4">
        <div>
          <span className="text-3xl font-black text-text-primary">
            ₹{hourlyRate}
          </span>
          <span className="text-xs text-text-secondary font-medium"> / hour</span>
        </div>
        <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
          Instant Keyless PIN
        </span>
      </div>

      {/* Date & Time Selectors */}
      <div className="space-y-4 text-xs">
        {/* Date Selector */}
        <div>
          <label className="block font-semibold text-text-secondary mb-1">Reservation Date</label>
          <div className="relative">
            <Calendar className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="date"
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-medium"
            />
          </div>
        </div>

        {/* Start Hour & Duration */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block font-semibold text-text-secondary mb-1">Start Time</label>
            <div className="relative">
              <Clock className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <select
                value={startHour}
                onChange={(e) => setStartHour(Number(e.target.value))}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-medium"
              >
                {Array.from({ length: 15 }, (_, i) => i + 8).map((hour) => (
                  <option key={hour} value={hour}>
                    {hour % 12 === 0 ? 12 : hour % 12}:00 {hour >= 12 ? 'PM' : 'AM'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-text-secondary mb-1">Duration</label>
            <select
              value={durationHours}
              onChange={(e) => setDurationHours(Number(e.target.value))}
              className="w-full px-3 py-2.5 rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-medium"
            >
              {[1, 2, 3, 4, 6, 8, 10, 12].map((hrs) => (
                <option key={hrs} value={hrs}>
                  {hrs} {hrs === 1 ? 'Hour' : 'Hours'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Guest Count */}
        <div>
          <label className="block font-semibold text-text-secondary mb-1">Number of Guests</label>
          <div className="relative">
            <Users className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <select
              value={guestCount}
              onChange={(e) => setGuestCount(Number(e.target.value))}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-medium"
            >
              {Array.from({ length: Math.min(space?.capacity || 10, 20) }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n} {n === 1 ? 'Guest' : 'Guests'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Authoritative Backend Price Breakdown */}
      <div className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-2.5 text-xs">
        <div className="flex items-center justify-between text-text-muted">
          <span>Authoritative Backend Quote:</span>
          {loadingPrecheck ? (
            <span className="text-primary font-semibold animate-pulse">Calculating...</span>
          ) : (
            <span className="text-emerald-500 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verified Valid</span>
            </span>
          )}
        </div>

        {precheckData ? (
          <>
            <div className="flex justify-between text-text-secondary">
              <span>
                Rental Subtotal ({durationHours} hr × ₹{hourlyRate})
              </span>
              <span className="font-semibold text-text-primary">
                ₹{precheckData.subtotal ?? precheckData.space_subtotal ?? hourlyRate * durationHours}
              </span>
            </div>

            <div className="flex justify-between text-text-secondary">
              <span className="flex items-center gap-1">
                <span>SpaceLoop Platform Fee (5%)</span>
              </span>
              <span className="font-semibold text-text-primary">
                ₹{precheckData.platform_fee}
              </span>
            </div>

            <div className="flex justify-between text-text-secondary">
              <button
                type="button"
                onClick={() => setShowDepositModal(true)}
                className="flex items-center gap-1 text-primary hover:underline font-medium text-left"
              >
                <span>Refundable Micro-Escrow</span>
                <Info className="w-3.5 h-3.5" />
              </button>
              <span className="font-semibold text-text-primary">
                ₹{precheckData.escrow_deposit ?? 100.0}
              </span>
            </div>

            {user?.is_student_verified && (
              <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-medium pt-1">
                <span className="flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Student Discount (15%)</span>
                </span>
                <span>Active</span>
              </div>
            )}

            <div className="pt-2 border-t border-border flex justify-between text-sm font-extrabold text-text-primary">
              <span>Total Payable</span>
              <span className="text-primary">₹{precheckData.total_amount}</span>
            </div>
          </>
        ) : precheckError ? (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{precheckError}</span>
          </div>
        ) : null}
      </div>

      {/* Action Button */}
      <Button
        variant="primary"
        size="lg"
        onClick={handleProceedToCheckout}
        disabled={loadingPrecheck || !!precheckError}
        className="w-full flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
      >
        <span>Proceed to Reserve & Entry PIN</span>
        <ArrowRight className="w-4 h-4" />
      </Button>

      {/* Safety Notice */}
      <div className="flex items-center justify-center gap-2 text-[11px] text-text-muted">
        <ShieldCheck className="w-4 h-4 text-emerald-500" />
        <span>100% Escrow Protected • Instant 4-Digit Arrival Code</span>
      </div>

      {/* Micro-Escrow ₹100 Explanation Modal */}
      {showDepositModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="max-w-md w-full bg-surface border border-border rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-primary font-bold">
                <ShieldCheck className="w-5 h-5" />
                <span>₹100 Refundable Micro-Escrow Guarantee</span>
              </div>
              <button
                type="button"
                onClick={() => setShowDepositModal(false)}
                className="text-text-muted hover:text-text-primary"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              SpaceLoop uses a deterministic internal ledger to guarantee property integrity and zero-friction entry:
            </p>
            <ul className="text-xs text-text-secondary space-y-2 list-disc pl-4">
              <li>
                <strong>During Booking:</strong> ₹100 is safely held in EscrowTransaction status <code className="bg-surface-elevated px-1 py-0.5 rounded">HELD</code>.
              </li>
              <li>
                <strong>At Checkout:</strong> Following normal checkout, 100% of this ₹100 is automatically released back to the seeker.
              </li>
              <li>
                <strong>Upon Cancellation:</strong> The seeker receives 100% of rental amount + 100% of ₹100 deposit (only the 5% platform fee is retained).
              </li>
            </ul>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDepositModal(false)}
              className="w-full mt-2"
            >
              Understood
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookingWidget;
