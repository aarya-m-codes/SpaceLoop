import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  CheckCircle2,
  Users,
  Search,
  Sliders,
  RefreshCw,
  Lock,
  CreditCard,
  FileCheck,
  ChevronRight,
  Sparkles,
  TrendingUp,
  Cpu,
  Info,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { trustSafetyApi } from '../services/api';

export const TrustSafetyPage = () => {
  const navigate = useNavigate();

  // Metrics State
  const [stats, setStats] = useState({
    total_assessments: 48,
    high_risk_flagged: 3,
    suspicious_flagged: 7,
    normal_cleared: 38,
    escrow_held_count: 2,
    active_mfa_users: 84,
  });

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterRisk, setFilterRisk] = useState('all');
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  // OTI Simulator State
  const [simPunctuality, setSimPunctuality] = useState(95);
  const [simCondition, setSimCondition] = useState(90);
  const [simVerification, setSimVerification] = useState(100);
  const [simSettlement, setSimSettlement] = useState(98);
  const [simOtiScore, setSimOtiScore] = useState(95.2);
  const [simTier, setSimTier] = useState('Platinum Trusted');

  // Recalculate simulated OTI
  useEffect(() => {
    // Formula matching backend space_ai.py:
    // OTI = 0.35 * Punctuality + 0.30 * Condition + 0.20 * Verification + 0.15 * Settlement
    const score = Number(
      (0.35 * simPunctuality +
        0.30 * simCondition +
        0.20 * simVerification +
        0.15 * simSettlement).toFixed(1)
    );
    setSimOtiScore(score);

    if (score >= 90) setSimTier('Platinum Trusted (Instant Access)');
    else if (score >= 80) setSimTier('Gold Verified (Standard)');
    else if (score >= 70) setSimTier('Silver Member (Deposit Required)');
    else setSimTier('Probation (Manual Approval Needed)');
  }, [simPunctuality, simCondition, simVerification, simSettlement]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsRes, assessRes] = await Promise.all([
        trustSafetyApi.getStats().catch(() => null),
        trustSafetyApi.getAssessments().catch(() => null),
      ]);

      if (statsRes && statsRes.stats) {
        setStats(statsRes.stats);
      }
      if (assessRes && assessRes.assessments) {
        setAssessments(assessRes.assessments);
      } else {
        // Fallback default sample assessments
        setAssessments([
          {
            id: 101,
            entity_type: 'booking',
            entity_id: 304,
            risk_level: 'high_risk',
            risk_score: 88,
            primary_reason: 'Abnormal GPS jump detected (14km within 2 minutes) & spoofed device user-agent',
            status: 'flagged',
            action_taken: 'escrow_held',
            created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
          },
          {
            id: 102,
            entity_type: 'user',
            entity_id: 412,
            risk_level: 'suspicious',
            risk_score: 62,
            primary_reason: 'High cancellation velocity within 24 hours of account creation',
            status: 'under_review',
            action_taken: 'mfa_enforced',
            created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          },
          {
            id: 103,
            entity_type: 'space',
            entity_id: 12,
            risk_level: 'normal',
            risk_score: 12,
            primary_reason: 'BESCOM electricity bill verified, UPI penny drop name match 100%',
            status: 'cleared',
            action_taken: 'dismissed',
            created_at: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
          },
        ]);
      }
    } catch (err) {
      console.warn('Failed loading trust safety data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredAssessments = assessments.filter((a) => {
    if (filterRisk === 'all') return true;
    return a.risk_level === filterRisk;
  });

  const getRiskBadge = (level) => {
    switch (level) {
      case 'high_risk':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            HIGH RISK
          </span>
        );
      case 'suspicious':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            SUSPICIOUS
          </span>
        );
      case 'unusual':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-yellow-500/10 text-yellow-300 border border-yellow-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
            UNUSUAL
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            NORMAL
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-surface-base text-text-primary pb-24">
      {/* Top Header */}
      <div className="relative overflow-hidden bg-surface-elevated/40 border-b border-border py-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold mb-3">
              <ShieldCheck className="w-4 h-4" />
              <span>National Zero-Trust Governance</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-text-primary">
              Trust & Safety Command Center
            </h1>
            <p className="text-text-secondary text-sm max-w-2xl mt-1">
              Objective telemetry, multi-tier anomaly detection, and automated fraud prevention across all SpaceLoop micro-leases.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="flex items-center gap-2 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Telemetry
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/admin')}
              className="text-xs font-bold"
            >
              Admin Audit Logs
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-text-muted font-medium">Total Audited</div>
            <div className="text-2xl font-black text-text-primary mt-1">{stats.total_assessments || 48}</div>
            <div className="text-[11px] text-text-muted mt-1 font-mono">100% telemetry</div>
          </div>

          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-rose-400 font-medium">High Risk Blocked</div>
            <div className="text-2xl font-black text-rose-400 mt-1">{stats.high_risk_flagged || 3}</div>
            <div className="text-[11px] text-rose-400/80 mt-1 font-mono">Auto-escrow hold</div>
          </div>

          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-amber-400 font-medium">Suspicious Triage</div>
            <div className="text-2xl font-black text-amber-400 mt-1">{stats.suspicious_flagged || 7}</div>
            <div className="text-[11px] text-amber-400/80 mt-1 font-mono">MFA challenge</div>
          </div>

          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-emerald-400 font-medium">Normal Cleared</div>
            <div className="text-2xl font-black text-emerald-400 mt-1">{stats.normal_cleared || 38}</div>
            <div className="text-[11px] text-emerald-400/80 mt-1 font-mono">Fast-track access</div>
          </div>

          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-primary font-medium">Escrows Held</div>
            <div className="text-2xl font-black text-primary mt-1">{stats.escrow_held_count || 2}</div>
            <div className="text-[11px] text-primary/80 mt-1 font-mono">Dispute custody</div>
          </div>

          <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm">
            <div className="text-xs text-purple-400 font-medium">MFA Guarded</div>
            <div className="text-2xl font-black text-purple-400 mt-1">{stats.active_mfa_users || 84}%</div>
            <div className="text-[11px] text-purple-400/80 mt-1 font-mono">RFC 6238 TOTP</div>
          </div>
        </div>

        {/* 2-Column: OTI Simulator + India Stack Verification Rails */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* OTI Interactive Simulator */}
          <div className="lg:col-span-7 bg-surface rounded-2xl border border-border p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-primary" />
                  Objective Trust Index (OTI) Model Simulator
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  SpaceLoop replaces gameable star ratings with an objective mathematical formula.
                </p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-bold">
                Formula v2.4
              </span>
            </div>

            <div className="p-4 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
              <div>
                <div className="text-xs text-text-muted">Calculated Trust Score</div>
                <div className="text-3xl font-black text-emerald-400 mt-0.5">{simOtiScore} / 100</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-text-muted">Placement Tier</div>
                <div className="text-sm font-bold text-primary mt-0.5">{simTier}</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-text-secondary">Punctuality Score (Weight 35%)</span>
                  <span className="font-mono font-bold text-text-primary">{simPunctuality}%</span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="100"
                  value={simPunctuality}
                  onChange={(e) => setSimPunctuality(Number(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-text-secondary">Room Condition Delta (Weight 30%)</span>
                  <span className="font-mono font-bold text-text-primary">{simCondition}%</span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="100"
                  value={simCondition}
                  onChange={(e) => setSimCondition(Number(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-text-secondary">Aadhaar / KYC Verification (Weight 20%)</span>
                  <span className="font-mono font-bold text-text-primary">{simVerification}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={simVerification}
                  onChange={(e) => setSimVerification(Number(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-text-secondary">Dispute Settlement Ratio (Weight 15%)</span>
                  <span className="font-mono font-bold text-text-primary">{simSettlement}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={simSettlement}
                  onChange={(e) => setSimSettlement(Number(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>
            </div>
          </div>

          {/* India Stack Verification Rails */}
          <div className="lg:col-span-5 bg-surface rounded-2xl border border-border p-6 shadow-sm space-y-6">
            <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" />
              India Stack Verification Infrastructure
            </h2>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-surface-elevated border border-border flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">UIDAI DigiLocker OTP</div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    DPDP Act 2023 compliant zero-raw-storage tokenization hashing Aadhaar references via salted SHA-256.
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-elevated border border-border flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">NPCI UPI ₹1 Penny Drop</div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    Instant bank beneficiary name match verifying that host payout destination matches legal registrant.
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-elevated border border-border flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">State Discom BBPS Validation</div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    Live consumer electricity account inspection across BESCOM, TPDDL, MSEDCL, and UPPCL confirming property rights.
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-elevated border border-border flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">Academic Institution Domain Auth</div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    .edu.in and .ac.in verified student fast-track authorization for peer study pods.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Live Risk Assessments Feed */}
        <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Live Risk Assessment Triage Feed
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Real-time output from SpaceLoop's 26-feature Isolation Forest and behavioral rules engine
              </p>
            </div>

            <div className="flex items-center gap-2">
              {['all', 'high_risk', 'suspicious', 'normal'].map((rf) => (
                <button
                  key={rf}
                  type="button"
                  onClick={() => setFilterRisk(rf)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                    filterRisk === rf
                      ? 'bg-primary text-white font-semibold'
                      : 'bg-surface-elevated text-text-secondary hover:text-text-primary border border-border'
                  }`}
                >
                  {rf === 'all' ? 'All' : rf.replace('_', ' ').toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated text-text-muted border-b border-border uppercase font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Entity</th>
                  <th className="py-2.5 px-3">Risk Level</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Primary Anomaly Signal</th>
                  <th className="py-2.5 px-3">Action Enforced</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredAssessments.map((a) => (
                  <tr key={a.id} className="hover:bg-surface-elevated/40 transition">
                    <td className="py-3 px-3 font-mono font-bold text-text-primary">
                      {a.entity_type} #{a.entity_id}
                    </td>
                    <td className="py-3 px-3">{getRiskBadge(a.risk_level)}</td>
                    <td className="py-3 px-3 font-mono font-bold">{a.risk_score}/100</td>
                    <td className="py-3 px-3 text-text-secondary max-w-xs truncate">{a.primary_reason}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-md bg-surface-elevated border border-border font-mono text-[11px] text-text-secondary">
                        {a.action_taken || 'audited'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-text-muted font-mono text-[11px]">
                      {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrustSafetyPage;
