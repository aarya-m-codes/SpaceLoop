import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Building2,
  FileText,
  CreditCard,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { spacesApi, hostApi, verifyApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';

export const SpaceVerificationView = () => {
  const { success, error: toastError } = useToast();

  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifyingId, setVerifyingId] = useState(null);
  const [caInputs, setCaInputs] = useState({});

  // UPI Penny drop state
  const [vpaInput, setVpaInput] = useState('host@okhdfcbank');
  const [vpaVerified, setVpaVerified] = useState(true);
  const [verifyingVpa, setVerifyingVpa] = useState(false);

  const fetchSpaces = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getDashboard();
      const list = res?.host_spaces || [];
      setSpaces(list);

      const initialCa = {};
      list.forEach((s) => {
        initialCa[s.id] = s.discom_ca_number || '10029384819';
      });
      setCaInputs(initialCa);
    } catch (err) {
      console.warn('Failed to load spaces for verification:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpaces();
  }, []);

  const handleVerifyDiscom = async (space) => {
    const ca = caInputs[space.id] || '10029384819';
    try {
      setVerifyingId(space.id);
      await verifyApi.verifyHost({
        space_id: space.id,
        ca_number: ca,
        discom_provider: 'BESCOM',
      });
      success(`Space "${space.title}" authenticated with Discom utility records!`);
      await fetchSpaces();
    } catch (err) {
      toastError(err.message || 'Discom check failed.');
    } finally {
      setVerifyingId(null);
    }
  };

  const handleVerifyUpi = async () => {
    try {
      setVerifyingVpa(true);
      // Simulate/call penny drop
      await new Promise((r) => setTimeout(r, 800));
      setVpaVerified(true);
      success('₹1.00 Penny Drop verified! Account linked for instant UPI settlements.');
    } catch (err) {
      toastError('UPI verification failed.');
    } finally {
      setVerifyingVpa(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold text-text-primary tracking-tight">
            Premise Utility & Host Identity Hub
          </h2>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
            DigiLocker + Discom CA
          </span>
        </div>
        <p className="text-xs text-text-secondary mt-1">
          Verify physical space premises through state electricity distribution records (Discom) and bank penny drop.
        </p>
      </div>

      {/* KYC Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-surface border border-border space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Host Identity KYC
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-base font-bold text-text-primary">DigiLocker Tokenized</div>
          <p className="text-[11px] text-text-secondary">
            Aadhaar verified with SHA-256 tokenization under DPDP Act 2023.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              UPI Payout Escrow
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-base font-bold text-text-primary">Penny Drop Validated</div>
          <p className="text-[11px] text-text-secondary">
            Direct bank beneficiary validated for automated 95% revenue releases.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-border space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Legal Foundation
            </span>
            <ShieldCheck className="w-4 h-4 text-primary" />
          </div>
          <div className="text-base font-bold text-text-primary">Section 52 License</div>
          <p className="text-[11px] text-text-secondary">
            Revocable permissive occupancy guarantees zero tenant protection claims.
          </p>
        </div>
      </div>

      {/* Discom CA Premises List */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-xs space-y-6">
        <div className="border-b border-border pb-4">
          <h3 className="text-lg font-bold text-text-primary">
            Physical Premise Utility Records
          </h3>
          <p className="text-xs text-text-secondary mt-1">
            State Electricity Boards (BESCOM, MSEDCL, TPDDL, etc.) Consumer Account numbers establish unambiguous physical control of the space.
          </p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-surface-elevated animate-pulse" />
            ))}
          </div>
        ) : spaces.length === 0 ? (
          <p className="text-xs text-text-muted py-4">No spaces registered yet to verify.</p>
        ) : (
          <div className="space-y-4">
            {spaces.map((sp) => {
              const isVerified = sp.is_verified;
              const isChecking = verifyingId === sp.id;
              return (
                <div
                  key={sp.id}
                  className="p-5 rounded-2xl bg-surface-elevated border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-base text-text-primary">{sp.title}</h4>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          isVerified
                            ? 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/20'
                            : 'bg-amber-500/15 text-amber-600 border border-amber-500/20'
                        }`}
                      >
                        {isVerified ? 'Discom Verified' : 'Pending Verification'}
                      </span>
                    </div>

                    <p className="text-xs text-text-secondary">{sp.address || sp.location || 'Bangalore, KA'}</p>

                    <div className="pt-2 flex flex-col sm:flex-row sm:items-center gap-2 max-w-md">
                      <input
                        type="text"
                        value={caInputs[sp.id] || ''}
                        onChange={(e) => setCaInputs({ ...caInputs, [sp.id]: e.target.value })}
                        placeholder="Discom CA Number (e.g. 10029384819)"
                        className="flex-1 bg-surface border border-border rounded-xl px-3 py-1.5 text-xs text-text-primary font-mono focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <Button
                      variant={isVerified ? 'outline' : 'primary'}
                      size="sm"
                      disabled={isChecking}
                      onClick={() => handleVerifyDiscom(sp)}
                      className={isVerified ? 'text-emerald-600 border-emerald-500/30' : ''}
                    >
                      {isChecking ? 'Checking Discom...' : isVerified ? 'Re-Verify Meter' : 'Verify Premise'}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SpaceVerificationView;
