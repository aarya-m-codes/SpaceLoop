import React, { useState, useEffect } from 'react';
import {
  Clock,
  CalendarCheck,
  DoorOpen,
  ShieldCheck,
  Vault,
  Building2,
  Filter,
} from 'lucide-react';
import { hostApi } from '../../../services/api';

export const ActivityAuditView = () => {
  const [category, setCategory] = useState('all');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchActivity = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getActivity(category);
      setEvents(res?.events || []);
    } catch (err) {
      console.warn('Failed to load activity events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
  }, [category]);

  const categories = [
    { id: 'all', label: 'All Operations' },
    { id: 'booking', label: 'Bookings' },
    { id: 'access', label: 'Access & Geofence' },
    { id: 'settlement', label: 'Settlement & Escrow' },
    { id: 'space', label: 'Spaces' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold text-text-primary tracking-tight">
            System Activity & Audit Trail
          </h2>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
            Immutable SQLite WAL Log
          </span>
        </div>
        <p className="text-xs text-text-secondary mt-1">
          Chronological record of every check-in handshake, escrow release, and property status modification.
        </p>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              category === cat.id
                ? 'bg-primary text-white shadow-xs'
                : 'bg-surface border border-border text-text-muted hover:text-text-primary'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Activity Timeline List */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
        <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
          <Clock className="w-4 h-4 text-primary" />
          <span>Chronological Telemetry Stream ({events.length})</span>
        </h3>

        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-surface-elevated animate-pulse" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <p className="text-xs text-text-muted py-6 text-center">
            No system operations logged for this category yet.
          </p>
        ) : (
          <div className="divide-y divide-border">
            {events.map((ev, idx) => (
              <div key={ev.id || idx} className="py-3.5 flex items-start gap-3 text-xs">
                <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                  {ev.category === 'access' ? (
                    <DoorOpen className="w-4 h-4 text-sky-500" />
                  ) : ev.category === 'settlement' ? (
                    <Vault className="w-4 h-4 text-emerald-500" />
                  ) : ev.category === 'space' ? (
                    <Building2 className="w-4 h-4 text-amber-500" />
                  ) : (
                    <CalendarCheck className="w-4 h-4 text-primary" />
                  )}
                </div>

                <div className="flex-1 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-text-primary">{ev.title}</span>
                    <span className="text-[10px] text-text-muted">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>
                  <p className="text-text-secondary leading-relaxed">{ev.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityAuditView;
