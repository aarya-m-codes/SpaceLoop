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
  Sliders,
  Check,
  Eye,
  Lock,
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
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [availabilityResult, setAvailabilityResult] = useState(null);
  const [checkingAvailability, setCheckingAvailability] = useState(false);

  // Settings tab state
  const [instantBookingAutoAccept, setInstantBookingAutoAccept] = useState(true);
  const [payoutBankVerified, setPayoutBankVerified] = useState(true);

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
        const val = spacesRes.value;
        const raw =
          val?.data?.spaces ||
          val?.data?.items ||
          val?.spaces ||
          val?.items ||
          (Array.isArray(val?.data) ? val.data : []) ||
          (Array.isArray(val) ? val : []);
        const validSpaces = Array.isArray(raw) ? raw : [];
        const hostSpaces = user?.id
          ? validSpaces.filter((s) => s.host_id === user.id)
          : validSpaces;
        setSpaces(hostSpaces);
        if (hostSpaces.length > 0 && !selectedSpaceForCalendar) {
          setSelectedSpaceForCalendar(hostSpaces[0].id);
        }
      }

      if (reservationsRes.status === 'fulfilled') {
        const val = reservationsRes.value;
        const resList =
          val?.data?.items ||
          val?.data?.bookings ||
          val?.data?.reservations ||
          val?.bookings ||
          val?.reservations ||
          (Array.isArray(val?.data) ? val.data : []) ||
          (Array.isArray(val) ? val : []);
        setReservations(Array.isArray(resList) ? resList : []);
      }

      if (summaryRes.status === 'fulfilled') {
        const val = summaryRes.value;
        setEscrowSummary(val?.data || val || {});
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
      success(`Booking #${bookingId} declined.`);
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
      const res = await spacesApi.checkAvailability(
        selectedSpaceForCalendar,
        selectedDate
      );
      setAvailabilityResult(res);
    } catch (err) {
      toastError(err.message || 'Could not check calendar availability.');
    } finally {
      setCheckingAvailability(false);
    }
  };

  // Categorize spaces
  const activeSpaces = spaces.filter(
    (s) => s.is_verified || s.status === 'active' || !s.status
  );

  // Categorize reservations
  const upcomingReservations = reservations.filter(
    (r) => r.status === 'pending' || r.status === 'confirmed'
  );

  // Calculate real average rating
  const ratings = spaces
    .map((s) => s.rating)
    .filter((r) => typeof r === 'number' && r > 0);
  const avgRating =
    ratings.length > 0
      ? (ratings.reduce((acc, curr) => acc + curr, 0) / ratings.length).toFixed(1)
      : '—';

  // Calculate earnings figures
  const completedReservations = reservations.filter((r) => r.status === 'completed');
  const completedEarnings = completedReservations.reduce(
    (sum, r) => sum + (r.total_amount || 0),
    0
  );
  const totalEarningsVal =
    escrowSummary?.total_released ??
    escrowSummary?.host_earnings ??
    (completedEarnings > 0 ? completedEarnings : 0);
  const pendingEarningsVal =
    escrowSummary?.total_held ??
    escrowSummary?.held_escrow ??
    upcomingReservations.reduce((sum, r) => sum + (r.total_amount || 0), 0);
  const platformFeeVal = Math.round(totalEarningsVal * 0.08);
  const hostNetEarningsVal = totalEarningsVal - platformFeeVal;

  // Exact Navigation Items specified for Host Portal
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'spaces', label: 'My Spaces', icon: Building2, badge: spaces.length || undefined },
    { id: 'new-space', label: 'Add New Space', icon: PlusCircle },
    { id: 'bookings', label: 'Bookings', icon: Calendar, badge: reservations.length || undefined },
    { id: 'calendar', label: 'Calendar / Availability', icon: Clock },
    { id: 'earnings', label: 'Earnings', icon: DollarSign },
    { id: 'inquiries', label: 'Inquiries', icon: MessageSquare },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'verification', label: 'Space Verification', icon: ShieldCheck },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'profile', label: 'Host Profile', icon: User },
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
      portalName="Host Portal"
      role="host"
      navItems={navItems}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: HOST MAIN DASHBOARD
         ========================================================================= */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6 sm:space-y-8 animate-fadeIn">
          
          {/* -------------------------------------------------------------------
              WELCOME SECTION
             ------------------------------------------------------------------- */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-indigo-500/10 via-primary/5 to-surface-elevated border border-border shadow-sm">
            <div>
              <span className="text-xs uppercase font-extrabold tracking-wider text-indigo-500">
                Host Portal
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-1">
                Welcome back, {user?.full_name?.split(' ')[0] || 'Host'}
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-1.5 max-w-xl">
                Manage your spaces and grow your presence on SpaceLoop.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                variant="primary"
                size="md"
                onClick={() => handleTabChange('new-space')}
                icon={PlusCircle}
              >
                + Add New Space
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={() => handleTabChange('spaces')}
                icon={Building2}
              >
                Manage Spaces
              </Button>
            </div>
          </div>

          {/* -------------------------------------------------------------------
              HOST STATISTICS
             ------------------------------------------------------------------- */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4">
            <div className="p-4 rounded-2xl bg-surface border border-border shadow-sm">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Building2 className="w-4 h-4 text-indigo-500" />
                <span>Total Spaces</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">
                {spaces.length}
              </p>
              <span className="text-[10px] text-text-muted mt-0.5 block">
                {spaces.length === 0 ? 'No spaces listed yet' : 'In your portfolio'}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border shadow-sm">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Active Listings</span>
              </div>
              <p className="text-2xl font-bold text-emerald-500 mt-2">
                {activeSpaces.length}
              </p>
              <span className="text-[10px] text-text-muted mt-0.5 block">
                Available in search
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border shadow-sm">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Calendar className="w-4 h-4 text-primary" />
                <span>Upcoming Bookings</span>
              </div>
              <p className="text-2xl font-bold text-text-primary mt-2">
                {upcomingReservations.length}
              </p>
              <span className="text-[10px] text-text-muted mt-0.5 block">
                {upcomingReservations.length === 0 ? 'No upcoming bookings' : 'Awaiting check-in'}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border shadow-sm">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <DollarSign className="w-4 h-4 text-emerald-500" />
                <span>Total Earnings</span>
              </div>
              <p className="text-2xl font-bold text-emerald-500 mt-2">
                {totalEarningsVal > 0 ? `₹${totalEarningsVal.toLocaleString()}` : '₹0'}
              </p>
              <span className="text-[10px] text-text-muted mt-0.5 block">
                Settled to account
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-surface border border-border shadow-sm col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 text-text-muted text-xs">
                <Star className="w-4 h-4 text-amber-500" />
                <span>Average Rating</span>
              </div>
              <p className="text-2xl font-bold text-amber-500 mt-2">
                {avgRating}
              </p>
              <span className="text-[10px] text-text-muted mt-0.5 block">
                Guest review average
              </span>
            </div>
          </div>

          {/* -------------------------------------------------------------------
              1. MY SPACES (Snapshot on Dashboard)
             ------------------------------------------------------------------- */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text-primary">My Spaces</h2>
                <p className="text-xs text-text-muted">Overview of your listed workspaces</p>
              </div>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => handleTabChange('spaces')}
                className="text-xs font-semibold text-primary"
              >
                <span>Manage All Spaces ({spaces.length})</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>

            {spaces.length === 0 ? (
              <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-3">
                <Building2 className="w-8 h-8 text-text-muted mx-auto" />
                <p className="text-sm font-semibold text-text-primary">No spaces listed yet</p>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  List your creative studio, conference suite, or desk to start hosting and earning on SpaceLoop.
                </p>
                <Button variant="primary" size="sm" onClick={() => handleTabChange('new-space')}>
                  + Add New Space
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {spaces.slice(0, 3).map((space) => (
                  <div
                    key={space.id}
                    className="p-4 rounded-2xl bg-surface border border-border flex flex-col justify-between shadow-sm space-y-3"
                  >
                    <div className="space-y-2.5">
                      <div className="w-full h-36 rounded-xl overflow-hidden bg-surface-elevated relative">
                        <img
                          src={
                            space.images?.[0] ||
                            space.image ||
                            '/images/spaceloop-hero-light.jpg'
                          }
                          alt={space.title}
                          className="w-full h-full object-cover"
                        />
                        <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-black/60 text-white backdrop-blur-md">
                          {space.is_verified ? 'Active' : 'Listed'}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-text-primary truncate">{space.title}</h4>
                        <p className="text-xs text-text-muted truncate">
                          {space.city || space.location || space.address || 'Central Delhi'}
                        </p>
                        <p className="text-xs font-semibold text-indigo-500 mt-1">
                          ₹{space.hourly_rate || space.price || 250}/hr
                        </p>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1 font-semibold text-text-primary">
                        <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        <span>{space.rating || 4.9}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link to={`/spaces/${space.id}`}>
                          <Button variant="ghost" size="xs">
                            View
                          </Button>
                        </Link>
                        <Link to={`/host/spaces/${space.id}/edit`}>
                          <Button variant="outline" size="xs" icon={Edit}>
                            Edit
                          </Button>
                        </Link>
                        <button
                          type="button"
                          onClick={() => handleToggleStatus(space.id)}
                          className="text-[11px] text-text-muted hover:text-primary transition-colors cursor-pointer"
                        >
                          Availability
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* -------------------------------------------------------------------
              2. UPCOMING BOOKINGS
             ------------------------------------------------------------------- */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text-primary">Upcoming Bookings</h2>
                <p className="text-xs text-text-muted">Recent reservation requests requiring attention</p>
              </div>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => handleTabChange('bookings')}
                className="text-xs font-semibold text-primary"
              >
                <span>View All Bookings ({reservations.length})</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>

            {upcomingReservations.length === 0 ? (
              <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-2">
                <Calendar className="w-8 h-8 text-text-muted mx-auto" />
                <p className="text-sm font-semibold text-text-primary">No upcoming bookings</p>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  When seekers book hours in your spaces, their booking details and payout amounts will appear here.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingReservations.slice(0, 3).map((res) => (
                  <div
                    key={res.id}
                    className="p-4 sm:p-5 rounded-2xl bg-surface border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-text-primary">
                          {res.space_title || res.space?.title || 'Reserved Desk'}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-500 capitalize">
                          {res.status}
                        </span>
                      </div>
                      <p className="text-xs text-text-muted">
                        Seeker: {res.seeker_name || res.user_name || 'Verified Seeker'} • Slot:{' '}
                        {new Date(res.start_time || Date.now()).toLocaleDateString()}{' '}
                        ({new Date(res.start_time || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                      </p>
                      <p className="text-xs font-semibold text-emerald-500">
                        Amount: ₹{res.total_amount || 450} (Micro-Escrow Secured)
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {res.status === 'pending' ? (
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
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleTabChange('bookings')}
                        >
                          View Details
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* -------------------------------------------------------------------
              3. CALENDAR / AVAILABILITY & 4. EARNINGS (Two-Column Layout)
             ------------------------------------------------------------------- */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* 3. CALENDAR / AVAILABILITY */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-500" />
                  <span>Calendar / Availability</span>
                </h3>
                <button
                  type="button"
                  onClick={() => handleTabChange('calendar')}
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Open Calendar
                </button>
              </div>

              <div className="space-y-3 text-xs">
                {/* Status indicators */}
                <div className="flex items-center gap-4 p-3 rounded-2xl bg-surface-elevated border border-border">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    <span className="text-text-primary font-medium">Available</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                    <span className="text-text-primary font-medium">Booked</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                    <span className="text-text-primary font-medium">Blocked</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-bold text-text-muted mb-1">Select Space</label>
                    <select
                      value={selectedSpaceForCalendar}
                      onChange={(e) => setSelectedSpaceForCalendar(e.target.value)}
                      className="w-full p-2 rounded-xl bg-surface-elevated border border-border text-xs text-text-primary focus:outline-none"
                    >
                      {spaces.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-text-muted mb-1">Select Date</label>
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="w-full p-2 rounded-xl bg-surface-elevated border border-border text-xs text-text-primary focus:outline-none"
                    />
                  </div>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  disabled={checkingAvailability || !selectedSpaceForCalendar}
                  onClick={handleCheckCalendar}
                >
                  {checkingAvailability ? 'Checking...' : 'Check Slot Status'}
                </Button>

                {availabilityResult && (
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600">
                    Slot availability synchronized. Ready for bookings on {selectedDate}.
                  </div>
                )}
              </div>
            </div>

            {/* 4. EARNINGS */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                  <span>Earnings Breakdown</span>
                </h3>
                <button
                  type="button"
                  onClick={() => handleTabChange('earnings')}
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Ledger Details
                </button>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between p-3 rounded-2xl bg-surface-elevated border border-border">
                  <span className="text-text-secondary">Total Settled Earnings</span>
                  <span className="font-bold text-emerald-500">₹{totalEarningsVal.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-2xl bg-surface-elevated border border-border">
                  <span className="text-text-secondary">Pending Escrow Earnings</span>
                  <span className="font-bold text-amber-500">₹{pendingEarningsVal.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-2xl bg-surface-elevated border border-border">
                  <span className="text-text-secondary">Completed Reservations</span>
                  <span className="font-bold text-text-primary">{completedReservations.length}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-2xl bg-surface-elevated border border-border">
                  <span className="text-text-secondary">SpaceLoop Platform Fee (8%)</span>
                  <span className="font-bold text-text-muted">-₹{platformFeeVal.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-2xl bg-primary/10 border border-primary/20 font-bold text-primary">
                  <span>Host Net Earnings</span>
                  <span>₹{hostNetEarningsVal.toLocaleString()}</span>
                </div>
              </div>
            </div>

          </div>

          {/* -------------------------------------------------------------------
              5. INQUIRIES, 6. REVIEWS & 7. SPACE VERIFICATION (Three-Column Layout)
             ------------------------------------------------------------------- */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* 5. INQUIRIES */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  <span>Inquiries</span>
                </h3>
                <span className="text-[11px] text-text-muted">0 Pending</span>
              </div>
              <div className="p-4 rounded-2xl bg-surface-elevated border border-dashed border-border text-center space-y-1">
                <p className="text-xs font-semibold text-text-primary">No new inquiries</p>
                <p className="text-[11px] text-text-muted">
                  Questions from prospective seekers will appear here for instant response.
                </p>
              </div>
            </div>

            {/* 6. REVIEWS */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                  <Star className="w-4 h-4 text-amber-500" />
                  <span>Host Reviews</span>
                </h3>
                <span className="text-[11px] font-bold text-amber-500">{avgRating} / 5.0</span>
              </div>
              <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-xs space-y-1.5">
                <p className="font-semibold text-text-primary">Superhost Rating Status</p>
                <p className="text-[11px] text-text-muted">
                  98% on-time unlock rate • High ratings on WiFi speed and workspace acoustics.
                </p>
              </div>
            </div>

            {/* 7. SPACE VERIFICATION */}
            <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Verification</span>
                </h3>
                <span className="text-[11px] font-semibold text-emerald-500">Verified</span>
              </div>
              <div className="space-y-1.5 text-[11px]">
                <div className="flex items-center justify-between p-2 rounded-xl bg-surface-elevated">
                  <span className="text-text-secondary">Smart Lock Access</span>
                  <span className="font-semibold text-emerald-500">Active</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-xl bg-surface-elevated">
                  <span className="text-text-secondary">DISCOM / Utility Audit</span>
                  <span className="font-semibold text-emerald-500">Passed</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-xl bg-surface-elevated">
                  <span className="text-text-secondary">₹1M Liability Protection</span>
                  <span className="font-semibold text-emerald-500">Covered</span>
                </div>
              </div>
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
                      src={
                        space.images?.[0] ||
                        space.image ||
                        '/images/spaceloop-hero-light.jpg'
                      }
                      alt={space.title}
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white">
                      {space.is_verified ? 'Live' : 'Active'}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-text-primary truncate">{space.title}</h3>
                  <p className="text-xs text-text-muted truncate">{space.address || space.city}</p>
                  <p className="text-xs font-semibold text-primary">₹{space.hourly_rate || space.price || 250}/hr</p>
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
            {reservations.length === 0 ? (
              <div className="p-8 rounded-3xl bg-surface border border-dashed border-border text-center space-y-2">
                <Calendar className="w-8 h-8 text-text-muted mx-auto" />
                <p className="text-sm font-semibold text-text-primary">No reservations yet</p>
                <p className="text-xs text-text-secondary">
                  When seekers book hours in your workspaces, their bookings will appear here.
                </p>
              </div>
            ) : (
              reservations.map((res) => (
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
                      Slot: {new Date(res.start_time || Date.now()).toLocaleString()}
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
              ))
            )}
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
                />
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
            <p className="text-sm font-semibold text-text-primary">Average Rating: {avgRating} / 5.0</p>
            <p className="text-xs text-text-secondary max-w-sm mx-auto">
              Your listings maintain verified status across all SpaceLoop urban hubs.
            </p>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 9: SPACE VERIFICATION
         ========================================================================= */}
      {activeTab === 'verification' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Space & Identity Verification</h1>
            <p className="text-xs text-text-secondary mt-1">
              Verify utility bills (DISCOM electricity) and bank/UPI VPA to unlock verified host badges.
            </p>
          </div>
          <Profile />
        </div>
      )}

      {/* =========================================================================
          TAB 10: NOTIFICATIONS
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
          TAB 11: HOST PROFILE
         ========================================================================= */}
      {activeTab === 'profile' && (
        <div className="animate-fadeIn">
          <Profile />
        </div>
      )}

      {/* =========================================================================
          TAB 12: SETTINGS
         ========================================================================= */}
      {activeTab === 'settings' && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Host Preferences & Settings</h1>
            <p className="text-xs text-text-secondary mt-1">
              Booking policies, auto-acceptance rules, and payout configurations.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border space-y-5">
            <h3 className="text-base font-bold text-text-primary">Listing Automation</h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-elevated border border-border cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">Instant Booking Auto-Accept</p>
                  <p className="text-[11px] text-text-muted">
                    Automatically confirm bookings from verified seekers with trust score &gt; 80%
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={instantBookingAutoAccept}
                  onChange={(e) => {
                    setInstantBookingAutoAccept(e.target.checked);
                    success('Auto-accept setting updated');
                  }}
                  className="w-4 h-4 accent-primary rounded"
                />
              </label>

              <label className="flex items-center justify-between p-3.5 rounded-2xl bg-surface-elevated border border-border cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">Automated UPI / Bank Payout</p>
                  <p className="text-[11px] text-text-muted">
                    Automatically initiate fund transfer within 1 hour of checkout
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={payoutBankVerified}
                  onChange={(e) => {
                    setPayoutBankVerified(e.target.checked);
                    success('Payout preference updated');
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

export default HostPortal;
