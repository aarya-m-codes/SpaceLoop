import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { Star, MapPin, Heart, Users, Zap, ShieldCheck } from 'lucide-react';
import { LazyImage } from '../common/LazyImage';
import { cardHoverMotion, cardImageMotion } from '../../utils/motion';

/**
 * SpaceCard Component
 * Normalizes backend Space model data with fallback for images, price (₹ INR), ratings, and badges.
 */
export const SpaceCard = ({ space }) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  const handleFavoriteToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFavorited(!isFavorited);
  };

  // Field normalizers for backend contract
  const spaceId = space.id;
  const title = space.title || 'Architectural Space';
  const category = space.space_type || space.category || 'Workspace';
  const location = space.location || (space.city ? `${space.address_line1 || ''}, ${space.city}` : 'India');
  const price = space.price_per_hour ?? space.price ?? 150;
  const rating = Number(space.rating || space.avg_rating || 4.9).toFixed(1);
  const reviewsCount = space.total_reviews ?? space.reviews_count ?? space.reviews ?? 12;
  const capacity = space.capacity ?? 8;
  const instantAccess = space.instant_booking_enabled ?? space.instantAccess ?? true;

  // Resolve best image URL
  const primaryImage =
    (Array.isArray(space.images) && space.images.length > 0 && space.images[0]) ||
    space.image ||
    'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80';

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
      <Link to={`/spaces/${spaceId}`} state={{ space }} className="flex flex-col flex-grow">
        {/* Card Image Container with Restrained Hover Zoom */}
        <div className="relative overflow-hidden aspect-[16/10] bg-surface-elevated">
          <motion.div {...imageMotionProps} className="w-full h-full">
            <LazyImage
              src={primaryImage}
              alt={title}
              aspectRatio="aspect-full h-full"
            />
          </motion.div>

          {/* Instant Access Badge */}
          {instantAccess && (
            <div className="absolute top-3 left-3 flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-surface/90 backdrop-blur-md text-text-primary border border-border shadow-sm">
              <Zap className="w-3 h-3 text-primary" />
              <span>Instant PIN Entry</span>
            </div>
          )}

          {/* Favorite Heart Button */}
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
              <span className="font-semibold uppercase tracking-wider text-primary text-[11px]">
                {category}
              </span>
              <div className="flex items-center gap-1 font-semibold text-text-primary">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{rating}</span>
                <span className="text-text-muted font-normal text-[11px]">({reviewsCount})</span>
              </div>
            </div>

            <h3 className="font-semibold text-base text-text-primary group-hover:text-primary transition-colors duration-150 line-clamp-1">
              {title}
            </h3>

            <div className="flex items-center gap-1.5 text-xs text-text-secondary mt-1 line-clamp-1">
              <MapPin className="w-3.5 h-3.5 text-text-muted shrink-0" />
              <span>{location}</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-border/60 text-xs">
            <div className="flex items-center gap-1 text-text-muted">
              <Users className="w-3.5 h-3.5" />
              <span>Up to {capacity} guests</span>
            </div>

            <div className="text-right">
              <span className="text-base font-extrabold text-text-primary">
                ₹{price}
              </span>
              <span className="text-text-muted text-[11px]"> / hr</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default SpaceCard;
