import React from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
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
} from 'lucide-react';
import { HeroInteractive } from '../components/home/HeroInteractive';
import { SpaceCard } from '../components/spaces/SpaceCard';
import { ScrollReveal } from '../components/common/ScrollReveal';
import { Button } from '../components/common/Button';
import { SPACES_DATA } from '../utils/constants';

export const LandingPage = () => {
  const shouldReduceMotion = useReducedMotion();

  const categories = [
    { name: 'All Spaces', icon: Compass, count: '120+' },
    { name: 'Coworking Desks', icon: Laptop, count: '45' },
    { name: 'Creative Studios', icon: Video, count: '28' },
    { name: 'Meeting Rooms', icon: Users, count: '32' },
    { name: 'Rooftops & Lounges', icon: Coffee, count: '15' },
  ];

  const steps = [
    {
      step: '01',
      title: 'Discover & Filter',
      description: 'Explore verified architectural spaces nearby with real-time availability and transparent hourly pricing.',
      icon: Compass,
    },
    {
      step: '02',
      title: 'Book in Seconds',
      description: 'Select your time slot and guest count. Receive an instant booking confirmation with no hidden platform fees.',
      icon: Clock,
    },
    {
      step: '03',
      title: 'Digital Key Access',
      description: 'Unlock your reserved space directly via our encrypted digital pass and QR access right on your phone.',
      icon: Key,
    },
  ];

  return (
    <div className="w-full">
      {/* 1. Hero Section with Interactive Building Interface */}
      <HeroInteractive />

      {/* 2. Popular Categories Bar */}
      <section className="py-8 border-y border-border bg-surface/60 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ScrollReveal delay={0}>
            <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none sm:justify-center">
              {categories.map((cat, idx) => {
                const Icon = cat.icon;
                return (
                  <Link
                    key={cat.name}
                    to={`/explore?category=${encodeURIComponent(cat.name)}`}
                    className="group shrink-0 flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-surface border border-border hover:border-primary/50 text-text-secondary hover:text-text-primary transition-all duration-200 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
                  >
                    <Icon className="w-4 h-4 text-primary transition-transform duration-200 group-hover:scale-110" />
                    <span className="text-sm font-medium">{cat.name}</span>
                    <span className="text-[11px] px-1.5 py-0.5 rounded-md bg-surface-elevated text-text-muted">
                      {cat.count}
                    </span>
                  </Link>
                );
              })}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* 3. Featured Spaces Section */}
      <section className="py-16 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
          <div>
            <ScrollReveal delay={0}>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Featured Spaces
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
                Handpicked Workspaces & Studios
              </h2>
            </ScrollReveal>
          </div>
          <ScrollReveal delay={1}>
            <Link to="/explore">
              <Button variant="outline" size="sm" className="gap-1.5">
                <span>Browse All Spaces</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </ScrollReveal>
        </div>

        {/* Space Cards Grid with Scroll Reveals */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {SPACES_DATA.map((space, index) => (
            <ScrollReveal key={space.id} delay={index % 3}>
              <SpaceCard space={space} />
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* 4. How SpaceLoop Works */}
      <section id="how-it-works" className="py-16 sm:py-24 bg-surface-elevated border-y border-border transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <ScrollReveal delay={0}>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Seamless Flow
              </span>
              <h2 className="text-3xl font-bold text-text-primary tracking-tight mt-1">
                How SpaceLoop Works
              </h2>
              <p className="text-text-secondary text-sm sm:text-base mt-3">
                From discovery to entering your private space, experience effortless access without traditional office friction.
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
                      <span className="text-2xl font-black text-text-muted/40 font-mono">
                        {item.step}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-text-primary mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-text-secondary leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </ScrollReveal>
              );
            })}
          </div>
        </div>
      </section>

      {/* 5. Trust & Host Section */}
      <section className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-surface border border-border p-8 sm:p-12 lg:p-16 shadow-lg">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Host on SpaceLoop
              </span>
              <h2 className="text-2xl sm:text-4xl font-extrabold text-text-primary tracking-tight mt-2">
                Turn your architectural space into passive revenue.
              </h2>
              <p className="mt-4 text-text-secondary text-sm sm:text-base leading-relaxed">
                Join verified hosts sharing distinctive architectural lofts, executive meeting spaces, and photo studios. Automated access passes, guest screening, and automated payouts.
              </p>

              <div className="mt-6 space-y-3">
                <div className="flex items-center gap-2.5 text-sm text-text-primary">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>$1,000,000 Host Liability & Property Protection</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm text-text-primary">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>Automated digital pass generation upon verified booking</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm text-text-primary">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>Instant Stripe direct deposit payouts</span>
                </div>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/host">
                  <Button variant="primary" size="lg">
                    <span>Become a Host</span>
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
                <Link to="/help">
                  <Button variant="outline" size="lg">
                    Host FAQ
                  </Button>
                </Link>
              </div>
            </div>

            <div className="relative rounded-2xl overflow-hidden border border-border aspect-[4/3] bg-surface-elevated">
              <img
                src="/images/hero-light.jpeg"
                alt="SpaceLoop Host Space Showcase"
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-4 left-4 right-4 p-4 rounded-xl bg-surface/90 backdrop-blur-md border border-border text-xs text-text-primary flex items-center justify-between">
                <div>
                  <p className="font-semibold">San Francisco Host</p>
                  <p className="text-text-muted">Earned $4,850 last month</p>
                </div>
                <div className="flex items-center gap-1 font-bold text-amber-500">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span>4.98</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
