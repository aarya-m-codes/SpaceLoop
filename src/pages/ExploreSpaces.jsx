import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, SlidersHorizontal, MapPin, Zap } from 'lucide-react';
import { SpaceCard } from '../components/spaces/SpaceCard';
import { ScrollReveal } from '../components/common/ScrollReveal';
import { Button } from '../components/common/Button';
import { SPACES_DATA } from '../utils/constants';

export const ExploreSpaces = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialCategory = searchParams.get('category') || 'All';
  
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [searchTerm, setSearchTerm] = useState('');
  const [maxPrice, setMaxPrice] = useState(100);
  const [onlyInstantAccess, setOnlyInstantAccess] = useState(false);

  const categories = ['All', 'Coworking & Lounge', 'Creative Studio', 'Conference Room', 'Outdoor & Lounge', 'Private Office', 'Event & Workshop'];

  const filteredSpaces = useMemo(() => {
    return SPACES_DATA.filter((space) => {
      const matchesCategory =
        selectedCategory === 'All' ||
        space.category.toLowerCase().includes(selectedCategory.toLowerCase());
      const matchesSearch =
        space.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        space.location.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesPrice = space.price <= maxPrice;
      const matchesInstant = !onlyInstantAccess || space.instantAccess;

      return matchesCategory && matchesSearch && matchesPrice && matchesInstant;
    });
  }, [selectedCategory, searchTerm, maxPrice, onlyInstantAccess]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-text-primary tracking-tight">
          Explore Spaces
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          Find and reserve architectural workspaces, lofts, and meeting rooms with instant digital entry.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface rounded-2xl p-4 sm:p-5 border border-border shadow-sm mb-8 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Search text */}
          <div className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by title, neighborhood or city..."
              className="w-full pl-10 pr-4 py-2 text-sm rounded-xl bg-surface-elevated border border-border-subtle focus:border-primary/50 text-text-primary placeholder:text-text-muted focus:outline-none"
            />
          </div>

          {/* Price Range Slider */}
          <div className="md:col-span-4 flex items-center gap-3 px-3 py-1.5 rounded-xl bg-surface-elevated border border-border-subtle text-xs">
            <span className="text-text-muted font-medium whitespace-nowrap">
              Max Price: <strong className="text-text-primary">${maxPrice}/hr</strong>
            </span>
            <input
              type="range"
              min="20"
              max="150"
              step="5"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          {/* Instant Access Toggle */}
          <div className="md:col-span-3 flex items-center justify-end">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-text-secondary select-none">
              <input
                type="checkbox"
                checked={onlyInstantAccess}
                onChange={(e) => setOnlyInstantAccess(e.target.checked)}
                className="w-4 h-4 rounded text-primary focus:ring-primary border-border cursor-pointer"
              />
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span>Instant Pass Only</span>
              </span>
            </label>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors duration-150 ${
                selectedCategory === cat
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface-elevated text-text-secondary hover:text-text-primary hover:bg-border/60'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between mb-6 text-xs text-text-muted">
        <span>Showing {filteredSpaces.length} spaces</span>
        <span>Verified Architectural Listings</span>
      </div>

      {/* Spaces Grid */}
      {filteredSpaces.length > 0 ? (
        <motion.div
          layout
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8"
        >
          <AnimatePresence>
            {filteredSpaces.map((space) => (
              <motion.div
                key={space.id}
                layout
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.25 }}
              >
                <SpaceCard space={space} />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      ) : (
        <div className="py-20 text-center rounded-2xl bg-surface border border-border">
          <p className="text-base font-semibold text-text-primary">No spaces found matching your filters</p>
          <p className="text-xs text-text-muted mt-1">Try resetting the price limit or changing your search keywords.</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => {
              setSelectedCategory('All');
              setSearchTerm('');
              setMaxPrice(100);
              setOnlyInstantAccess(false);
            }}
          >
            Reset Filters
          </Button>
        </div>
      )}
    </div>
  );
};

export default ExploreSpaces;
