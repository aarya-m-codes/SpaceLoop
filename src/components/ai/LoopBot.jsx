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
} from 'lucide-react';
import { aiApi } from '../../services/api';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी (Hindi)' },
  { code: 'hinglish', label: 'Hinglish' },
  { code: 'mr', label: 'मराठी (Marathi)' },
];

const DEFAULT_SUGGESTED_ACTIONS = [
  'Find study desks near Bangalore under ₹200',
  'How does the ₹100 refundable escrow work?',
  'What is the cancellation policy?',
  'How do I verify as a student for 15% discount?',
];

export const LoopBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'bot',
      text: 'Namaste! I am LoopBot, your SpaceLoop concierge. How can I help you find, book, or verify architectural spaces today?',
      intent: 'GREETING',
      sources: ['SpaceLoop Guidebook', 'Trust & Safety Policies'],
      suggested_actions: DEFAULT_SUGGESTED_ACTIONS,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(() => `conv_${Date.now()}`);
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
      // Connect to real backend endpoint POST /api/ai/chat
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
        text: response.response || response.message || 'I have processed your request.',
        intent: response.intent || 'GENERAL_QUERY',
        sources: response.sources || [],
        suggested_actions: response.suggested_actions || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.warn('AI chat error:', err);
      // Graceful fallback according to specification
      const fallbackMessage = {
        id: `bot-fallback-${Date.now()}`,
        sender: 'bot',
        text:
          "I'm currently answering from our verified policy knowledge base: SpaceLoop spaces can be booked hourly with an instant 4-digit PIN. Every reservation holds a 100% refundable ₹100 escrow deposit and a 5% platform fee. All check-ins are verified within 100m geofencing.",
        intent: 'POLICY_FALLBACK',
        sources: ['Internal SpaceLoop Knowledge Base'],
        suggested_actions: [
          'Explore Spaces',
          'Review Escrow Terms',
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

  const resetConversation = () => {
    setConversationId(`conv_${Date.now()}`);
    setMessages([
      {
        id: 'init-fresh',
        sender: 'bot',
        text: 'Session reset! What architectural space or booking inquiry can I assist you with?',
        intent: 'GREETING',
        sources: [],
        suggested_actions: DEFAULT_SUGGESTED_ACTIONS,
        timestamp: new Date(),
      },
    ]);
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
            className="fixed bottom-20 right-4 sm:right-6 z-50 w-[95vw] sm:w-[420px] h-[600px] max-h-[85vh] flex flex-col rounded-3xl bg-surface border border-border shadow-2xl overflow-hidden backdrop-blur-xl"
          >
            {/* Header */}
            <div className="px-5 py-4 bg-surface-elevated border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-text-primary">LoopBot</h3>
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                      LIVE
                    </span>
                  </div>
                  <p className="text-[11px] text-text-muted">SpaceLoop Marketplace Concierge</p>
                </div>
              </div>

              {/* Language Selector & Controls */}
              <div className="flex items-center gap-1.5">
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
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

                  <div className={`max-w-[82%] space-y-2`}>
                    <div
                      className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-primary text-white rounded-tr-sm'
                          : 'bg-surface-elevated border border-border text-text-primary rounded-tl-sm'
                      }`}
                    >
                      <p className="whitespace-pre-line">{msg.text}</p>
                    </div>

                    {/* Sources Badge */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex flex-wrap gap-1 text-[10px] text-text-muted">
                        <span className="font-semibold text-text-secondary">Sources:</span>
                        {msg.sources.map((src, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-surface-elevated border border-border">
                            {src}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Suggested Actions Chips */}
                    {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
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
                  placeholder={`Ask in ${LANGUAGES.find((l) => l.code === selectedLanguage)?.label || 'English'}...`}
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
                <span>RAG Verified • Privacy Protected</span>
                <span>SpaceLoop v1.0</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default LoopBot;
