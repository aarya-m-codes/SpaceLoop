import React, { useState, useEffect } from 'react';
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
  Sparkles,
  Building2,
  MessageSquare,
  Send,
  Heart,
} from 'lucide-react';
import { spacesApi, wishlistApi, inquiriesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import { BookingWidget } from '../components/booking/BookingWidget';
import { ErrorState } from '../components/common/ErrorState';

export const SpaceDetails = () => {
  const { id } = useParams();
  const { user, isAuthenticated } = useAuth();
  const { success, error: toastError } = useToast();

  const [space, setSpace] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeImageIdx, setActiveImageIdx] = useState(0);
  const [notFound, setNotFound] = useState(false);

  // Wishlist state
  const [isWishlisted, setIsWishlisted] = useState(false);

  // Inquiry Modal state
  const [inquiryModalOpen, setInquiryModalOpen] = useState(false);
  const [inquiryMessage, setInquiryMessage] = useState('');
  const [submittingInquiry, setSubmittingInquiry] = useState(false);

  // New Review Form
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    // Check initial wishlist status from storage
    try {
      const stored = JSON.parse(localStorage.getItem('spaceloop_wishlist') || '[]');
      if (Array.isArray(stored) && stored.some((item) => (item.id || item) === Number(id) || (item.id || item) === id)) {
        setIsWishlisted(true);
      }
    } catch {
      // ignore
    }

    const fetchSpaceData = async () => {
      try {
        setLoading(true);
        const [spaceRes, reviewsRes] = await Promise.allSettled([
          spacesApi.getSpace(id),
          spacesApi.getReviews(id),
        ]);

        if (spaceRes.status === 'fulfilled') {
          const val = spaceRes.value;
          const s = val?.data || val?.space || (val && !val.success ? val : val);
          if (s && (s.id || s.title)) {
            setSpace(s);
          } else {
            setNotFound(true);
          }
        } else {
          setNotFound(true);
        }

        if (reviewsRes.status === 'fulfilled') {
          const rVal = reviewsRes.value;
          const rList =
            rVal?.data?.items ||
            rVal?.data?.reviews ||
            rVal?.reviews ||
            rVal?.items ||
            (Array.isArray(rVal?.data) ? rVal.data : []) ||
            (Array.isArray(rVal) ? rVal : []);
          setReviews(rList);
        }
      } catch (err) {
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    };

    fetchSpaceData();
  }, [id]);

  const handleToggleWishlist = async () => {
    if (!space) return;
    const newState = !isWishlisted;
    setIsWishlisted(newState);

    try {
      const stored = JSON.parse(localStorage.getItem('spaceloop_wishlist') || '[]');
      let updated;
      if (newState) {
        updated = [...stored.filter((item) => (item.id || item) !== space.id), space];
        success(`Saved "${space.title}" to your wishlist`);
        if (isAuthenticated) {
          await wishlistApi.addToWishlist(space.id);
        }
      } else {
        updated = stored.filter((item) => (item.id || item) !== space.id);
        success(`Removed "${space.title}" from your wishlist`);
        if (isAuthenticated) {
          await wishlistApi.removeFromWishlist(space.id);
        }
      }
      localStorage.setItem('spaceloop_wishlist', JSON.stringify(updated));
    } catch {
      // safe fallback
    }
  };

  const handleSendInquiry = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toastError('Please sign in to send an inquiry to the host.');
      return;
    }
    if (!inquiryMessage.trim()) return;

    setSubmittingInquiry(true);
    try {
      await inquiriesApi.sendInquiry(id, { message: inquiryMessage.trim() });
      success('Inquiry sent to host! You can view responses in your Seeker Portal.');
      setInquiryMessage('');
      setInquiryModalOpen(false);
    } catch (err) {
      toastError(err.message || 'Failed to send inquiry to host.');
    } finally {
      setSubmittingInquiry(false);
    }
  };

  const handleAddReview = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toastError('Please sign in to write a review.');
      return;
    }

    setSubmittingReview(true);
    try {
      await spacesApi.createReview(id, {
        rating: Number(reviewRating),
        comment: reviewComment,
      });
      success('Review posted successfully!');
      setReviewComment('');
      // Refresh reviews
      const fresh = await spacesApi.getReviews(id);
      setReviews(fresh.reviews || (Array.isArray(fresh) ? fresh : []));
    } catch (err) {
      toastError(err.message || 'Failed to submit review.');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (notFound) {
    return (
      <div className="py-24 px-4">
        <ErrorState
          type="unavailable"
          title="Space Not Found"
          description="The architectural space you are looking for does not exist or has been removed."
          onBack={() => (window.location.href = '/explore')}
          actionText="Explore Active Spaces"
          actionFn={() => (window.location.href = '/explore')}
        />
      </div>
    );
  }

  if (loading || !space) {
    return (
      <div className="py-24 text-center">
        <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-text-secondary">Loading architectural blueprints & availability...</p>
      </div>
    );
  }

  const imagesList =
    Array.isArray(space.images) && space.images.length > 0
      ? space.images
      : [
          space.image ||
            'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80',
        ];

  const rating = Number(space.rating || 4.9).toFixed(1);
  const locationStr = space.location || (space.city ? `${space.address_line1 || ''}, ${space.city}` : 'India');
  const instantAccess = space.instant_booking_enabled ?? space.instantAccess ?? true;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back Link */}
      <Link
        to="/explore"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to all spaces</span>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left Column: Media & Overview */}
        <div className="lg:col-span-7 space-y-8">
          {/* Main Photo & Thumbnail Gallery */}
          <div className="space-y-3">
            <div className="relative rounded-3xl overflow-hidden border border-border shadow-md aspect-[16/10] bg-surface-elevated">
              <img
                src={imagesList[activeImageIdx] || imagesList[0]}
                alt={space.title}
                className="w-full h-full object-cover transition-all duration-300"
              />
              {instantAccess && (
                <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-surface/90 backdrop-blur-md text-text-primary border border-border shadow-sm">
                  <Zap className="w-3.5 h-3.5 text-primary" />
                  <span>Instant 4-Digit PIN Access</span>
                </div>
              )}
              <button
                type="button"
                onClick={handleToggleWishlist}
                aria-label="Save to Wishlist"
                className={`absolute top-4 right-4 p-2.5 rounded-full backdrop-blur-md transition-all shadow-md cursor-pointer ${
                  isWishlisted
                    ? 'bg-rose-500 text-white'
                    : 'bg-surface/90 hover:bg-surface text-text-primary border border-border'
                }`}
              >
                <Heart className={`w-4 h-4 ${isWishlisted ? 'fill-current' : ''}`} />
              </button>
            </div>

            {imagesList.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {imagesList.map((img, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setActiveImageIdx(idx)}
                    className={`relative w-20 h-16 rounded-xl overflow-hidden border-2 shrink-0 transition-all ${
                      activeImageIdx === idx ? 'border-primary ring-2 ring-primary/20' : 'border-border opacity-70 hover:opacity-100'
                    }`}
                  >
                    <img src={img} alt="Thumb" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Title & Metadata */}
          <div>
            <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
              <span className="font-bold text-primary uppercase tracking-wider text-[11px]">
                {space.space_type || space.category}
              </span>
              <span>•</span>
              <div className="flex items-center gap-1 text-text-primary font-bold">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{rating}</span>
                <span className="text-text-muted font-normal">
                  ({reviews.length || space.reviews_count || 12} reviews)
                </span>
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              {space.title}
            </h1>

            <div className="flex items-center gap-2 text-sm text-text-secondary mt-2">
              <MapPin className="w-4 h-4 text-primary shrink-0" />
              <span>{locationStr}</span>
            </div>
          </div>

          {/* Description */}
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-2">
            <h3 className="text-sm font-bold text-text-primary">
              Architectural & Spatial Overview
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed whitespace-pre-line">
              {space.description ||
                'High-speed ergonomic workspace equipped with keyless digital locks, natural illumination, and premium acoustics.'}
            </p>
          </div>

          {/* Amenities */}
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <h3 className="text-sm font-bold text-text-primary">
              Verified Amenities & Spatial Features
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(space.amenities || [
                'High-speed 1Gbps WiFi',
                'Smart Keyless Access',
                'Ergonomic Herman Miller Chairs',
                'Secure Soundproofing',
              ]).map((am, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs text-text-secondary">
                  <div className="w-5 h-5 rounded-md bg-emerald-500/10 text-emerald-600 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <span>{am}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Host Trust & Identity Card */}
          <div className="p-6 rounded-3xl bg-surface border border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center font-bold text-lg">
                <Building2 className="w-6 h-6" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-text-primary">
                  {space.host?.full_name || 'SpaceLoop Host'}
                </h4>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  {space.host?.is_host_verified ? (
                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" />
                      <span>DISCOM Utility Verified</span>
                    </span>
                  ) : (
                    <span className="text-[10px] font-semibold text-text-muted bg-surface border border-border px-2 py-0.5 rounded-full">
                      Utility Verification Pending
                    </span>
                  )}
                  {space.host?.is_verified ? (
                    <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                      Aadhaar Tokenized
                    </span>
                  ) : (
                    <span className="text-[10px] font-semibold text-text-muted bg-surface border border-border px-2 py-0.5 rounded-full">
                      Identity Pending
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:items-end gap-2 w-full sm:w-auto">
              <span className="text-xs text-text-muted">Host response rate: 100%</span>
              <Button
                variant="outline"
                size="xs"
                icon={MessageSquare}
                onClick={() => setInquiryModalOpen(true)}
              >
                Ask Host a Question
              </Button>
            </div>
          </div>

          {/* Reviews Section */}
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary" />
                <span>Renter Reviews ({reviews.length})</span>
              </h3>
            </div>

            {/* Existing Reviews */}
            <div className="space-y-4 divide-y divide-border">
              {reviews.map((rev, idx) => (
                <div key={idx} className="pt-4 first:pt-0 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <strong className="text-text-primary">
                      {rev.author_name || rev.user?.full_name || 'Verified Seeker'}
                    </strong>
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star className="w-3 h-3 fill-amber-400" />
                      <span>{rev.rating || 5}</span>
                    </div>
                  </div>
                  <p className="text-text-secondary">{rev.comment || 'Great architectural vibe and seamless arrival.'}</p>
                </div>
              ))}
              {reviews.length === 0 && (
                <p className="text-xs text-text-muted">No reviews yet for this listing. Be the first to review!</p>
              )}
            </div>

            {/* Add Review Form */}
            {isAuthenticated && (
              <form onSubmit={handleAddReview} className="pt-4 border-t border-border space-y-3">
                <h4 className="text-xs font-bold text-text-primary">Leave a verified review</h4>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-text-secondary">Rating:</span>
                  <select
                    value={reviewRating}
                    onChange={(e) => setReviewRating(Number(e.target.value))}
                    className="px-2 py-1 text-xs rounded-lg bg-surface-elevated border border-border text-text-primary"
                  >
                    {[5, 4, 3, 2, 1].map((r) => (
                      <option key={r} value={r}>
                        {r} Stars
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    required
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    placeholder="Share your experience regarding noise, WiFi, and ergonomics..."
                    className="flex-1 px-3.5 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary"
                  />
                  <Button type="submit" variant="primary" size="sm" disabled={submittingReview}>
                    {submittingReview ? 'Posting...' : 'Post Review'}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right Column: Authoritative Booking Widget */}
        <div className="lg:col-span-5">
          <BookingWidget space={space} />
        </div>
      </div>

      {/* Host Inquiry Modal */}
      {inquiryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md bg-surface border border-border rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary" />
                <h3 className="text-base font-bold text-text-primary">Send Host Inquiry</h3>
              </div>
              <button
                type="button"
                onClick={() => setInquiryModalOpen(false)}
                className="text-text-muted hover:text-text-primary text-xs font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-text-secondary">
              Ask {space.host?.full_name || 'the host'} regarding equipment, quiet hours, or special accommodations for "{space.title}".
            </p>
            <form onSubmit={handleSendInquiry} className="space-y-3">
              <textarea
                required
                rows={4}
                value={inquiryMessage}
                onChange={(e) => setInquiryMessage(e.target.value)}
                placeholder="Hi, I'm planning to work here tomorrow. Is there high-speed WiFi and space for two laptop setups?"
                className="w-full px-3.5 py-2.5 text-xs rounded-2xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary resize-none"
              />
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setInquiryModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  icon={Send}
                  disabled={submittingInquiry || !inquiryMessage.trim()}
                >
                  {submittingInquiry ? 'Sending...' : 'Send Message'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpaceDetails;
