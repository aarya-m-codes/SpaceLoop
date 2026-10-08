import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  Globe,
  RotateCcw,
  Compass,
  CreditCard,
  ShieldCheck,
  ChevronDown,
  Info,
  Key,
  QrCode,
  MapPin,
  CheckCircle,
  AlertTriangle,
  Clock,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { aiApi } from '../../services/api';
import { useI18n } from '../../i18n/I18nContext';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'gsw', label: 'गढ़वळि (Garhwali)' },
  { code: 'kfy', label: 'कुमाउँनी (Kumaoni)' },
  { code: 'jns', label: 'जौनसारी (Jaunsari)' },
];

const LOOPBOT_INIT_MESSAGES = {
  en: 'Namaste! I am LoopBot, your SpaceLoop AI concierge. How can I help you find verified physical spaces, calculate micro-escrow quotes, or assist with PIN check-in today?',
  hi: 'नमस्ते! मैं लूपबॉट हूँ, आपका स्पेस-लूप AI सहायक। आज मैं आपको सत्यापित जगहें खोजने, माइक्रो-एस्क्रो उद्धरणों की गणना करने या पिन चेक-इन में कैसे मदद कर सकता हूँ?',
  mr: 'नमस्कार! मी लूपबॉट आहे, तुमचा स्पेस-लूप AI सहाय्यक. आज मी तुम्हाला पडताळलेली जागा शोधण्यात, अनामत रकमेची गणना करण्यात किंवा पिन चेक-इन मध्ये कशी मदत करू शकतो?',
  gsw: 'नमस्कार! मैं लूपबॉट छौं, तुमरो स्पेस-लूप AI सहायक। आज मैं तुमते जांची-परखी ठौर खोजण, धरोहर हिसाब लगाण या पिन चेक-इन म क्या मदद करि सकदूँ?',
  kfy: 'नमस्कार! मैं लूपबॉट छुँ, तुमरो स्पेस-लूप AI सहायक। आज मैं तुमूंकै जाँची-परखी ठौर खोजण, धरोहर हिसाब लगाण या पिन चेक-इन में कै मदद करि सकूँला?',
  jns: 'नमस्कार! मुं लूपबॉट आं, तुमरो स्पेस-लूप AI सहायक। आज मुं तुमूखे जांची-परखी जगा खोजणे, धरोहर हिसाब लगाणे या पिन चेक-इन म क्या मदद करि सकूँ?',
};

const LOCALIZED_SUGGESTED_ACTIONS = {
  en: [
    'Find quiet desks in Bengaluru under ₹400',
    'How does the ₹100 refundable escrow work?',
    'What is the cancellation policy (5% fee)?',
    'What is Section 52 Leave and License?',
    'How does 50m GPS & PIN check-in work?',
  ],
  hi: [
    'बेंगलुरु में ₹400 के अंदर शांत डेस्क खोजें',
    '₹100 रिफंडेबल एस्क्रो कैसे काम करता है?',
    'रद्दीकरण नीति (5% शुल्क) क्या है?',
    'धारा 52 लीव एंड लाइसेंस क्या है?',
    '50 मीटर जीपीएस और पिन चेक-इन कैसे काम करता है?',
  ],
  mr: [
    'बेंगळुरूमध्ये ₹400 च्या आत शांत डेस्क शोधा',
    '₹100 परतावा अनामत रक्कम कशी कार्य करते?',
    'रद्द करण्याचे धोरण (5% शुल्क) काय आहे?',
    'कलम 52 लिव्ह अँड लायसन्स करार म्हणजे काय?',
    '50 मी जीपीएस आणि पिन चेक-इन कसे कार्य करते?',
  ],
  gsw: [
    'बेंगलुरु म ₹400 भीतर शांत कमरा/डेस्क खोजा',
    '₹100 धरोहर वापसी कनक काम करदी?',
    'बुकिंग रद्द करणा कु नियम (5% शुल्क) क्या च?',
    'धारा 52 अनुमति पत्र क्या हुंद?',
    '50 मीटर जीपीएस अर पिन चेक-इन कनक काम करदु?',
  ],
  kfy: [
    'बेंगलुरु में ₹400 भितर शांत कमरा/डेस्क खोजा',
    '₹100 धरोहर वापसी कसी काम करछ?',
    'बुकिंग रद्द करनो कु नियम (5% शुल्क) क्या छू?',
    'धारा 52 अनुमति पत्र क्या हुनो?',
    '50 मीटर जीपीएस अर पिन चेक-इन कसी काम करछ?',
  ],
  jns: [
    'बेंगलुरु म ₹400 भितर शांत कमरा/डेस्क खोजो',
    '₹100 धरोहर वापसी किक काम करदी?',
    'बुकिंग रद्द करणे रो नियम (5% शुल्क) क्या आ?',
    'धारा 52 अनुमति पत्र क्या होलो?',
    '50 मीटर जीपीएस अर पिन चेक-इन किक काम करदो?',
  ],
};

export const LoopBot = () => {
  const navigate = useNavigate();
  const { language: currentLang, setLanguage: setGlobalLang } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(currentLang || 'en');
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'bot',
      text: LOOPBOT_INIT_MESSAGES[currentLang || 'en'] || LOOPBOT_INIT_MESSAGES.en,
      intent: 'GENERAL',
      type: 'message',
      sources: ['SpaceLoop Platform Specifications', 'Section 52 Legal Framework'],
      suggested_actions: LOCALIZED_SUGGESTED_ACTIONS[currentLang || 'en'] || LOCALIZED_SUGGESTED_ACTIONS.en,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(() => `conv_${Date.now()}`);

  useEffect(() => {
    if (currentLang && currentLang !== selectedLanguage) {
      setSelectedLanguage(currentLang);
    }
  }, [currentLang]);

  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].sender === 'bot') {
        const welcome = LOOPBOT_INIT_MESSAGES[selectedLanguage] || LOOPBOT_INIT_MESSAGES.en;
        const actions = LOCALIZED_SUGGESTED_ACTIONS[selectedLanguage] || LOCALIZED_SUGGESTED_ACTIONS.en;
        return [
          {
            ...prev[0],
            text: welcome,
            suggested_actions: actions,
          },
        ];
      }
      return prev;
    });
  }, [selectedLanguage]);
  const [copiedCode, setCopiedCode] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages]);

  const copyToClipboard = (text, id) => {
    navigator.clipboard?.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Connect to native backend endpoint POST /api/v1/loopbot/chat
      const response = await aiApi.chat({
        message: query,
        language: selectedLanguage,
        conversation_id: conversationId,
        context: {
          platform: 'web',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
      });

      const botMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: response.message || response.response || 'I have processed your request.',
        intent: response.intent || response.standard_intent || 'GENERAL',
        type: response.type || 'message',
        data: response.data || {},
        sources: (response.sources || []).map((s) => s.title || s.domain || s),
        suggested_actions: (response.suggested_actions || []).map((a) =>
          typeof a === 'string' ? a : a.label
        ),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.warn('LoopBot AI chat error:', err);
      // Graceful fallback grounded in SpaceLoop platform rules
      const fallbackMessage = {
        id: `bot-fallback-${Date.now()}`,
        sender: 'bot',
        text:
          'SpaceLoop operates on deterministic platform rules: Spaces can be booked hourly with an instant 4-digit arrival PIN. Every reservation holds a refundable ₹100 escrow deposit and a 5% platform fee. All check-ins require 50m GPS geofencing and the 15-minute start window.',
        intent: 'POLICY_FALLBACK',
        type: 'message',
        sources: ['Internal SpaceLoop Knowledge Base'],
        suggested_actions: [
          'Find quiet desks in Bengaluru under ₹400',
          'How does the ₹100 refundable escrow work?',
          'Contact Support',
        ],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetConversation = async () => {
    try {
      await aiApi.resetConversation(conversationId);
    } catch (e) {
      // ignore
    }
    const freshId = `conv_${Date.now()}`;
    setConversationId(freshId);
    setMessages([
      {
        id: 'init-fresh',
        sender: 'bot',
        text: LOOPBOT_INIT_MESSAGES[selectedLanguage] || LOOPBOT_INIT_MESSAGES.en,
        intent: 'GENERAL',
        type: 'message',
        sources: [],
        suggested_actions: LOCALIZED_SUGGESTED_ACTIONS[selectedLanguage] || LOCALIZED_SUGGESTED_ACTIONS.en,
        timestamp: new Date(),
      },
    ]);
  };

  // =========================================================================
  // Renderers for Interactive Payload Cards
  // =========================================================================

  const renderCardContent = (msg) => {
    const { type, data } = msg;
    if (!data) return null;

    // 1. Space Results List
    if (type === 'space_results' && data.spaces && data.spaces.length > 0) {
      return (
        <div className="space-y-2 mt-2 pt-1 border-t border-border/50">
          <div className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
            Verified Physical Spaces ({data.count || data.spaces.length})
          </div>
          <div className="space-y-2">
            {data.spaces.slice(0, 3).map((sp) => (
              <div
                key={sp.id}
                className="p-2.5 rounded-xl bg-surface border border-border hover:border-primary/40 transition-all flex flex-col gap-1.5"
              >
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <h4 className="font-bold text-xs text-text-primary line-clamp-1">
                      {sp.title}
                    </h4>
                    <p className="text-[11px] text-text-muted flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-primary shrink-0" />
                      {sp.neighborhood ? `${sp.neighborhood}, ` : ''}
                      {sp.city}
                    </p>
                  </div>
                  <span className="font-extrabold text-xs text-primary shrink-0">
                    ₹{sp.price_per_hour}/hr
                  </span>
                </div>
                {sp.amenities && (
                  <div className="flex flex-wrap gap-1">
                    {(Array.isArray(sp.amenities) ? sp.amenities : []).slice(0, 3).map((am, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 rounded text-[9px] bg-surface-elevated text-text-muted border border-border"
                      >
                        {am}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-1.5 pt-1">
                  <button
                    type="button"
                    onClick={() => handleSend(`Book space ${sp.id} for 2 hours`)}
                    className="flex-1 py-1 px-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-[11px] font-semibold transition-colors"
                  >
                    Book via LoopBot
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsOpen(false);
                      navigate(`/spaces/${sp.id}`);
                    }}
                    className="p-1 rounded-lg border border-border hover:bg-surface-elevated text-text-muted hover:text-text-primary text-[11px]"
                    title="View Space Details"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // 2. Booking Preview / Authoritative Pricing Quote
    if (type === 'booking_preview' && data.pricing) {
      const p = data.pricing;
      return (
        <div className="mt-2.5 p-3 rounded-2xl bg-surface border border-primary/20 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-text-primary">
            <span>Authoritative Price Quote</span>
            <span className="text-emerald-500 text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded">
              Verified
            </span>
          </div>
          <div className="space-y-1 text-[11px] text-text-secondary">
            <div className="flex justify-between">
              <span>Rental Subtotal ({data.duration_hours || 2}h):</span>
              <span className="font-semibold text-text-primary">₹{p.subtotal?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Platform Fee (5%):</span>
              <span>₹{p.platform_fee?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Refundable Escrow Deposit:</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                ₹{p.escrow_deposit?.toFixed(2)}
              </span>
            </div>
            <div className="pt-1.5 border-t border-border flex justify-between font-bold text-xs text-text-primary">
              <span>Total Payable:</span>
              <span className="text-primary text-sm">₹{p.final_amount?.toFixed(2)}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => handleSend(`Book space ${data.space?.id || data.space_id} for 2 hours`)}
            className="w-full py-1.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-semibold transition-all mt-1"
          >
            Request Reservation
          </button>
        </div>
      );
    }

    // 3. Consequential Action Confirmation Gate (Explicit Yes/No)
    if (type === 'confirmation_required') {
      const isCreate = data.action === 'create_booking';
      return (
        <div className="mt-2.5 p-3.5 rounded-2xl bg-amber-500/10 border-2 border-amber-500/30 space-y-2.5">
          <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Explicit Confirmation Required</span>
          </div>
          <p className="text-xs text-text-primary leading-relaxed font-medium">
            {data.action_summary}
          </p>
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={() => handleSend('Yes, please confirm and proceed')}
              className="flex-1 py-1.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-1 shadow-sm transition-all"
            >
              <Check className="w-3.5 h-3.5" />
              Yes, Confirm
            </button>
            <button
              type="button"
              onClick={() => handleSend('No, cancel request and keep it')}
              className="flex-1 py-1.5 px-3 rounded-xl bg-surface-elevated hover:bg-rose-500/10 border border-border text-text-secondary hover:text-rose-500 font-semibold text-xs flex items-center justify-center gap-1 transition-all"
            >
              <X className="w-3.5 h-3.5" />
              Cancel
            </button>
          </div>
        </div>
      );
    }

    // 4. Booking Status / Confirmed Session Card
    if (type === 'booking_status' && data.booking) {
      const b = data.booking;
      return (
        <div className="mt-2.5 p-3.5 rounded-2xl bg-surface border border-emerald-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-text-primary">
              Booking #{b.id} Confirmed
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
              {b.status?.toUpperCase()}
            </span>
          </div>
          {b.arrival_pin && (
            <div className="p-2.5 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
              <div>
                <span className="text-[10px] text-text-muted uppercase tracking-wider block">
                  Arrival PIN (Door Lock)
                </span>
                <span className="font-mono text-base font-extrabold text-primary tracking-widest">
                  {b.arrival_pin}
                </span>
              </div>
              <button
                type="button"
                onClick={() => copyToClipboard(b.arrival_pin, `pin-${b.id}`)}
                className="p-1.5 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-surface"
                title="Copy PIN"
              >
                {copiedCode === `pin-${b.id}` ? (
                  <Check className="w-4 h-4 text-emerald-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          )}
          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              navigate(`/bookings/${b.id}`);
            }}
            className="w-full py-1.5 text-center text-xs font-semibold text-primary hover:underline"
          >
            View Reservation Details →
          </button>
        </div>
      );
    }

    // 5. Access Status (PIN, 50m Geofence, 15m Temporal Window)
    if (type === 'access_status') {
      const temporal = data.temporal_guard || {};
      const geofence = data.geofence || {};
      return (
        <div className="mt-2.5 p-3 rounded-2xl bg-surface border border-border space-y-2.5">
          <div className="flex items-center justify-between text-xs font-bold text-text-primary">
            <span className="flex items-center gap-1.5">
              <Key className="w-4 h-4 text-primary" />
              Physical Access Status
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-bold">
              {data.session_state || 'not_started'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-2 rounded-xl bg-surface-elevated border border-border">
              <span className="text-[10px] text-text-muted block">Arrival PIN</span>
              <span className="font-mono font-bold text-sm text-text-primary">
                {data.arrival_pin || 'Pending'}
              </span>
            </div>
            <div className="p-2 rounded-xl bg-surface-elevated border border-border">
              <span className="text-[10px] text-text-muted block">50m Geofence</span>
              <span
                className={`font-semibold text-xs ${
                  geofence.within_geofence
                    ? 'text-emerald-500'
                    : 'text-text-secondary'
                }`}
              >
                {geofence.within_geofence ? 'Inside Range' : 'Max 50m'}
              </span>
            </div>
          </div>
          <div className="text-[11px] text-text-muted flex items-center gap-1.5 bg-surface-elevated p-2 rounded-xl border border-border">
            <Clock className="w-3.5 h-3.5 text-primary shrink-0" />
            <span>
              15-Min Guard:{' '}
              {temporal.eligible ? (
                <strong className="text-emerald-500">Active (Unlocked)</strong>
              ) : (
                'Locked until 15 mins prior'
              )}
            </span>
          </div>
        </div>
      );
    }

    // 6. Escrow Status & Double-Entry Ledger
    if (type === 'escrow_status' && data.escrow) {
      const e = data.escrow;
      return (
        <div className="mt-2.5 p-3 rounded-2xl bg-surface border border-border space-y-2 text-[11px]">
          <div className="flex items-center justify-between font-bold text-xs text-text-primary">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              Micro-Escrow Ledger
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
              {e.status || 'HELD'}
            </span>
          </div>
          <div className="space-y-1 text-text-secondary">
            <div className="flex justify-between">
              <span>Security Deposit (Refundable):</span>
              <span className="font-bold text-emerald-600">₹{e.deposit_amount || 100.0}</span>
            </div>
            <div className="flex justify-between">
              <span>Platform Fee (5%):</span>
              <span>₹{e.platform_fee || 0.0}</span>
            </div>
          </div>
          <p className="text-[10px] text-text-muted pt-1 border-t border-border">
            Protected by SpaceLoop double-entry micro-escrow. Deposit released upon checkout.
          </p>
        </div>
      );
    }

    return null;
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <motion.button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label={isOpen ? 'Close LoopBot Assistant' : 'Open LoopBot Assistant'}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`flex items-center gap-2.5 px-4 py-3 rounded-full shadow-2xl transition-all duration-300 font-semibold text-sm ${
            isOpen
              ? 'bg-surface-elevated text-text-primary border border-border shadow-lg'
              : 'bg-primary text-white hover:bg-primary-hover shadow-primary/25 hover:shadow-primary/40'
          }`}
        >
          {isOpen ? (
            <>
              <X className="w-5 h-5 text-text-primary" />
              <span className="hidden sm:inline">Close</span>
            </>
          ) : (
            <>
              <div className="relative">
                <Bot className="w-5 h-5 text-white" />
                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <span className="tracking-wide">LoopBot AI</span>
            </>
          )}
        </motion.button>
      </div>

      {/* Floating Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-20 right-4 sm:right-6 z-50 w-[95vw] sm:w-[440px] h-[620px] max-h-[85vh] flex flex-col rounded-3xl bg-surface border border-border shadow-2xl overflow-hidden backdrop-blur-xl"
          >
            {/* Header */}
            <div className="px-5 py-3.5 bg-surface-elevated border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-text-primary">LoopBot</h3>
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                      LIVE CONCIERGE
                    </span>
                  </div>
                  <p className="text-[10px] text-text-muted">India's Workspace AI Assistant</p>
                </div>
              </div>

              {/* Language Selector & Controls */}
              <div className="flex items-center gap-1.5">
                <select
                  value={selectedLanguage}
                  onChange={(e) => {
                    const newL = e.target.value;
                    setSelectedLanguage(newL);
                    setGlobalLang(newL);
                  }}
                  className="text-xs bg-surface border border-border rounded-lg px-2 py-1 text-text-secondary focus:outline-none focus:border-primary"
                  title="Choose conversation language"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.label}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  onClick={resetConversation}
                  title="Reset conversation"
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'bot' && (
                    <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className="max-w-[85%] space-y-2">
                    <div
                      className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-primary text-white rounded-tr-sm'
                          : 'bg-surface-elevated border border-border text-text-primary rounded-tl-sm'
                      }`}
                    >
                      <p className="whitespace-pre-line">{msg.text}</p>
                      {/* Rich Cards Attached to Message */}
                      {renderCardContent(msg)}
                    </div>

                    {/* Sources Badge */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex flex-wrap gap-1 text-[10px] text-text-muted px-1">
                        <span className="font-semibold text-text-secondary">RAG Grounded:</span>
                        {msg.sources.map((src, i) => (
                          <span
                            key={i}
                            className="px-1.5 py-0.5 rounded bg-surface-elevated border border-border"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Suggested Actions Chips */}
                    {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1 px-1">
                        {msg.suggested_actions.map((action, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSend(action)}
                            className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-surface-elevated hover:bg-primary/10 text-text-secondary hover:text-primary border border-border hover:border-primary/30 transition-all text-left"
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="w-7 h-7 rounded-lg bg-text-primary text-surface flex items-center justify-center shrink-0 mt-0.5">
                      <UserIcon className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-3 rounded-2xl bg-surface-elevated border border-border flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-surface-elevated border-t border-border">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Ask LoopBot in ${LANGUAGES.find((l) => l.code === selectedLanguage)?.label || 'English'}...`}
                  className="flex-1 px-3.5 py-2.5 text-xs sm:text-sm bg-surface border border-border rounded-xl focus:outline-none focus:border-primary text-text-primary placeholder:text-text-muted"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="p-2.5 rounded-xl bg-primary text-white hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  aria-label="Send message"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
              <div className="mt-1.5 flex items-center justify-between text-[10px] text-text-muted px-1">
                <span>Section 52 & Escrow Protected</span>
                <span>SpaceLoop LoopBot v1.0</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default LoopBot;
