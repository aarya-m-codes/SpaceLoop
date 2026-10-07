import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X, Search, Compass, Bot, ArrowRight, CheckCircle2 } from 'lucide-react';
import { spacesApi } from '../../services/api';
import { SpaceCard } from './SpaceCard';

const SAMPLE_QUERIES = [
  'Quiet study desk with high-speed WiFi in Bangalore under ₹200/hr',
  'Natural light podcast studio in Mumbai for 4 people with acoustic treatment',
  'Architectural conference boardroom for 10 near Delhi Metro',
  'Sunlit rooftop terrace workspace for evening creative sprint',
];

export const AiSearchModal = ({ isOpen, onClose, onSelectSpace }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async (queryText) => {
    const q = (queryText || query).trim();
    if (!q || loading) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      // Connect to real backend endpoint POST /api/spaces/ai-match
      const data = await spacesApi.aiMatch({ query: q });
      setResult(data);
    } catch (err) {
      setError(err.message || 'AI space matching service encountered a temporary error.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-4xl bg-surface border border-border rounded-3xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-surface-elevated">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-primary to-indigo-500 text-white flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
                <span>AI Natural-Language Space Discovery</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                  Gemini + Vector RAG
                </span>
              </h2>
              <p className="text-xs text-text-secondary">
                Describe your architectural space needs, vibe, amenities, and budget in plain English or Hinglish.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Query Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSearch();
            }}
            className="flex gap-2"
          >
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-text-muted absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. 4-person design sprint room with standing desks and espresso in Koramangala..."
                className="w-full pl-11 pr-4 py-3 text-sm rounded-2xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary shadow-sm"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 rounded-2xl bg-primary text-white font-semibold text-sm hover:bg-primary-hover disabled:opacity-50 transition-all flex items-center gap-2 shrink-0 shadow-md shadow-primary/20"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Matching...' : 'AI Match'}</span>
            </button>
          </form>

          {/* Sample Prompts */}
          {!result && !loading && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Try describing a scenario:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SAMPLE_QUERIES.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuery(sample);
                      handleSearch(sample);
                    }}
                    className="p-3 text-left rounded-xl bg-surface-elevated hover:bg-primary/5 border border-border hover:border-primary/30 text-xs text-text-secondary hover:text-primary transition-all flex items-center justify-between group"
                  >
                    <span>{sample}</span>
                    <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center animate-spin">
                <Sparkles className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-bold text-text-primary">Extracting Semantic Constraints...</h4>
              <p className="text-xs text-text-secondary max-w-sm">
                Parsing budget thresholds, minimum capacity, amenities, and spatial acoustics via Gemini LLM pipeline.
              </p>
            </div>
          )}

          {/* Error Notice */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs">
              {error}
            </div>
          )}

          {/* Match Results */}
          {result && (
            <div className="space-y-6">
              {/* Reasoning Card */}
              {result.explanation && (
                <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 text-xs text-text-secondary leading-relaxed flex items-start gap-3">
                  <Bot className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-text-primary block mb-1">Architectural Match Analysis:</strong>
                    <span>{result.explanation}</span>
                  </div>
                </div>
              )}

              {/* Matched Spaces */}
              <div>
                <h3 className="text-sm font-bold text-text-primary mb-3">
                  Matching Spaces ({(result.spaces || result.matches || []).length} Found)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(result.spaces || result.matches || []).map((sp) => (
                    <div key={sp.id} onClick={onClose}>
                      <SpaceCard space={sp} />
                    </div>
                  ))}
                </div>
                {(result.spaces || result.matches || []).length === 0 && (
                  <p className="text-xs text-text-muted text-center py-8">
                    No physical spaces matched the exact criteria. Try broadening your budget or location parameters.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default AiSearchModal;
