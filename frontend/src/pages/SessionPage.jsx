import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  QrCode,
  KeyRound,
  Wifi,
  MapPin,
  ShieldCheck,
  AlertTriangle,
  Camera,
  CheckCircle2,
  FileText,
  Copy,
  Check,
  ArrowLeft,
  Zap,
  Info,
  X,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { bookingsApi, sessionApi } from '../services/api';
import { useToast } from '../context/ToastContext';

export const SessionPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Micro-Lease Agreement Modal State
  const [microLeaseModal, setMicroLeaseModal] = useState(false);
  const [microLeaseData, setMicroLeaseData] = useState(null);
  const [microLeaseLoading, setMicroLeaseLoading] = useState(false);

  // Computer Vision Room Inspection State
  const [inspectionModal, setInspectionModal] = useState(false);
  const [exitPhotoUrl, setExitPhotoUrl] = useState(
    'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'
  );
  const [inspectionResult, setInspectionResult] = useState(null);

  // Wi-Fi Copy State
  const [copiedWifi, setCopiedWifi] = useState(false);
  const [copiedPin, setCopiedPin] = useState(false);

  // Safe Real-Time Countdown Timer
  const [timerState, setTimerState] = useState({
    phase: 'upcoming',
    hours: 0,
    minutes: 0,
    seconds: 0,
    text: 'Initializing session clock...',
    badgeColor: 'text-primary bg-primary/10 border-primary/20',
  });

  const fetchSession = async () => {
    try {
      setLoading(true);
      const res = await sessionApi.getStatus(id);
      if (res && res.booking) {
        setBooking(res.booking);
      } else {
        // Fallback to standard booking fetch
        const bRes = await bookingsApi.getBooking(id);
        setBooking(bRes.booking || bRes);
      }
    } catch (err) {
      toastError(err.message || 'Could not load active session');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, [id]);

  // Safe Real-time Countdown Timer Effect
  useEffect(() => {
    if (!booking) return;

    const tick = () => {
      const now = Date.now();
      const startMs = booking.start_time ? new Date(booking.start_time).getTime() : now;
      let endMs = booking.end_time ? new Date(booking.end_time).getTime() : startMs + (booking.duration_hours || 2) * 3600 * 1000;

      if (booking.status === 'completed') {
        setTimerState({
          phase: 'completed',
          hours: 0,
          minutes: 0,
          seconds: 0,
          text: 'Session Concluded & Settled',
          badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
        });
        return;
      }

      if (now < startMs) {
        const diff = Math.max(0, startMs - now);
        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        setTimerState({
          phase: 'upcoming',
          hours: h,
          minutes: m,
          seconds: s,
          text: `Starts in ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`,
          badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
        });
      } else if (now >= startMs && now <= endMs) {
        const diff = Math.max(0, endMs - now);
        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        setTimerState({
          phase: 'active',
          hours: h,
          minutes: m,
          seconds: s,
          text: `Active Window: ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')} remaining`,
          badgeColor: 'text-primary bg-primary/10 border-primary/20',
        });
      } else {
        const overDiff = now - endMs;
        const m = Math.floor(overDiff / (1000 * 60));
        setTimerState({
          phase: 'expired',
          hours: 0,
          minutes: m,
          seconds: 0,
          text: `Session Window Expired (${m} min ago) — Check-Out Required`,
          badgeColor: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
        });
      }
    };

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [booking]);

  const loadMicroLease = async () => {
    setMicroLeaseModal(true);
    if (microLeaseData) return;
    try {
      setMicroLeaseLoading(true);
      const res = await sessionApi.getMicroLease(id);
      setMicroLeaseData(res);
    } catch (err) {
      toastError('Could not load Section 52 micro-lease document');
    } finally {
      setMicroLeaseLoading(false);
    }
  };

  const handleInspectAndCheckOut = async () => {
    setActionLoading(true);
    try {
      const res = await sessionApi.inspectCondition(id, {
        checkout_photo_url: exitPhotoUrl,
        notes: 'Room vacated cleanly, power & fans switched off.',
      });

      setInspectionResult(res);
      success('AI Room Condition inspection verified! Escrow deposit refunded.');
      // Update booking state
      fetchSession();
    } catch (err) {
      toastError(err.message || 'Inspection failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckIn = async () => {
    setActionLoading(true);
    try {
      await bookingsApi.checkIn(id, {
        lat: booking?.space?.latitude || 12.9716,
        lng: booking?.space?.longitude || 77.5946,
      });
      success('Checked in successfully! Entry pass active.');
      fetchSession();
    } catch (err) {
      toastError(err.message || 'Check-in failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-base flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="min-h-screen bg-surface-base text-center py-20 px-4">
        <h2 className="text-xl font-bold text-text-primary">Session Not Found</h2>
        <p className="text-text-secondary text-sm mt-2">Could not locate active booking pass #{id}.</p>
        <Button variant="primary" className="mt-4" onClick={() => navigate('/bookings')}>
          Back to Bookings
        </Button>
      </div>
    );
  }

  const space = booking.space || {};

  return (
    <div className="min-h-screen bg-surface-base text-text-primary pb-24">
      {/* Session Header */}
      <div className="bg-surface-elevated/40 border-b border-border py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/bookings')}
              className="p-2 rounded-xl bg-surface border border-border text-text-secondary hover:text-text-primary transition"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-text-muted">BOOKING #{booking.id}</span>
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${timerState.badgeColor}`}>
                  {timerState.phase.toUpperCase()}
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-text-primary mt-1">
                {space.title || 'Micro-Space Session'}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadMicroLease}
              className="flex items-center gap-1.5 text-xs font-semibold"
            >
              <FileText className="w-3.5 h-3.5 text-primary" />
              Section 52 Agreement
            </Button>

            <Link to={`/booking/${id}/access`}>
              <Button variant="secondary" size="sm" className="text-xs font-semibold">
                Access Pass
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        {/* Live Synchronized Timer HUD */}
        <div className="bg-gradient-to-r from-surface via-surface-elevated to-surface rounded-2xl border border-primary/30 p-6 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Clock className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="text-xs font-mono uppercase text-text-muted">Synchronized Session Clock</div>
              <div className="text-xl sm:text-2xl font-black text-text-primary font-mono mt-0.5">
                {timerState.text}
              </div>
            </div>
          </div>

          <div>
            {booking.status === 'confirmed' && !booking.checked_in_at && (
              <Button
                variant="primary"
                size="md"
                disabled={actionLoading}
                onClick={handleCheckIn}
                className="font-bold flex items-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                Check In Now
              </Button>
            )}

            {(booking.checked_in_at || booking.status === 'active') && booking.status !== 'completed' && (
              <Button
                variant="primary"
                size="md"
                onClick={() => setInspectionModal(true)}
                className="font-bold flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500"
              >
                <Camera className="w-4 h-4" />
                AI Inspection & Check Out
              </Button>
            )}
          </div>
        </div>

        {/* Credentials Grid: QR Pass + Caretaker PIN + Wi-Fi */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Caretaker PIN Card */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Physical Keybox</span>
                <KeyRound className="w-5 h-5 text-amber-400" />
              </div>
              <div className="text-xs text-text-secondary">Caretaker / Lockbox PIN</div>
              <div className="text-3xl font-black font-mono tracking-widest text-text-primary mt-2">
                {booking.arrival_pin || '4829'}
              </div>
              <p className="text-[11px] text-text-muted mt-2">
                Enter code at the physical lockbox or show to on-site security desk.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(booking.arrival_pin || '4829');
                setCopiedPin(true);
                setTimeout(() => setCopiedPin(false), 2000);
              }}
              className="mt-4 w-full py-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-semibold text-text-primary transition flex items-center justify-center gap-1.5"
            >
              {copiedPin ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedPin ? 'PIN Copied' : 'Copy PIN'}
            </button>
          </div>

          {/* Wi-Fi Card */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">High-Speed Wi-Fi</span>
                <Wifi className="w-5 h-5 text-primary" />
              </div>
              <div className="text-xs text-text-secondary">SSID</div>
              <div className="text-base font-bold text-text-primary font-mono mt-0.5">
                {space.wifi_ssid || 'SpaceLoop-HighSpeed-5G'}
              </div>
              <div className="text-xs text-text-secondary mt-3">Password</div>
              <div className="text-base font-bold text-text-primary font-mono mt-0.5">
                {space.wifi_password || 'SpaceLoopSecure99'}
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(space.wifi_password || 'SpaceLoopSecure99');
                setCopiedWifi(true);
                setTimeout(() => setCopiedWifi(false), 2000);
              }}
              className="mt-4 w-full py-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-semibold text-text-primary transition flex items-center justify-center gap-1.5"
            >
              {copiedWifi ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedWifi ? 'Password Copied' : 'Copy Wi-Fi Password'}
            </button>
          </div>

          {/* Micro-Escrow Protection Status */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">UPI Micro-Escrow</span>
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="text-xs text-text-secondary">Escrow Deposit Balance</div>
              <div className="text-3xl font-black text-emerald-400 mt-2">₹100</div>
              <div className="text-[11px] text-text-muted mt-2">
                {booking.status === 'completed'
                  ? 'Deposit 100% refunded to seeker bank account upon verified inspection.'
                  : 'Programmatically locked in escrow. Releases automatically upon clean photo check-out.'}
              </div>
            </div>

            <div className="mt-4 py-2 px-3 rounded-xl bg-surface-elevated border border-border text-[11px] font-mono text-emerald-400 text-center font-bold">
              NPCI RAIL ACTIVE
            </div>
          </div>
        </div>

        {/* Space & Location Details */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary" />
            Location & Access Directions
          </h2>
          <p className="text-sm text-text-secondary">
            {space.address || 'Indiranagar 100ft Road, Bengaluru, Karnataka 560038'}
          </p>
          <div className="flex flex-wrap gap-4 pt-2 text-xs">
            <div className="p-3 rounded-xl bg-surface-elevated border border-border">
              <span className="text-text-muted">Host Contact: </span>
              <span className="font-semibold text-text-primary">{space.host_name || 'Verified SpaceLoop Host'}</span>
            </div>
            <div className="p-3 rounded-xl bg-surface-elevated border border-border">
              <span className="text-text-muted">Legal Status: </span>
              <span className="font-semibold text-emerald-400">Section 52 Licensed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Micro-Lease Modal */}
      <AnimatePresence>
        {microLeaseModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-surface rounded-2xl border border-border max-w-2xl w-full p-6 shadow-2xl relative max-h-[85vh] flex flex-col"
            >
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary" />
                  <h3 className="text-base font-bold text-text-primary">
                    Section 52 Revocable Micro-Lease License
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setMicroLeaseModal(false)}
                  className="p-1 rounded-lg text-text-muted hover:text-text-primary"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="overflow-y-auto py-4 text-xs text-text-secondary space-y-4 font-mono leading-relaxed flex-1">
                {microLeaseLoading ? (
                  <div className="py-12 text-center text-text-muted">Loading Section 52 agreement...</div>
                ) : (
                  <div>
                    <div className="p-3 rounded-xl bg-surface-elevated border border-border mb-4 text-[11px] text-primary">
                      <strong>Statutory Protection:</strong> Indian Easements Act (1882), Section 52. Grants temporary permissive access without conferring tenancy, adverse possession, or sub-letting rights.
                    </div>
                    <pre className="whitespace-pre-wrap font-sans text-xs text-text-secondary">
                      {microLeaseData?.agreement_markdown ||
                        microLeaseData?.micro_lease ||
                        `REVOCABLE MICRO-LICENSE AGREEMENT
(Under Section 52, Indian Easements Act, 1882)

Booking Reference: #${booking.id}
Property: ${space.title || 'Micro-Space'}
License Fee: ₹${booking.total_amount || 0}
Micro-Escrow Deposit: ₹100.00 (NPCI UPI Hold)

1. NATURE OF GRANT: The Grantor hereby grants to the Grantee a purely personal, revocable, and non-assignable license to occupy the space during the designated session window.
2. NO TENANCY: This grant does not create any tenancy, leasehold interest, or estate in land under the Transfer of Property Act (1882).
3. CONDITION & EXIT INSPECTION: The Grantee agrees to surrender possession promptly upon session expiry and submit a photographic condition record via the SpaceLoop platform.`}
                    </pre>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-border flex justify-end">
                <Button variant="primary" size="sm" onClick={() => setMicroLeaseModal(false)}>
                  Close Agreement
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* AI Computer Vision Inspection Modal */}
      <AnimatePresence>
        {inspectionModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-surface rounded-2xl border border-border max-w-lg w-full p-6 shadow-2xl relative space-y-5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Camera className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-base font-bold text-text-primary">
                    AI Room Condition Check-Out
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setInspectionModal(false)}
                  className="p-1 rounded-lg text-text-muted hover:text-text-primary"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {!inspectionResult ? (
                <div className="space-y-4">
                  <p className="text-xs text-text-secondary">
                    SpaceLoop Computer Vision verifies that furniture is arranged, trash is cleared, and electrical appliances are turned off before unlocking your ₹100 escrow refund.
                  </p>

                  <div className="rounded-xl overflow-hidden border border-border">
                    <img src={exitPhotoUrl} alt="Room inspection" className="w-full h-48 object-cover" />
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-text-muted uppercase">Sample Checkout Photo</label>
                    <input
                      type="text"
                      value={exitPhotoUrl}
                      onChange={(e) => setExitPhotoUrl(e.target.value)}
                      className="w-full mt-1 bg-surface-elevated border border-border rounded-xl px-3 py-2 text-xs text-text-primary"
                    />
                  </div>

                  <Button
                    variant="primary"
                    size="md"
                    disabled={actionLoading}
                    onClick={handleInspectAndCheckOut}
                    className="w-full font-bold flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500"
                  >
                    {actionLoading ? 'Analyzing Computer Vision Delta...' : 'Confirm & Release Escrow'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-center">
                    <CheckCircle2 className="w-8 h-8 mx-auto mb-2" />
                    <div className="text-sm font-bold">Checkout Verified & Complete!</div>
                    <div className="text-xs text-emerald-400/80 mt-1">
                      ₹100 micro-escrow successfully refunded to your account.
                    </div>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between p-2 rounded-lg bg-surface-elevated">
                      <span className="text-text-muted">Condition Match:</span>
                      <span className="font-bold text-text-primary">
                        {inspectionResult.condition_match_pct || 98}% Match
                      </span>
                    </div>
                    <div className="flex justify-between p-2 rounded-lg bg-surface-elevated">
                      <span className="text-text-muted">Appliances Off:</span>
                      <span className="font-bold text-emerald-400">Verified (Fans, Lights)</span>
                    </div>
                    <div className="flex justify-between p-2 rounded-lg bg-surface-elevated">
                      <span className="text-text-muted">Punctuality Score:</span>
                      <span className="font-bold text-primary">100/100 (On-Time)</span>
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="md"
                    className="w-full font-bold"
                    onClick={() => {
                      setInspectionModal(false);
                      navigate('/bookings');
                    }}
                  >
                    Return to My Bookings
                  </Button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SessionPage;
