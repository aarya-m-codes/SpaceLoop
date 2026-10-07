import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Star,
  MapPin,
  Users,
  ShieldCheck,
  Zap,
  ArrowLeft,
  Check,
  Calendar,
  Clock,
  QrCode,
  Sparkles,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { SPACES_DATA } from '../utils/constants';

export const SpaceDetails = () => {
  const { id } = useParams();
  const space = SPACES_DATA.find((s) => s.id === id) || SPACES_DATA[0];

  const [hours, setHours] = useState(3);
  const [guests, setGuests] = useState(2);
  const [selectedDate, setSelectedDate] = useState('Today');
  const [showPassModal, setShowPassModal] = useState(false);

  const subtotal = space.price * hours;
  const serviceFee = Math.round(subtotal * 0.1);
  const total = subtotal + serviceFee;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link
        to="/explore"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-text-secondary hover:text-primary mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to all spaces</span>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left Column: Media & Overview */}
        <div className="lg:col-span-7 space-y-8">
          {/* Gallery View */}
          <div className="relative rounded-3xl overflow-hidden border border-border shadow-md aspect-[16/10] bg-surface-elevated">
            <img
              src={space.image}
              alt={space.title}
              className="w-full h-full object-cover"
            />
            {space.instantAccess && (
              <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-surface/90 backdrop-blur-md text-text-primary border border-border shadow-sm">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span>Instant Digital Entry Available</span>
              </div>
            )}
          </div>

          {/* Heading & Meta */}
          <div>
            <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
              <span className="font-semibold text-primary uppercase tracking-wider">
                {space.category}
              </span>
              <span>•</span>
              <div className="flex items-center gap-1 text-text-primary font-bold">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{space.rating}</span>
                <span className="text-text-muted font-normal">({space.reviews} reviews)</span>
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              {space.title}
            </h1>

            <div className="flex items-center gap-2 text-sm text-text-secondary mt-2">
              <MapPin className="w-4 h-4 text-primary shrink-0" />
              <span>{space.location}</span>
            </div>
          </div>

          {/* Description */}
          <div className="p-6 rounded-2xl bg-surface border border-border">
            <h3 className="text-base font-bold text-text-primary mb-2">
              About this architectural space
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {space.description}
            </p>
          </div>

          {/* Amenities */}
          <div>
            <h3 className="text-base font-bold text-text-primary mb-4">
              Included Amenities & Equipment
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {space.amenities.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-2.5 p-3 rounded-xl bg-surface border border-border text-xs font-medium text-text-primary"
                >
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Host & Verification */}
          <div className="p-6 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-lg border border-primary/20">
                SL
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h4 className="text-sm font-bold text-text-primary">SpaceLoop Verified Host</h4>
                  <ShieldCheck className="w-4 h-4 text-primary" />
                </div>
                <p className="text-xs text-text-muted">Host responds in under 5 minutes • 100% verified entry</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Sticky Booking Widget */}
        <div className="lg:col-span-5">
          <div className="sticky top-24 bg-surface rounded-3xl p-6 sm:p-7 border border-border shadow-lg space-y-6">
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <div>
                <span className="text-3xl font-extrabold text-text-primary">${space.price}</span>
                <span className="text-xs text-text-muted"> / hour</span>
              </div>
              <span className="text-xs font-medium text-emerald-600 bg-emerald-500/10 px-2.5 py-1 rounded-full">
                Instant Confirmation
              </span>
            </div>

            {/* Time slot picker */}
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-surface-elevated border border-border-subtle">
                  <label className="block text-[10px] uppercase font-semibold text-text-muted mb-1">
                    Booking Date
                  </label>
                  <select
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-full bg-transparent font-medium text-text-primary focus:outline-none cursor-pointer"
                  >
                    <option value="Today">Today, Oct 7</option>
                    <option value="Tomorrow">Tomorrow, Oct 8</option>
                    <option value="Friday">Friday, Oct 9</option>
                  </select>
                </div>

                <div className="p-3 rounded-xl bg-surface-elevated border border-border-subtle">
                  <label className="block text-[10px] uppercase font-semibold text-text-muted mb-1">
                    Duration (Hours)
                  </label>
                  <div className="flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => setHours(Math.max(1, hours - 1))}
                      className="w-6 h-6 rounded bg-surface border border-border font-bold text-text-primary hover:bg-border/50"
                    >
                      -
                    </button>
                    <span className="font-bold text-sm text-text-primary">{hours} hrs</span>
                    <button
                      type="button"
                      onClick={() => setHours(hours + 1)}
                      className="w-6 h-6 rounded bg-surface border border-border font-bold text-text-primary hover:bg-border/50"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>

              {/* Guests Count */}
              <div className="p-3 rounded-xl bg-surface-elevated border border-border-subtle flex items-center justify-between">
                <div>
                  <label className="block text-[10px] uppercase font-semibold text-text-muted">
                    Guests (Max {space.capacity})
                  </label>
                  <span className="text-xs font-medium text-text-primary">
                    {guests} {guests === 1 ? 'person' : 'people'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setGuests(Math.max(1, guests - 1))}
                    className="w-6 h-6 rounded bg-surface border border-border font-bold text-text-primary hover:bg-border/50"
                  >
                    -
                  </button>
                  <button
                    type="button"
                    onClick={() => setGuests(Math.min(space.capacity, guests + 1))}
                    className="w-6 h-6 rounded bg-surface border border-border font-bold text-text-primary hover:bg-border/50"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="space-y-2 text-xs border-t border-border pt-4">
              <div className="flex justify-between text-text-secondary">
                <span>
                  ${space.price} × {hours} hours
                </span>
                <span>${subtotal}</span>
              </div>
              <div className="flex justify-between text-text-secondary">
                <span>Digital Pass Access & Service Fee</span>
                <span>${serviceFee}</span>
              </div>
              <div className="flex justify-between font-bold text-sm text-text-primary pt-2 border-t border-border-subtle">
                <span>Total</span>
                <span>${total}</span>
              </div>
            </div>

            {/* Action Button */}
            <Button
              variant="primary"
              size="lg"
              className="w-full shadow-md"
              onClick={() => setShowPassModal(true)}
            >
              <span>Instant Reserve Space</span>
            </Button>

            <p className="text-[11px] text-center text-text-muted">
              Free cancellation up to 1 hour before scheduled start time.
            </p>
          </div>
        </div>
      </div>

      {/* Instant Digital Pass Modal */}
      <AnimatePresence>
        {showPassModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.22 }}
              className="relative w-full max-w-sm rounded-3xl bg-surface border border-border p-6 shadow-2xl text-center space-y-4"
            >
              <div className="w-12 h-12 rounded-2xl bg-primary-light text-primary flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>

              <div>
                <h3 className="text-lg font-bold text-text-primary">Digital Pass Ready</h3>
                <p className="text-xs text-text-secondary mt-1">
                  Reservation confirmed for {space.title}. Present this QR pass or PIN upon arrival.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-border inline-block shadow-inner">
                <QrCode className="w-32 h-32 text-stone-900 mx-auto" />
                <p className="font-mono text-xs font-bold text-stone-800 mt-2 tracking-widest">
                  PASS #SL-8842
                </p>
              </div>

              <div className="text-xs text-text-muted space-y-1">
                <p>PIN Code: <strong className="font-mono text-text-primary">4920#</strong></p>
                <p>Valid: {selectedDate} ({hours} hours duration)</p>
              </div>

              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => setShowPassModal(false)}
              >
                Close Pass
              </Button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SpaceDetails;
