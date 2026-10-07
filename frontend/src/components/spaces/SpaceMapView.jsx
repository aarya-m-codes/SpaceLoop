import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Navigation, Eye, Star, Zap, Users, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Interactive Space Map / Location presentation
 * Renders a visual geospatial layout of spaces with active pin selection and quick inspection cards.
 */
export const SpaceMapView = ({ spaces = [], onSelectSpace }) => {
  const [selectedSpace, setSelectedSpace] = useState(spaces[0] || null);

  // Group spaces by city or approximate location
  return (
    <div className="relative w-full rounded-3xl bg-surface border border-border overflow-hidden min-h-[500px] flex flex-col lg:flex-row shadow-sm">
      {/* Mock Map Interactive Canvas */}
      <div className="relative flex-1 bg-gradient-to-br from-slate-900 via-zinc-900 to-stone-900 min-h-[380px] p-6 flex flex-col justify-between overflow-hidden">
        {/* Subtle Map Grid lines */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, #6366f1 1px, transparent 0)`,
            backgroundSize: '32px 32px',
          }}
        />

        {/* Map Header Bar */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white text-xs font-semibold">
            <Navigation className="w-3.5 h-3.5 text-primary" />
            <span>Interactive Geofence Map (India Metro Hubs)</span>
          </div>
          <span className="text-[11px] text-zinc-400 font-mono">
            {spaces.length} Spaces Mapped
          </span>
        </div>

        {/* Spatial Markers Spread */}
        <div className="relative z-10 grid grid-cols-2 sm:grid-cols-3 gap-6 my-auto py-8">
          {spaces.slice(0, 6).map((space, idx) => {
            const isSelected = selectedSpace?.id === space.id;
            const price = space.price_per_hour ?? space.price ?? 150;
            return (
              <motion.button
                key={space.id}
                type="button"
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedSpace(space)}
                className={`flex flex-col items-center gap-1.5 p-2 rounded-2xl transition-all ${
                  isSelected
                    ? 'ring-2 ring-primary ring-offset-2 ring-offset-zinc-950 scale-105'
                    : 'opacity-90 hover:opacity-100'
                }`}
              >
                <div
                  className={`px-3 py-1.5 rounded-full font-bold text-xs shadow-lg flex items-center gap-1 transition-colors ${
                    isSelected
                      ? 'bg-primary text-white'
                      : 'bg-white/90 text-zinc-900 hover:bg-white'
                  }`}
                >
                  <MapPin className="w-3.5 h-3.5" />
                  <span>₹{price}/hr</span>
                </div>
                <span className="text-[10px] text-zinc-300 font-medium truncate max-w-[120px] bg-black/40 px-2 py-0.5 rounded-md">
                  {space.city || space.location?.split(',')[0] || space.title}
                </span>
              </motion.button>
            );
          })}
        </div>

        {/* Map Footer Note */}
        <div className="relative z-10 text-[11px] text-zinc-400 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Real-time GPS geofence enabled (100-meter arrival threshold)</span>
        </div>
      </div>

      {/* Selected Space Preview Sidebar */}
      <div className="w-full lg:w-96 p-6 bg-surface border-t lg:border-t-0 lg:border-l border-border flex flex-col justify-between">
        {selectedSpace ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-primary">
                {selectedSpace.space_type || selectedSpace.category}
              </span>
              <div className="flex items-center gap-1 text-xs font-semibold text-text-primary">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{selectedSpace.rating || 4.9}</span>
              </div>
            </div>

            <div className="relative aspect-video rounded-2xl overflow-hidden bg-surface-elevated border border-border">
              <img
                src={
                  (Array.isArray(selectedSpace.images) && selectedSpace.images[0]) ||
                  selectedSpace.image ||
                  'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'
                }
                alt={selectedSpace.title}
                className="w-full h-full object-cover"
              />
            </div>

            <div>
              <h3 className="text-base font-bold text-text-primary line-clamp-1">
                {selectedSpace.title}
              </h3>
              <p className="text-xs text-text-secondary mt-1 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-primary shrink-0" />
                <span>{selectedSpace.location || selectedSpace.address_line1 || 'Bangalore Central'}</span>
              </p>
            </div>

            <div className="flex items-center gap-4 text-xs text-text-muted py-2 border-y border-border">
              <div className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5" />
                <span>Capacity: {selectedSpace.capacity || 10}</span>
              </div>
              <div className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span>Arrival PIN Ready</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <div>
                <span className="text-lg font-black text-text-primary">
                  ₹{selectedSpace.price_per_hour ?? selectedSpace.price ?? 150}
                </span>
                <span className="text-xs text-text-muted"> / hour</span>
              </div>

              <Link
                to={`/spaces/${selectedSpace.id}`}
                className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <span>View Details</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="py-16 text-center text-xs text-text-muted">
            Select a pin on the map to preview space amenities and booking status.
          </div>
        )}
      </div>
    </div>
  );
};

export default SpaceMapView;
