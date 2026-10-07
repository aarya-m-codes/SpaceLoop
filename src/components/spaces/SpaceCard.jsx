import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { Star, MapPin, Heart, Users, Zap } from 'lucide-react';
import { LazyImage } from '../common/LazyImage';
import { cardHoverMotion, cardImageMotion } from '../../utils/motion';

/**
 * SpaceCard Component
 * Displays a space listing with restrained hover lift, image zoom, and micro-interactions.
 */
export const SpaceCard = ({ space }) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  const handleFavoriteToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFavorited(!isFavorited);
  };

  const cardMotionProps = shouldReduceMotion
    ? {}
    : {
        variants: cardHoverMotion,
        initial: 'rest',
        whileHover: 'hover',
        animate: 'rest',
      };

  const imageMotionProps = shouldReduceMotion
    ? {}
    : {
        variants: cardImageMotion,
      };

  return (
    <motion.div
      {...cardMotionProps}
      className="group relative flex flex-col bg-surface rounded-2xl border border-border overflow-hidden transition-shadow duration-250 hover:shadow-hover hover:border-primary/30"
    >
      <Link to={`/spaces/${space.id}`} className="flex flex-col flex-grow">
        {/* Card Image Container with Restrained Hover Zoom */}
        <div className="relative overflow-hidden aspect-[16/10] bg-surface-elevated">
          <motion.div {...imageMotionProps} className="w-full h-full">
            <LazyImage
              src={space.image}
              alt={space.title}
              aspectRatio="aspect-full h-full"
            />
          </motion.div>

          {/* Instant Access Badge */}
          {space.instantAccess && (
            <div className="absolute top-3 left-3 flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface/90 backdrop-blur-md text-text-primary border border-border shadow-sm">
              <Zap className="w-3 h-3 text-primary" />
              <span>Instant Pass</span>
            </div>
          )}

          {/* Favorite Heart Button with Pop Motion */}
          <motion.button
            type="button"
            onClick={handleFavoriteToggle}
            aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
            whileTap={{ scale: 0.8 }}
            className={`absolute top-3 right-3 p-2 rounded-full backdrop-blur-md transition-colors duration-150 ${
              isFavorited
                ? 'bg-primary text-white shadow-md'
                : 'bg-black/30 text-white/90 hover:bg-black/50 hover:text-white'
            }`}
          >
            <motion.div
              animate={{ scale: isFavorited ? [1, 1.3, 1] : 1 }}
              transition={{ duration: 0.25 }}
            >
              <Heart
                className="w-4 h-4"
                fill={isFavorited ? 'currentColor' : 'none'}
              />
            </motion.div>
          </motion.button>
        </div>

        {/* Card Content */}
        <div className="p-4 flex flex-col flex-grow justify-between gap-3">
          <div>
            <div className="flex items-center justify-between gap-2 text-xs text-text-muted mb-1">
              <span className="font-medium uppercase tracking-wider text-primary">
                {space.category}
              </span>
              <div className="flex items-center gap-1 font-semibold text-text-primary">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{space.rating}</span>
                <span className="text-text-muted font-normal">({space.reviews})</span>
              </div>
            </div>

            <h3 className="font-semibold text-base text-text-primary group-hover:text-primary transition-colors duration-150 line-clamp-1">
              {space.title}
            </h3>

            <div className="flex items-center gap-1 text-xs text-text-secondary mt-1">
              <MapPin className="w-3.5 h-3.5 shrink-0 text-text-muted" />
              <span className="truncate">{space.location}</span>
            </div>
          </div>

          {/* Capacity and Price footer */}
          <div className="pt-2 border-t border-border-subtle flex items-center justify-between text-xs">
            <span className="flex items-center gap-1 text-text-muted">
              <Users className="w-3.5 h-3.5" />
              <span>Up to {space.capacity} guests</span>
            </span>
            <div className="text-right">
              <span className="text-base font-bold text-text-primary">${space.price}</span>
              <span className="text-text-muted font-normal"> / hour</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default SpaceCard;
