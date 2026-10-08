import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Compass,
  Layers,
  Shield,
  Cpu,
  Terminal,
  Activity,
  Check,
  Mail,
  Linkedin,
  ExternalLink,
  X,
  Sparkles,
  Zap,
  Lock,
  ArrowRight,
  Database,
  FileText,
  Server,
} from 'lucide-react';
import { Button } from '../components/common/Button';

const TEAM_MEMBERS = [
  {
    id: 'architect-aarya',
    badgeNumber: '01',
    name: 'Aarya Maurya',
    role: 'System Architect & Security Lead',
    domain: 'Zero-Trust Boundary, DPDP Act 2023 & Fraud Prevention',
    intro:
      'Architected SpaceLoop’s zero-trust security perimeter, DPDP Act 2023 tokenized Aadhaar identity verification, and multi-tier fraud & collusion detection engine.',
    email: 'mauryaaarya13@gmail.com',
    linkedin:
      'https://www.linkedin.com/in/aarya-maurya-49b467320?utm_source=share_via&utm_content=profile&utm_medium=member_android',
    photoUrl: '/team/aarya.jpg',
    accentColor: 'from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-400',
    subsystem: {
      title: 'Zero-Trust Defense & Multi-Tier Anomaly Engine',
      codename: 'SEC-ZERO-TRUST-SHIELD',
      metric: {
        label: 'Audit Security',
        value: '100%',
      },
      highlights: [
        'DPDP Act 2023 compliant zero-raw-storage tokenization pipeline hashing Aadhaar OTP credentials via SHA-256 salts.',
        '26-feature Isolation Forest unsupervised anomaly detection layer trained on tabular behavior metrics.',
        'Strict IDOR protection, sliding-window rate limiters, session cookie regeneration, and immutable audit telemetry.',
      ],
      techStack: ['Zero-Trust', 'Isolation Forest', 'Scikit-Learn', 'DigiLocker', 'DPDP Act 2023', 'NetworkX'],
    },
  },
  {
    id: 'architect-kanishk',
    badgeNumber: '02',
    name: 'Kanishk Singh',
    role: 'Founding Architect & Backend Lead',
    domain: 'High-Concurrency WSGI Services & Section 52 Protocol',
    intro:
      'Engineered SpaceLoop’s high-performance Flask 3.0 backend, Section 52 revocable micro-leasing protocol under the Indian Easements Act (1882), automated ₹100 UPI micro-escrow holds, and hybrid semantic search engine.',
    email: 'kanishksingh0005@gmail.com',
    linkedin:
      'https://www.linkedin.com/in/kanishk-singh-a10a38315?utm_source=share_via&utm_content=profile&utm_medium=member_android',
    photoUrl: '/team/kanishk.png',
    accentColor: 'from-indigo-500/20 to-blue-500/20 border-indigo-500/30 text-indigo-400',
    subsystem: {
      title: 'Section 52 Engine & UPI Micro-Escrow',
      codename: 'CORE-WSGI-TRANSACT',
      metric: {
        label: 'P95 API Latency',
        value: '28ms',
      },
      highlights: [
        'Section 52 Indian Easements Act legal framework generating instant enforceable temporary space licenses.',
        'Automated ₹100 UPI micro-escrow hold protocol with instant conditional release upon GPS and QR checkout.',
        'Scalable Flask 3.0 WSGI architecture pre-configured with SQLite WAL concurrency and PostgreSQL containers.',
      ],
      techStack: ['Python 3.11', 'Flask 3.0', 'SQLAlchemy Core', 'PostgreSQL', 'UPI / NPCI API', 'Docker'],
    },
  },
  {
    id: 'architect-zara',
    badgeNumber: '03',
    name: 'Zara Quadri',
    role: 'Frontend / UI-UX Lead Developer',
    domain: 'High-Fidelity React Systems & Interactive HUDs',
    intro:
      'Crafted SpaceLoop’s responsive React 18 client architecture, Ocean Breeze and Midnight design systems, tactile glassmorphic controls, and mobile navigation HUD.',
    email: 'zeequadriworks@gmail.com',
    linkedin:
      'https://www.linkedin.com/in/zara-quadri-122b54411?utm_source=share_via&utm_content=profile&utm_medium=member_android',
    photoUrl: '/team/zara.jpg',
    accentColor: 'from-violet-500/20 to-purple-500/20 border-violet-500/30 text-violet-400',
    subsystem: {
      title: 'Reactive Viewport & Dual-Theme System',
      codename: 'UI-REACT-VIEWPORT',
      metric: {
        label: 'Lighthouse Score',
        value: '99/100',
      },
      highlights: [
        'Zero-overflow mobile HUD interface featuring synchronized session timers, passes, and offline credentials.',
        'Dual-palette design token system powering Ocean Breeze and Midnight Neon palettes.',
        'Interactive geospatial explore view with dynamic radius slider, category chips, and instant listing preview cards.',
      ],
      techStack: ['React 18', 'TypeScript', 'Tailwind CSS', 'Vite 6', 'Lucide Icons', 'HTML5 Canvas'],
    },
  },
  {
    id: 'architect-rohit',
    badgeNumber: '04',
    name: 'Rohit Pal',
    role: 'AI / ML & Computer Vision Specialist',
    domain: 'Multimodal Room Vision & Section 52 Matching Engine',
    intro:
      'Leads SpaceLoop’s multimodal computer vision and spatial intelligence pipeline. Architected the post-occupancy room condition delta analyzer, automatic electrical appliance off-detection, and the Groq + Gemini dual-engine intent parser.',
    email: 'rohitpal.dev@gmail.com',
    linkedin: 'https://www.linkedin.com/in/rohit-pal',
    photoUrl: '/team/rohit.jpg',
    accentColor: 'from-cyan-500/20 to-teal-500/20 border-cyan-500/30 text-cyan-400',
    subsystem: {
      title: 'Multimodal Room Vision & Semantic Matcher',
      codename: 'CV-ROOM-DELTA-SCAN',
      metric: {
        label: 'CV Accuracy',
        value: '96.4%',
      },
      highlights: [
        'Computer vision delta inspection comparing check-in vs check-out photos for furniture arrangement and waste.',
        'Automated energy efficiency detection verifying that fans, lights, and appliances are switched off before exit.',
        'Dual Groq Llama-3 + Gemini Pro natural language semantic parser mapping ambiguous seeker queries to listings.',
      ],
      techStack: ['Computer Vision', 'PyTorch', 'Gemini Pro', 'Groq Llama-3', 'Embeddings', 'OpenCV'],
    },
  },
];

export const ArchitecturePage = () => {
  const navigate = useNavigate();
  const [activeMember, setActiveMember] = useState(null);
  const [copiedEmail, setCopiedEmail] = useState(null);

  const handleCopyEmail = (email, id) => {
    navigator.clipboard.writeText(email);
    setCopiedEmail(id);
    setTimeout(() => setCopiedEmail(null), 2500);
  };

  return (
    <div className="min-h-screen bg-surface-base text-text-primary pb-24">
      {/* Blueprint Hero Section */}
      <div className="relative overflow-hidden bg-surface-elevated/40 border-b border-border py-16 px-4 sm:px-6 lg:px-8 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold mb-4">
            <Layers className="w-4 h-4" />
            <span>LogicLoop Architectural Blueprint</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-text-primary mb-4">
            System Architecture & Founding Team
          </h1>
          <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto">
            Engineered by Team LogicLoop at Hack2Ignite 2026. A production-grade distributed architecture merging the Indian Easements Act, India Stack digital rails, and zero-trust telemetry.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <a
              href="https://spaceloop.onrender.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-primary/90 shadow-sm transition"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Live Demo (Render)</span>
            </a>
            <a
              href="https://spaceloop.vercel.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-semibold text-text-primary transition"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Vercel Edge Deployment</span>
            </a>
            <a
              href="https://github.com/kanishksingh-01/spaceloop"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-semibold text-text-primary transition"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>GitHub Repository</span>
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 space-y-16">
        {/* Architect Profiles Grid */}
        <div>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-text-primary">The Architectural Core</h2>
            <p className="text-text-secondary text-sm mt-1">Lead engineers and subsystem owners</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {TEAM_MEMBERS.map((member) => (
              <div
                key={member.id}
                className="bg-surface rounded-2xl border border-border overflow-hidden shadow-sm flex flex-col justify-between hover:border-primary/40 transition group"
              >
                <div>
                  <div className="relative h-64 overflow-hidden bg-surface-elevated">
                    <img
                      src={member.photoUrl}
                      alt={member.name}
                      className="w-full h-full object-cover object-top group-hover:scale-105 transition duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-transparent" />
                    <span className="absolute top-3 right-3 font-mono text-[11px] font-bold px-2.5 py-1 rounded-full bg-surface/90 text-text-primary border border-border backdrop-blur-md">
                      #{member.badgeNumber}
                    </span>
                  </div>

                  <div className="p-5">
                    <h3 className="text-lg font-bold text-text-primary group-hover:text-primary transition-colors">
                      {member.name}
                    </h3>
                    <div className="text-xs font-semibold text-primary mt-0.5">{member.role}</div>
                    <p className="text-xs text-text-secondary mt-3 leading-relaxed line-clamp-3">
                      {member.intro}
                    </p>
                  </div>
                </div>

                <div className="p-5 pt-0 border-t border-border/50 mt-2">
                  <div className="flex items-center justify-between text-xs py-2">
                    <span className="text-text-muted">{member.subsystem.metric.label}:</span>
                    <span className="font-mono font-bold text-emerald-400">
                      {member.subsystem.metric.value}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <button
                      type="button"
                      onClick={() => setActiveMember(member)}
                      className="flex-1 py-1.5 px-3 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-semibold text-text-primary transition text-center"
                    >
                      Subsystem Specs
                    </button>

                    <button
                      type="button"
                      onClick={() => handleCopyEmail(member.email, member.id)}
                      className="p-1.5 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-text-secondary hover:text-text-primary transition"
                      title={copiedEmail === member.id ? 'Copied!' : member.email}
                    >
                      {copiedEmail === member.id ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Mail className="w-4 h-4" />
                      )}
                    </button>

                    <a
                      href={member.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-xl bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-text-secondary hover:text-primary transition"
                    >
                      <Linkedin className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Distributed Architectural Blueprint Diagram */}
        <div className="bg-surface rounded-2xl border border-border p-8 shadow-sm space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
            <div>
              <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                <Server className="w-5 h-5 text-primary" />
                SpaceLoop Protocol — Multi-Tier System Blueprint
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                From Seeker Mobile HUD to Government Digital Verification Rails
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold font-mono">
                P95 &lt; 30ms
              </span>
              <span className="px-2.5 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-bold font-mono">
                Zero-Trust
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1: Client Edge */}
            <div className="p-5 rounded-xl bg-surface-elevated border border-border space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                <Compass className="w-4 h-4" />
                Tier 1: Client & Viewport Edge
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                React 18 + TailwindCSS + Vite single-page application. Features responsive mobile navigation HUD, offline-first arrival pass caching, real-time session countdown timers, and client-side GPS geofencing.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {['React 18', 'TailwindCSS', 'Framer Motion', 'Lucide Icons', 'HTML5 Geolocation'].map((t) => (
                  <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface border border-border text-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Tier 2: WSGI Core & Engines */}
            <div className="p-5 rounded-xl bg-surface-elevated border border-border space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <Terminal className="w-4 h-4" />
                Tier 2: WSGI Core & Multi-Engine Suite
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                High-concurrency Flask 3.0 runtime powering the 22-method Space AI intelligence engine, Section 52 micro-leasing agreement generator, RFC 6238 TOTP MFA authenticator, and automated ₹100 UPI micro-escrow ledger.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {['Flask 3.0', 'SQLAlchemy Core', 'SQLite WAL', 'PostgreSQL', 'RFC 6238 TOTP'].map((t) => (
                  <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface border border-border text-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Tier 3: National Rails & Vision */}
            <div className="p-5 rounded-xl bg-surface-elevated border border-border space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-400">
                <Shield className="w-4 h-4" />
                Tier 3: National Rails & ML Vision
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Integrated with India Stack rails: UIDAI DigiLocker OTP with DPDP Act 2023 tokenization, NPCI UPI penny-drop bank account validation, State Discom BBPS consumer inspection, and Computer Vision room condition delta scans.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {['UIDAI DigiLocker', 'NPCI UPI', 'State Discom BBPS', 'Isolation Forest', 'PyTorch / OpenCV'].map((t) => (
                  <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface border border-border text-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Subsystem Inspection Modal */}
      <AnimatePresence>
        {activeMember && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-surface rounded-2xl border border-border max-w-lg w-full p-6 shadow-2xl relative space-y-5"
            >
              <button
                type="button"
                onClick={() => setActiveMember(null)}
                className="absolute top-4 right-4 p-1.5 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 text-text-muted hover:text-text-primary transition"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3">
                <img
                  src={activeMember.photoUrl}
                  alt={activeMember.name}
                  className="w-12 h-12 rounded-xl object-cover border border-border"
                />
                <div>
                  <h3 className="text-base font-bold text-text-primary">{activeMember.name}</h3>
                  <div className="text-xs font-semibold text-primary">{activeMember.role}</div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-elevated border border-border">
                <div className="text-[11px] font-mono uppercase text-text-muted">Subsystem Codename</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                  {activeMember.subsystem.codename}
                </div>
                <div className="text-xs text-text-primary font-semibold mt-1">
                  {activeMember.subsystem.title}
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-text-primary uppercase tracking-wider mb-2">
                  Key Architectural Contributions
                </div>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {activeMember.subsystem.highlights.map((h, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-primary font-bold">•</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="text-xs font-bold text-text-primary uppercase tracking-wider mb-2">
                  Engineered With
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {activeMember.subsystem.techStack.map((tech) => (
                    <span
                      key={tech}
                      className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-surface-elevated border border-border text-text-primary"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ArchitecturePage;
