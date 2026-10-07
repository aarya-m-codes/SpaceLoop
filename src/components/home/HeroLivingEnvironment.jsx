import React, { useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * HeroLivingEnvironment Component
 * Fullscreen first impression / front page of SpaceLoop.
 * 
 * Entrance Sequence (Completed within <= 2.0s):
 * 1. (0.0s - 0.3s) Sky with slow-drifting clouds is visible first.
 * 2. (0.3s - 1.5s) Building rises up smoothly from the bottom.
 * 3. (0.3s - 1.5s) Simultaneously, "SPACELOOP" drops from the top and
 *    "Find a space, make it yours" in italics fades in smoothly below it.
 * 4. (1.9s) Header appears at top after animation is done.
 * 
 * Completely edge-to-edge: No white/black lines on borders or corners.
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
    <section className="relative w-full h-screen min-h-[580px] flex flex-col justify-between items-center overflow-hidden select-none border-none m-0 p-0">
      
      {/* ==========================================================================
          1. SKY BASE LAYER (Shown first before and behind the rising building)
         ========================================================================== */}
      <div
        className={`absolute inset-0 z-0 transition-colors duration-700 ${
          isDark
            ? 'bg-gradient-to-b from-[#050a16] via-[#0d172b] to-[#182846]'
            : 'bg-gradient-to-b from-[#d2c5b4] via-[#f6ce9d] to-[#fbc286]'
        }`}
      />

      {/* ==========================================================================
          2. ENVIRONMENTAL MOTION: ☁️ SLOW DRIFTING CLOUDS (Moving across the sky)
         ========================================================================== */}
      {!shouldReduceMotion && (
        <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden h-[60%]">
          {/* Layer 1: Distant Slow Clouds */}
          <div className="absolute top-[6%] w-[220%] h-32 opacity-35 cloud-layer-back">
            <svg viewBox="0 0 1200 120" className="w-full h-full fill-white/85 dark:fill-slate-300/40">
              <path d="M50,80 Q90,30 150,50 Q200,20 260,45 Q310,15 380,50 Q430,35 480,75 Q520,40 580,60 Q630,25 700,55 Q760,30 820,65 Q880,35 940,60 Q1000,20 1060,55 Q1120,40 1180,80 Z" filter="blur(8px)" />
            </svg>
          </div>

          {/* Layer 2: Mid-ground Drifting Clouds */}
          <div className="absolute top-[14%] w-[240%] h-40 opacity-45 cloud-layer-mid">
            <svg viewBox="0 0 1400 140" className="w-full h-full fill-white/95 dark:fill-slate-200/50">
              <path d="M40,90 Q100,40 170,60 Q230,25 300,55 Q370,20 440,65 Q510,35 580,70 Q660,25 740,60 Q820,30 900,75 Q980,35 1060,65 Q1140,25 1220,70 Q1300,45 1370,90 Z" filter="blur(11px)" />
            </svg>
          </div>

          {/* Layer 3: Closer Gentle Wisps */}
          <div className="absolute top-[22%] w-[260%] h-36 opacity-40 cloud-layer-fore">
            <svg viewBox="0 0 1500 130" className="w-full h-full fill-white dark:fill-slate-100/40">
              <path d="M60,85 Q130,45 210,65 Q290,30 370,65 Q450,25 530,70 Q620,35 710,65 Q800,25 890,70 Q980,40 1070,75 Q1160,30 1250,70 Q1340,45 1430,85 Z" filter="blur(14px)" />
            </svg>
          </div>
        </div>
      )}

      {/* ==========================================================================
          3. BUILDING RISING ANIMATION LAYER
             Image extends beyond edges by 6px (inset-[-6px]) to eliminate any edge lines.
             Rises smoothly from bottom (0.3s - 1.5s).
         ========================================================================== */}
      <motion.div
        initial={shouldReduceMotion ? { y: 0 } : { y: '30%', opacity: 0.8 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.2, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className="absolute inset-[-6px] z-15 pointer-events-none overflow-hidden"
      >
        {/* Light Theme: Sunset Architectural Building */}
        <img
          src="/images/spaceloop-hero-light.jpg"
          alt="SpaceLoop Architectural Workspace - Sunset Light Theme"
          className={`absolute inset-0 w-full h-full object-cover object-bottom transition-opacity duration-700 ease-smooth ${
            !isDark ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* Dark Theme: Twilight Architectural Building */}
        <img
          src="/images/spaceloop-hero-dark.jpg"
          alt="SpaceLoop Architectural Workspace - Twilight Dark Theme"
          className={`absolute inset-0 w-full h-full object-cover object-bottom transition-opacity duration-700 ease-smooth ${
            isDark ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* Subtle Vignette for Text Readability */}
        <div
          className={`absolute inset-0 pointer-events-none transition-colors duration-700 ${
            isDark
              ? 'bg-gradient-to-b from-black/55 via-black/20 to-black/60'
              : 'bg-gradient-to-b from-black/35 via-transparent to-black/35'
          }`}
        />

        {/* Gentle Breeze on Rooftop Foliage */}
        {!shouldReduceMotion && (
          <div
            className="absolute pointer-events-none foliage-breeze"
            style={{
              top: '67%',
              left: '26%',
              width: '48%',
              height: '14%',
            }}
          >
            <div
              className={`w-full h-full rounded-full blur-md opacity-25 ${
                isDark ? 'bg-emerald-950/40' : 'bg-emerald-600/20'
              }`}
            />
          </div>
        )}

        {/* Natural Sun Glow Pulse (Light Theme) */}
        {!isDark && !shouldReduceMotion && (
          <div
            className="absolute pointer-events-none sun-ambient-pulse"
            style={{
              bottom: '20%',
              left: '17%',
              width: '180px',
              height: '180px',
            }}
          >
            <div className="w-full h-full rounded-full bg-gradient-to-r from-amber-200/50 via-yellow-100/35 to-transparent blur-2xl" />
          </div>
        )}
      </motion.div>

      {/* Top spacer */}
      <div className="w-full pt-12 z-30" />

      {/* ==========================================================================
          4. TYPOGRAPHY: "SPACELOOP" & "Find a space , make it yours"
             Descends from top simultaneously as the building rises from bottom.
             Completed well within <= 2.0s.
         ========================================================================== */}
      <div className="relative z-30 text-center px-4 max-w-4xl mx-auto my-auto space-y-3.5">
        {/* Brand Title: SPACELOOP */}
        <motion.h1
          initial={shouldReduceMotion ? {} : { opacity: 0, y: -40, letterSpacing: '0.12em' }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0, letterSpacing: '0.24em' }}
          transition={{ duration: 1.1, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl sm:text-7xl lg:text-8xl font-black text-white tracking-[0.24em] uppercase drop-shadow-[0_4px_28px_rgba(0,0,0,0.75)]"
        >
          SPACELOOP
        </motion.h1>

        {/* Brand Subtitle in Italics: "Find a space , make it yours" */}
        <motion.p
          initial={shouldReduceMotion ? {} : { opacity: 0, y: -20 }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          transition={{ duration: 1.0, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="text-base sm:text-xl lg:text-2xl font-light italic text-white/95 tracking-wide drop-shadow-[0_2px_14px_rgba(0,0,0,0.85)]"
        >
          Find a space , make it yours
        </motion.p>
      </div>

      {/* ==========================================================================
          5. SLEEK SCROLL INDICATOR
             Triggers the upward slide / page-turn animation into the content below.
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
