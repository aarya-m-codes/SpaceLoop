import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Building2,
  CheckCircle2,
  Users,
} from 'lucide-react';
import { hostApi, bookingsApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useI18n } from '../../../i18n/I18nContext';

export const CalendarView = () => {
  const { formatCurrency } = useI18n();

  const [bookings, setBookings] = useState([]);
  const [spaces, setSpaces] = useState([]);
  const [selectedSpaceId, setSelectedSpaceId] = useState('all');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState(new Date().getDate());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await hostApi.getDashboard();
        if (res) {
          setBookings(res.host_bookings || []);
          setSpaces(res.host_spaces || []);
        }
      } catch (err) {
        console.warn('Failed to load calendar data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handlePrev = () => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() - 1);
    setCurrentDate(d);
  };

  const handleNext = () => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() + 1);
    setCurrentDate(d);
  };

  const handleToday = () => {
    const now = new Date();
    setCurrentDate(now);
    setSelectedDay(now.getDate());
  };

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const monthName = currentDate.toLocaleString('default', { month: 'long' });
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanksArray = Array.from({ length: firstDayOfMonth }, (_, i) => i);

  const filteredBookings = bookings.filter((b) => {
    if (selectedSpaceId !== 'all' && b.space_id !== Number(selectedSpaceId)) return false;
    return true;
  });

  const getBookingsForDay = (day) => {
    return filteredBookings.filter((b) => {
      if (!b.start_time) return false;
      const bDate = new Date(b.start_time);
      return (
        bDate.getDate() === day &&
        bDate.getMonth() === month &&
        bDate.getFullYear() === year
      );
    });
  };

  const selectedDayBookings = getBookingsForDay(selectedDay);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-primary tracking-tight">
            Operational Schedule & Timeline
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Cross-space reservation timeline, session turnaround windows, and availability buffers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {spaces.length > 0 && (
            <select
              value={selectedSpaceId}
              onChange={(e) => setSelectedSpaceId(e.target.value)}
              className="bg-surface border border-border rounded-xl px-3 py-1.5 text-xs text-text-primary focus:outline-none"
            >
              <option value="all">All Spaces ({spaces.length})</option>
              {spaces.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          )}

          <Button variant="outline" size="sm" onClick={handleToday}>
            Today
          </Button>
        </div>
      </div>

      {/* Calendar Controls */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-extrabold text-text-primary">
            {monthName} {year}
          </h3>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={handlePrev}
              className="p-2 rounded-xl hover:bg-surface-elevated text-text-muted hover:text-text-primary transition"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={handleNext}
              className="p-2 rounded-xl hover:bg-surface-elevated text-text-muted hover:text-text-primary transition"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Days of Week */}
        <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-bold uppercase tracking-wider text-text-muted pb-2 border-b border-border">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d}>{d}</div>
          ))}
        </div>

        {/* Month Grid */}
        <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
          {blanksArray.map((i) => (
            <div key={`blank-${i}`} className="h-16 sm:h-20 rounded-xl bg-surface-elevated/20" />
          ))}

          {daysArray.map((day) => {
            const dayBookings = getBookingsForDay(day);
            const isSelected = selectedDay === day;
            const hasBookings = dayBookings.length > 0;

            return (
              <button
                key={day}
                type="button"
                onClick={() => setSelectedDay(day)}
                className={`h-16 sm:h-20 rounded-xl p-2 text-left flex flex-col justify-between transition border ${
                  isSelected
                    ? 'border-primary bg-primary/10 shadow-xs'
                    : hasBookings
                    ? 'border-border bg-surface-elevated hover:border-primary/40'
                    : 'border-border/40 hover:bg-surface-elevated'
                }`}
              >
                <span className={`text-xs font-bold ${isSelected ? 'text-primary' : 'text-text-primary'}`}>
                  {day}
                </span>

                {hasBookings && (
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    <span className="text-[10px] font-bold text-primary truncate">
                      {dayBookings.length} Slot(s)
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Day Agenda */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
        <h4 className="text-base font-bold text-text-primary">
          Agenda for {monthName} {selectedDay}, {year}
        </h4>

        {selectedDayBookings.length === 0 ? (
          <p className="text-xs text-text-muted py-4">
            No bookings scheduled for this date. Space is available for instant reservations.
          </p>
        ) : (
          <div className="space-y-3">
            {selectedDayBookings.map((b) => (
              <div
                key={b.id}
                className="p-4 rounded-xl bg-surface-elevated border border-border flex items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-text-muted">Booking #{b.id}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/15 text-primary">
                      {b.status || 'Confirmed'}
                    </span>
                  </div>
                  <div className="font-bold text-sm text-text-primary">
                    {b.space?.title || `Space #${b.space_id}`}
                  </div>
                  <div className="text-xs text-text-secondary flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-text-muted" />
                      <span>{b.duration_hours || 2} Hours</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-text-muted" />
                      <span>{b.user?.full_name || 'Verified Seeker'}</span>
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-mono text-sm font-bold text-text-primary">
                    {formatCurrency(b.total_amount || 300)}
                  </div>
                  <div className="text-[10px] text-emerald-600 font-semibold">15m Buffer Active</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CalendarView;
