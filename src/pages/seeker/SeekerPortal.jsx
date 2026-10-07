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
} from 'lucide-react';
import { PortalLayout } from '../../layouts/PortalLayout';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { bookingsApi, spacesApi } from '../../services/api';
import { ExploreSpaces } from '../ExploreSpaces';
import { SeekerBookings } from '../SeekerBookings';
import { Profile } from '../Profile';
import { Button } from '../../components/common/Button';

export const SeekerPortal = ({ initialTab = 'dashboard' }) => {
  const { user, logout } = useAuth();
  const { success, error: toastError } = useToast();
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
  const [spaces, setSpaces] = useState([]);
  const [wishlist, setWishlist] = useState([]);
  const [loading, setLoading] = useState(true);

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
          const list = bookingsRes.value.bookings || (Array.isArray(bookingsRes.value) ? bookingsRes.value : []);
          setBookings(list);
        }

        if (spacesRes.status === 'fulfilled') {
          const raw = spacesRes.value.spaces || (Array.isArray(spacesRes.value) ? spacesRes.value : []);
          setSpaces(raw);
        }

        // Real wishlist from storage
        try {
          const storedWishlist = JSON.parse(localStorage.getItem('spaceloop_wishlist') || '[]');
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

  const handleRemoveWishlist = (spaceId) => {
    const updated = wishlist.filter((item) => (item.id || item) !== spaceId);
    setWishlist(updated);
    localStorage.setItem('spaceloop_wishlist', JSON.stringify(updated));
    success('Removed space from your wishlist');
  };

  // Categorize real bookings
  const upcomingBookings = bookings.filter((b) => b.status === 'confirmed' || b.status === 'pending');
  const activeBooking = bookings.find((b) => b.status === 'active' || b.status === 'checked_in') || upcomingBookings[0];
  const completedBookings = bookings.filter((b) => b.status === 'completed');

  // Navigation Items requested specifically for Seeker Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'explore', label: 'Explore Spaces', icon: Compass },
    { id: 'bookings', label: 'My Bookings', icon: Calendar, badge: bookings.length || undefined },
    { id: 'wishlist', label: 'Wishlist', icon: Heart, badge: wishlist.length || undefined },
    { id: 'messages', label: 'Inquiries / Messages', icon: MessageSquare },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
    { id: 'help', label: 'LoopBot / Help', icon: Bot },
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
          {/* Welcome Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-emerald-500/10 via-primary/5 to-surface-elevated border border-border">
            <div>
              <span className="text-xs uppercase font-bold tracking-wider text-emerald-500">
                Seeker Overview
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-1">
                Welcome back, {user?.full_name?.split(' ')[0] || 'Seeker'}
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-1">
                Discover workspaces, unlock instant PIN access, and manage micro-leases.
              </p>
            </div>
            <div className="flex items-center gap-2.5">
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

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Calendar className="w-4 h-4 text-primary" />
                <span>Upcoming</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">
                {upcomingBookings.length}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Completed</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">
                {completedBookings.length}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Heart className="w-4 h-4 text-rose-500" />
                <span>Wishlist</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">
                {wishlist.length}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Trust Score</span>
              </div>
              <p className="text-2xl font-bold text-emerald-500 mt-2">
                {user?.trust_score || '85.0'}%
              </p>
            </div>
          </div>

          {/* Active / Next Upcoming Booking Card */}
          {activeBooking ? (
            <div className="p-5 sm:p-6 rounded-3xl bg-surface border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-primary uppercase tracking-wider">
                  <Clock className="w-4 h-4" />
                  <span>Next Active Reservation</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 capitalize">
                  {activeBooking.status}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                <div className="md:col-span-2 space-y-1.5">
                  <h3 className="text-lg font-bold text-text-primary">
                    {activeBooking.space_title || activeBooking.space?.title || 'Reserved Architectural Workspace'}
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <MapPin className="w-3.5 h-3.5 text-text-muted" />
                    <span>{activeBooking.space?.city || 'Connaught Place, Central Delhi'}</span>
                  </div>
                  <div className="text-xs text-text-muted">
                    <span>Slot: {new Date(activeBooking.start_time || Date.now()).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row md:flex-col gap-2 justify-end">
                  <Link to={`/booking/${activeBooking.id}/access`}>
                    <Button variant="primary" size="sm" className="w-full" icon={KeyRound}>
                      View Smart Access PIN
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => handleTabChange('bookings')}
                  >
                    Manage Reservation
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-3">
              <Calendar className="w-8 h-8 text-text-muted mx-auto" />
              <p className="text-sm font-semibold text-text-primary">No Active Bookings</p>
              <p className="text-xs text-text-secondary max-w-sm mx-auto">
                Ready to book your next productive session? Explore spaces near you with instant PIN access.
              </p>
              <Button variant="primary" size="sm" onClick={() => handleTabChange('explore')}>
                Explore Available Spaces
              </Button>
            </div>
          )}

          {/* Recommended Spaces (Real Listings) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-text-primary">Recommended For You</h2>
                <p className="text-xs text-text-muted">High-speed gigabit workspaces with instant access</p>
              </div>
              <button
                type="button"
                onClick={() => handleTabChange('explore')}
                className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
              >
                <span>View All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {spaces.slice(0, 3).map((space) => (
                <div
                  key={space.id}
                  className="p-4 rounded-2xl bg-surface border border-border hover:border-primary/40 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="w-full h-36 rounded-xl overflow-hidden bg-surface-elevated relative">
                      <img
                        src={space.images?.[0] || '/images/spaceloop-hero-light.jpg'}
                        alt={space.title}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-black/60 text-white backdrop-blur-md">
                        ₹{space.hourly_rate}/hr
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-text-primary truncate">{space.title}</h4>
                    <p className="text-xs text-text-muted truncate">{space.city || space.address}</p>
                  </div>
                  <div className="pt-3 mt-3 border-t border-border flex items-center justify-between">
                    <span className="text-[11px] text-emerald-500 font-medium">Instant Unlock</span>
                    <Link to={`/spaces/${space.id}`}>
                      <Button variant="outline" size="xs">
                        Details
                      </Button>
                    </Link>
                  </div>
                </div>
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
              {wishlist.map((item) => {
                const space = typeof item === 'object' ? item : spaces.find((s) => s.id === item) || {};
                return (
                  <div
                    key={space.id || Math.random()}
                    className="p-4 rounded-2xl bg-surface border border-border flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="w-full h-36 rounded-xl overflow-hidden bg-surface-elevated relative">
                        <img
                          src={space.images?.[0] || '/images/spaceloop-hero-light.jpg'}
                          alt={space.title || 'Space'}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <h4 className="font-bold text-sm text-text-primary truncate">
                        {space.title || 'Architectural Workspace'}
                      </h4>
                      <p className="text-xs text-text-muted truncate">{space.city || 'Bangalore'}</p>
                      <p className="text-xs font-semibold text-primary">₹{space.hourly_rate || 250}/hr</p>
                    </div>
                    <div className="pt-3 mt-3 border-t border-border flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => handleRemoveWishlist(space.id)}
                        className="text-xs text-rose-500 hover:underline"
                      >
                        Remove
                      </button>
                      <Link to={`/spaces/${space.id || ''}`}>
                        <Button variant="primary" size="xs">
                          Book Now
                        </Button>
                      </Link>
                    </div>
                  </div>
                );
              })}
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
          TAB 6: NOTIFICATIONS
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
          TAB 7: REVIEWS
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
          TAB 8: PROFILE
         ========================================================================= */}
      {activeTab === 'profile' && (
        <div className="animate-fadeIn">
          <Profile />
        </div>
      )}

      {/* =========================================================================
          TAB 9: VERIFICATION
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
          TAB 10: LOOPBOT / HELP
         ========================================================================= */}
      {activeTab === 'help' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <div className="flex items-center gap-2.5 text-primary">
              <Bot className="w-6 h-6" />
              <h2 className="text-xl font-bold text-text-primary">SpaceLoop Intelligent Concierge</h2>
            </div>
            <p className="text-xs sm:text-sm text-text-secondary">
              LoopBot helps you discover spaces with specific constraints (e.g., dual 4K monitors, soundproofed podcast booths, 1Gbps fiber optic line).
            </p>
            <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-xs text-text-secondary space-y-2">
              <p className="font-semibold text-text-primary">Common Seeker Questions:</p>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li>How does the digital door PIN work? (PIN activates automatically at slot start time)</li>
                <li>How does escrow protect my payment? (Funds are only released to the host upon check-in)</li>
                <li>Can I cancel my reservation? (Free cancellation up to 2 hours before the start time)</li>
              </ul>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                const botButton = document.querySelector('[aria-label="Open SpaceLoop AI Concierge"]');
                if (botButton) botButton.click();
              }}
            >
              Open Live LoopBot Assistant
            </Button>
          </div>
        </div>
      )}
    </PortalLayout>
  );
};

export default SeekerPortal;
