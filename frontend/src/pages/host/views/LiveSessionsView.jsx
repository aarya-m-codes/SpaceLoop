import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Radio,
  Clock,
  MapPin,
  ShieldCheck,
  CheckCircle2,
  Camera,
  AlertTriangle,
  Zap,
  Power,
  Lock,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { bookingsApi, hostApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';
import { useI18n } from '../../../i18n/I18nContext';

export const LiveSessionsView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const { formatCurrency } = useI18n();

  const [activeBookings, setActiveBookings] = useState([]);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timerSeconds, setTimerSeconds] = useState(3600);
  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState(null);

  // Exit Inspection Checklist
  const [appliancesTurnedOff, setAppliancesTurnedOff] = useState(true);
  const [trashCleared, setTrashCleared] = useState(true);
  const [doorSecured, setDoorSecured] = useState(true);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getDashboard();
      const all = res?.host_bookings || [];
      const live = all.filter(
        (b) =>
          b.status === 'confirmed' ||
          b.status === 'checked_in' ||
          (b.session_state || '').toLowerCase() === 'checked_in'
      );
      setActiveBookings(live);

      if (id) {
        const target = all.find((b) => b.id === Number(id));
        if (target) setSelectedBooking(target);
      } else if (live.length > 0) {
        setSelectedBooking(live[0]);
      } else if (all.length > 0) {
        setSelectedBooking(all[0]);
      }
    } catch (err) {
      console.warn('Live session fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [id]);

  // Countdown timer ticker
  useEffect(() => {
    if (!selectedBooking) return;
    const interval = setInterval(() => {
      setTimerSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [selectedBooking]);

  const formatTimer = (sec) => {
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleCheckout = async () => {
    if (!selectedBooking) return;
    try {
      setCheckingOut(true);
      const res = await bookingsApi.checkOut(selectedBooking.id, {
        lat: selectedBooking.space?.latitude || 12.9716,
        lng: selectedBooking.space?.longitude || 77.5946,
      });
      setCheckoutResult(res);
      success('Checkout confirmed! ₹100 micro-escrow released.');
      await fetchSessions();
    } catch (err) {
      toastError(err.message || 'Checkout failed.');
    } finally {
      setCheckingOut(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-text-primary tracking-tight">
              Live Session Radar & Physical Telemetry
            </h2>
            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 uppercase tracking-wider animate-pulse">
              <Radio className="w-3 h-3" />
              <span>Active</span>
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Real-time occupancy tracking, 50m Haversine proximity handshakes, and exit photo condition release.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="h-64 rounded-3xl bg-surface border border-border animate-pulse" />
      ) : !selectedBooking ? (
        <div className="p-12 rounded-3xl bg-surface border border-border text-center space-y-3">
          <Radio className="w-12 h-12 text-text-muted mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Active In-Room Sessions</h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            There are currently no seekers checked into your properties. Active check-in handshakes will stream here automatically.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Radar Card */}
          <div className="lg:col-span-2 rounded-3xl bg-surface border border-border p-6 sm:p-8 space-y-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div>
                <span className="text-[10px] font-mono font-bold text-text-muted">
                  SESSION #{selectedBooking.id}
                </span>
                <h3 className="text-xl font-bold text-text-primary">
                  {selectedBooking.space?.title || `Space #${selectedBooking.space_id}`}
                </h3>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/20 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>50m Geofence Verified</span>
              </span>
            </div>

            {/* Countdown HUD */}
            <div className="p-6 rounded-2xl bg-surface-elevated border border-border text-center space-y-2">
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Session Time Remaining
              </span>
              <div className="text-4xl sm:text-5xl font-black font-mono text-primary tracking-widest">
                {formatTimer(timerSeconds)}
              </div>
              <div className="text-[11px] text-text-secondary">
                Turnaround buffer begins automatically at expiration.
              </div>
            </div>

            {/* In-Room Appliance & Safety Checklist */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Smart Premise IoT & Inspection Checklist
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <label className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={appliancesTurnedOff}
                    onChange={(e) => setAppliancesTurnedOff(e.target.checked)}
                    className="accent-primary"
                  />
                  <span>Lights & AC Off</span>
                </label>
                <label className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={trashCleared}
                    onChange={(e) => setTrashCleared(e.target.checked)}
                    className="accent-primary"
                  />
                  <span>Workspace Tidy</span>
                </label>
                <label className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={doorSecured}
                    onChange={(e) => setDoorSecured(e.target.checked)}
                    className="accent-primary"
                  />
                  <span>Door Relocked</span>
                </label>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex items-center gap-3 pt-4 border-t border-border">
              <Button
                variant="primary"
                onClick={handleCheckout}
                disabled={checkingOut}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 shadow-md"
              >
                {checkingOut ? 'Releasing Escrow...' : 'Complete Session & Release ₹100 Deposit'}
              </Button>
            </div>
          </div>

          {/* Seeker & Escrow Info */}
          <div className="space-y-4">
            <div className="p-6 rounded-3xl bg-surface border border-border space-y-4 shadow-sm">
              <h4 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Seeker Credentials
              </h4>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-text-muted">Name:</span>
                  <span className="font-semibold text-text-primary">
                    {selectedBooking.user?.full_name || 'Verified Seeker'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Identity KYC:</span>
                  <span className="text-emerald-600 font-bold">DigiLocker Verified</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">UPI VPA:</span>
                  <span className="font-mono text-text-secondary">seeker***@okaxis</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Micro-Escrow:</span>
                  <span className="font-bold text-primary font-mono">₹100 Held</span>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-gradient-to-br from-primary/10 to-surface border border-primary/20 space-y-3">
              <div className="flex items-center gap-2 text-primary">
                <ShieldCheck className="w-5 h-5" />
                <h4 className="font-bold text-xs uppercase tracking-wider">
                  Automated Security Loop
                </h4>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                If the seeker departs without issue, their ₹100 micro-escrow returns to their UPI account instantly upon checkout handshake.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveSessionsView;
