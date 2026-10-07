import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Filter,
  SlidersHorizontal,
  MapPin,
  Zap,
  Sparkles,
  Map,
  LayoutGrid,
  RefreshCw,
} from 'lucide-react';
import { SpaceCard } from '../components/spaces/SpaceCard';
import { SpaceMapView } from '../components/spaces/SpaceMapView';
import { AiSearchModal } from '../components/spaces/AiSearchModal';
import { ScrollReveal } from '../components/common/ScrollReveal';
import { Button } from '../components/common/Button';
import { AnimatedBackground } from '@/components/core/animated-background';
import { SPACES_DATA } from '../utils/constants';
import { spacesApi } from '../services/api';
import { useToast } from '../context/ToastContext';

export const ExploreSpaces = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialCategory = searchParams.get('category') || 'All';
  const { error: toastError } = useToast();

  const [spaces, setSpaces] = useState(SPACES_DATA);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [searchTerm, setSearchTerm] = useState('');
  const [maxPrice, setMaxPrice] = useState(500);
  const [onlyInstantAccess, setOnlyInstantAccess] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'map'
  const [aiModalOpen, setAiModalOpen] = useState(false);

  const categories = [
    'All',
    'Coworking & Lounge',
    'Creative Studio',
    'Conference Room',
    'Outdoor & Lounge',
    'Private Office',
    'Event & Workshop',
  ];

  // Fetch real spaces from backend API
  const fetchSpaces = async () => {
    try {
      setLoading(true);
      const res = await spacesApi.getSpaces();
      const list = res.spaces || (Array.isArray(res) ? res : []);
      if (list && list.length > 0) {
        setSpaces(list);
      }
    } catch {
      // Retain fallback spaces when offline / dev mode
      setSpaces(SPACES_DATA);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpaces();
  }, []);

  // Filter logic
  const filteredSpaces = useMemo(() => {
    return spaces.filter((space) => {
      const category = space.space_type || space.category || '';
      const title = space.title || '';
      const location = space.location || space.city || space.address_line1 || '';
      const price = space.price_per_hour ?? space.price ?? 150;
      const instant = space.instant_booking_enabled ?? space.instantAccess ?? true;

      const matchesCategory =
        selectedCategory === 'All' || category.toLowerCase().includes(selectedCategory.toLowerCase());
      const matchesSearch =
        title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        location.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesPrice = price <= maxPrice;
      const matchesInstant = !onlyInstantAccess || instant;

      return matchesCategory && matchesSearch && matchesPrice && matchesInstant;
    });
  }, [spaces, selectedCategory, searchTerm, maxPrice, onlyInstantAccess]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-primary">
              Real-Time Marketplace
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
            Discover Architectural Spaces
          </h1>
          <p className="text-text-secondary text-xs sm:text-sm mt-1 max-w-xl">
            Book hourly coworking pavilions, lofts, and meeting studios with instant keyless 4-digit PIN access.
          </p>
        </div>

        {/* Action Controls: AI Search & Map Toggle */}
        <div className="flex items-center gap-2">
          {/* AI Semantic Search Button */}
          <Button
            variant="primary"
            size="sm"
            onClick={() => setAiModalOpen(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-primary to-indigo-600 shadow-md shadow-primary/20"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Natural Search</span>
          </Button>

          {/* Grid vs Map Toggle */}
          <div className="flex items-center bg-surface-elevated p-1 rounded-xl border border-border">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${
                viewMode === 'grid'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('map')}
              className={`p-1.5 rounded-lg transition-colors ${
                viewMode === 'map'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
              title="Map & Location View"
            >
              <Map className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface rounded-3xl p-4 sm:p-5 border border-border shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Keyword Search Input */}
          <div className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by neighborhood, city, or title..."
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
            />
          </div>

          {/* Price Range Slider */}
          <div className="md:col-span-4 flex items-center gap-3 px-3 py-2 rounded-xl bg-surface-elevated border border-border text-xs">
            <span className="text-text-muted font-medium whitespace-nowrap">
              Max: <strong className="text-text-primary">₹{maxPrice}/hr</strong>
            </span>
            <input
              type="range"
              min="50"
              max="2000"
              step="25"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          {/* Instant PIN Access Toggle */}
          <div className="md:col-span-3 flex items-center justify-end">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-text-secondary select-none">
              <input
                type="checkbox"
                checked={onlyInstantAccess}
                onChange={(e) => setOnlyInstantAccess(e.target.checked)}
                className="w-4 h-4 rounded text-primary focus:ring-primary border-border cursor-pointer"
              />
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span>Instant PIN Entry Only</span>
              </span>
            </label>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface-elevated text-text-secondary hover:text-text-primary hover:bg-surface-elevated/80 border border-border'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* View Content: Grid vs Map */}
      {loading ? (
        <div className="py-24 text-center">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-text-secondary">Connecting to SpaceLoop live spaces catalog...</p>
        </div>
      ) : viewMode === 'map' ? (
        <SpaceMapView spaces={filteredSpaces} />
      ) : filteredSpaces.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatedBackground
            className="rounded-3xl bg-zinc-200/80 dark:bg-zinc-800 border border-zinc-300/70 dark:border-zinc-700/70 shadow-sm"
            transition={{
              type: 'spring',
              bounce: 0.2,
              duration: 0.6,
            }}
            enableHover
          >
            {filteredSpaces.map((space, index) => (
              <div
                key={space.id}
                data-id={`card-${space.id || index}`}
                className="p-2 w-full h-full flex flex-col"
              >
                <SpaceCard space={space} />
              </div>
            ))}
          </AnimatedBackground>
        </div>
      ) : (
        <div className="text-center py-20 bg-surface rounded-3xl border border-border p-8 space-y-3">
          <MapPin className="w-10 h-10 text-text-muted mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Matching Spaces Found</h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            Try adjusting your price ceiling or search terms, or use the AI Natural Search assistant.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSelectedCategory('All');
              setSearchTerm('');
              setMaxPrice(2000);
              setOnlyInstantAccess(false);
            }}
          >
            Reset Filters
          </Button>
        </div>
      )}

      {/* AI Natural Language Search Modal */}
      <AiSearchModal
        isOpen={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        onSelectSpace={(sp) => {
          setAiModalOpen(false);
        }}
      />
    </div>
  );
};

export default ExploreSpaces;
