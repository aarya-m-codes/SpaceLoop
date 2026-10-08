import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  ShieldCheck,
  QrCode,
  CheckCircle2,
  Lock,
  Zap,
  MapPin,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  UserCheck,
  KeyRound,
  Layers,
} from 'lucide-react';
import { Button } from '../components/common/Button';

export const HowItWorksPage = () => {
  const navigate = useNavigate();

  const STEPS = [
    {
      step: '01',
      title: 'Search & Match',
      desc: 'Filter verified micro-spaces by metro radius, hourly pricing, noise levels, and amenities like high-speed Wi-Fi and power backup.',
      icon: Search,
      color: 'text-primary',
      bg: 'bg-primary/10 border-primary/20',
    },
    {
      step: '02',
      title: 'Instant Booking & Micro-Escrow',
      desc: 'Lock in your slot instantly. An automated ₹100 UPI micro-escrow hold guarantees accountability while generating a Section 52 micro-lease.',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      step: '03',
      title: 'Geofenced Zero-Hardware Entry',
      desc: 'Arrive within 100m to unlock your dynamic QR access pass and live caretaker PIN. Zero expensive hardware or proprietary smart-locks needed.',
      icon: QrCode,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
    {
      step: '04',
      title: 'AI Inspection & Instant Settlement',
      desc: 'Check out with a quick condition photo. SpaceLoop AI validates room condition deltas, releases escrow deposits, and updates your Objective Trust Index.',
      icon: Zap,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
    },
  ];

  const PILLARS = [
    {
      title: 'Section 52 Legal Framework',
      subtitle: 'Indian Easements Act (1882)',
      desc: 'Every booking issues a non-possessory revocable license. Hosts are legally protected against tenancy claims, and seekers receive certified temporary occupancy rights.',
      icon: FileText,
    },
    {
      title: 'Zero-Hardware Access',
      subtitle: 'GPS Geofencing + Dynamic QR',
      desc: 'No expensive proprietary smart-locks required. Entry credentials activate exclusively when seeker GPS aligns with the property boundary.',
      icon: Lock,
    },
    {
      title: '₹100 Micro-Escrow Hold',
      subtitle: 'Instant Automated UPI Rail',
      desc: 'A nominal ₹100 micro-escrow is captured at checkout and programmatically released immediately upon clean checkout inspection.',
      icon: Zap,
    },
    {
      title: 'Objective Trust Index (OTI)',
      subtitle: 'Verifiable Telemetry vs Fake Reviews',
      desc: 'Replaces subjective star ratings with 4 verifiable pillars: Punctuality, Condition Match, Identity Verification, and Dispute Settlement rate.',
      icon: UserCheck,
    },
  ];

  return (
    <div className="min-h-screen bg-surface-base text-text-primary pb-24">
      {/* Top Banner */}
      <div className="relative overflow-hidden bg-surface-elevated/40 border-b border-border py-16 px-4 sm:px-6 lg:px-8 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold mb-4">
            <Sparkles className="w-4 h-4" />
            <span>The SpaceLoop Protocol</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-text-primary mb-4">
            How SpaceLoop Works
          </h1>
          <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto">
            A frictionless, zero-hardware protocol connecting seekers to verified hyper-local spaces with legal and financial safety built-in.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 space-y-16">
        {/* 4 Steps Section */}
        <div>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-text-primary">The 4-Step Guest Journey</h2>
            <p className="text-text-secondary text-sm mt-1">From initial discovery to verified exit in minutes</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {STEPS.map((s) => {
              const Icon = s.icon;
              return (
                <div
                  key={s.step}
                  className="bg-surface rounded-2xl border border-border p-6 shadow-sm flex flex-col justify-between hover:border-primary/40 transition group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="font-mono text-xs font-bold px-2 py-1 rounded-md bg-surface-elevated text-text-secondary border border-border">
                        STEP {s.step}
                      </span>
                      <div className={`p-2.5 rounded-xl border ${s.bg}`}>
                        <Icon className={`w-5 h-5 ${s.color}`} />
                      </div>
                    </div>
                    <h3 className="text-base font-bold text-text-primary mb-2 group-hover:text-primary transition-colors">
                      {s.title}
                    </h3>
                    <p className="text-xs text-text-secondary leading-relaxed">{s.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 4 Architectural Pillars */}
        <div>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-text-primary">Built On Verifiable Infrastructure</h2>
            <p className="text-text-secondary text-sm mt-1">
              Engineered with national digital rails to eliminate platform risk
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {PILLARS.map((p, idx) => {
              const Icon = p.icon;
              return (
                <div
                  key={idx}
                  className="bg-surface rounded-2xl border border-border p-6 shadow-sm flex items-start gap-4 hover:border-border-strong transition"
                >
                  <div className="p-3 rounded-xl bg-surface-elevated border border-border shrink-0">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-text-primary">{p.title}</h3>
                    <div className="text-xs font-semibold text-primary mb-2">{p.subtitle}</div>
                    <p className="text-xs text-text-secondary leading-relaxed">{p.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CTA Banner */}
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-primary/15 via-purple-500/10 to-surface-elevated border border-primary/30 text-center relative overflow-hidden">
          <h2 className="text-2xl sm:text-3xl font-black text-text-primary mb-3">
            Ready to Experience Next-Gen Space Sharing?
          </h2>
          <p className="text-sm text-text-secondary max-w-xl mx-auto mb-6">
            Join thousands of professionals, creators, and hosts across India's top metro hubs.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button
              variant="primary"
              size="lg"
              className="flex items-center gap-2 font-bold"
              onClick={() => navigate('/explore')}
            >
              Explore Spaces Now
              <ArrowRight className="w-4 h-4" />
            </Button>
            <Button
              variant="secondary"
              size="lg"
              className="font-bold"
              onClick={() => navigate('/calculator')}
            >
              Calculate Host Earnings
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorksPage;
