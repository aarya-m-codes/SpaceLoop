import React, { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * HeroLivingEnvironment Component
 * Fullscreen first impression / front page of SpaceLoop.
 * 
 * Strict Observable Timeline Sequence:
 * - 0.0s: Clean atmospheric sky visible.
 * - 0.0s -> 1.4s: Buildings start at translateY(100vh) and visibly glide upward into place.
 * - 0.2s -> 1.2s: "SPACELOOP" visibly descends from translateY(-60px) + opacity: 0 -> translateY(0) + opacity: 1.
 * - 1.0s -> 1.8s: "Find a space, make it yours" in italics descends from translateY(-40px) + opacity: 0 -> translateY(0) + opacity: 1.
 * - 1.8s -> 2.4s: Scroll explore cue fades in smoothly.
 * - 2.0s -> 2.6s: Existing header smoothly slides down from top.
 * 
 * Edge-to-Edge: 16px bleed and matched background prevent any white/black seams.
 */
export const HeroLivingEnvironment = ({ onScrollExplore }) => {
  const { isDark } = useTheme();
  const [mountKey, setMountKey] = useState(0);

  useEffect(() => {
    // Generates fresh animation key on mount to ensure intro replays on reload & navigation
    setMountKey(Date.now());
  }, []);

  return (
    <section
      key={mountKey}
      className="relative w-full h-[100dvh] min-h-[580px] flex flex-col justify-between items-center overflow-hidden select-none border-none m-0 p-0 bg-[#d0c3b3] dark:bg-[#060e1c]"
    >
      
      {/* ==========================================================================
          1. SKY BASE LAYER (0.0s -> Continuous)
             Color-matched to the sky portion of the photo.
         ========================================================================== */}
      <div
        className={`absolute inset-0 z-0 transition-colors duration-700 ${
          isDark
            ? 'bg-gradient-to-b from-[#060e1c] via-[#0d1b32] to-[#1e3458]'
            : 'bg-gradient-to-b from-[#d0c3b3] via-[#ebd2ba] to-[#fbc286]'
        }`}
      />

      {/* ==========================================================================
          2. BUILDINGS RISING ANIMATION (0.0s -> 1.4s)
             - Starts visibly below the viewport at translateY(100vh)
             - Smoothly and noticeably glides up to translateY(0) in 1.4s
             - 16px bleed completely eliminates any corner or edge seams
         ========================================================================== */}
      <div className="hero-buildings-rise absolute -top-4 -bottom-4 -left-4 -right-4 z-10 pointer-events-none overflow-hidden">
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

        {/* Soft Vignette for Text Contrast */}
        <div
          className={`absolute inset-0 pointer-events-none transition-colors duration-700 ${
            isDark
              ? 'bg-gradient-to-b from-black/55 via-black/20 to-black/60'
              : 'bg-gradient-to-b from-black/35 via-transparent to-black/35'
          }`}
        />

        {/* Gentle Breeze Sway on Rooftop Foliage */}
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

        {/* Natural Sun Glow Pulse (Light Theme) */}
        {!isDark && (
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
      </div>

      {/* Top spacer */}
      <div className="w-full pt-16 z-30" />

      {/* ==========================================================================
          4. TYPOGRAPHY
             - "SPACELOOP" enters from above (-60px) + opacity fade (0.2s -> 1.2s)
             - "Find a space, make it yours" enters from above (-40px) + opacity fade (1.0s -> 1.8s)
         ========================================================================== */}
      <div className="relative z-30 text-center px-4 max-w-4xl mx-auto my-auto space-y-3.5">
        {/* Brand Title: SPACELOOP */}
        <h1 className="hero-title-enter text-5xl sm:text-7xl lg:text-8xl font-black text-white tracking-[0.24em] uppercase drop-shadow-[0_4px_28px_rgba(0,0,0,0.85)]">
          SPACELOOP
        </h1>

        {/* Brand Subtitle in Italics: "Find a space, make it yours" */}
        <p className="hero-subtitle-enter text-base sm:text-xl lg:text-2xl font-light italic text-white/95 tracking-wide drop-shadow-[0_2px_14px_rgba(0,0,0,0.9)]">
          Find a space, make it yours
        </p>
      </div>

      {/* ==========================================================================
          5. SLEEK SCROLL / EXPLORE INDICATOR
             Fades in smoothly at 1.8s. Triggers the page-turn upward slide transition.
         ========================================================================== */}
      <div className="hero-explore-cue relative z-30 pb-8 flex flex-col items-center">
        <button
          type="button"
          onClick={onScrollExplore}
          aria-label="Scroll to explore SpaceLoop spaces"
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
