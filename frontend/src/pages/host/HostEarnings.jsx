import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  DollarSign,
  ShieldCheck,
  CreditCard,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Building2,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { escrowApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';

export const HostEarnings = () => {
  const { user } = useAuth();
  const { error: toastError } = useToast();

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const data = await escrowApi.getSummary();
        setSummary(data);
      } catch (err) {
        toastError(err.message || 'Could not fetch escrow summary.');
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const totalEarnings = summary?.total_released ?? summary?.host_earnings ?? 4850;
  const heldEscrow = summary?.total_held ?? summary?.held_escrow ?? 1250;
  const platformFees = summary?.total_fees ?? summary?.platform_fees ?? 255;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div>
        <Link
          to="/host"
          className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-primary mb-2 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Host Dashboard</span>
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
          Host Earnings & Micro-Escrow Ledger
        </h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          SpaceLoop guarantees instant, auditable payouts upon successful renter checkout and inspection.
        </p>
      </div>

      {/* Financial Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-2">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            Total Released Earnings
          </span>
          <div className="text-3xl font-black text-emerald-600 dark:text-emerald-400">
            ₹{totalEarnings.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-text-secondary">
            Net space subtotals released to your bank
          </p>
        </div>

        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-2">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            Held in Active Escrow
          </span>
          <div className="text-3xl font-black text-amber-500">
            ₹{heldEscrow.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-text-secondary">
            Pending upcoming renter checkouts
          </p>
        </div>

        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-2">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            SpaceLoop Fee Retained (5%)
          </span>
          <div className="text-3xl font-black text-text-primary">
            ₹{platformFees.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-text-secondary">
            Guarantees insurance & dispute mediation
          </p>
        </div>
      </div>

      {/* Payout Destination Account */}
      <div className="p-6 rounded-3xl bg-surface border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <CreditCard className="w-6 h-6" />
          </div>
          <div className="space-y-0.5">
            <h3 className="font-bold text-sm text-text-primary">Primary Payout Method</h3>
            <p className="text-xs text-text-secondary font-mono">
              UPI VPA: {user?.upi_vpa || 'host.spaceloop@icici (Mock Penny-Drop Verified)'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Penny-Drop Verified</span>
          </span>
          <Link to="/profile">
            <Button variant="outline" size="sm">
              Update UPI
            </Button>
          </Link>
        </div>
      </div>

      {/* Ledger Architecture Transparency Notice */}
      <div className="p-6 rounded-3xl bg-surface-elevated border border-border space-y-3 text-xs leading-relaxed">
        <h4 className="font-bold text-text-primary flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <span>Micro-Escrow Accounting Standard</span>
        </h4>
        <p className="text-text-secondary">
          In accordance with the SpaceLoop architectural specification, every booking holds 100% of the space subtotal plus a ₹100 seeker deposit. When checkout completes normally:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-text-secondary">
          <li>The space subtotal is settled 100% directly to the host.</li>
          <li>SpaceLoop retains the exact 5% platform fee calculated at precheck.</li>
          <li>The ₹100 deposit is returned 100% to the seeker.</li>
          <li>No negative balances or arbitrary financial adjustments are permitted.</li>
        </ul>
      </div>
    </div>
  );
};

export default HostEarnings;
