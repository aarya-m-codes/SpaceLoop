/**
 * SpaceLoop Unified API Service Layer
 * Direct connection to SpaceLoop Flask REST APIs.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Helper to get active JWT auth headers
 */
function getAuthHeaders(isFormData = false) {
  const headers = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  const token = localStorage.getItem('spaceloop_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const activeRole = localStorage.getItem('spaceloop_active_role');
  if (activeRole) {
    headers['X-SpaceLoop-Role'] = activeRole;
  }
  return headers;
}

/**
 * Generic request wrapper with normalized response & error handling
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...getAuthHeaders(isFormData),
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
      if (endpoint.startsWith('/api') && typeof data === 'string' && contentType && contentType.includes('text/html')) {
        const error = new Error('Received HTML response instead of JSON from API. If deployed on Vercel, set VITE_API_URL in Environment Variables to point to your backend server.');
        error.status = 502;
        error.data = data;
        throw error;
      }
    }

    if (!response.ok) {
      let errorMessage = '';
      if (data && typeof data === 'object') {
        if (typeof data.error === 'string') {
          errorMessage = data.error;
        } else if (data.error && typeof data.error === 'object') {
          errorMessage = data.error.message || data.error.description || data.error.detail || data.error.code || '';
        } else if (typeof data.message === 'string') {
          errorMessage = data.message;
        } else if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        }
      } else if (typeof data === 'string' && data.trim()) {
        errorMessage = data.trim();
      }

      if (!errorMessage || errorMessage === '[object Object]') {
        if (response.status === 401) {
          errorMessage = 'Invalid email or password.';
        } else if (response.status === 403) {
          errorMessage = 'Access denied. You do not have permission for this action.';
        } else if (response.status >= 500) {
          errorMessage = 'Something went wrong on the server.';
        } else {
          errorMessage = `HTTP ${response.status}: ${response.statusText || 'Request failed'}`;
        }
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const error = new Error('Unable to connect to SpaceLoop.');
      error.status = 0;
      throw error;
    }
    if (err && (typeof err.message !== 'string' || err.message === '[object Object]')) {
      err.message = 'Authentication failed. Please verify credentials.';
    }
    throw err;
  }
}

// ==========================================
// AUTHENTICATION & IDENTITY APIS
// ==========================================
export const authApi = {
  login: (credentials) =>
    request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  register: (payload) =>
    request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  me: () =>
    request('/api/v1/auth/me', {
      method: 'GET',
    }),

  logout: () =>
    request('/api/v1/auth/logout', {
      method: 'POST',
    }),

  switchContext: (activeRole) =>
    request('/api/v1/auth/context', {
      method: 'POST',
      body: JSON.stringify({ active_role: activeRole }),
    }),

  setupMfa: () =>
    request('/api/v1/auth/mfa/setup', {
      method: 'POST',
    }),

  verifySetupMfa: (code) =>
    request('/api/v1/auth/mfa/verify-setup', {
      method: 'POST',
      body: JSON.stringify(typeof code === 'object' ? code : { code }),
    }),

  verifyMfa: (payload) =>
    request('/api/v1/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify(typeof payload === 'string' ? { code: payload } : payload),
    }),

  verifyEmail: (token) =>
    request(`/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`, {
      method: 'GET',
    }),

  resendVerification: (email) =>
    request('/api/v1/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  instantVerify: () =>
    request('/api/v1/auth/instant-verify', {
      method: 'POST',
    }),

  disableMfa: (payload) =>
    request('/api/v1/auth/mfa/disable', {
      method: 'POST',
      body: JSON.stringify(typeof payload === 'string' ? { password: payload } : payload),
    }),

  regenerateRecoveryCodes: (payload) =>
    request('/api/v1/auth/mfa/recovery-codes/regenerate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  refreshToken: (refreshToken) =>
    request('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
};

// ==========================================
// SPACES & SEARCH APIS
// ==========================================
export const spacesApi = {
  getSpaces: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/spaces${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },

  getSpace: (id) =>
    request(`/api/spaces/${id}`, { method: 'GET' }),

  searchSpaces: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/spaces/search${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },

  aiMatch: (payload) =>
    request('/api/spaces/ai-match', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  createSpace: (payload) =>
    request('/api/spaces', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateSpace: (id, payload) =>
    request(`/api/spaces/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  toggleStatus: (id) =>
    request(`/api/spaces/${id}/toggle-status`, {
      method: 'POST',
    }),

  checkAvailability: (id, date) =>
    request(`/api/spaces/${id}/check-availability?date=${encodeURIComponent(date)}`, {
      method: 'GET',
    }),

  getReviews: (id) =>
    request(`/api/spaces/${id}/reviews`, { method: 'GET' }),

  createReview: (id, payload) =>
    request(`/api/spaces/${id}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  uploadPhoto: (formData) =>
    request('/api/spaces/upload-photo', {
      method: 'POST',
      body: formData,
    }),

  assistListing: (payload) =>
    request('/api/spaces/assist-listing', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  aiScan: (formData) =>
    request('/api/spaces/ai-scan', {
      method: 'POST',
      body: formData,
    }),

  getInquiries: (spaceId) =>
    request(`/api/v1/spaces/${spaceId}/inquiries`, { method: 'GET' }),

  submitInquiry: (spaceId, payload) =>
    request(`/api/v1/spaces/${spaceId}/inquiries`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  replyInquiry: (inquiryId, payload) =>
    request(`/api/v1/spaces/inquiries/${inquiryId}/reply`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getQrPass: (spaceId) =>
    request(`/api/v1/spaces/${spaceId}/qr-pass`, { method: 'GET' }),
};

// ==========================================
// BOOKING ENGINE APIS
// ==========================================
export const bookingsApi = {
  /**
   * Authoritative backend price calculation & availability precheck
   * Returns: { subtotal, platform_fee, escrow_deposit: 100, total_amount, space_id, duration_hours }
   */
  precheck: (payload) =>
    request('/api/bookings/precheck', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  createBooking: (payload) =>
    request('/api/bookings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getBooking: (id) =>
    request(`/api/bookings/${id}`, { method: 'GET' }),

  getMyBookings: () =>
    request('/api/bookings/my-bookings', { method: 'GET' }),

  getHostReservations: () =>
    request('/api/bookings/host-reservations', { method: 'GET' }),

  acceptBooking: (id) =>
    request(`/api/bookings/${id}/accept`, { method: 'POST' }),

  rejectBooking: (id, reason = '') =>
    request(`/api/bookings/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: reason }),
    }),

  cancelBooking: (id, reason = '') =>
    request(`/api/bookings/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ cancellation_reason: reason }),
    }),

  checkIn: (id, payload) =>
    request(`/api/bookings/${id}/check-in`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  checkOut: (id, payload = {}) =>
    request(`/api/bookings/${id}/check-out`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  disputeBooking: (id, reason) =>
    request(`/api/bookings/${id}/dispute`, {
      method: 'POST',
      body: JSON.stringify({ dispute_reason: reason }),
    }),

  getMicroLease: (id) =>
    request(`/api/v1/bookings/${id}/micro-lease`, { method: 'GET' }),

  inspectCondition: (id, payload) =>
    request(`/api/v1/bookings/${id}/inspect-condition`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getSessionStatus: (id) =>
    request(`/api/v1/bookings/${id}/status`, { method: 'GET' }),
};

// ==========================================
// MICRO-ESCROW & LEDGER APIS
// ==========================================
export const escrowApi = {
  getBookingEscrow: (bookingId) =>
    request(`/api/escrow/${bookingId}`, { method: 'GET' }),

  getBookingLedger: (bookingId) =>
    request(`/api/escrow/${bookingId}/ledger`, { method: 'GET' }),

  getSummary: () =>
    request('/api/escrow/summary', { method: 'GET' }),

  verifyVpa: (vpa) =>
    request('/api/escrow/verify-vpa', {
      method: 'POST',
      body: JSON.stringify({ vpa }),
    }),
};

// ==========================================
// LOOPBOT & AI APIS
// ==========================================
export const aiApi = {
  chat: (payload) =>
    request('/api/v1/loopbot/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  askAssistant: (query) =>
    request('/api/v1/loopbot/chat', {
      method: 'POST',
      body: JSON.stringify({ message: typeof query === 'string' ? query : query?.message || '' }),
    }),

  loopbotChat: (payload) =>
    request('/api/v1/loopbot/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  resetConversation: (conversationId) =>
    request('/api/v1/loopbot/conversation/reset', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId }),
    }),

  conciergeChat: (payload) =>
    request('/api/concierge/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  nlpDispatch: (payload) =>
    request('/api/nlp/dispatch', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ==========================================
// INQUIRIES & DIRECT MESSAGING APIS
// ==========================================
export const inquiriesApi = {
  sendInquiry: (spaceId, payload) =>
    request(`/api/spaces/${spaceId}/inquiries`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMyInquiries: () =>
    request('/api/spaces/my-inquiries', { method: 'GET' }),
};

// ==========================================
// WISHLIST & SAVED SPACES APIS
// ==========================================
export const wishlistApi = {
  getWishlist: () =>
    request('/api/spaces/my-wishlist', { method: 'GET' }),

  addToWishlist: (spaceId) =>
    request(`/api/spaces/${spaceId}/wishlist`, { method: 'POST' }),

  removeFromWishlist: (spaceId) =>
    request(`/api/spaces/${spaceId}/wishlist`, { method: 'DELETE' }),
};

// ==========================================
// REVIEWS APIS
// ==========================================
export const reviewsApi = {
  getMyReviews: () =>
    request('/api/spaces/my-reviews', { method: 'GET' }),

  getSpaceReviews: (spaceId) =>
    request(`/api/spaces/${spaceId}/reviews`, { method: 'GET' }),

  createReview: (spaceId, payload) =>
    request(`/api/spaces/${spaceId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ==========================================
// NOTIFICATIONS APIS
// ==========================================
export const notificationsApi = {
  getMyNotifications: () =>
    request('/api/spaces/my-notifications', { method: 'GET' }),

  markAsRead: (id) =>
    request(`/api/spaces/notifications/${id}/read`, { method: 'POST' }),
};

// ==========================================
// VERIFICATION ADAPTER APIS
// ==========================================
export const verifyApi = {
  verifyStudent: (payload) =>
    request('/api/verify/student', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  verifyAadhaar: (payload) =>
    request('/api/verify/aadhaar', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  verifyHost: (payload) =>
    request('/api/verify/host', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ==========================================
// TRUST, SAFETY & FRAUD APIS (Admin & Governance)
// ==========================================
export const trustSafetyApi = {
  getAssessments: () =>
    request('/api/trust-safety/assessments', { method: 'GET' }),

  evaluate: (payload) =>
    request('/api/trust-safety/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getGraph: (type, id) =>
    request(`/api/trust-safety/graph/${type}/${id}`, { method: 'GET' }),

  getFraudAlerts: () =>
    request('/api/fraud/alerts', { method: 'GET' }),

  scoreFraud: (payload) =>
    request('/api/fraud/score', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getOtiBreakdown: (entityType, entityId) =>
    request(`/api/v1/trust/oti-breakdown?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`, { method: 'GET' }),

  simulateOti: (payload) =>
    request('/api/v1/trust/simulate-oti', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getStats: () =>
    request('/api/v1/trust/stats', { method: 'GET' }),

  takeAction: (assessmentId, action, notes = '') =>
    request(`/api/trust-safety/assessments/${assessmentId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    }),
};

// ==========================================
// DYNAMIC HOST EARNINGS CALCULATOR APIS
// ==========================================
export const calculatorApi = {
  estimate: (payload) =>
    request('/api/v1/calculator/estimate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCategories: () =>
    request('/api/v1/calculator/categories', { method: 'GET' }),
};

// ==========================================
// REAL-TIME SESSION COCKPIT APIS
// ==========================================
export const sessionApi = {
  getStatus: (bookingId) =>
    request(`/api/v1/bookings/${bookingId}/status`, { method: 'GET' }),

  getMicroLease: (bookingId) =>
    request(`/api/v1/bookings/${bookingId}/micro-lease`, { method: 'GET' }),

  inspectCondition: (bookingId, payload) =>
    request(`/api/v1/bookings/${bookingId}/inspect-condition`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ==========================================
// SYSTEM STATUS & MULTI-RAIL TELEMETRY APIS
// ==========================================
export const systemApi = {
  getStatus: () =>
    request('/api/v1/system/status', { method: 'GET' }),

  getConnectivity: () =>
    request('/api/v1/system/connectivity', { method: 'GET' }),

  toggleAiSimulation: (enabled) =>
    request('/api/v1/system/dev/toggle-ai-simulation', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
};

// ==========================================
// ADMIN OPERATIONS & COMPLIANCE APIS
// ==========================================
export const adminApi = {
  getStats: () =>
    request('/api/v1/admin/stats', { method: 'GET' }),

  getUsers: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/v1/admin/users${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },

  toggleUserStatus: (userId) =>
    request(`/api/v1/admin/users/${userId}/toggle-status`, { method: 'POST' }),

  getSpaces: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/v1/admin/spaces${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },

  toggleSpaceStatus: (spaceId) =>
    request(`/api/v1/admin/spaces/${spaceId}/toggle-status`, { method: 'POST' }),

  getBookings: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/v1/admin/bookings${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },

  getFinancials: () =>
    request('/api/v1/admin/financials', { method: 'GET' }),

  getDisputes: () =>
    request('/api/v1/admin/disputes', { method: 'GET' }),

  adjudicateDispute: (bookingId, payload) =>
    request(`/api/v1/admin/disputes/${bookingId}/adjudicate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAuditLogs: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, v);
    });
    const qs = query.toString();
    return request(`/api/v1/admin/audit-logs${qs ? `?${qs}` : ''}`, { method: 'GET' });
  },
};

// ==========================================
// SESSIONS, CALCULATOR & LEASE APIS
// ==========================================
export const sessionsApi = {
  getActive: () =>
    request('/api/v1/sessions/active', { method: 'GET' }),

  getStatus: (id, coords) => {
    const qs = coords && coords.lat != null && coords.lng != null ? `?lat=${coords.lat}&lng=${coords.lng}` : '';
    return request(`/api/v1/sessions/${id}${qs}`, { method: 'GET' });
  },

  extend: (id, hours = 1.0) =>
    request(`/api/v1/sessions/${id}/extend`, {
      method: 'POST',
      body: JSON.stringify({ extension_hours: hours }),
    }),
};

export const leasesApi = {
  getBookingLease: (bookingId) =>
    request(`/api/v1/leases/bookings/${bookingId}/lease`, { method: 'GET' }),

  getSpaceTemplate: (spaceId) =>
    request(`/api/v1/leases/spaces/${spaceId}/lease-template`, { method: 'GET' }),
};

export const doorPassApi = {
  getDoorPass: (spaceId) =>
    request(`/api/v1/spaces/${spaceId}/door-pass`, { method: 'GET' }),
};

// ==========================================
// HOST PORTAL APIS
// ==========================================
export const hostApi = {
  getDashboard: () =>
    request('/api/v1/hosts/dashboard', { method: 'GET' }),

  getActivity: (category) => {
    const qs = category && category !== 'all' ? `?category=${category}` : '';
    return request(`/api/v1/hosts/activity${qs}`, { method: 'GET' });
  },

  getNotifications: () =>
    request('/api/v1/hosts/notifications', { method: 'GET' }),

  markNotificationRead: (id) =>
    request(`/api/v1/hosts/notifications/${id}/read`, { method: 'POST' }),

  markAllNotificationsRead: () =>
    request('/api/v1/hosts/notifications/read-all', { method: 'POST' }),

  deleteNotification: (id) =>
    request(`/api/v1/hosts/notifications/${id}`, { method: 'DELETE' }),

  getEscrowLedger: () =>
    request('/api/v1/hosts/escrow/ledger', { method: 'GET' }),

  getAccessLogs: () =>
    request('/api/v1/hosts/access-logs', { method: 'GET' }),

  getSettings: () =>
    request('/api/v1/hosts/settings', { method: 'GET' }),

  updateSettings: (settings) =>
    request('/api/v1/hosts/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
};

export default {
  auth: authApi,
  admin: adminApi,
  spaces: spacesApi,
  bookings: bookingsApi,
  escrow: escrowApi,
  ai: aiApi,
  verify: verifyApi,
  trustSafety: trustSafetyApi,
  inquiries: inquiriesApi,
  wishlist: wishlistApi,
  reviews: reviewsApi,
  notifications: notificationsApi,
  calculator: calculatorApi,
  session: sessionApi,
  sessions: sessionsApi,
  system: systemApi,
  leases: leasesApi,
  doorPass: doorPassApi,
  host: hostApi,
};

