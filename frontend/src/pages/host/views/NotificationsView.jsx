import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bell,
  CheckCircle2,
  Trash2,
  CalendarCheck,
  DoorOpen,
  ShieldCheck,
  Vault,
  MessageSquare,
  ArrowRight,
} from 'lucide-react';
import { hostApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';

export const NotificationsView = () => {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const fetchNotifs = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getNotifications();
      setNotifications(res?.notifications || []);
    } catch (err) {
      console.warn('Failed to load host notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, []);

  const handleMarkRead = async (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, unread: false } : n))
    );
    try {
      await hostApi.markNotificationRead(id);
    } catch (e) {}
  };

  const handleMarkAllRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    try {
      await hostApi.markAllNotificationsRead();
      success('All notifications marked as read.');
    } catch (e) {}
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await hostApi.deleteNotification(id);
    } catch (e) {}
  };

  const filteredNotifs = notifications.filter((n) => {
    if (filter === 'unread') return n.unread;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-text-primary tracking-tight">
              Host Notifications & Dispatch
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
              Live Feed
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Instant operational alerts for booking requests, check-in arrivals, and escrow settlements.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            Mark All as Read
          </Button>
        </div>
      </div>

      {/* Notifications Container */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-4">
        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-2xl bg-surface-elevated animate-pulse" />
            ))}
          </div>
        ) : filteredNotifs.length === 0 ? (
          <p className="text-xs text-text-muted py-6 text-center">
            No active notifications. You are completely caught up!
          </p>
        ) : (
          <div className="divide-y divide-border">
            {filteredNotifs.map((n) => (
              <div
                key={n.id}
                onClick={() => {
                  handleMarkRead(n.id);
                  if (n.action_url) navigate(n.action_url);
                }}
                className={`py-4 px-3 rounded-2xl flex items-start justify-between gap-4 cursor-pointer transition ${
                  n.unread ? 'bg-primary/5 hover:bg-primary/10' : 'hover:bg-surface-elevated'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                    {n.type === 'new_booking' ? (
                      <CalendarCheck className="w-4 h-4 text-emerald-500" />
                    ) : n.type === 'access' ? (
                      <DoorOpen className="w-4 h-4 text-sky-500" />
                    ) : n.type === 'settlement' ? (
                      <Vault className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Bell className="w-4 h-4 text-primary" />
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-xs text-text-primary">{n.title}</h4>
                      {n.unread && (
                        <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed">{n.message}</p>
                    <span className="text-[10px] text-text-muted block">
                      {n.timestamp ? new Date(n.timestamp).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={(e) => handleDelete(n.id, e)}
                  className="p-1.5 rounded-lg text-text-muted hover:text-rose-500 hover:bg-surface transition"
                  title="Dismiss notification"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsView;
