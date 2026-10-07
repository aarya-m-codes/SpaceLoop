import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Sparkles, ShieldCheck, Wifi, Users, KeyRound } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * HeroArchitecturalVisual Component
 * The SINGLE visual identity for the SpaceLoop landing page.
 * Architecturally inspired by the reference proportions: multi-tier modern glass pavilion,
 * rooftop garden terrace, and warm interior illumination.
 * Fully vector-rendered with zero raster screenshots, adapting seamlessly to Light and Dark themes.
 */
export const HeroArchitecturalVisual = () => {
  const { isDark } = useTheme();
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="relative w-full rounded-3xl overflow-hidden border border-border shadow-lift-light dark:shadow-lift-dark bg-surface transition-colors duration-500">
      {/* Dynamic Architectural Canvas */}
      <div className="relative w-full aspect-[16/10] sm:aspect-[21/10] overflow-hidden">
        
        {/* Sky Background Gradient */}
        <div
          className={`absolute inset-0 transition-all duration-700 ${
            isDark
              ? 'bg-gradient-to-b from-[#080d1a] via-[#0f172a] to-[#131d33]'
              : 'bg-gradient-to-b from-[#fed7aa]/35 via-[#ffedd5]/25 to-[#fef3c7]/20'
          }`}
        />

        {/* Ambient Twilight Stars / Sunset particles (Dark Mode only) */}
        {isDark && !shouldReduceMotion && (
          <div className="absolute inset-0 pointer-events-none opacity-40">
            <div className="absolute top-1/4 left-1/5 w-1 h-1 bg-amber-200 rounded-full animate-ping" style={{ animationDuration: '4s' }} />
            <div className="absolute top-1/6 right-1/4 w-1.5 h-1.5 bg-amber-100 rounded-full opacity-60" />
            <div className="absolute top-1/3 right-1/6 w-1 h-1 bg-sky-200 rounded-full animate-pulse" style={{ animationDuration: '6s' }} />
          </div>
        )}

        {/* SVG Architectural Pavilion */}
        <svg
          viewBox="0 0 1000 550"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
          preserveAspectRatio="xMidYEnd meet"
        >
          <defs>
            {/* Window Glow Filter */}
            <filter id="windowGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            {/* Linear Gradients for Facade */}
            <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={isDark ? '#263449' : '#e6ded3'} />
              <stop offset="100%" stopColor={isDark ? '#1a2433' : '#d5cbbe'} />
            </linearGradient>

            <linearGradient id="windowLightGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={isDark ? '#fef08a' : '#fffbeb'} stopOpacity={isDark ? '0.95' : '0.8'} />
              <stop offset="100%" stopColor={isDark ? '#f59e0b' : '#fed7aa'} stopOpacity={isDark ? '0.75' : '0.5'} />
            </linearGradient>

            <linearGradient id="terracePenthouseGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={isDark ? '#2b3a52' : '#ebdcd0'} />
              <stop offset="100%" stopColor={isDark ? '#1f2b3e' : '#d8c7b8'} />
            </linearGradient>
          </defs>

          {/* ==========================================================================
              TOP LEVEL: ROOFTOP PENTHOUSE & GARDEN TERRACE
             ========================================================================== */}
          {/* Penthouse structure */}
          <rect x="360" y="160" width="280" height="110" rx="4" fill="url(#terracePenthouseGrad)" />
          
          {/* Penthouse top roof coping */}
          <rect x="355" y="152" width="290" height="9" rx="2" fill={isDark ? '#3d4d6b' : '#c9b7a7'} />

          {/* Penthouse Upper Glass Windows */}
          <rect
            x="510"
            y="175"
            width="110"
            height="85"
            rx="2"
            fill="url(#windowLightGrad)"
            filter={isDark ? 'url(#windowGlow)' : undefined}
          />
          {/* Mullions on Penthouse Window */}
          <line x1="565" y1="175" x2="565" y2="260" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="4" />
          <line x1="510" y1="217" x2="620" y2="217" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="3" />

          {/* Rooftop Glass Parapet Railing */}
          <rect
            x="240"
            y="245"
            width="520"
            height="26"
            rx="3"
            fill={isDark ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.45)'}
            stroke={isDark ? '#38bdf8' : '#cbd5e1'}
            strokeWidth="1.5"
          />

          {/* Rooftop Garden Greenery (Trees & shrubs) */}
          <g fill={isDark ? '#14532d' : '#22c55e'} opacity={isDark ? '0.85' : '0.9'}>
            <circle cx="265" cy="242" r="22" />
            <circle cx="295" cy="238" r="25" />
            <circle cx="325" cy="245" r="20" />
            <circle cx="350" cy="248" r="16" />
            {/* Right side greenery */}
            <circle cx="650" cy="248" r="18" />
            <circle cx="680" cy="240" r="24" />
            <circle cx="715" cy="244" r="22" />
            <circle cx="740" cy="247" r="17" />
          </g>

          {/* Terrace Ambient String Lights */}
          <g fill={isDark ? '#fbbf24' : '#f59e0b'}>
            <circle cx="280" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
            <circle cx="320" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
            <circle cx="360" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
            <circle cx="640" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
            <circle cx="680" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
            <circle cx="720" cy="254" r="3.5" filter={isDark ? 'url(#windowGlow)' : undefined} />
          </g>

          {/* ==========================================================================
              MAIN LEVEL: THE TWO-STORY GLASS PAVILION
             ========================================================================== */}
          {/* Main Facade Structure */}
          <rect x="220" y="270" width="560" height="280" rx="6" fill="url(#wallGrad)" />
          
          {/* Structural Band dividing stories */}
          <rect x="210" y="265" width="580" height="14" rx="2" fill={isDark ? '#3d4d6b' : '#bda997'} />

          {/* Large Left Glass Window Bay (Floor-to-ceiling) */}
          <rect
            x="245"
            y="295"
            width="240"
            height="215"
            rx="4"
            fill="url(#windowLightGrad)"
            filter={isDark ? 'url(#windowGlow)' : undefined}
          />
          {/* Left Window Mullions & Grids */}
          <line x1="325" y1="295" x2="325" y2="510" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="5" />
          <line x1="405" y1="295" x2="405" y2="510" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="5" />
          <line x1="245" y1="365" x2="485" y2="365" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="4" />
          <line x1="245" y1="435" x2="485" y2="435" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="4" />

          {/* Left Window Interior Silhouettes (Workstation & Pendant Lamps) */}
          <g fill={isDark ? '#92400e' : '#a8a29e'} opacity="0.6">
            <rect x="280" y="460" width="70" height="15" rx="2" />
            <rect x="360" y="460" width="70" height="15" rx="2" />
            <circle cx="315" cy="345" r="7" fill={isDark ? '#fbbf24' : '#e07a5f'} />
            <circle cx="395" cy="345" r="7" fill={isDark ? '#fbbf24' : '#e07a5f'} />
            <line x1="315" y1="295" x2="315" y2="345" stroke={isDark ? '#fbbf24' : '#a8a29e'} strokeWidth="1.5" />
            <line x1="395" y1="295" x2="395" y2="345" stroke={isDark ? '#fbbf24' : '#a8a29e'} strokeWidth="1.5" />
          </g>

          {/* Large Right Glass Window Bay (Floor-to-ceiling) */}
          <rect
            x="515"
            y="295"
            width="240"
            height="215"
            rx="4"
            fill="url(#windowLightGrad)"
            filter={isDark ? 'url(#windowGlow)' : undefined}
          />
          {/* Right Window Mullions & Grids */}
          <line x1="595" y1="295" x2="595" y2="510" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="5" />
          <line x1="675" y1="295" x2="675" y2="510" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="5" />
          <line x1="515" y1="365" x2="755" y2="365" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="4" />
          <line x1="515" y1="435" x2="755" y2="435" stroke={isDark ? '#0f172a' : '#78716c'} strokeWidth="4" />

          {/* Right Window Interior Silhouettes (Bookshelves & Lounge) */}
          <g fill={isDark ? '#92400e' : '#a8a29e'} opacity="0.6">
            <rect x="535" y="380" width="18" height="110" rx="2" />
            <rect x="630" y="465" width="85" height="15" rx="2" />
            <circle cx="635" cy="345" r="7" fill={isDark ? '#fbbf24' : '#e07a5f'} />
            <circle cx="715" cy="345" r="7" fill={isDark ? '#fbbf24' : '#e07a5f'} />
            <line x1="635" y1="295" x2="635" y2="345" stroke={isDark ? '#fbbf24' : '#a8a29e'} strokeWidth="1.5" />
            <line x1="715" y1="295" x2="715" y2="345" stroke={isDark ? '#fbbf24' : '#a8a29e'} strokeWidth="1.5" />
          </g>

          {/* Central Architectural Entrance Glass Door & Keypad Sensor */}
          <rect
            x="485"
            y="435"
            width="30"
            height="75"
            fill={isDark ? '#1e293b' : '#fafaf9'}
            stroke={isDark ? '#f59e0b' : '#c25e1a'}
            strokeWidth="2"
          />
          <circle cx="508" cy="470" r="3" fill={isDark ? '#10b981' : '#10b981'} />
        </svg>

        {/* Ambient Warm Vignette & Horizon */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-background via-transparent to-transparent opacity-90" />

        {/* Floating Architectural Badge */}
        <div className="absolute top-4 left-4 sm:top-6 sm:left-6 z-20">
          <motion.div
            initial={shouldReduceMotion ? {} : { opacity: 0, x: -10 }}
            animate={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            transition={{ duration: 0.35 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-surface/90 backdrop-blur-md text-text-primary border border-border shadow-sm"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Digital Pass Active</span>
            <KeyRound className="w-3.5 h-3.5 text-primary ml-1" />
          </motion.div>
        </div>

        {/* Floating Building Specification Card */}
        <div className="absolute bottom-4 left-4 right-4 sm:bottom-6 sm:left-6 sm:right-6 z-20 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <motion.div
            initial={shouldReduceMotion ? {} : { opacity: 0, y: 10 }}
            animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="p-4 sm:p-5 rounded-2xl bg-surface/95 backdrop-blur-md border border-border shadow-lg max-w-md space-y-1.5"
          >
            <div className="flex items-center gap-2 text-xs font-medium text-primary uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Flagship Architectural Venue</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-text-primary tracking-tight">
              The Glass Loft Pavilion & Terrace
            </h3>
            <p className="text-xs text-text-secondary line-clamp-2">
              Multi-level workspace with panoramic acoustic glass, rooftop garden lounges, and encrypted IoT digital key access.
            </p>
            <div className="flex items-center gap-4 pt-2 text-[11px] text-text-muted border-t border-border-subtle">
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3 text-primary" /> Up to 18 guests
              </span>
              <span className="flex items-center gap-1">
                <Wifi className="w-3 h-3 text-primary" /> 1 Gbps WiFi
              </span>
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-500" /> Verified Host
              </span>
            </div>
          </motion.div>
        </div>

      </div>
    </div>
  );
};

export default HeroArchitecturalVisual;
