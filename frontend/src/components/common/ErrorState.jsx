import React from 'react';
import {
  AlertTriangle,
  Clock,
  Lock,
  CalendarX,
  CreditCard,
  MapPinOff,
  QrCode,
  BotOff,
  ShieldAlert,
  Flame,
  HelpCircle,
  RefreshCw,
  ArrowLeft,
} from 'lucide-react';
import { Button } from './Button';

const STATE_CONFIG = {
  unavailable: {
    icon: CalendarX,
    title: 'Space Unavailable',
    description: 'This space is not currently accepting reservations or has been temporarily paused by the host.',
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
  },
  expired: {
    icon: Clock,
    title: 'Booking Window Expired',
    description: 'The time window for this reservation or access code has passed. Please book a new slot.',
    color: 'text-zinc-400',
    bg: 'bg-zinc-500/10',
    borderColor: 'border-zinc-500/20',
  },
  unauthorized: {
    icon: Lock,
    title: 'Authentication Required',
    description: 'You need to sign in or switch your account role to access this section.',
    color: 'text-rose-500',
    bg: 'bg-rose-500/10',
    borderColor: 'border-rose-500/20',
  },
  booking_conflict: {
    icon: AlertTriangle,
    title: 'Schedule Conflict',
    description: 'Another verified user has already booked this space during your selected time slot.',
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
  },
  payment_failure: {
    icon: CreditCard,
    title: 'Payment / Ledger Hold Failed',
    description: 'The micro-escrow authorization could not be completed. Your funds have not been debited.',
    color: 'text-rose-500',
    bg: 'bg-rose-500/10',
    borderColor: 'border-rose-500/20',
  },
  gps_unavailable: {
    icon: MapPinOff,
    title: 'GPS Verification Unavailable',
    description: 'Could not access device location. Please enable location permissions or use the 4-digit Arrival PIN fallback.',
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
  },
  qr_invalid: {
    icon: QrCode,
    title: 'Invalid QR Digital Pass',
    description: 'This digital access pass is invalid or does not match an active check-in token for this physical space.',
    color: 'text-rose-500',
    bg: 'bg-rose-500/10',
    borderColor: 'border-rose-500/20',
  },
  ai_unavailable: {
    icon: BotOff,
    title: 'AI Concierge Operating in Offline Mode',
    description: 'AI model services are currently unavailable. SpaceLoop is providing deterministic verified answers and marketplace actions.',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10',
    borderColor: 'border-indigo-500/20',
  },
  verification_pending: {
    icon: ShieldAlert,
    title: 'Identity Verification Required',
    description: 'Complete student, Aadhaar, or host DISCOM verification to unlock this feature and student discounts.',
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
  },
  fraud_review: {
    icon: Flame,
    title: 'Under Trust & Safety Review',
    description: 'This transaction triggered our autonomous fraud anomaly threshold (≥0.60). Our safety desk is reviewing your activity.',
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
  },
  dispute: {
    icon: AlertTriangle,
    title: 'Escrow Frozen (Dispute Active)',
    description: 'A formal dispute has been filed. Escrow funds are secured and frozen until resolution by the SpaceLoop arbitrator.',
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
  },
};

export const ErrorState = ({
  type = 'unavailable',
  title,
  description,
  onRetry,
  onBack,
  actionText,
  actionFn,
  className = '',
}) => {
  const config = STATE_CONFIG[type] || {
    icon: HelpCircle,
    title: title || 'Notice',
    description: description || 'An unexpected condition occurred.',
    color: 'text-text-secondary',
    bg: 'bg-surface-elevated',
    borderColor: 'border-border',
  };

  const Icon = config.icon;
  const displayTitle = title || config.title;
  const displayDesc = description || config.description;

  return (
    <div
      className={`rounded-2xl border p-6 sm:p-8 text-center flex flex-col items-center justify-center max-w-lg mx-auto bg-surface ${config.borderColor} ${className}`}
      role="alert"
    >
      <div className={`w-14 h-14 rounded-2xl ${config.bg} flex items-center justify-center mb-4`}>
        <Icon className={`w-7 h-7 ${config.color}`} />
      </div>

      <h3 className="text-lg font-bold text-text-primary tracking-tight mb-2">
        {displayTitle}
      </h3>

      <p className="text-sm text-text-secondary leading-relaxed mb-6">
        {displayDesc}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onBack && (
          <Button variant="outline" size="sm" onClick={onBack} className="flex items-center gap-1.5">
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </Button>
        )}
        {onRetry && (
          <Button variant="primary" size="sm" onClick={onRetry} className="flex items-center gap-1.5">
            <RefreshCw className="w-4 h-4" />
            <span>Try Again</span>
          </Button>
        )}
        {actionText && actionFn && (
          <Button variant="primary" size="sm" onClick={actionFn}>
            {actionText}
          </Button>
        )}
      </div>
    </div>
  );
};

export default ErrorState;
