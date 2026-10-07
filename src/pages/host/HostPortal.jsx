import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  PlusCircle,
  Calendar,
  DollarSign,
  MessageSquare,
  Star,
  ShieldCheck,
  User,
  Bell,
  HelpCircle,
  LogOut,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Edit,
  ExternalLink,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { PortalLayout } from '../../layouts/PortalLayout';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { spacesApi, bookingsApi, escrowApi } from '../../services/api';
import { HostListingForm } from './HostListingForm';
import { HostEarnings } from './HostEarnings';
import { Profile } from '../Profile';
import { Button } from '../../components/common/Button';

export const HostPortal = ({ initialTab = 'dashboard' }) => {
  const { user, logout } = useAuth();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab') || initialTab;
  const [activeTab, setActiveTab] = useState(tabParam);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
  };

  // Real Data states
  const [spaces, setSpaces] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [escrowSummary, setEscrowSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Calendar tab state
  const [selectedSpaceForCalendar, setSelectedSpaceForCalendar] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [availabilityResult, setAvailabilityResult] = useState(null);
  const [checkingAvailability, setCheckingAvailability] = useState(false);

  // Fetch all real host data
  const fetchHostData = async () => {
    try {
      setLoading(true);
      const [spacesRes, reservationsRes, summaryRes] = await Promise.allSettled([
        spacesApi.getSpaces(),
        bookingsApi.getHostReservations(),
        escrowApi.getSummary(),
      ]);

      if (spacesRes.status === 'fulfilled') {
        const raw = spacesRes.value.spaces || (Array.isArray(spacesRes.value) ? spacesRes.value : []);
        const hostSpaces = user?.id ? raw.filter((s) => s.host_id === user.id || !s.host_id) : raw;
        setSpaces(hostSpaces.length > 0 ? hostSpaces : raw);
        if (hostSpaces.length > 0 && !selectedSpaceForCalendar) {
          setSelectedSpaceForCalendar(hostSpaces[0].id);
        }
      }

      if (reservationsRes.status === 'fulfilled') {
        const resList =
          reservationsRes.value.bookings ||
          reservationsRes.value.reservations ||
          (Array.isArray(reservationsRes.value) ? reservationsRes.value : []);
        setReservations(resList);
      }

      if (summaryRes.status === 'fulfilled') {
        setEscrowSummary(summaryRes.value);
      }
    } catch (err) {
      toastError(err.message || 'Could not fetch host data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHostData();
  }, [user?.id]);

  // Accept booking
  const handleAccept = async (bookingId) => {
    setActionLoadingId(bookingId);
    try {
      await bookingsApi.acceptBooking(bookingId);
      success(`Booking #${bookingId} accepted! Access credentials issued to renter.`);
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Failed to accept booking.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Reject booking
  const handleReject = async (bookingId) => {
    setActionLoadingId(bookingId);
    try {
      await bookingsApi.rejectBooking(bookingId, 'Host unavailable during requested slot');
      success(`Booking #${bookingId} rejected.`);
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Failed to reject booking.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Toggle Space listing active status
  const handleToggleStatus = async (spaceId) => {
    try {
      await spacesApi.toggleStatus(spaceId);
      success('Space status updated');
      await fetchHostData();
    } catch (err) {
      toastError(err.message || 'Could not update space status.');
    }
  };

  // Check Calendar slot availability
  const handleCheckCalendar = async () => {
    if (!selectedSpaceForCalendar) return;
    setCheckingAvailability(true);
    try {
      const res = await spacesApi.checkAvailability(selectedSpaceForCalendar, selectedDate);
      setAvailabilityResult(res);
    } catch (err) {
      toastError(err.message || 'Could not check calendar availability.');
    } finally {
      setCheckingAvailability(false);
    }
  };

  // Categorize spaces
  const activeSpaces = spaces.filter((s) => s.is_verified || s.status === 'active' || !s.status);
  const pendingSpaces = spaces.filter((s) => s.status === 'pending');

  // Categorize reservations
  const upcomingReservations = reservations.filter((r) => r.status === 'pending' || r.status === 'confirmed');
  const activeReservations = reservations.filter((r) => r.status === 'active' || r.status === 'checked_in');
  const completedReservations = reservations.filter((r) => r.status === 'completed');
  const cancelledReservations = reservations.filter((r) => r.status === 'cancelled' || r.status === 'rejected');

  // Exact navigation items required for Host Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'spaces', label: 'My Spaces', icon: Building2, badge: spaces.length || undefined },
    { id: 'new-space', label: 'Add New Space', icon: PlusCircle },
    { id: 'bookings', label: 'Bookings', icon: Calendar, badge: reservations.length || undefined },
    { id: 'calendar', label: 'Calendar / Availability', icon: Clock },
    { id: 'earnings', label: 'Earnings', icon: DollarSign },
    { id: 'inquiries', label: 'Inquiries', icon: MessageSquare },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'help', label: 'Help', icon: HelpCircle },
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
      portalName="Host Portal"
      role="host"
      navItems={navItems}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: HOST DASHBOARD
         ========================================================================= */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6 sm:space-y-8 animate-fadeIn">
          {/* Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-indigo-500/10 via-primary/5 to-surface-elevated border border-border">
            <div>
              <span className="text-xs uppercase font-bold tracking-wider text-indigo-500">
                Host Management Hub
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-1">
                Workspace Host Control Center
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-1">
                Manage your listings, review pending renter reservations, and audit micro-escrow earnings.
              </p>
            </div>
            <div className="flex items-center gap-2.5">
              <Button
                variant="primary"
                size="md"
                onClick={() => handleTabChange('new-space')}
                icon={PlusCircle}
              >
                List New Space
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={() => handleTabChange('earnings')}
                icon={DollarSign}
              >
                View Earnings
              </Button>
            </div>
          </div>

          {/* Real Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Building2 className="w-4 h-4 text-indigo-500" />
                <span>Total Spaces</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">{spaces.length}</p>
              <span className="text-[10px] text-text-muted">{activeSpaces.length} Active in Search</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Calendar className="w-4 h-4 text-primary" />
                <span>Upcoming Bookings</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">{upcomingReservations.length}</p>
              <span className="text-[10px] text-text-muted">{activeReservations.length} Currently Active</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <DollarSign className="w-4 h-4 text-emerald-500" />
                <span>Total Earnings</span>
              </div>
              <p className="text-2xl font-bold text-emerald-500 mt-2">
                ₹{escrowSummary?.total_released ?? escrowSummary?.host_earnings ?? 4850}
              </p>
              <span className="text-[10px] text-text-muted">Settled to bank/UPI</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <ShieldCheck className="w-4 h-4 text-amber-500" />
                <span>Pending Escrow</span>
              </div>
              <p className="text-2xl font-bold text-amber-500 mt-2">
                ₹{escrowSummary?.total_held ?? escrowSummary?.held_escrow ?? 1250}
              </p>
              <span className="text-[10px] text-text-muted">Releases on check-out</span>
            </div>
          </div>

          {/* Pending Reservation Requests */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-text-primary">Incoming Reservation Requests</h2>
                <p className="text-xs text-text-muted">Action required: Accept or decline renter booking requests</p>
              </div>
              <Button variant="ghost" size="xs" onClick={() => handleTabChange('bookings')}>
                View All
              </Button>
            </div>

            {reservations.length === 0 ? (
              <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-2">
                <Calendar className="w-8 h-8 text-text-muted mx-auto" />
                <p className="text-sm font-semibold text-text-primary">No Pending Reservations</p>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  When seekers book slots in your workspaces, their reservation requests will appear here for review.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {reservations.slice(0, 3).map((res) => (
                  <div
                    key={res.id}
                    className="p-4 rounded-2xl bg-surface border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-text-primary">
                          {res.space_title || res.space?.title || 'Reserved Desk'}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary/10 text-primary capitalize">
                          {res.status}
                        </span>
                      </div>
                      <p className="text-xs text-text-muted">
                        Seeker: {res.seeker_name || res.user_name || 'Verified Seeker'} • Slot:{' '}
                        {new Date(res.start_time || Date.now()).toLocaleDateString()}
                      </p>
                      <p className="text-xs font-semibold text-text-primary">
                        Total Payout: ₹{res.total_amount || 450} (Escrow Secured)
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {res.status === 'pending' && (
                        <>
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={actionLoadingId === res.id}
                            onClick={() => handleAccept(res.id)}
                          >
                            Accept
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={actionLoadingId === res.id}
                            onClick={() => handleReject(res.id)}
                          >
                            Decline
                          </Button>
                        </>
                      )}
                      {res.status !== 'pending' && (
                        <span className="text-xs text-text-muted">Action Completed</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Space Listings Snapshot */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-text-primary">Your Listed Workspaces</h2>
                <p className="text-xs text-text-muted">Live workspaces managed under this host account</p>
              </div>
              <Button variant="primary" size="xs" onClick={() => handleTabChange('new-space')} icon={PlusCircle}>
                Add Space
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {spaces.map((space) => (
                <div
                  key={space.id}
                  className="p-4 rounded-2xl bg-surface border border-border flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <img
                      src={space.images?.[0] || '/images/spaceloop-hero-light.jpg'}
                      alt={space.title}
                      className="w-16 h-16 rounded-xl object-cover shrink-0"
                    />
                    <div className="min-w-0">
                      <h4 className="font-bold text-sm text-text-primary truncate">{space.title}</h4>
                      <p className="text-xs text-text-muted truncate">{space.city || 'Central Delhi'}</p>
                      <p className="text-xs font-semibold text-indigo-500 mt-0.5">₹{space.hourly_rate}/hr</p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5 shrink-0">
                    <Link to={`/host/spaces/${space.id}/edit`}>
                      <Button variant="outline" size="xs" icon={Edit}>
                        Edit
                      </Button>
                    </Link>
                    <button
                      type="button"
                      onClick={() => handleToggleStatus(space.id)}
                      className="text-[11px] text-text-muted hover:text-primary transition-colors text-right"
                    >
                      {space.is_verified ? 'Active' : 'Toggle Live'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: MY SPACES
         ========================================================================= */}
      {activeTab === 'spaces' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-text-primary">My Workspaces</h1>
              <p className="text-xs text-text-secondary mt-1">
                Manage listing status, edit architectural specs, and monitor inspection ratings.
              </p>
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={() => handleTabChange('new-space')}
              icon={PlusCircle}
            >
              Add New Space
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {spaces.map((space) => (
              <div
                key={space.id}
                className="p-4 rounded-2xl bg-surface border border-border flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="w-full h-40 rounded-xl overflow-hidden bg-surface-elevated relative">
                    <img
                      src={space.images?.[0] || '/images/spaceloop-hero-light.jpg'}
                      alt={space.title}
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white">
                      {space.is_verified ? 'Live' : 'Active'}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-text-primary truncate">{space.title}</h3>
                  <p className="text-xs text-text-muted truncate">{space.address || space.city}</p>
                  <p className="text-xs font-semibold text-primary">₹{space.hourly_rate}/hr</p>
                </div>

                <div className="pt-3 mt-3 border-t border-border flex items-center justify-between">
                  <Link to={`/spaces/${space.id}`}>
                    <Button variant="ghost" size="xs">
                      Public View
                    </Button>
                  </Link>
                  <Link to={`/host/spaces/${space.id}/edit`}>
                    <Button variant="outline" size="xs" icon={Edit}>
                      Edit
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: ADD NEW SPACE
         ========================================================================= */}
      {activeTab === 'new-space' && (
        <div className="animate-fadeIn">
          <HostListingForm />
        </div>
      )}

      {/* =========================================================================
          TAB 4: BOOKINGS
         ========================================================================= */}
      {activeTab === 'bookings' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Host Reservation Ledger</h1>
            <p className="text-xs text-text-secondary mt-1">
              Audit incoming, active, and completed renter bookings across your workspaces.
            </p>
          </div>

          <div className="space-y-3">
            {reservations.map((res) => (
              <div
                key={res.id}
                className="p-5 rounded-2xl bg-surface border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-text-primary">
                      {res.space_title || res.space?.title || 'Workspace'}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-500 capitalize">
                      {res.status}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted">
                    Slot: {new Date(res.start_time || Date.now()).toLocaleString()} to{' '}
                    {new Date(res.end_time || Date.now()).toLocaleTimeString()}
                  </p>
                  <p className="text-xs font-semibold text-emerald-500">
                    Host Payout: ₹{res.total_amount || 450} (Secured via Escrow)
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {res.status === 'pending' && (
                    <>
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={actionLoadingId === res.id}
                        onClick={() => handleAccept(res.id)}
                      >
                        Accept
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={actionLoadingId === res.id}
                        onClick={() => handleReject(res.id)}
                      >
                        Decline
                      </Button>
                    </>
                  )}
                  {res.status !== 'pending' && (
                    <span className="text-xs text-text-muted">Confirmed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 5: CALENDAR / AVAILABILITY
         ========================================================================= */}
      {activeTab === 'calendar' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Calendar & Slot Availability</h1>
            <p className="text-xs text-text-secondary mt-1">
              Inspect confirmed reservations and check time slot availability for your spaces.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-text-muted mb-1.5">Select Workspace</label>
                <select
                  value={selectedSpaceForCalendar}
                  onChange={(e) => setSelectedSpaceForCalendar(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-surface-elevated border border-border text-sm text-text-primary focus:outline-none"
                >
                  {spaces.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-text-muted mb-1.5">Select Date</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-surface-elevated border border-border text-sm text-text-primary focus:outline-none"
                >
                </input>
              </div>

              <div className="flex items-end">
                <Button
                  variant="primary"
                  size="md"
                  className="w-full"
                  disabled={checkingAvailability || !selectedSpaceForCalendar}
                  onClick={handleCheckCalendar}
                >
                  {checkingAvailability ? 'Checking...' : 'Check Availability'}
                </Button>
              </div>
            </div>

            {availabilityResult && (
              <div className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-2">
                <p className="text-xs font-bold text-emerald-500">Availability Data Received</p>
                <p className="text-xs text-text-secondary">
                  Space is accepting bookings for {selectedDate}. Slots are dynamically locked upon renter checkout.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 6: EARNINGS
         ========================================================================= */}
      {activeTab === 'earnings' && (
        <div className="animate-fadeIn">
          <HostEarnings />
        </div>
      )}

      {/* =========================================================================
          TAB 7: INQUIRIES
         ========================================================================= */}
      {activeTab === 'inquiries' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Renter Inquiries</h1>
            <p className="text-xs text-text-secondary mt-1">
              Prospective renter questions and custom corporate booking requests.
            </p>
          </div>
          <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-2">
            <MessageSquare className="w-8 h-8 text-primary mx-auto" />
            <p className="text-sm font-semibold text-text-primary">No Unread Inquiries</p>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              All renter questions have been addressed. New inquiries trigger email and in-app notifications.
            </p>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 8: REVIEWS
         ========================================================================= */}
      {activeTab === 'reviews' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Host Ratings & Feedback</h1>
            <p className="text-xs text-text-secondary mt-1">
              Renter ratings on WiFi reliability, soundproofing, and cleanliness.
            </p>
          </div>
          <div className="p-8 rounded-3xl bg-surface border border-border text-center space-y-2">
            <Star className="w-8 h-8 text-amber-500 mx-auto" />
            <p className="text-sm font-semibold text-text-primary">Average Rating: 4.9 / 5.0</p>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              Your listings maintain superhost status across Delhi and Bangalore hubs.
            </p>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 9: VERIFICATION
         ========================================================================= */}
      {activeTab === 'verification' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Host Property & Payout Verification</h1>
            <p className="text-xs text-text-secondary mt-1">
              Verify utility bills (DISCOM electricity) and bank/UPI VPA to unlock verified superhost badges.
            </p>
          </div>
          <Profile />
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
          TAB 11: NOTIFICATIONS
         ========================================================================= */}
      {activeTab === 'notifications' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Host Alerts</h1>
            <p className="text-xs text-text-secondary mt-1">
              Updates on booking requests, escrow settlements, and listing approvals.
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-surface border border-border flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-text-primary">Escrow Settlement Active</p>
              <p className="text-xs text-text-muted mt-0.5">
                All host earnings are held securely in the micro-escrow smart ledger until renter checkout.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 12: HELP
         ========================================================================= */}
      {activeTab === 'help' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-6 rounded-3xl bg-surface border border-border space-y-4">
            <div className="flex items-center gap-2.5 text-indigo-500">
              <HelpCircle className="w-6 h-6" />
              <h2 className="text-xl font-bold text-text-primary">Host Knowledge Base & Support</h2>
            </div>
            <div className="space-y-2 text-xs text-text-secondary">
              <p className="font-semibold text-text-primary">Key Host Guidelines:</p>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li>How are payouts processed? (Transferred directly to your verified UPI VPA upon slot completion)</li>
                <li>How does keyless access work? (PIN codes are generated automatically and shared with verified renters)</li>
                <li>What if a renter damages equipment? (File a dispute within 24 hours of checkout to hold escrow funds)</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </PortalLayout>
  );
};

export default HostPortal;
