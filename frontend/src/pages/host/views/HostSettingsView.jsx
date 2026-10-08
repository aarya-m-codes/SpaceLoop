import React, { useState, useEffect } from 'react';
import {
  Settings,
  CreditCard,
  Bell,
  Shield,
  Save,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { hostApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';

export const HostSettingsView = () => {
  const { success, error: toastError } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [upiVpa, setUpiVpa] = useState('');
  const [bufferMinutes, setBufferMinutes] = useState(15);
  const [instantBooking, setInstantBooking] = useState(true);
  const [geofenceRadius, setGeofenceRadius] = useState(50);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [arrivalChime, setArrivalChime] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const res = await hostApi.getSettings();
        if (res && res.settings) {
          const s = res.settings;
          setName(s.profile?.name || '');
          setPhone(s.profile?.phone || '');
          setUpiVpa(s.payout?.upi_vpa_masked || 'host@okhdfcbank');
          setBufferMinutes(s.defaults?.default_buffer_minutes || 15);
          setInstantBooking(s.defaults?.instant_booking_enabled ?? true);
          setGeofenceRadius(s.defaults?.geofence_radius_meters || 50);
          setEmailAlerts(s.notifications?.email_alerts ?? true);
          setArrivalChime(s.notifications?.arrival_chime ?? true);
        }
      } catch (err) {
        console.warn('Failed to load host settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await hostApi.updateSettings({
        name,
        phone,
        upi_vpa: upiVpa,
        default_buffer_minutes: Number(bufferMinutes),
        instant_booking_enabled: instantBooking,
        geofence_radius_meters: Number(geofenceRadius),
      });
      success('Host configuration and payout preferences saved!');
    } catch (err) {
      toastError('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-text-primary tracking-tight">
          Host Configuration & Settlement Settings
        </h2>
        <p className="text-xs text-text-secondary mt-1">
          Configure direct UPI escrow payouts, turnaround cleaning buffers, and physical geofence radius.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Payout & Banking */}
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-text-primary">
            <CreditCard className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-base">Direct UPI Payout Account</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-text-secondary block mb-1">
                UPI Virtual Payment Address (VPA)
              </label>
              <input
                type="text"
                value={upiVpa}
                onChange={(e) => setUpiVpa(e.target.value)}
                placeholder="e.g. host@okhdfcbank"
                className="w-full bg-surface-elevated border border-border focus:border-primary rounded-xl px-4 py-2.5 text-xs text-text-primary font-mono focus:outline-none transition"
              />
              <span className="text-[10px] text-text-muted mt-1 block">
                95% net revenue credited directly via UPI IMPS upon session checkout.
              </span>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary block mb-1">
                Payout Frequency
              </label>
              <div className="p-2.5 rounded-xl bg-surface-elevated border border-border text-xs text-text-primary font-medium flex items-center justify-between">
                <span>Instant Post-Inspection</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                  ACTIVE
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Operational Automation */}
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-text-primary">
            <Settings className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-base">Operational Automation</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-text-secondary block mb-1">
                Session Buffer Turnaround
              </label>
              <select
                value={bufferMinutes}
                onChange={(e) => setBufferMinutes(Number(e.target.value))}
                className="w-full bg-surface-elevated border border-border focus:border-primary rounded-xl px-4 py-2.5 text-xs text-text-primary focus:outline-none transition"
              >
                <option value={15}>15 Minutes Cleaning</option>
                <option value={30}>30 Minutes Turnaround</option>
                <option value={60}>1 Hour Sanitization</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary block mb-1">
                Geofence Radius
              </label>
              <select
                value={geofenceRadius}
                onChange={(e) => setGeofenceRadius(Number(e.target.value))}
                className="w-full bg-surface-elevated border border-border focus:border-primary rounded-xl px-4 py-2.5 text-xs text-text-primary focus:outline-none transition"
              >
                <option value={30}>30 Meters (Tight)</option>
                <option value={50}>50 Meters (Standard)</option>
                <option value={100}>100 Meters (Campus/Courtyard)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary block mb-1">
                Instant Booking Protocol
              </label>
              <label className="p-2.5 rounded-xl bg-surface-elevated border border-border flex items-center justify-between cursor-pointer text-xs">
                <span>Auto-Approve (OTI &gt; 80)</span>
                <input
                  type="checkbox"
                  checked={instantBooking}
                  onChange={(e) => setInstantBooking(e.target.checked)}
                  className="accent-primary"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Notifications & Chimes */}
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-text-primary">
            <Bell className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-base">Alert & Chime Preferences</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <label className="p-4 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-text-primary">Email Notifications</div>
                <div className="text-[11px] text-text-muted">Instant email for new bookings & check-outs</div>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="accent-primary"
              />
            </label>

            <label className="p-4 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-text-primary">Arrival Radar Chime</div>
                <div className="text-[11px] text-text-muted">Audio chime when seeker verifies 50m check-in</div>
              </div>
              <input
                type="checkbox"
                checked={arrivalChime}
                onChange={(e) => setArrivalChime(e.target.checked)}
                className="accent-primary"
              />
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            className="flex items-center gap-2 shadow-md px-6 py-2.5"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Host Settings'}</span>
          </Button>
        </div>
      </form>
    </div>
  );
};

export default HostSettingsView;
