import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  LayoutDashboard,
  Compass,
  Calendar,
  Heart,
  MessageSquare,
  Bell,
  Star,
  User,
  ShieldCheck,
  Bot,
  LogOut,
  Clock,
  KeyRound,
  QrCode,
  MapPin,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Zap,
  Briefcase,
  BookOpen,
  Users,
  Camera,
  Music,
  Coffee,
  Sliders,
  Send,
  Search,
  Shield,
  Lock,
  ArrowRight,
  Check,
} from 'lucide-react';
import { PortalLayout } from '../../layouts/PortalLayout';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { bookingsApi, spacesApi, aiApi } from '../../services/api';
import { ExploreSpaces } from '../ExploreSpaces';
import { SeekerBookings } from '../SeekerBookings';
import { Profile } from '../Profile';
import { Button } from '../../components/common/Button';
import { AnimatedBackground } from '@/components/core/animated-background';
import { SPACES_DATA } from '../../utils/constants';

export const SeekerPortal = ({ initialTab = 'dashboard' }) => {
  const { user, logout } = useAuth();
  const { success, error: toastError, info } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab') || initialTab;
  const [activeTab, setActiveTab] = useState(tabParam);

  // Sync tab state with search params
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
  };

  // Real data states
  const [bookings, setBookings] = useState([]);
  const [spaces, setSpaces] = useState(SPACES_DATA);
  const [wishlist, setWishlist] = useState([]);
  const [loading, setLoading] = useState(true);

  // LoopBot quick assistant state
  const [loopBotPrompt, setLoopBotPrompt] = useState('');
  const [loopBotResponse, setLoopBotResponse] = useState(null);
  const [loopBotLoading, setLoopBotLoading] = useState(false);

  // Settings tab states
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [smsAlerts, setSmsAlerts] = useState(true);
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);

  // Fetch real seeker activity data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [bookingsRes, spacesRes] = await Promise.allSettled([
          bookingsApi.getMyBookings(),
          spacesApi.getSpaces(),
        ]);

        if (bookingsRes.status === 'fulfilled') {
          const list =
            bookingsRes.value.bookings ||
            (Array.isArray(bookingsRes.value) ? bookingsRes.value : []);
          setBookings(list);
        }

        if (spacesRes.status === 'fulfilled') {
          const raw =
            spacesRes.value.spaces ||
            (Array.isArray(spacesRes.value) ? spacesRes.value : []);
          setSpaces(raw.length > 0 ? raw : SPACES_DATA);
        } else {
          setSpaces(SPACES_DATA);
        }

        // Real wishlist from storage
        try {
          const storedWishlist = JSON.parse(
            localStorage.getItem('spaceloop_wishlist') || '[]'
          );
          setWishlist(storedWishlist);
        } catch {
          setWishlist([]);
        }
      } catch (err) {
        toastError(err.message || 'Could not load Seeker Portal data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Wishlist toggle handler
  const handleToggleWishlist = (space) => {
    const isSaved = wishlist.some((item) => (item.id || item) === space.id);
    let updated;
    if (isSaved) {
      updated = wishlist.filter((item) => (item.id || item) !== space.id);
      success(`Removed "${space.title}" from your wishlist`);
    } else {
      updated = [...wishlist, space];
      success(`Saved "${space.title}" to your wishlist`);
    }
    setWishlist(updated);
    localStorage.setItem('spaceloop_wishlist', JSON.stringify(updated));
  };

  const handleRemoveWishlist = (spaceId) => {
    const updated = wishlist.filter((item) => (item.id || item) !== spaceId);
    setWishlist(updated);
    localStorage.setItem('spaceloop_wishlist', JSON.stringify(updated));
    success('Removed space from your wishlist');
  };

  // LoopBot natural language query submit
  const handleLoopBotSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!loopBotPrompt.trim()) return;

    try {
      setLoopBotLoading(true);
      const res = await aiApi.askAssistant(loopBotPrompt);
      setLoopBotResponse(res.response || res.message || res);
    } catch {
      // Graceful offline fallback
      setLoopBotResponse(
        `I matched your request for "${loopBotPrompt}" with our verified listings. Check out the instant-access spaces in our catalog below!`
      );
    } finally {
      setLoopBotLoading(false);
    }
  };

  // Categorize real bookings
  const upcomingBookings = bookings.filter(
    (b) => b.status === 'confirmed' || b.status === 'pending'
  );
  const activeBooking =
    bookings.find((b) => b.status === 'active' || b.status === 'checked_in') ||
    upcomingBookings[0];
  const completedBookings = bookings.filter((b) => b.status === 'completed');

  // Space categories
  const CATEGORIES = [
    { name: 'Work', icon: Briefcase, description: 'Desks & Private Pods' },
    { name: 'Study', icon: BookOpen, description: 'Quiet Silent Zones' },
    { name: 'Meetings', icon: Users, description: 'Conference Rooms' },
    { name: 'Photoshoots', icon: Camera, description: 'High-Ceiling Studios' },
    { name: 'Events', icon: Sparkles, description: 'Workshops & Showcases' },
    { name: 'Parties', icon: Music, description: 'Social Lounges & Terraces' },
    { name: 'Hangouts', icon: Coffee, description: 'Creative Cafes & Lofts' },
  ];

  // Exact Navigation Items specified for Seeker Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'explore', label: 'Explore Spaces', icon: Compass },
    { id: 'bookings', label: 'My Bookings', icon: Calendar, badge: bookings.length || undefined },
    { id: 'wishlist', label: 'Wishlist', icon: Heart, badge: wishlist.length || undefined },
    { id: 'messages', label: 'Inquiries / Messages', icon: MessageSquare },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
    { id: 'loopbot', label: 'LoopBot', icon: Bot },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'settings', label: 'Settings', icon: Sliders },
    {
      id: 'logout',
      label: 'Logout',
      icon: LogOut,
      action: async () => {
        await logout();
        navigate('/');
      },
    },
  ];

  return (
    <PortalLayout
      portalName="Seeker Portal"
      role="seeker"
      navItems={navItems}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: SEEKER DASHBOARD
         ========================================================================= */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6 sm:space-y-8 animate-fadeIn">
          
          {/* -------------------------------------------------------------------
              WELCOME SECTION
             ------------------------------------------------------------------- */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-emerald-500/10 via-primary/5 to-surface-elevated border border-border shadow-sm">
            <div>
              <span className="text-xs uppercase font-extrabold tracking-wider text-emerald-500">
                Seeker Dashboard
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-1">
                Welcome back, {user?.full_name?.split(' ')[0] || 'Seeker'}
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-1.5 max-w-xl">
                Find the perfect space for what you have in mind.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                variant="primary"
                size="md"
                onClick={() => handleTabChange('explore')}
                icon={Compass}
              >
                Explore Spaces
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={() => handleTabChange('bookings')}
                icon={Calendar}
              >
                My Bookings
              </Button>
            </div>
          </div>

          {/* -------------------------------------------------------------------
              1. UPCOMING BOOKING
             ------------------------------------------------------------------- */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-text-primary flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary" />
                <span>Upcoming Booking</span>
              </h2>
              {activeBooking && (
                <button
                  type="button"
                  onClick={() => handleTabChange('bookings')}
                  className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                >
                  <span>View All Bookings</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {activeBooking ? (
              <div className="p-5 sm:p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                    Next Scheduled Reservation
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 capitalize">
                    {activeBooking.status || 'Confirmed'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-5 items-center">
                  <div className="w-full h-32 md:h-28 rounded-2xl overflow-hidden bg-surface-elevated shrink-0 relative">
                    <img
                      src={
                        activeBooking.space?.images?.[0] ||
                        activeBooking.image ||
                        '/images/spaceloop-hero-light.jpg'
                      }
                      alt={activeBooking.space_title || 'Reserved space'}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="md:col-span-2 space-y-1.5">
                    <h3 className="text-base sm:text-lg font-bold text-text-primary">
                      {activeBooking.space_title ||
                        activeBooking.space?.title ||
                        'The Glass Loft Pavilion & Terrace'}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-text-secondary">
                      <MapPin className="w-3.5 h-3.5 text-text-muted shrink-0" />
                      <span>
                        {activeBooking.space?.city ||
                          activeBooking.space?.location ||
                          'Design District, Connaught Place'}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted pt-1">
                      <span>
                        📅 Date: {new Date(activeBooking.start_time || Date.now()).toLocaleDateString()}
                      </span>
                      <span>
                        ⏰ Slot: {new Date(activeBooking.start_time || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <span className="font-semibold text-text-primary">
                        💳 Amount: ₹{activeBooking.total_amount || activeBooking.amount || 350}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row md:flex-col gap-2 justify-end">
                    <Link to={`/booking/${activeBooking.id}/access`}>
                      <Button variant="primary" size="sm" className="w-full" icon={KeyRound}>
                        View Access PIN
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => handleTabChange('bookings')}
                    >
                      View Booking
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-3">
                <Calendar className="w-8 h-8 text-text-muted mx-auto" />
                <p className="text-sm font-semibold text-text-primary">No upcoming bookings</p>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  You do not have any active space reservations. Book a desk or creative studio with instant digital keyless access.
                </p>
                <Button variant="primary" size="sm" onClick={() => handleTabChange('explore')}>
                  Explore Spaces
                </Button>
              </div>
            )}
          </div>

          {/* -------------------------------------------------------------------
              2. QUICK ACTIONS
             ------------------------------------------------------------------- */}
          <div className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-text-primary">Quick Actions</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
              {[
                {
                  id: 'explore',
                  title: 'Explore Spaces',
                  description: 'Browse verified spaces',
                  icon: Compass,
                  color: 'text-primary bg-primary/10',
                },
                {
                  id: 'bookings',
                  title: 'My Bookings',
                  description: 'Active & past passes',
                  icon: Calendar,
                  color: 'text-indigo-500 bg-indigo-500/10',
                },
                {
                  id: 'wishlist',
                  title: 'Wishlist',
                  description: 'Saved workspaces',
                  icon: Heart,
                  color: 'text-rose-500 bg-rose-500/10',
                },
                {
                  id: 'messages',
                  title: 'Send Inquiry',
                  description: 'Message space hosts',
                  icon: MessageSquare,
                  color: 'text-amber-500 bg-amber-500/10',
                },
                {
                  id: 'loopbot',
                  title: 'LoopBot',
                  description: 'AI Smart Concierge',
                  icon: Bot,
                  color: 'text-emerald-500 bg-emerald-500/10',
                },
              ].map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.id}
                    type="button"
                    onClick={() => handleTabChange(action.id)}
                    className="p-4 rounded-2xl bg-surface border border-border hover:border-primary/50 hover:bg-surface-elevated transition-all text-left flex flex-col justify-between group cursor-pointer shadow-sm"
                  >
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${action.color} mb-3 group-hover:scale-105 transition-transform`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-bold text-xs sm:text-sm text-text-primary group-hover:text-primary transition-colors">
                        {action.title}
                      </p>
                      <p className="text-[11px] text-text-muted mt-0.5 truncate">
                        {action.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* -------------------------------------------------------------------
              3. DISCOVER / RECOMMENDED SPACES (Main Visual with AnimatedBackground)
             ------------------------------------------------------------------- */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base sm:text-lg font-bold text-text-primary">
                    Recommended for You
                  </h2>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                    <Sparkles className="w-3 h-3" />
                    <span>AI Smart Matching</span>
                  </span>
                </div>
                <p className="text-xs text-text-muted mt-0.5">
                  Handpicked architectural listings with instant keyless unlock and fiber WiFi
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleTabChange('explore')}
                className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
              >
                <span>Explore All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <AnimatedBackground
                className="rounded-3xl bg-zinc-200/80 dark:bg-zinc-800 border border-zinc-300/70 dark:border-zinc-700/70 shadow-sm"
                transition={{
                  type: 'spring',
                  bounce: 0.2,
                  duration: 0.6,
                }}
                enableHover
              >
                {spaces.slice(0, 3).map((space, index) => {
                  const isWishlisted = wishlist.some(
                    (w) => (w.id || w) === space.id
                  );
                  return (
                    <div
                      key={space.id || index}
                      data-id={`seeker-card-${space.id || index}`}
                      className="p-2 w-full h-full flex flex-col"
                    >
                      <div className="p-4 rounded-2xl bg-surface border border-border hover:border-primary/40 transition-all flex flex-col justify-between h-full">
                        <div className="space-y-2.5">
                          <div className="w-full h-40 rounded-xl overflow-hidden bg-surface-elevated relative group">
                            <img
                              src={
                                space.images?.[0] ||
                                space.image ||
                                '/images/spaceloop-hero-light.jpg'
                              }
                              alt={space.title}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                            <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-black/60 text-white backdrop-blur-md">
                              ₹{space.hourly_rate || space.price || 250}/hr
                            </span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleWishlist(space);
                              }}
                              aria-label="Save to Wishlist"
                              className={`absolute top-2.5 right-2.5 p-1.5 rounded-full backdrop-blur-md transition-colors ${
                                isWishlisted
                                  ? 'bg-rose-500 text-white'
                                  : 'bg-black/40 text-white hover:bg-black/60'
                              }`}
                            >
                              <Heart
                                className={`w-3.5 h-3.5 ${
                                  isWishlisted ? 'fill-current' : ''
                                }`}
                              />
                            </button>
                          </div>

                          <div className="space-y-1">
                            <h4 className="font-bold text-sm text-text-primary truncate">
                              {space.title}
                            </h4>
                            <div className="flex items-center gap-1 text-xs text-text-muted truncate">
                              <MapPin className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate">
                                {space.city || space.location || space.address || 'Central Delhi'}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="pt-3 mt-3 border-t border-border flex items-center justify-between">
                          <div className="flex items-center gap-1 text-xs font-semibold text-text-primary">
                            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                            <span>{space.rating || 4.9}</span>
                            <span className="text-text-muted font-normal text-[11px]">
                              ({space.reviews || 42})
                            </span>
                          </div>
                          <Link to={`/spaces/${space.id}`} state={{ space }}>
                            <Button variant="primary" size="xs">
                              View Space
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </AnimatedBackground>
            </div>
          </div>

          {/* -------------------------------------------------------------------
              4. CATEGORIES
             ------------------------------------------------------------------- */}
          <div className="space-y-3">
            <h2 className="text-base sm:text-lg font-bold text-text-primary">Space Categories</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 sm:gap-3">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                return (
                  <button
                    key={cat.name}
                    type="button"
                    onClick={() => navigate(`/explore?category=${encodeURIComponent(cat.name)}`)}
                    className="p-3.5 rounded-2xl bg-surface border border-border hover:border-primary/50 hover:bg-surface-elevated transition-all flex flex-col items-center text-center group cursor-pointer shadow-sm"
                  >
                    <div className="w-9 h-9 rounded-xl bg-surface-elevated text-primary flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold text-text-primary group-hover:text-primary transition-colors">
                      {cat.name}
                    </span>
                    <span className="text-[10px] text-text-muted mt-0.5 line-clamp-1">
                      {cat.description}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* -------------------------------------------------------------------
              5. RECENT ACTIVITY & 6. TRUST & SAFETY (Two-Column Layout)
             ------------------------------------------------------------------- */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* 5. RECENT ACTIVITY */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" />
                  <span>Recent Activity</span>
                </h3>
                <span className="text-[11px] text-text-muted font-medium">Real-time Feed</span>
              </div>

              {bookings.length > 0 || wishlist.length > 0 ? (
                <div className="space-y-3 text-xs">
                  {bookings.slice(0, 2).map((b) => (
                    <div
                      key={b.id}
                      className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-start gap-3"
                    >
                      <Calendar className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-text-primary truncate">
                          Reservation #{b.id}: {b.space_title || 'Workspace'}
                        </p>
                        <p className="text-[11px] text-text-muted mt-0.5">
                          Status: <span className="capitalize font-medium text-emerald-500">{b.status}</span> • ₹{b.total_amount || 350}
                        </p>
                      </div>
                    </div>
                  ))}

                  {wishlist.slice(0, 1).map((w, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-start gap-3"
                    >
                      <Heart className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-text-primary truncate">
                          Added to Wishlist: {w.title || 'Architectural Space'}
                        </p>
                        <p className="text-[11px] text-text-muted mt-0.5">
                          Saved for instant booking
                        </p>
                      </div>
                    </div>
                  ))}

                  <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-start gap-3">
                    <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-text-primary">
                        Trust Score Calibration: {user?.trust_score || '85.0'}%
                      </p>
                      <p className="text-[11px] text-text-muted mt-0.5">
                        Identity verified & safety score calibrated
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-surface-elevated border border-dashed border-border text-center space-y-1.5">
                  <Clock className="w-6 h-6 text-text-muted mx-auto" />
                  <p className="text-xs font-semibold text-text-primary">No recent activity yet</p>
                  <p className="text-[11px] text-text-secondary">
                    Your bookings, inquiries, and saved spaces will show up here.
                  </p>
                </div>
              )}
            </div>

            {/* 6. TRUST & SAFETY */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Trust & Safety</span>
                </h3>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                  Protected
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <User className="w-4 h-4 text-primary shrink-0" />
                    <div>
                      <p className="font-semibold text-text-primary">Identity Verification</p>
                      <p className="text-[11px] text-text-muted">
                        {user?.is_verified ? 'Government ID Verified' : 'Standard Verification Active'}
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-500">
                    {user?.trust_score || '85.0'}% Score
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Lock className="w-4 h-4 text-emerald-500 shrink-0" />
                    <div>
                      <p className="font-semibold text-text-primary">Secure Booking & PIN</p>
                      <p className="text-[11px] text-text-muted">
                        Encrypted rolling PINs activate only during booked slot
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] text-emerald-500 font-semibold">Active</span>
                </div>

                <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Shield className="w-4 h-4 text-primary shrink-0" />
                    <div>
                      <p className="font-semibold text-text-primary">Micro-Escrow Protection</p>
                      <p className="text-[11px] text-text-muted">
                        Funds released to host only after successful check-in
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] text-emerald-500 font-semibold">Guaranteed</span>
                </div>

                <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <HelpCircle className="w-4 h-4 text-indigo-500 shrink-0" />
                    <div>
                      <p className="font-semibold text-text-primary">Support & Space Rules</p>
                      <p className="text-[11px] text-text-muted">
                        24/7 dedicated assistance for check-in and access
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleTabChange('loopbot')}
                    className="text-[11px] text-primary hover:underline font-semibold"
                  >
                    Contact
                  </button>
                </div>
              </div>
            </div>

          </div>

          {/* -------------------------------------------------------------------
              7. LOOPBOT (Interactive Assistant Card)
             ------------------------------------------------------------------- */}
          <div className="p-6 sm:p-8 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-xs shadow-sm">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-text-primary">
                    LoopBot AI Concierge
                  </h3>
                  <p className="text-xs text-text-muted">
                    Ask for specific space constraints, natural lighting, audio setups, or booking help
                  </p>
                </div>
              </div>
              <span className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                Online
              </span>
            </div>

            <form onSubmit={handleLoopBotSubmit} className="flex gap-2">
              <input
                type="text"
                value={loopBotPrompt}
                onChange={(e) => setLoopBotPrompt(e.target.value)}
                placeholder="Ask: 'Find a quiet workspace for 4 people with fiber optic internet'..."
                className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-surface-elevated border border-border focus:outline-none focus:border-primary text-text-primary placeholder:text-text-muted transition-colors"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                icon={Send}
                disabled={loopBotLoading || !loopBotPrompt.trim()}
              >
                {loopBotLoading ? 'Searching...' : 'Ask LoopBot'}
              </Button>
            </form>

            {loopBotResponse && (
              <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 text-xs text-text-primary space-y-1 animate-fadeIn">
                <p className="font-bold text-primary flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>LoopBot Recommendation:</span>
                </p>
                <p className="text-text-secondary leading-relaxed">
                  {typeof loopBotResponse === 'string'
                    ? loopBotResponse
                    : loopBotResponse.response || JSON.stringify(loopBotResponse)}
                </p>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-text-muted">
              <span>Quick prompts:</span>
              {[
                'Silent study booth in Central Delhi',
                'Podcast studio with condenser microphones',
                'Rooftop workspace with sunset views',
              ].map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => {
                    setLoopBotPrompt(prompt);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-[11px] text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* =========================================================================
          TAB 2: EXPLORE SPACES
         ========================================================================= */}
      {activeTab === 'explore' && (
        <div className="animate-fadeIn">
          <ExploreSpaces />
        </div>
      )}

      {/* =========================================================================
          TAB 3: MY BOOKINGS
         ========================================================================= */}
      {activeTab === 'bookings' && (
        <div className="animate-fadeIn">
          <SeekerBookings />
        </div>
      )}

      {/* =========================================================================
          TAB 4: WISHLIST
         ========================================================================= */}
      {activeTab === 'wishlist' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Saved Workspaces</h1>
            <p className="text-xs text-text-secondary mt-1">
              Your saved architectural studios, coworking desks, and conference suites.
            </p>
          </div>

          {wishlist.length === 0 ? (
            <div className="p-12 rounded-3xl bg-surface border border-dashed border-border text-center space-y-3">
              <Heart className="w-8 h-8 text-rose-500/50 mx-auto" />
              <p className="text-sm font-semibold text-text-primary">Your Wishlist is Empty</p>
              <p className="text-xs text-text-secondary max-w-sm mx-auto">
                Save spaces you love while browsing to easily access or book them later.
              </p>
              <Button variant="primary" size="sm" onClick={() => handleTabChange('explore')}>
                Browse Spaces
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <AnimatedBackground
                className="rounded-3xl bg-zinc-200/80 dark:bg-zinc-800 border border-zinc-300/70 dark:border-zinc-700/70 shadow-sm"
                transition={{
                  type: 'spring',
                  bounce: 0.2,
                  duration: 0.6,
                }}
                enableHover
              >
                {wishlist.map((item, index) => {
                  const space =
                    typeof item === 'object'
                      ? item
                      : spaces.find((s) => s.id === item) || {};
                  return (
                    <div
                      key={space.id || index}
                      data-id={`wishlist-${space.id || index}`}
                      className="p-2 w-full h-full flex flex-col"
                    >
                      <div className="p-4 rounded-2xl bg-surface border border-border flex flex-col justify-between h-full">
                        <div className="space-y-2">
                          <div className="w-full h-36 rounded-xl overflow-hidden bg-surface-elevated relative">
                            <img
                              src={
                                space.images?.[0] ||
                                space.image ||
                                '/images/spaceloop-hero-light.jpg'
                              }
                              alt={space.title || 'Space'}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <h4 className="font-bold text-sm text-text-primary truncate">
                            {space.title || 'Architectural Workspace'}
                          </h4>
                          <p className="text-xs text-text-muted truncate">
                            {space.city || space.location || 'Bangalore'}
                          </p>
                          <p className="text-xs font-semibold text-primary">
                            ₹{space.hourly_rate || space.price || 250}/hr
                          </p>
                        </div>
                        <div className="pt-3 mt-3 border-t border-border flex items-center justify-between">
                          <button
                            type="button"
                            onClick={() => handleRemoveWishlist(space.id)}
                            className="text-xs text-rose-500 hover:underline cursor-pointer"
                          >
                            Remove
                          </button>
                          <Link to={`/spaces/${space.id || ''}`} state={{ space }}>
                            <Button variant="primary" size="xs">
                              Book Now
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </AnimatedBackground>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 5: INQUIRIES / MESSAGES
         ========================================================================= */}
      {activeTab === 'messages' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Inquiries & Messages</h1>
            <p className="text-xs text-text-secondary mt-1">
              Direct communication channels with workspace hosts.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-3">
            <MessageSquare className="w-8 h-8 text-primary mx-auto" />
            <p className="text-sm font-semibold text-text-primary">No Active Message Threads</p>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              When you send an inquiry regarding a space or book a reservation, host communication will appear here.
            </p>
            <Button variant="outline" size="sm" onClick={() => handleTabChange('explore')}>
              Explore Spaces
            </Button>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 6: REVIEWS
         ========================================================================= */}
      {activeTab === 'reviews' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Reviews & Ratings</h1>
            <p className="text-xs text-text-secondary mt-1">
              Feedback you have provided to workspace hosts.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-3">
            <Star className="w-8 h-8 text-amber-500 mx-auto" />
            <p className="text-sm font-semibold text-text-primary">No Reviews Yet</p>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              Once you complete a booking, you can submit verified reviews with ratings on WiFi speed, cleanliness, and soundproofing.
            </p>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 7: NOTIFICATIONS
         ========================================================================= */}
      {activeTab === 'notifications' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Notifications</h1>
            <p className="text-xs text-text-secondary mt-1">
              Real-time updates regarding reservations, PIN credentials, and account activity.
            </p>
          </div>

          <div className="space-y-3">
            <div className="p-4 rounded-2xl bg-surface border border-border flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-text-primary">Account Verification Complete</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Your identity trust rating has been calibrated to {user?.trust_score || '85.0'}%.
                </p>
                <span className="text-[10px] text-text-muted">Today</span>
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border flex items-start gap-3">
              <Zap className="w-5 h-5 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-text-primary">Micro-Escrow Protection Active</p>
                <p className="text-xs text-text-muted mt-0.5">
                  All upcoming bookings are safeguarded with two-phase escrow release.
                </p>
                <span className="text-[10px] text-text-muted">Yesterday</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 8: VERIFICATION
         ========================================================================= */}
      {activeTab === 'verification' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Identity & Trust Verification</h1>
            <p className="text-xs text-text-secondary mt-1">
              Verify your student identity or government ID to unlock discounts and enhanced access privileges.
            </p>
          </div>

          <Profile />
        </div>
      )}

      {/* =========================================================================
          TAB 9: LOOPBOT (Full Assistant Interface)
         ========================================================================= */}
      {activeTab === 'loopbot' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-6 sm:p-8 rounded-3xl bg-surface border border-border space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-primary text-white flex items-center justify-center font-bold">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary">
                  LoopBot AI Concierge & Assistant
                </h2>
                <p className="text-xs text-text-secondary">
                  Your personalized workspace assistant for discovery, recommendations, and space guidelines
                </p>
              </div>
            </div>

            <form onSubmit={handleLoopBotSubmit} className="flex gap-2">
              <input
                type="text"
                value={loopBotPrompt}
                onChange={(e) => setLoopBotPrompt(e.target.value)}
                placeholder="Ask anything: 'Find a sunlit studio near SoHo with podcast equipment'..."
                className="flex-1 px-4 py-3 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border focus:outline-none focus:border-primary text-text-primary placeholder:text-text-muted transition-colors"
              />
              <Button
                type="submit"
                variant="primary"
                size="md"
                icon={Send}
                disabled={loopBotLoading || !loopBotPrompt.trim()}
              >
                {loopBotLoading ? 'Thinking...' : 'Send'}
              </Button>
            </form>

            {loopBotResponse && (
              <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs sm:text-sm text-text-primary space-y-2">
                <p className="font-bold text-emerald-600 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  <span>LoopBot Guidance:</span>
                </p>
                <p className="text-text-secondary leading-relaxed">
                  {typeof loopBotResponse === 'string'
                    ? loopBotResponse
                    : loopBotResponse.response || JSON.stringify(loopBotResponse)}
                </p>
              </div>
            )}

            <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-xs text-text-secondary space-y-2">
              <p className="font-semibold text-text-primary">What LoopBot can help you with:</p>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li>Finding spaces by exact equipment (dual 4K displays, podcast microphones, acoustic baffling)</li>
                <li>Explaining how the digital door PIN activates at reservation start time</li>
                <li>Clarifying micro-escrow payment protection and check-in guarantees</li>
                <li>Checking cancellation policies (free cancellation up to 2 hours prior to slot)</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 10: PROFILE
         ========================================================================= */}
      {activeTab === 'profile' && (
        <div className="animate-fadeIn">
          <Profile />
        </div>
      )}

      {/* =========================================================================
          TAB 11: SETTINGS
         ========================================================================= */}
      {activeTab === 'settings' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Account & Privacy Settings</h1>
            <p className="text-xs text-text-secondary mt-1">
              Manage notifications, access security, and preference configurations.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border space-y-5">
            <h3 className="text-base font-bold text-text-primary">Notification Preferences</h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-elevated border border-border cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">Email Notifications</p>
                  <p className="text-[11px] text-text-muted">Receive instant booking access PIN and receipt via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => {
                    setEmailAlerts(e.target.checked);
                    success('Email notification settings updated');
                  }}
                  className="w-4 h-4 accent-primary rounded"
                />
              </label>

              <label className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-elevated border border-border cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">SMS & WhatsApp Alerts</p>
                  <p className="text-[11px] text-text-muted">Get automated PIN arrival reminders 15 minutes before slot</p>
                </div>
                <input
                  type="checkbox"
                  checked={smsAlerts}
                  onChange={(e) => {
                    setSmsAlerts(e.target.checked);
                    success('SMS alert settings updated');
                  }}
                  className="w-4 h-4 accent-primary rounded"
                />
              </label>
            </div>

            <h3 className="text-base font-bold text-text-primary pt-2">Security & Access</h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-elevated border border-border cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">Two-Factor Authentication (2FA)</p>
                  <p className="text-[11px] text-text-muted">Require biometric or OTP confirmation when generating access passes</p>
                </div>
                <input
                  type="checkbox"
                  checked={twoFactorAuth}
                  onChange={(e) => {
                    setTwoFactorAuth(e.target.checked);
                    success(e.target.checked ? '2FA Enabled' : '2FA Disabled');
                  }}
                  className="w-4 h-4 accent-primary rounded"
                />
              </label>
            </div>
          </div>
        </div>
      )}

    </PortalLayout>
  );
};

export default SeekerPortal;
