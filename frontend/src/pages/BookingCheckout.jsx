import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Clock,
  Users,
  MapPin,
  CreditCard,
  QrCode,
  KeyRound,
  ArrowRight,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { bookingsApi, escrowApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';

export const BookingCheckout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { success, error: toastError } = useToast();

  const stateData = location.state || {};
  const { space, precheck, bookingParams } = stateData;

  const [upiVpa, setUpiVpa] = useState('seeker@okhdfcbank');
  const [vpaVerified, setVpaVerified] = useState(false);
  const [verifyingVpa, setVerifyingVpa] = useState(false);
  const [loading, setLoading] = useState(false);
  const [confirmedBooking, setConfirmedBooking] = useState(null);

  if (!space || !precheck || !bookingParams) {
    return (
      <div className="max-w-md mx-auto py-20 px-4 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-text-primary">No Active Booking Session</h2>
        <p className="text-xs text-text-secondary">
          Please select a space and valid time slot before checking out.
        </p>
        <Link to="/explore">
          <Button variant="primary" size="sm">
            Explore Spaces
          </Button>
        </Link>
      </div>
    );
  }

  const handleVerifyVpa = async () => {
    if (!upiVpa || !upiVpa.includes('@')) {
      toastError('Please enter a valid UPI ID (e.g. name@okhdfcbank)');
      return;
    }
    setVerifyingVpa(true);
    try {
      const res = await escrowApi.verifyVpa(upiVpa);
      if (res.valid || res.status === 'valid') {
        setVpaVerified(true);
        success(`UPI ID verified: ${res.account_name || upiVpa}`);
      } else {
        toastError(res.message || 'UPI VPA could not be verified.');
      }
    } catch (err) {
      toastError(err.message || 'UPI validation server unreachable.');
    } finally {
      setVerifyingVpa(false);
    }
  };

  const handleConfirmBooking = async () => {
    setLoading(true);
    try {
      // Connect to real backend endpoint POST /api/bookings
      const bookingPayload = {
        space_id: space.id,
        start_time: bookingParams.start_time,
        end_time: bookingParams.end_time,
        duration_hours: bookingParams.duration_hours,
        guest_count: bookingParams.guest_count,
        subtotal: precheck.subtotal,
        platform_fee: precheck.platform_fee,
        escrow_deposit: precheck.escrow_deposit ?? 100.0,
        total_amount: precheck.total_amount,
        payment_method: 'UPI',
        vpa: upiVpa,
      };

      const result = await bookingsApi.createBooking(bookingPayload);
      const created = result.booking || result;
      setConfirmedBooking(created);
      success('Booking confirmed! Secure arrival PIN generated.');
    } catch (err) {
      toastError(err.message || 'Booking creation failed. Please check schedule availability.');
    } finally {
      setLoading(false);
    }
  };

  const startTimeStr = new Date(bookingParams.start_time).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
  const endTimeStr = new Date(bookingParams.end_time).toLocaleTimeString('en-IN', {
    timeStyle: 'short',
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {!confirmedBooking ? (
        <div className="space-y-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              Finalize Reservation & Micro-Escrow
            </h1>
            <p className="text-xs sm:text-sm text-text-secondary mt-1">
              Your payment is safeguarded in the SpaceLoop escrow ledger until successful check-in and inspection.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Left Column: Space Summary & Time */}
            <div className="md:col-span-7 space-y-6">
              {/* Space Card Summary */}
              <div className="p-5 rounded-2xl bg-surface border border-border flex gap-4 items-center">
                <img
                  src={
                    (Array.isArray(space.images) && space.images[0]) ||
                    space.image ||
                    'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'
                  }
                  alt={space.title}
                  className="w-20 h-20 rounded-xl object-cover border border-border shrink-0"
                />
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                    {space.space_type || space.category}
                  </span>
                  <h3 className="font-bold text-sm text-text-primary line-clamp-1">
                    {space.title}
                  </h3>
                  <p className="text-xs text-text-secondary flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-text-muted shrink-0" />
                    <span>{space.location || space.city}</span>
                  </p>
                </div>
              </div>

              {/* Reservation Schedule Details */}
              <div className="p-5 rounded-2xl bg-surface border border-border space-y-3 text-xs">
                <h4 className="font-bold text-text-primary text-sm">Reservation Window</h4>
                <div className="flex items-center gap-3 text-text-secondary">
                  <Calendar className="w-4 h-4 text-primary shrink-0" />
                  <span>
                    <strong>From:</strong> {startTimeStr}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-text-secondary">
                  <Clock className="w-4 h-4 text-primary shrink-0" />
                  <span>
                    <strong>Until:</strong> {endTimeStr} ({bookingParams.duration_hours} Hours)
                  </span>
                </div>
                <div className="flex items-center gap-3 text-text-secondary">
                  <Users className="w-4 h-4 text-primary shrink-0" />
                  <span>{bookingParams.guest_count} Registered Guests</span>
                </div>
              </div>

              {/* UPI Payment Adapter */}
              <div className="p-5 rounded-2xl bg-surface border border-border space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-text-primary text-sm flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-primary" />
                    <span>UPI Micro-Escrow Authorization</span>
                  </h4>
                  <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    Internal Ledger Mock
                  </span>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-text-secondary">
                    Virtual Payment Address (VPA)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={upiVpa}
                      onChange={(e) => {
                        setUpiVpa(e.target.value);
                        setVpaVerified(false);
                      }}
                      placeholder="e.g. mobile@upi or username@okhdfcbank"
                      className="flex-1 px-3.5 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleVerifyVpa}
                      disabled={verifyingVpa}
                    >
                      {verifyingVpa ? 'Verifying...' : vpaVerified ? 'Verified ✓' : 'Verify'}
                    </Button>
                  </div>
                  <p className="text-[11px] text-text-muted">
                    Test Mode: SpaceLoop internal ledger creates an auditable deposit hold without executing real bank debits.
                  </p>
                </div>
              </div>
            </div>

            {/* Right Column: Ledger Accounting Summary */}
            <div className="md:col-span-5 space-y-6">
              <div className="p-6 rounded-3xl bg-surface border border-border space-y-4 shadow-sm">
                <h3 className="font-bold text-sm text-text-primary border-b border-border pb-3">
                  Authoritative Escrow Breakdown
                </h3>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between text-text-secondary">
                    <span>Space Subtotal</span>
                    <span className="font-semibold text-text-primary">
                      ₹{precheck.subtotal}
                    </span>
                  </div>

                  <div className="flex justify-between text-text-secondary">
                    <span>SpaceLoop Platform Fee (5%)</span>
                    <span className="font-semibold text-text-primary">
                      ₹{precheck.platform_fee}
                    </span>
                  </div>

                  <div className="flex justify-between text-text-secondary">
                    <span className="flex items-center gap-1">
                      <span>Refundable Security Deposit</span>
                    </span>
                    <span className="font-semibold text-text-primary">
                      ₹{precheck.escrow_deposit ?? 100.0}
                    </span>
                  </div>

                  <div className="pt-3 border-t border-border flex justify-between text-base font-black text-text-primary">
                    <span>Total Deposit Hold</span>
                    <span className="text-primary">₹{precheck.total_amount}</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-primary/5 border border-primary/20 text-[11px] text-text-secondary space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-primary">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Refund Guarantee</span>
                  </div>
                  <p>
                    If cancelled before check-in, 100% of rental (₹{precheck.subtotal}) + 100% of deposit (₹100) is returned. Only the 5% platform fee (₹{precheck.platform_fee}) is retained.
                  </p>
                </div>

                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleConfirmBooking}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
                >
                  <KeyRound className="w-4 h-4" />
                  <span>{loading ? 'Securing Escrow...' : `Pay & Hold ₹${precheck.total_amount}`}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Confirmation Receipt & Instant Access PIN */
        <div className="max-w-lg mx-auto bg-surface border border-border rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 text-center">
          <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-widest text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              Booking Confirmed • Escrow Held
            </span>
            <h2 className="text-2xl font-black text-text-primary tracking-tight mt-3">
              You're Ready to Access!
            </h2>
            <p className="text-xs text-text-secondary mt-1">
              Booking ID: <strong className="font-mono text-text-primary">#{confirmedBooking.id}</strong>
            </p>
          </div>

          {/* Secure 4-Digit Arrival PIN Card */}
          <div className="p-5 rounded-2xl bg-surface-elevated border border-border space-y-2">
            <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block">
              Your 4-Digit Arrival Access PIN
            </span>
            <div className="text-4xl font-black tracking-[0.4em] font-mono text-primary py-1">
              {confirmedBooking.arrival_pin || confirmedBooking.access_code || '1234'}
            </div>
            <p className="text-[11px] text-text-secondary">
              Enter this PIN on the smart lock keypad or show the digital pass on arrival.
            </p>
          </div>

          {/* Booking Summary Stats */}
          <div className="grid grid-cols-2 gap-3 text-xs text-left p-4 rounded-xl bg-surface-elevated border border-border">
            <div>
              <span className="text-text-muted block text-[10px]">Space</span>
              <strong className="text-text-primary truncate block">{space.title}</strong>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">Held Escrow Amount</span>
              <strong className="text-text-primary block">₹{confirmedBooking.total_price || confirmedBooking.total_amount}</strong>
            </div>
          </div>

          {/* Action Links */}
          <div className="space-y-2 pt-2">
            <Link to={`/booking/${confirmedBooking.id}/access`}>
              <Button variant="primary" className="w-full flex items-center justify-center gap-2">
                <QrCode className="w-4 h-4" />
                <span>Open Digital Pass & Check-In</span>
              </Button>
            </Link>
            <Link to="/bookings">
              <Button variant="outline" className="w-full">
                View All Bookings
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookingCheckout;
