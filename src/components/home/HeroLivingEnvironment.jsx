import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * HeroLivingEnvironment Component
 * Fullscreen first impression / front page of SpaceLoop.
 * Uses the user-provided architectural images (Light Sunset / Dark Twilight)
 * with a living, calm environmental animation:
 * - ☁️ Slow-moving clouds drifting horizontally with multi-layer depth
 * - 🌿 🌳 Gentle breeze swaying rooftop foliage and leaves
 * - ☀️ Subtle sunlight breathing on the horizon in Light mode
 * - Centered typography: "SPACELOOP" and "Find a space , make it yours"
 */
export const HeroLivingEnvironment = () => {
  const { isDark } = useTheme();
  const shouldReduceMotion = useReducedMotion();

  const handleScrollDown = () => {
    const target = document.getElementById('spaceloop-content');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative w-full h-screen min-h-[640px] flex flex-col justify-between items-center overflow-hidden select-none">
      
      {/* ==========================================================================
          1. THE ARCHITECTURAL BASE ENVIRONMENT (User Provided Images)
         ========================================================================== */}
      {/* Light Theme: Sunset Architectural Building */}
      <img
        src="/images/spaceloop-hero-light.jpg"
        alt="SpaceLoop Architectural Workspace - Sunset Light Theme"
        className={`absolute inset-0 w-full h-full object-cover object-bottom transition-opacity duration-700 ease-smooth ${
          !isDark ? 'opacity-100 z-0' : 'opacity-0 -z-10'
        }`}
      />

      {/* Dark Theme: Twilight Architectural Building */}
      <img
        src="/images/spaceloop-hero-dark.jpg"
        alt="SpaceLoop Architectural Workspace - Twilight Dark Theme"
        className={`absolute inset-0 w-full h-full object-cover object-bottom transition-opacity duration-700 ease-smooth ${
          isDark ? 'opacity-100 z-0' : 'opacity-0 -z-10'
        }`}
      />

      {/* Soft Vignette Overlay for maximum text contrast across both day and night */}
      <div
        className={`absolute inset-0 z-10 pointer-events-none transition-colors duration-700 ${
          isDark
            ? 'bg-gradient-to-b from-black/55 via-black/25 to-black/60'
            : 'bg-gradient-to-b from-black/35 via-transparent to-black/35'
        }`}
      />

      {/* ==========================================================================
          2. ENVIRONMENTAL MOTION: ☁️ SLOW DRIFTING CLOUDS
         ========================================================================== */}
      {!shouldReduceMotion && (
        <div className="absolute inset-0 z-15 pointer-events-none overflow-hidden h-[65%]">
          {/* Layer 1: Distant Slow Clouds */}
          <div className="absolute top-[8%] w-[220%] h-32 opacity-30 cloud-layer-back">
            <svg viewBox="0 0 1200 120" className="w-full h-full fill-white/80 dark:fill-slate-300/40">
              <path d="M50,80 Q90,30 150,50 Q200,20 260,45 Q310,15 380,50 Q430,35 480,75 Q520,40 580,60 Q630,25 700,55 Q760,30 820,65 Q880,35 940,60 Q1000,20 1060,55 Q1120,40 1180,80 Z" filter="blur(8px)" />
            </svg>
          </div>

          {/* Layer 2: Mid-ground Drifting Clouds */}
          <div className="absolute top-[16%] w-[240%] h-40 opacity-40 cloud-layer-mid">
            <svg viewBox="0 0 1400 140" className="w-full h-full fill-white/90 dark:fill-slate-200/50">
              <path d="M40,90 Q100,40 170,60 Q230,25 300,55 Q370,20 440,65 Q510,35 580,70 Q660,25 740,60 Q820,30 900,75 Q980,35 1060,65 Q1140,25 1220,70 Q1300,45 1370,90 Z" filter="blur(12px)" />
            </svg>
          </div>

          {/* Layer 3: Closer Gentle Wisps */}
          <div className="absolute top-[26%] w-[260%] h-36 opacity-35 cloud-layer-fore">
            <svg viewBox="0 0 1500 130" className="w-full h-full fill-white dark:fill-slate-100/40">
              <path d="M60,85 Q130,45 210,65 Q290,30 370,65 Q450,25 530,70 Q620,35 710,65 Q800,25 890,70 Q980,40 1070,75 Q1160,30 1250,70 Q1340,45 1430,85 Z" filter="blur(14px)" />
            </svg>
          </div>
        </div>
      )}

      {/* ==========================================================================
          3. ENVIRONMENTAL MOTION: 🌿 🌳 GENTLE BREEZE ON ROOFTOP FOLIAGE
         ========================================================================== */}
      {!shouldReduceMotion && (
        <div
          className="absolute z-20 pointer-events-none foliage-breeze"
          style={{
            top: '68%',
            left: '26%',
            width: '48%',
            height: '12%',
          }}
        >
          {/* Subtle natural foliage wind shimmer overlay matching the rooftop garden */}
          <div
            className={`w-full h-full rounded-full blur-md opacity-25 ${
              isDark ? 'bg-emerald-950/40' : 'bg-emerald-600/20'
            }`}
          />
        </div>
      )}

      {/* ==========================================================================
          4. ENVIRONMENTAL MOTION: ☀️ NATURAL SUN PULSE (Light Theme)
         ========================================================================== */}
      {!isDark && !shouldReduceMotion && (
        <div
          className="absolute z-15 pointer-events-none sun-ambient-pulse"
          style={{
            bottom: '22%',
            left: '18%',
            width: '160px',
            height: '160px',
          }}
        >
          <div className="w-full h-full rounded-full bg-gradient-to-r from-amber-200/50 via-yellow-100/40 to-transparent blur-2xl" />
        </div>
      )}

      {/* Top buffer for balanced centering */}
      <div className="w-full pt-16 z-30" />

      {/* ==========================================================================
          5. TYPOGRAPHY: "SPACELOOP" & "Find a space , make it yours"
             (The ONLY text and elements on the front page)
         ========================================================================== */}
      <div className="relative z-30 text-center px-4 max-w-4xl mx-auto my-auto space-y-4">
        {/* Brand Title: SPACELOOP */}
        <motion.h1
          initial={shouldReduceMotion ? {} : { opacity: 0, y: -16, letterSpacing: '0.15em' }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0, letterSpacing: '0.24em' }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl sm:text-7xl lg:text-8xl font-black text-white tracking-[0.24em] uppercase drop-shadow-[0_4px_24px_rgba(0,0,0,0.7)]"
        >
          SPACELOOP
        </motion.h1>

        {/* Brand Subtitle: "Find a space , make it yours" */}
        <motion.p
          initial={shouldReduceMotion ? {} : { opacity: 0, y: 12 }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="text-base sm:text-xl lg:text-2xl font-light text-white/95 tracking-wide drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]"
        >
          Find a space , make it yours
        </motion.p>
      </div>

      {/* ==========================================================================
          6. SLEEK SCROLL INDICATOR (Transitions to content below)
         ========================================================================== */}
      <div className="relative z-30 pb-8 flex flex-col items-center">
        <button
          type="button"
          onClick={handleScrollDown}
          aria-label="Scroll down to explore SpaceLoop content"
          className="flex flex-col items-center gap-1.5 text-white/80 hover:text-white transition-colors duration-200 group focus:outline-none"
        >
          <span className="text-[11px] uppercase tracking-[0.2em] font-medium drop-shadow-sm">
            Scroll to explore
          </span>
          <div className="scroll-indicator-bounce p-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 group-hover:bg-white/20 transition-colors">
            <ChevronDown className="w-4 h-4 text-white" />
          </div>
        </button>
      </div>

    </section>
  );
};

export default HeroLivingEnvironment;
