import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  Flame,
  Activity,
  Users,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Bot,
  RefreshCw,
  Eye,
  GitBranch,
} from 'lucide-react';
import { trustSafetyApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';
import { ErrorState } from '../../components/common/ErrorState';

export const AdminDashboard = () => {
  const { user, isAdmin } = useAuth();
  const { success, error: toastError } = useToast();

  const [activeTab, setActiveTab] = useState('assessments'); // 'assessments' | 'alerts' | 'evaluator'
  const [assessments, setAssessments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Evaluator Interactive Form
  const [evalEntityType, setEvalEntityType] = useState('user');
  const [evalEntityId, setEvalEntityId] = useState('1');
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const [assessRes, alertsRes] = await Promise.allSettled([
        trustSafetyApi.getAssessments(),
        trustSafetyApi.getFraudAlerts(),
      ]);

      if (assessRes.status === 'fulfilled') {
        setAssessments(assessRes.value.assessments || (Array.isArray(assessRes.value) ? assessRes.value : []));
      }
      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.alerts || (Array.isArray(alertsRes.value) ? alertsRes.value : []));
      }
    } catch (err) {
      toastError(err.message || 'Could not load Trust & Safety assessments.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRunEvaluation = async (e) => {
    e.preventDefault();
    setEvaluating(true);
    setEvaluationResult(null);

    try {
      const res = await trustSafetyApi.evaluate({
        entity_type: evalEntityType,
        entity_id: evalEntityId,
      });
      setEvaluationResult(res);
      success('Trust & Safety bipartite graph evaluation completed!');
      await fetchAdminData();
    } catch (err) {
      toastError(err.message || 'Risk evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  if (!isAdmin && !(user?.is_admin || user?.role === 'admin')) {
    return (
      <div className="py-24 px-4">
        <ErrorState
          type="unauthorized"
          title="Admin Authorization Required"
          description="Access to Marketplace Trust & Safety and the Autonomous ML Fraud Engine is restricted to platform administrators."
          actionText="Return to Explore"
          actionFn={() => (window.location.href = '/explore')}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Admin Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold text-text-primary tracking-tight">
              Trust, Safety & Fraud Operations
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-600 text-white">
              Admin Restricted
            </span>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Dual architecture: Marketplace Trust & Safety (System A) + Autonomous ML Anomaly Engine (System B).
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchAdminData}
          className="flex items-center gap-1.5"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Telemetry</span>
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border text-xs font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab('assessments')}
          className={`px-4 py-2.5 rounded-xl transition-all ${
            activeTab === 'assessments'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          System A: Behavioral Assessments ({assessments.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2.5 rounded-xl transition-all ${
            activeTab === 'alerts'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          System B: ML Fraud Alerts ({alerts.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('evaluator')}
          className={`px-4 py-2.5 rounded-xl transition-all ${
            activeTab === 'evaluator'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          Run On-Demand Evaluation
        </button>
      </div>

      {/* Tab 1: Assessments */}
      {activeTab === 'assessments' && (
        <div className="space-y-4">
          <h2 className="text-base font-bold text-text-primary">
            Marketplace Trust & Safety Assessments
          </h2>
          {assessments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {assessments.map((item, idx) => {
                const riskScore = item.risk_score ?? item.score ?? 0;
                const status = (item.status || 'review').toLowerCase();
                const signals = item.signals || item.behavioral_signals || [];

                return (
                  <div
                    key={idx}
                    className="p-5 rounded-3xl bg-surface border border-border space-y-3 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-text-muted">
                        Entity: {item.entity_type || 'user'} #{item.entity_id}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          riskScore >= 0.8
                            ? 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
                            : riskScore >= 0.6
                            ? 'bg-amber-500/10 text-amber-600 border border-amber-500/20'
                            : riskScore >= 0.4
                            ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20'
                            : 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                        }`}
                      >
                        Risk: {(riskScore * 100).toFixed(0)}% •{' '}
                        {riskScore >= 0.8
                          ? 'BLOCK'
                          : riskScore >= 0.6
                          ? 'HOLD/REVIEW'
                          : riskScore >= 0.4
                          ? 'CHALLENGE'
                          : 'ALLOW'}
                      </span>
                    </div>

                    <p className="text-xs text-text-secondary leading-relaxed">
                      {item.forensic_narrative || item.explanation || 'No anomalies detected.'}
                    </p>

                    {signals.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {signals.map((sig, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded-md bg-surface-elevated border border-border text-[10px] font-mono text-rose-500"
                          >
                            {sig}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-8 rounded-2xl bg-surface border border-border text-center text-xs text-text-secondary">
              No active assessments recorded yet. Run an evaluation below to inspect user or space graph cycles.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Fraud Alerts */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <h2 className="text-base font-bold text-text-primary">
            System B: Autonomous ML Anomaly Alerts
          </h2>
          {alerts.length > 0 ? (
            <div className="divide-y divide-border border border-border rounded-2xl overflow-hidden bg-surface">
              {alerts.map((al, idx) => (
                <div key={idx} className="p-4 flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-text-primary">{al.alert_type || 'ANOMALY_SPIKE'}</span>
                      <span className="text-[10px] text-text-muted">{al.created_at || 'Recent'}</span>
                    </div>
                    <p className="text-text-secondary">{al.message || al.description}</p>
                  </div>
                  <span className="font-mono font-bold text-rose-500 text-sm">
                    Score: {al.anomaly_score || al.score || '0.74'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 rounded-2xl bg-surface border border-border text-center text-xs text-text-secondary">
              No high-severity ML fraud anomalies reported. System is within normal baseline.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Interactive Evaluator */}
      {activeTab === 'evaluator' && (
        <div className="p-8 rounded-3xl bg-surface border border-border space-y-6 max-w-2xl">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Run Graph Risk Assessment</h2>
            <p className="text-xs text-text-secondary mt-1">
              Evaluates collusion loops, velocity spikes, self-bookings, device reuse, and discom mismatches.
            </p>
          </div>

          <form onSubmit={handleRunEvaluation} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Entity Type</label>
                <select
                  value={evalEntityType}
                  onChange={(e) => setEvalEntityType(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                >
                  <option value="user">User</option>
                  <option value="space">Space</option>
                  <option value="booking">Booking</option>
                  <option value="device">Device</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Entity ID</label>
                <input
                  type="text"
                  required
                  value={evalEntityId}
                  onChange={(e) => setEvalEntityId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-mono"
                />
              </div>
            </div>

            <Button type="submit" variant="primary" size="sm" disabled={evaluating}>
              {evaluating ? 'Analyzing Graph Cycles...' : 'Run Forensic Evaluation'}
            </Button>
          </form>

          {evaluationResult && (
            <div className="p-5 rounded-2xl bg-surface-elevated border border-border space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-text-primary text-sm">Evaluation Output</span>
                <span className="font-mono text-xs font-bold text-primary">
                  Decision: {evaluationResult.decision || 'ALLOW'}
                </span>
              </div>
              <p className="text-text-secondary leading-relaxed">
                {evaluationResult.forensic_narrative || evaluationResult.explanation || 'Verified normal activity.'}
              </p>
              <pre className="p-3 rounded-xl bg-zinc-950 text-emerald-400 font-mono text-[10px] overflow-x-auto">
                {JSON.stringify(evaluationResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
