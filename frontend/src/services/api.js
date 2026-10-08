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
};
