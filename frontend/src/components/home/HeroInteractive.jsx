import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Calendar, ShieldCheck } from 'lucide-react';
import { Button } from '../common/Button';
import { HeroArchitecturalVisual } from './HeroArchitecturalVisual';

/**
 * HeroInteractive Component
 * Appears ONLY ONCE at the very top of the SpaceLoop landing page.
 * Contains the headline, search entry, and the single hero visual identity.
 */
export const HeroInteractive = () => {
  const shouldReduceMotion = useReducedMotion();
  const navigate = useNavigate();

  const [locationQuery, setLocationQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(`/explore?location=${encodeURIComponent(locationQuery)}&type=${selectedType}`);
  };

  return (
    <section className="relative w-full pt-8 pb-14 lg:pt-14 lg:pb-20 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Top Announcement Tag */}
        <div className="flex justify-center mb-6">
          <motion.div
            initial={shouldReduceMotion ? {} : { opacity: 0, y: -8 }}
            animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium bg-surface-elevated text-text-secondary border border-border shadow-sm"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Instant Digital Key Access on all verified locations</span>
            <ShieldCheck className="w-3.5 h-3.5 text-primary" />
          </motion.div>
        </div>

        {/* Hero Title & Supporting Copy */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <motion.h1
            initial={shouldReduceMotion ? {} : { opacity: 0, y: 12 }}
            animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
            transition={{ duration: 0.42, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-text-primary leading-[1.12]"
          >
            Flexible modern spaces,{' '}
            <span className="text-primary inline-block">
              unlocked on demand.
            </span>
          </motion.h1>

          <motion.p
            initial={shouldReduceMotion ? {} : { opacity: 0, y: 10 }}
            animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
            className="mt-4 text-base sm:text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed"
          >
            Book premium architecturally designed workspaces, private studios, and meeting venues by the hour or day with seamless digital entry.
          </motion.p>
        </div>

        {/* Interactive Search Bar Widget */}
        <motion.div
          initial={shouldReduceMotion ? {} : { opacity: 0, y: 14 }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          transition={{ duration: 0.42, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl mx-auto mb-12"
        >
          <form
            onSubmit={handleSearch}
            className="bg-surface rounded-2xl sm:rounded-3xl p-3 sm:p-4 border border-border shadow-md hover:shadow-lg transition-shadow duration-200"
          >
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              {/* Location Input */}
              <div className="md:col-span-5 flex items-center gap-3 px-3 py-2 rounded-xl bg-surface-elevated border border-border-subtle focus-within:border-primary/50 transition-colors">
                <MapPin className="w-5 h-5 text-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                    Location
                  </label>
                  <input
                    type="text"
                    value={locationQuery}
                    onChange={(e) => setLocationQuery(e.target.value)}
                    placeholder="City, neighborhood, or address"
                    className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                  />
                </div>
              </div>

              {/* Space Type */}
              <div className="md:col-span-4 flex items-center gap-3 px-3 py-2 rounded-xl bg-surface-elevated border border-border-subtle focus-within:border-primary/50 transition-colors">
                <Calendar className="w-5 h-5 text-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                    Space Type
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full bg-transparent text-sm text-text-primary focus:outline-none cursor-pointer"
                  >
                    <option value="all">All Space Types</option>
                    <option value="coworking">Coworking Desks</option>
                    <option value="studio">Private Studio</option>
                    <option value="meeting">Conference Room</option>
                    <option value="rooftop">Rooftop Lounge</option>
                  </select>
                </div>
              </div>

              {/* Submit CTA */}
              <div className="md:col-span-3">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full shadow-md"
                  icon={Search}
                >
                  Search Spaces
                </Button>
              </div>
            </div>
          </form>
        </motion.div>

        {/* ==========================================================================
            EXACTLY ONE HERO VISUAL / ANIMATION
            Appears ONLY ONCE at the top of the landing page.
            Never repeats in any other section or page.
           ========================================================================== */}
        <motion.div
          initial={shouldReduceMotion ? {} : { opacity: 0, scale: 0.98, y: 16 }}
          animate={shouldReduceMotion ? {} : { opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.48, delay: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-5xl mx-auto"
        >
          <HeroArchitecturalVisual />
        </motion.div>

      </div>
    </section>
  );
};

export default HeroInteractive;
