import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  QrCode,
  KeyRound,
  MapPin,
  Clock,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Navigation,
  Camera,
  ArrowLeft,
  DollarSign,
  FileText,
  RotateCcw,
} from 'lucide-react';
import { bookingsApi, escrowApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import { ErrorState } from '../components/common/ErrorState';

export const BookingAccess = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { success, error: toastError } = useToast();

  const [booking, setBooking] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorType, setErrorType] = useState(null);

  // GPS & Geofence State
  const [userLocation, setUserLocation] = useState(null);
  const [gpsStatus, setGpsStatus] = useState('prompt'); // 'prompt' | 'granted' | 'denied'
  const [distanceMeters, setDistanceMeters] = useState(null);

  // Inspection / Checkout State
  const [inspectionNotes, setInspectionNotes] = useState('');
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);
  const [disputeModalOpen, setDisputeModalOpen] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');

  // Fetch booking and escrow ledger
  const fetchBookingData = async () => {
    try {
      setLoading(true);
      const res = await bookingsApi.getBooking(id);
      const data = res.booking || res;
      setBooking(data);

      // Fetch immutable ledger
      try {
        const ledgerRes = await escrowApi.getBookingLedger(id);
        setLedger(ledgerRes.transactions || ledgerRes.ledger || []);
      } catch (lErr) {
        // Non-fatal ledger fetch
      }
    } catch (err) {
      if (err.status === 404) {
        setErrorType('unavailable');
      } else if (err.status === 403 || err.status === 401) {
        setErrorType('unauthorized');
      } else {
        toastError(err.message || 'Could not load booking access pass');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookingData();
  }, [id]);

  // Request browser GPS
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setGpsStatus('denied');
      toastError('Geolocation is not supported by your browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setUserLocation({ lat, lng });
        setGpsStatus('granted');
        // Space coordinates fallback (Indiranagar / Bangalore)
        const spaceLat = booking?.space?.latitude ?? 12.9716;
        const spaceLng = booking?.space?.longitude ?? 77.5946;

        // Haversine formula calculation
        const R = 6371e3; // metres
        const φ1 = (lat * Math.PI) / 180;
        const φ2 = (spaceLat * Math.PI) / 180;
        const Δφ = ((spaceLat - lat) * Math.PI) / 180;
        const Δλ = ((spaceLng - lng) * Math.PI) / 180;
        const a =
          Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
          Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const dist = Math.round(R * c);
        setDistanceMeters(dist);
      },
      (err) => {
        console.warn('GPS error:', err);
        setGpsStatus('denied');
        toastError('Location access was denied. You may use the 4-digit PIN fallback.');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Perform Check-in
  const handleCheckIn = async (usePinFallback = false) => {
    setCheckingIn(true);
    try {
      const payload = {
        pin: booking.arrival_pin || booking.access_code || '1234',
        lat: userLocation?.lat ?? 12.9716,
        lng: userLocation?.lng ?? 77.5946,
        override_geofence: usePinFallback || gpsStatus === 'denied',
      };

      await bookingsApi.checkIn(booking.id, payload);
      success('Check-in confirmed! Welcome to the space.');
      await fetchBookingData();
    } catch (err) {
      toastError(err.message || 'Check-in validation failed.');
    } finally {
      setCheckingIn(false);
    }
  };

  // Perform Check-out & trigger micro-escrow deposit release
  const handleCheckOut = async () => {
    setCheckingOut(true);
    try {
      await bookingsApi.checkOut(booking.id, {
        inspection_notes: inspectionNotes || 'Standard check-out with zero property damage.',
      });
      success('Checked out successfully! ₹100 deposit release processed.');
      await fetchBookingData();
    } catch (err) {
      toastError(err.message || 'Checkout failed.');
    } finally {
      setCheckingOut(false);
    }
  };

  // File dispute
  const handleFileDispute = async () => {
    if (!disputeReason.trim()) {
      toastError('Please describe the reason for filing a dispute.');
      return;
    }
    try {
      await bookingsApi.disputeBooking(booking.id, disputeReason);
      success('Dispute submitted. Escrow funds have been safely frozen.');
      setDisputeModalOpen(false);
      await fetchBookingData();
    } catch (err) {
      toastError(err.message || 'Dispute submission failed.');
    }
  };

  if (errorType) {
    return (
      <div className="py-20 px-4">
        <ErrorState
          type={errorType}
          onBack={() => navigate('/bookings')}
          actionText="Explore Spaces"
          actionFn={() => navigate('/explore')}
        />
      </div>
    );
  }

  if (loading || !booking) {
    return (
      <div className="py-24 text-center">
        <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-text-secondary">Loading digital pass & geofence telemetry...</p>
      </div>
    );
  }

  const isCheckedIn = booking.session_state === 'checked_in';
  const isCheckedOut = booking.session_state === 'checked_out';
  const isDisputed = booking.escrow_status === 'disputed' || booking.status === 'disputed';
  const isCancelled = booking.status === 'cancelled';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header & Back */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/bookings"
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-primary mb-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to My Bookings</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
            Digital Access Pass & Physical Check-In
          </h1>
          <p className="text-xs text-text-secondary mt-1">
            Booking <strong className="font-mono text-text-primary">#{booking.id}</strong> •{' '}
            {booking.space?.title || 'Architectural Space'}
          </p>
        </div>

        {/* Status Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              isDisputed
                ? 'bg-orange-500/10 text-orange-600 border border-orange-500/20'
                : isCheckedOut
                ? 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/20'
                : isCheckedIn
                ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                : 'bg-primary/10 text-primary border border-primary/20'
            }`}
          >
            Session: {booking.session_state?.replace('_', ' ') || 'not started'}
          </span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              booking.escrow_status === 'released'
                ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                : booking.escrow_status === 'refunded'
                ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20'
                : 'bg-amber-500/10 text-amber-600 border border-amber-500/20'
            }`}
          >
            Escrow: {booking.escrow_status || 'held'}
          </span>
        </div>
      </div>

      {/* Disputed Alert Banner */}
      {isDisputed && (
        <div className="p-4 rounded-2xl bg-orange-500/10 border border-orange-500/20 text-orange-600 dark:text-orange-400 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>
            This reservation has an active dispute. Escrow funds (₹{booking.total_price || booking.total_amount}) are frozen and protected in our internal ledger until review.
          </span>
        </div>
      )}

      {/* Main Access Pass Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Column: QR Code & 4-Digit Arrival PIN */}
        <div className="md:col-span-6 space-y-6">
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-6 text-center shadow-md">
            <span className="text-[11px] font-bold uppercase tracking-widest text-text-muted">
              Physical Space Digital Key
            </span>

            {/* QR Pass Code Visualization */}
            <div className="w-48 h-48 mx-auto p-4 rounded-2xl bg-white border border-border shadow-inner flex flex-col items-center justify-center">
              <QrCode className="w-36 h-36 text-zinc-950" />
            </div>

            {/* Arrival PIN Fallback */}
            <div className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-1">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                Keypad Arrival PIN (Fallback)
              </span>
              <div className="text-3xl font-black font-mono tracking-[0.4em] text-primary">
                {booking.arrival_pin || booking.access_code || '1234'}
              </div>
              <p className="text-[10px] text-text-secondary">
                Works on offline keypad or when GPS permissions are unavailable.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Geofence Verification & Action State */}
        <div className="md:col-span-6 space-y-6">
          {/* GPS Geofence Verification Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <h3 className="font-bold text-sm text-text-primary flex items-center gap-2">
              <Navigation className="w-4 h-4 text-primary" />
              <span>Geofence & Location Telemetry</span>
            </h3>

            <p className="text-xs text-text-secondary">
              SpaceLoop verifies physical presence within 100 meters of the space address before permitting regular check-in.
            </p>

            {gpsStatus === 'prompt' && (
              <Button
                variant="outline"
                size="sm"
                onClick={requestLocation}
                className="w-full flex items-center justify-center gap-2"
              >
                <MapPin className="w-4 h-4 text-primary" />
                <span>Verify Device GPS Location</span>
              </Button>
            )}

            {gpsStatus === 'granted' && (
              <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-400 space-y-1">
                <div className="flex items-center gap-2 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>GPS Telemetry Acquired</span>
                </div>
                {distanceMeters !== null && (
                  <p className="text-[11px]">
                    Estimated Distance: <strong>{distanceMeters}m</strong> (Threshold: 100m)
                  </p>
                )}
              </div>
            )}

            {gpsStatus === 'denied' && (
              <div className="p-3.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-600 dark:text-blue-400 space-y-1">
                <div className="flex items-center gap-2 font-bold">
                  <KeyRound className="w-4 h-4" />
                  <span>PIN Fallback Mode Active</span>
                </div>
                <p className="text-[11px]">
                  Browser location was not provided. You can check in using your verified 4-digit Arrival PIN.
                </p>
              </div>
            )}

            {/* Check-In / Check-Out Action Buttons */}
            <div className="pt-2 border-t border-border space-y-3">
              {!isCheckedIn && !isCheckedOut && !isCancelled && (
                <div className="space-y-2">
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={() => handleCheckIn(false)}
                    disabled={checkingIn || isDisputed}
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{checkingIn ? 'Verifying Check-In...' : 'Confirm Arrival & Check-In'}</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCheckIn(true)}
                    disabled={checkingIn || isDisputed}
                    className="w-full text-xs"
                  >
                    Check In via 4-Digit PIN Fallback
                  </Button>
                </div>
              )}

              {isCheckedIn && !isCheckedOut && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-text-secondary">
                      Condition & Inspection Notes (Optional)
                    </label>
                    <textarea
                      rows={2}
                      value={inspectionNotes}
                      onChange={(e) => setInspectionNotes(e.target.value)}
                      placeholder="e.g. Left space spotless, lights switched off, door locked."
                      className="w-full p-3 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                    />
                  </div>

                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleCheckOut}
                    disabled={checkingOut}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{checkingOut ? 'Processing Checkout...' : 'Check Out & Release ₹100 Deposit'}</span>
                  </Button>
                </div>
              )}

              {isCheckedOut && (
                <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-center space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                  <h4 className="text-sm font-bold text-text-primary">Reservation Completed</h4>
                  <p className="text-xs text-text-secondary">
                    Check-out was inspected successfully. Your ₹100 escrow security deposit has been released.
                  </p>
                </div>
              )}
            </div>

            {/* Dispute Trigger Link */}
            {!isCheckedOut && !isDisputed && !isCancelled && (
              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => setDisputeModalOpen(true)}
                  className="text-xs text-rose-500 hover:underline inline-flex items-center gap-1"
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Report An Issue / Freeze Escrow Dispute</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Immutable Escrow Ledger Audit Trail */}
      <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
        <h3 className="font-bold text-sm text-text-primary flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <span>Immutable Financial Ledger Audit Trail</span>
        </h3>
        <p className="text-xs text-text-secondary">
          Every monetary transaction for booking #{booking.id} is registered cryptographically with internal ledger timestamps.
        </p>

        <div className="divide-y divide-border border border-border rounded-2xl overflow-hidden">
          {ledger.length > 0 ? (
            ledger.map((tx) => (
              <div key={tx.id} className="p-4 bg-surface-elevated flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold uppercase tracking-wider text-primary text-[11px] block">
                    {tx.transaction_type}
                  </span>
                  <span className="text-text-muted text-[10px]">
                    {new Date(tx.created_at).toLocaleString('en-IN')} • ID: {tx.id}
                  </span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-text-primary text-sm block">
                    ₹{tx.amount}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400">
                    {tx.status}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 bg-surface-elevated text-xs text-text-muted text-center">
              Ledger transactions initializing...
            </div>
          )}
        </div>
      </div>

      {/* Dispute Modal */}
      {disputeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="max-w-md w-full bg-surface border border-border rounded-3xl p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-text-primary flex items-center gap-2 text-rose-500">
              <AlertTriangle className="w-5 h-5" />
              <span>Freeze Escrow & Open Dispute</span>
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Filing a dispute immediately freezes host payout and seeker deposit in our micro-escrow ledger until our trust & safety team conducts an investigation.
            </p>
            <textarea
              rows={3}
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="State the reason (e.g. space was locked, amenities not as described, double booked)..."
              className="w-full p-3 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-rose-500"
            />
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDisputeModalOpen(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleFileDispute}
                className="flex-1 bg-rose-600 hover:bg-rose-700 text-white"
              >
                Submit Dispute
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookingAccess;
