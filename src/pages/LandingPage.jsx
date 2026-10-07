import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  Compass,
  Laptop,
  Video,
  Users,
  Coffee,
  Key,
  Shield,
  Clock,
  ArrowRight,
  Star,
  CheckCircle2,
  Bot,
  Sparkles,
  Zap,
  Building,
  Lock,
  Search,
  MapPin,
  Calendar,
  Send,
} from 'lucide-react';
import { HeroLivingEnvironment } from '../components/home/HeroLivingEnvironment';
import { SpaceCard } from '../components/spaces/SpaceCard';
import { ScrollReveal } from '../components/common/ScrollReveal';
import { Button } from '../components/common/Button';
import { AnimatedBackground } from '@/components/core/animated-background';
import { SPACES_DATA } from '../utils/constants';
import { spacesApi, aiApi } from '../services/api';

export const LandingPage = () => {
  const navigate = useNavigate();

  const [locationQuery, setLocationQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [loopBotPrompt, setLoopBotPrompt] = useState('');
  const [loopBotResponse, setLoopBotResponse] = useState(null);
  const [loopBotLoading, setLoopBotLoading] = useState(false);
  const [liveSpaces, setLiveSpaces] = useState(SPACES_DATA);
  const [windowHeight, setWindowHeight] = useState(800);

  useEffect(() => {
    // Fetch live spaces from backend
    spacesApi.getSpaces().then((res) => {
      const list = res?.spaces || (Array.isArray(res) ? res : []);
      if (list.length > 0) {
        setLiveSpaces(list);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setWindowHeight(window.innerHeight || 800);
    const handleResize = () => setWindowHeight(window.innerHeight || 800);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Scroll-linked transition for Hero -> Explore transition ONLY
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, windowHeight], ['0%', '-30%']);
  const heroScale = useTransform(scrollY, [0, windowHeight], [1, 0.92]);
  const heroOpacity = useTransform(scrollY, [0, windowHeight * 0.8, windowHeight], [1, 0.6, 0.2]);

  const handleScrollExplore = () => {
    const target = document.getElementById('spaceloop-content');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const categories = [
    { name: 'All Spaces', icon: Compass, count: '120+' },
    { name: 'Coworking Desks', icon: Laptop, count: '45' },
    { name: 'Creative Studios', icon: Video, count: '28' },
    { name: 'Meeting Rooms', icon: Users, count: '32' },
    { name: 'Rooftops & Lounges', icon: Coffee, count: '15' },
  ];

  const keyFeatures = [
    {
      title: 'Encrypted Digital Key Pass',
      description: 'Zero physical key handoffs. Your reservation automatically generates an encrypted QR pass and keypad PIN on your phone.',
      icon: Key,
    },
    {
      title: 'True Hourly Flexibility',
      description: 'Book for 1 hour or a full day. Transparent hourly pricing with instant confirmation and no recurring membership lock-in.',
      icon: Clock,
    },
    {
      title: 'Curated Architectural Quality',
      description: 'Every space is inspected for natural light, acoustic isolation, high-speed mesh WiFi, and ergonomic design.',
      icon: Building,
    },
    {
      title: 'Automated Host Protection',
      description: 'Enterprise grade insurance, guest identity verification, and direct automated bank deposits powered by Stripe.',
      icon: Shield,
    },
  ];

  const steps = [
    {
      step: '01',
      title: 'Discover & Match',
      description: 'Search by neighborhood, capacity, or natural lighting needs. Filter instantly or let LoopBot recommend the optimal spot.',
      icon: Compass,
    },
    {
      step: '02',
      title: 'Instant Reservation',
      description: 'Select your exact date and hourly duration. Confirm securely in one click with transparent pricing and no surprise fees.',
      icon: Clock,
    },
    {
      step: '03',
      title: 'Keyless Entry & Access',
      description: 'Arrive at the location and unlock the smart door with your phone pass. Enjoy focus, collaborate, and check out seamlessly.',
      icon: Key,
    },
  ];

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    navigate(`/explore?location=${encodeURIComponent(locationQuery)}&type=${selectedType}`);
  };

  const handleLoopBotSubmit = async (e) => {
    e.preventDefault();
    if (!loopBotPrompt.trim()) return;
    setLoopBotLoading(true);
    try {
      const res = await aiApi.chat({ message: loopBotPrompt });
      setLoopBotResponse({
        query: loopBotPrompt,
        recommended: liveSpaces[0] || SPACES_DATA[0],
        reason: res.response || 'Matched architectural workspace based on your requirements.',
        sources: res.sources || [],
      });
    } catch (err) {
      setLoopBotResponse({
        query: loopBotPrompt,
        recommended: liveSpaces[0] || SPACES_DATA[0],
        reason: 'Matched: 1Gbps WiFi, panoramic natural light, rooftop breakout lounge, and instant pass entry.',
      });
    } finally {
      setLoopBotLoading(false);
    }
  };

  return (
    <div className="w-full relative m-0 p-0 overflow-x-hidden border-none">
      
      {/* ==========================================================================
          SLIDE 1: FULLSCREEN LIVING ENVIRONMENTAL HERO
          Pinned at top with cinematic upward page-lift / slide transition on scroll.
          100% seamless: No visible edge, margin, border, or line.
         ========================================================================== */}
      <motion.div
        style={{
          y: heroY,
          scale: heroScale,
          opacity: heroOpacity,
        }}
        className="sticky top-0 h-[100dvh] w-full overflow-hidden z-0 border-none m-0 p-0 bg-[#d0c3b3] dark:bg-[#060e1c]"
      >
        <HeroLivingEnvironment onScrollExplore={handleScrollExplore} />
      </motion.div>

      {/* ==========================================================================
          SLIDE 2: THE SPACELOOP PLATFORM CONTENT (EXPLORE SECTION)
          Slides upward over the hero like turning a page upward.
          This effect appears ONLY HERE for the Hero -> Explore transition.
          Zero borders at the bottom or sides.
         ========================================================================== */}
      <div
        id="spaceloop-content"
        className="relative z-10 w-full bg-background rounded-t-[32px] sm:rounded-t-[48px] shadow-[0_-25px_60px_rgba(0,0,0,0.45)] border-none overflow-hidden transition-all duration-300"
      >
        {/* Subtle slide handle indicator */}
        <div className="w-full flex justify-center pt-3 pb-1">
          <div className="w-12 h-1 rounded-full bg-border opacity-60" />
        </div>

        {/* Search Bar Widget (Reveals as part of Slide 2) */}
        <section className="py-8 bg-surface border-b border-border">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <ScrollReveal delay={0}>
              <form
                onSubmit={handleSearchSubmit}
                className="bg-surface-elevated rounded-2xl p-3 sm:p-4 border border-border shadow-md"
              >
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                  {/* Location */}
                  <div className="md:col-span-5 flex items-center gap-3 px-3 py-2 rounded-xl bg-surface border border-border-subtle focus-within:border-primary/50 transition-colors">
                    <MapPin className="w-5 h-5 text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                        Location
                      </label>
                      <input
                        type="text"
                        value={locationQuery}
                        onChange={(e) => setLocationQuery(e.target.value)}
                        placeholder="City, neighborhood, or address"
                        className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                      />
                    </div>
                  </div>

                  {/* Space Type */}
                  <div className="md:col-span-4 flex items-center gap-3 px-3 py-2 rounded-xl bg-surface border border-border-subtle focus-within:border-primary/50 transition-colors">
                    <Calendar className="w-5 h-5 text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                        Space Type
                      </label>
                      <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="w-full bg-transparent text-sm text-text-primary focus:outline-none cursor-pointer"
                      >
                        <option value="all">All Space Types</option>
                        <option value="coworking">Coworking Desks</option>
                        <option value="studio">Private Studio</option>
                        <option value="meeting">Conference Room</option>
                        <option value="rooftop">Rooftop Lounge</option>
                      </select>
                    </div>
                  </div>

                  {/* Search CTA */}
                  <div className="md:col-span-3">
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      className="w-full shadow-md"
                      icon={Search}
                    >
                      Search Spaces
                    </Button>
                  </div>
                </div>
              </form>
            </ScrollReveal>
          </div>
        </section>

        {/* ==========================================================================
            WHAT SPACELOOP IS (Normal scrolling continues from here onwards)
           ========================================================================== */}
        <section className="py-16 sm:py-20 bg-background transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto text-center">
              <ScrollReveal delay={0}>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                  What SpaceLoop Is
                </span>
                <h2 className="text-2xl sm:text-4xl font-extrabold text-text-primary tracking-tight mt-2 leading-tight">
                  An on-demand architectural network for modern creative work.
                </h2>
                <p className="mt-4 text-sm sm:text-base text-text-secondary leading-relaxed">
                  SpaceLoop bridges the gap between rigid commercial leases and noisy cafes. We unlock distinctive architectural pavilions, design lofts, and soundproof studios on demand, giving creators, teams, and independent thinkers instant access to spaces that inspire.
                </p>
              </ScrollReveal>
            </div>

            {/* Quick Metrics */}
            <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              {[
                { label: 'Verified Spaces', value: '1,450+' },
                { label: 'Instant Digital Access', value: '100%' },
                { label: 'Average User Rating', value: '4.94 / 5' },
                { label: 'Global Cities', value: '24' },
              ].map((metric, i) => (
                <ScrollReveal key={metric.label} delay={i}>
                  <div className="p-4 sm:p-5 rounded-2xl bg-surface border border-border text-center shadow-sm">
                    <div className="text-xl sm:text-2xl font-black text-text-primary font-mono">
                      {metric.value}
                    </div>
                    <div className="text-xs text-text-muted mt-1 font-medium">
                      {metric.label}
                    </div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ==========================================================================
            EXPLORE SPACES (Space Discovery)
           ========================================================================== */}
        <section className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
            <div>
              <ScrollReveal delay={0}>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Space Discovery
                </span>
                <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                  Explore Available Spaces
                </h2>
                <p className="text-xs sm:text-sm text-text-secondary mt-1">
                  Bookable right now with instant digital key access.
                </p>
              </ScrollReveal>
            </div>

            <ScrollReveal delay={1}>
              <Link to="/explore">
                <Button variant="outline" size="sm" className="gap-1.5">
                  <span>View All 1,450+ Spaces</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </ScrollReveal>
          </div>

          {/* Category Navigation */}
          <div className="mb-8">
            <ScrollReveal delay={0}>
              <div className="flex items-center gap-2.5 overflow-x-auto pb-2 scrollbar-none">
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <Link
                      key={cat.name}
                      to={`/explore?category=${encodeURIComponent(cat.name)}`}
                      className="group shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-xl bg-surface border border-border hover:border-primary/50 text-text-secondary hover:text-text-primary text-xs font-medium transition-all shadow-sm hover:shadow"
                    >
                      <Icon className="w-3.5 h-3.5 text-primary" />
                      <span>{cat.name}</span>
                      <span className="text-[10px] px-1 rounded bg-surface-elevated text-text-muted">
                        {cat.count}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </ScrollReveal>
          </div>

          {/* Space Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            <AnimatedBackground
              className="rounded-3xl bg-zinc-100 dark:bg-zinc-800"
              transition={{
                type: 'spring',
                bounce: 0.2,
                duration: 0.6,
              }}
              enableHover
            >
              {liveSpaces.slice(0, 6).map((space, index) => (
                <div
                  key={space.id}
                  data-id={`card-${space.id || index}`}
                  className="p-2 w-full h-full flex flex-col"
                >
                  <ScrollReveal delay={index % 3} className="w-full h-full flex flex-col">
                    <SpaceCard space={space} />
                  </ScrollReveal>
                </div>
              ))}
            </AnimatedBackground>
          </div>
        </section>

        {/* ==========================================================================
            KEY FEATURES
           ========================================================================== */}
        <section className="py-16 sm:py-24 bg-surface border-y border-border transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto text-center mb-14">
              <ScrollReveal delay={0}>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Platform Capabilities
                </span>
                <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                  Engineered for Effortless Access
                </h2>
                <p className="text-text-secondary text-sm mt-2">
                  Everything you need to reserve, enter, work, and leave with zero friction.
                </p>
              </ScrollReveal>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {keyFeatures.map((feat, idx) => {
                const Icon = feat.icon;
                return (
                  <ScrollReveal key={feat.title} delay={idx}>
                    <div className="p-6 rounded-2xl bg-surface-elevated border border-border shadow-sm hover:shadow-md transition-shadow duration-200 flex flex-col justify-between h-full">
                      <div>
                        <div className="w-10 h-10 rounded-xl bg-primary-light text-primary flex items-center justify-center mb-4">
                          <Icon className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-base text-text-primary mb-2">
                          {feat.title}
                        </h3>
                        <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                          {feat.description}
                        </p>
                      </div>
                    </div>
                  </ScrollReveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ==========================================================================
            HOW SPACELOOP WORKS
           ========================================================================== */}
        <section id="how-it-works" className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <ScrollReveal delay={0}>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Step-by-Step Flow
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                How SpaceLoop Works
              </h2>
              <p className="text-text-secondary text-sm mt-2">
                Three simple steps from discovery to physical door unlock.
              </p>
            </ScrollReveal>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((item, idx) => {
              const Icon = item.icon;
              return (
                <ScrollReveal key={item.step} delay={idx}>
                  <div className="relative p-6 sm:p-8 rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-xl bg-primary-light flex items-center justify-center text-primary">
                        <Icon className="w-6 h-6" />
                      </div>
                      <span className="text-2xl font-black text-text-muted/30 font-mono">
                        {item.step}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-text-primary mb-2">
                      {item.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </ScrollReveal>
              );
            })}
          </div>
        </section>

        {/* ==========================================================================
            AI SMART MATCHING & LOOPBOT
           ========================================================================== */}
        <section className="py-16 sm:py-24 bg-surface-elevated border-y border-border transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
              <div className="lg:col-span-6 space-y-4">
                <ScrollReveal delay={0}>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary-light text-primary border border-primary/20">
                    <Bot className="w-3.5 h-3.5" />
                    <span>AI Powered Discovery</span>
                  </span>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight mt-2">
                    Meet LoopBot: Your intelligent workspace curator.
                  </h2>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    Instead of fiddling with 10 filter dropdowns, simply type what your team needs in natural language. LoopBot parses attendee size, acoustic requirements, natural lighting, and equipment to match you with verified spaces instantly.
                  </p>

                  <div className="pt-2 space-y-2 text-xs text-text-secondary">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary shrink-0" />
                      <span>Real-time availability and dynamic capacity calculations</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary shrink-0" />
                      <span>Context-aware recommendations based on meeting type</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary shrink-0" />
                      <span>Instant booking pass generation directly from chat</span>
                    </div>
                  </div>
                </ScrollReveal>
              </div>

              {/* LoopBot Interactive Chat Preview */}
              <div className="lg:col-span-6">
                <ScrollReveal delay={1}>
                  <div className="p-6 rounded-3xl bg-surface border border-border shadow-lg space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-xs shadow-sm">
                          LB
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-text-primary">LoopBot SmartMatch</h4>
                          <p className="text-[10px] text-emerald-500 font-medium">Online • Instant Query Parsing</p>
                        </div>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded-md bg-surface-elevated text-text-muted">
                        v2.0
                      </span>
                    </div>

                    <div className="space-y-3 text-xs">
                      <div className="p-3 rounded-2xl bg-surface-elevated text-text-primary border border-border-subtle max-w-[85%]">
                        "I need a quiet space for 4 people with natural light and an external monitor this afternoon."
                      </div>

                      <div className="p-3.5 rounded-2xl bg-primary-light text-text-primary border border-primary/20 max-w-[90%] ml-auto space-y-2">
                        <p className="font-semibold text-primary text-[11px]">
                          ✨ Found 1 perfect match available at 2:00 PM:
                        </p>
                        <div className="p-2.5 rounded-xl bg-surface border border-border text-xs flex items-center justify-between gap-2">
                          <div>
                            <p className="font-bold text-text-primary">The Atrium Sunlit Studio</p>
                            <p className="text-[11px] text-text-muted">$45/hr • SoHo Arts District</p>
                          </div>
                          <Link to="/spaces/2">
                            <Button size="sm" variant="primary" className="text-xs h-7 px-2.5">
                              Book
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>

                    <form onSubmit={handleLoopBotSubmit} className="pt-2 flex items-center gap-2">
                      <input
                        type="text"
                        value={loopBotPrompt}
                        onChange={(e) => setLoopBotPrompt(e.target.value)}
                        placeholder="Try: 'Rooftop for 8 people with sunset view'..."
                        className="flex-grow px-3.5 py-2 text-xs rounded-xl bg-surface-elevated border border-border-subtle focus:border-primary/50 text-text-primary placeholder:text-text-muted focus:outline-none"
                      />
                      <Button type="submit" size="sm" variant="primary" icon={Send}>
                        Ask
                      </Button>
                    </form>

                    {loopBotResponse && (
                      <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-text-primary">
                        <p className="font-semibold text-emerald-600">SmartMatch Recommendation:</p>
                        <p className="text-[11px] text-text-secondary mt-0.5">{loopBotResponse.reason}</p>
                      </div>
                    )}
                  </div>
                </ScrollReveal>
              </div>
            </div>
          </div>
        </section>

        {/* ==========================================================================
            TRUST & SAFETY
           ========================================================================== */}
        <section className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <ScrollReveal delay={0}>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Trust & Safety
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                Protection for Every Host & Seeker
              </h2>
              <p className="text-text-secondary text-sm mt-2">
                Built on verified digital identities, property guarantees, and automated IoT safety checks.
              </p>
            </ScrollReveal>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: '$1,000,000 Property Shield',
                description: 'Comprehensive property damage protection and third-party host liability cover included automatically on every booking.',
                icon: Shield,
              },
              {
                title: 'Verified ID & Guest Screening',
                description: 'Every seeker and host passes automated identity and safety verification before any access pass can be generated.',
                icon: CheckCircle2,
              },
              {
                title: 'Encrypted Digital Key Access',
                description: 'Encrypted rolling digital PINs and QR passes that expire precisely when your booking duration concludes.',
                icon: Lock,
              },
            ].map((item, idx) => {
              const Icon = item.icon;
              return (
                <ScrollReveal key={item.title} delay={idx}>
                  <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm text-left space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-primary-light text-primary flex items-center justify-center">
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-base text-text-primary">{item.title}</h3>
                    <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </ScrollReveal>
              );
            })}
          </div>
        </section>

        {/* ==========================================================================
            HOST AND SEEKER BENEFITS
           ========================================================================== */}
        <section className="py-16 sm:py-24 bg-surface border-y border-border transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <ScrollReveal delay={0}>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Ecosystem
                </span>
                <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                  Built for Seekers & Hosts Alike
                </h2>
              </ScrollReveal>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* For Seekers */}
              <ScrollReveal delay={0}>
                <div className="p-8 rounded-3xl bg-surface-elevated border border-border shadow-sm h-full flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-primary-light text-primary">
                      For Space Seekers
                    </div>
                    <h3 className="text-xl font-bold text-text-primary">
                      Inspiring workspaces wherever you are.
                    </h3>
                    <ul className="space-y-3 text-xs sm:text-sm text-text-secondary">
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Zero monthly subscriptions — pay only for the hours you use</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Instant digital pass generation directly on your smartphone</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Guaranteed WiFi speeds and focus-tested acoustics</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Flexible 1-hour cancellation policy for ultimate peace of mind</span>
                      </li>
                    </ul>
                  </div>
                  <div className="pt-6">
                    <Link to="/explore">
                      <Button variant="primary" size="md">
                        Find a Space Now
                      </Button>
                    </Link>
                  </div>
                </div>
              </ScrollReveal>

              {/* For Hosts */}
              <ScrollReveal delay={1}>
                <div className="p-8 rounded-3xl bg-surface-elevated border border-border shadow-sm h-full flex flex-col justify-between">
                  <div className="space-y-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400">
                      For Space Hosts
                    </div>
                    <h3 className="text-xl font-bold text-text-primary">
                      Monetize unused architectural capacity.
                    </h3>
                    <ul className="space-y-3 text-xs sm:text-sm text-text-secondary">
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>100% automated keyless entry integration with standard smart locks</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Set custom hourly pricing, minimum durations, and calendar blocks</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>$1,000,000 host liability coverage on every single booking</span>
                      </li>
                      <li className="flex items-center gap-2.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span>Automated Stripe payouts deposited directly into your bank account</span>
                      </li>
                    </ul>
                  </div>
                  <div className="pt-6">
                    <Link to="/host">
                      <Button variant="secondary" size="md">
                        Calculate Host Earnings
                      </Button>
                    </Link>
                  </div>
                </div>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* ==========================================================================
            FINAL CTA
           ========================================================================== */}
        <section className="py-20 sm:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ScrollReveal delay={0}>
            <div className="rounded-3xl bg-surface border border-border p-8 sm:p-14 text-center max-w-4xl mx-auto shadow-xl space-y-6">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Ready to Get Started?
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
                Unlock your next creative workspace in seconds.
              </h2>
              <p className="text-text-secondary text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
                Explore spaces nearby or list your own architectural property to start generating recurring revenue.
              </p>
              <div className="pt-2 flex flex-wrap items-center justify-center gap-4">
                <Link to="/explore">
                  <Button variant="primary" size="lg" icon={Compass}>
                    Explore Spaces Nearby
                  </Button>
                </Link>
                <Link to="/host">
                  <Button variant="outline" size="lg">
                    Become a Host
                  </Button>
                </Link>
              </div>
            </div>
          </ScrollReveal>
        </section>

      </div>
    </div>
  );
};

export default LandingPage;
