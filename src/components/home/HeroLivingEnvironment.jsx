import React from 'react';
import { ChevronDown } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

/**
 * HeroLivingEnvironment Component
 * Fullscreen first impression / front page of SpaceLoop.
 * 
 * Strict Timeline Animation Sequence (Maximum 2.0s):
 * - 0.0s: Sky visible, clouds visible and slowly moving.
 * - 0.0s -> 1.2s: Buildings start below viewport and rise smoothly into position.
 * - 0.2s -> 1.2s: SPACELOOP descends from above and fades in (simultaneous with rising buildings).
 * - 1.0s -> 1.8s: "Find a space, make it yours" in italics descends and fades in.
 * - 1.8s -> 2.4s: Scroll explore cue fades in.
 * - 0.0s -> continuously: Clouds continuously drift horizontally.
 * 
 * 100% Edge-to-Edge: 12px bleed and matched background prevent any edge line or corner seam.
 */
export const HeroLivingEnvironment = ({ onScrollExplore }) => {
  const { isDark } = useTheme();

  return (
    <section className="relative w-full h-[100dvh] min-h-[580px] flex flex-col justify-between items-center overflow-hidden select-none border-none m-0 p-0 bg-[#d0c3b3] dark:bg-[#060e1c]">
      
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
          2. CLOUD ANIMATION (0.0s -> Continuous before, during, & after intro)
             Seamless infinite horizontal drift with multi-layer parallax depth.
         ========================================================================== */}
      <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden h-[62%]">
        {/* Layer 1: Distant Slow Clouds */}
        <div className="absolute top-[6%] w-[200%] h-32 opacity-45 cloud-layer-back flex">
          <svg viewBox="0 0 1200 120" className="w-1/2 h-full fill-white/85 dark:fill-slate-300/40 shrink-0">
            <path d="M50,80 Q90,30 150,50 Q200,20 260,45 Q310,15 380,50 Q430,35 480,75 Q520,40 580,60 Q630,25 700,55 Q760,30 820,65 Q880,35 940,60 Q1000,20 1060,55 Q1120,40 1180,80 Z" filter="blur(3px)" />
          </svg>
          <svg viewBox="0 0 1200 120" className="w-1/2 h-full fill-white/85 dark:fill-slate-300/40 shrink-0">
            <path d="M50,80 Q90,30 150,50 Q200,20 260,45 Q310,15 380,50 Q430,35 480,75 Q520,40 580,60 Q630,25 700,55 Q760,30 820,65 Q880,35 940,60 Q1000,20 1060,55 Q1120,40 1180,80 Z" filter="blur(3px)" />
          </svg>
        </div>

        {/* Layer 2: Mid-ground Drifting Clouds */}
        <div className="absolute top-[14%] w-[200%] h-40 opacity-55 cloud-layer-mid flex">
          <svg viewBox="0 0 1400 140" className="w-1/2 h-full fill-white/95 dark:fill-slate-200/50 shrink-0">
            <path d="M40,90 Q100,40 170,60 Q230,25 300,55 Q370,20 440,65 Q510,35 580,70 Q660,25 740,60 Q820,30 900,75 Q980,35 1060,65 Q1140,25 1220,70 Q1300,45 1370,90 Z" filter="blur(4px)" />
          </svg>
          <svg viewBox="0 0 1400 140" className="w-1/2 h-full fill-white/95 dark:fill-slate-200/50 shrink-0">
            <path d="M40,90 Q100,40 170,60 Q230,25 300,55 Q370,20 440,65 Q510,35 580,70 Q660,25 740,60 Q820,30 900,75 Q980,35 1060,65 Q1140,25 1220,70 Q1300,45 1370,90 Z" filter="blur(4px)" />
          </svg>
        </div>

        {/* Layer 3: Closer Gentle Wisps */}
        <div className="absolute top-[22%] w-[200%] h-36 opacity-50 cloud-layer-fore flex">
          <svg viewBox="0 0 1500 130" className="w-1/2 h-full fill-white dark:fill-slate-100/40 shrink-0">
            <path d="M60,85 Q130,45 210,65 Q290,30 370,65 Q450,25 530,70 Q620,35 710,65 Q800,25 890,70 Q980,40 1070,75 Q1160,30 1250,70 Q1340,45 1430,85 Z" filter="blur(5px)" />
          </svg>
          <svg viewBox="0 0 1500 130" className="w-1/2 h-full fill-white dark:fill-slate-100/40 shrink-0">
            <path d="M60,85 Q130,45 210,65 Q290,30 370,65 Q450,25 530,70 Q620,35 710,65 Q800,25 890,70 Q980,40 1070,75 Q1160,30 1250,70 Q1340,45 1430,85 Z" filter="blur(5px)" />
          </svg>
        </div>
      </div>

      {/* ==========================================================================
          3. BUILDINGS RISING ANIMATION (0.0s -> 1.2s)
             - Starts below viewport at transform: translate3d(0, 100%, 0)
             - Smoothly rises to position at translate3d(0, 0, 0) in 1.2s
             - 12px bleed completely eliminates any corner or edge seams
         ========================================================================== */}
      <div className="hero-buildings-rise absolute -top-3 -bottom-3 -left-3 -right-3 z-15 pointer-events-none overflow-hidden">
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
             - "SPACELOOP" descends from top and fades in (0.2s -> 1.2s)
             - "Find a space, make it yours" in italics descends and fades in (1.0s -> 1.8s)
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
