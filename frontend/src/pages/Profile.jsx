import React, { useState } from 'react';
import {
  User,
  ShieldCheck,
  GraduationCap,
  KeyRound,
  Lock,
  Building2,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Zap,
  Sparkles,
  CreditCard,
  Hash,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authApi } from '../services/api';
import { Button } from '../components/common/Button';

export const Profile = () => {
  const { user, activeRole, switchContext, verifyStudent, verifyAadhaar, verifyHost, refreshUser } = useAuth();
  const { success, error: toastError } = useToast();

  // Student verification form state
  const [studentId, setStudentId] = useState('');
  const [universityEmail, setUniversityEmail] = useState('');
  const [verifyingStudent, setVerifyingStudent] = useState(false);

  // Aadhaar verification form state
  const [aadhaarNumber, setAadhaarNumber] = useState('');
  const [verifyingAadhaar, setVerifyingAadhaar] = useState(false);

  // Host DISCOM & UPI verification form state
  const [consumerNumber, setConsumerNumber] = useState('');
  const [discomProvider, setDiscomProvider] = useState('BESCOM');
  const [hostUpiVpa, setHostUpiVpa] = useState('');
  const [verifyingHost, setVerifyingHost] = useState(false);

  // MFA State
  const [mfaData, setMfaData] = useState(null);
  const [mfaOtp, setMfaOtp] = useState('');
  const [settingUpMfa, setSettingUpMfa] = useState(false);
  const [mfaPassword, setMfaPassword] = useState('');
  const [mfaDisableOtp, setMfaDisableOtp] = useState('');
  const [activeRecoveryCodes, setActiveRecoveryCodes] = useState(null);
  const [copiedCodes, setCopiedCodes] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [regenModalOpen, setRegenModalOpen] = useState(false);
  const [regenPassword, setRegenPassword] = useState('');
  const [regenOtp, setRegenOtp] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Handle Student Verification
  const handleStudentVerify = async (e) => {
    e.preventDefault();
    setVerifyingStudent(true);
    try {
      const res = await verifyStudent(studentId, universityEmail);
      success(
        res.message ||
          `Student verified! 15% discount unlocked (${res.discount_rate ? res.discount_rate * 100 : 15}% off).`
      );
      setStudentId('');
      setUniversityEmail('');
    } catch (err) {
      toastError(err.message || 'Student verification failed. Ensure valid university domain.');
    } finally {
      setVerifyingStudent(false);
    }
  };

  // Handle Aadhaar SHA-256 Tokenization Verification
  const handleAadhaarVerify = async (e) => {
    e.preventDefault();
    setVerifyingAadhaar(true);
    try {
      const res = await verifyAadhaar(aadhaarNumber);
      success(
        res.message ||
          `Aadhaar tokenized & verified! Masked identity: ${res.masked_aadhaar || 'XXXX-XXXX-XXXX'}`
      );
      setAadhaarNumber('');
    } catch (err) {
      toastError(err.message || 'Aadhaar verification failed. Enter 12 digits.');
    } finally {
      setVerifyingAadhaar(false);
    }
  };

  // Handle Host DISCOM & Penny Drop Verification
  const handleHostVerify = async (e) => {
    e.preventDefault();
    setVerifyingHost(true);
    try {
      const res = await verifyHost(consumerNumber, discomProvider, hostUpiVpa);
      success(res.message || 'Host utility and UPI beneficiary verified successfully!');
      setConsumerNumber('');
      setHostUpiVpa('');
    } catch (err) {
      toastError(err.message || 'Host verification failed.');
    } finally {
      setVerifyingHost(false);
    }
  };

  // MFA Flow
  const startMfaSetup = async () => {
    setSettingUpMfa(true);
    try {
      const res = await authApi.setupMfa();
      const payload = res?.data || res;
      setMfaData(payload);
    } catch (err) {
      toastError(err.message || 'MFA setup initialization failed.');
    } finally {
      setSettingUpMfa(false);
    }
  };

  const confirmMfaSetup = async (e) => {
    e.preventDefault();
    try {
      await authApi.verifySetupMfa(mfaOtp);
      success('Two-factor authentication (MFA) successfully enabled!');
      if (mfaData?.recovery_codes) {
        setActiveRecoveryCodes(mfaData.recovery_codes);
      }
      setMfaData(null);
      setMfaOtp('');
      await refreshUser();
    } catch (err) {
      toastError(err.message || 'Invalid 6-digit TOTP code. Please check and try again.');
    }
  };

  const disableMfa = async (e) => {
    e.preventDefault();
    try {
      await authApi.disableMfa({
        password: mfaPassword,
        code: mfaDisableOtp,
      });
      success('MFA disabled on your account.');
      setMfaPassword('');
      setMfaDisableOtp('');
      await refreshUser();
    } catch (err) {
      toastError(err.message || 'MFA disablement failed. Verify your password and 6-digit TOTP code.');
    }
  };

  const handleRegenerateRecoveryCodes = async (e) => {
    e.preventDefault();
    setIsRegenerating(true);
    try {
      const res = await authApi.regenerateRecoveryCodes({
        password: regenPassword,
        code: regenOtp,
      });
      const payload = res?.data || res;
      const codes = payload?.recovery_codes;
      if (codes) {
        setActiveRecoveryCodes(codes);
        success('New emergency recovery codes generated! Old codes are now invalid.');
        setRegenModalOpen(false);
        setRegenPassword('');
        setRegenOtp('');
      }
    } catch (err) {
      toastError(err.message || 'Failed to regenerate recovery codes. Verify password and code.');
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header Profile Bar */}
      <div className="p-8 rounded-3xl bg-surface border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary to-indigo-600 text-white flex items-center justify-center font-extrabold text-2xl shadow-md">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black text-text-primary tracking-tight">
                {user?.full_name || 'SpaceLoop Member'}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
                {activeRole} mode
              </span>
            </div>
            <p className="text-xs text-text-secondary">{user?.email}</p>
            <p className="text-[11px] text-text-muted">Phone: {user?.phone || 'Verified SMS'}</p>
          </div>
        </div>

        {/* Switch Role Quick Actions */}
        <div className="flex items-center gap-2">
          {activeRole === 'seeker' ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => switchContext('host')}
              className="flex items-center gap-1.5"
            >
              <Building2 className="w-4 h-4 text-primary" />
              <span>Switch to Host Mode</span>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => switchContext('seeker')}
              className="flex items-center gap-1.5"
            >
              <User className="w-4 h-4 text-emerald-500" />
              <span>Switch to Seeker Mode</span>
            </Button>
          )}
        </div>
      </div>

      {/* Verification Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 1. Student Verification (15% Discount) */}
        <div className="p-6 rounded-3xl bg-surface border border-border space-y-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-text-primary">Student Verification</h3>
                <p className="text-[11px] text-text-secondary">Unlocks 15% discount on all desk bookings</p>
              </div>
            </div>
            {user?.is_student_verified ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>15% DISCOUNT ACTIVE</span>
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-600 border border-amber-500/20">
                UNVERIFIED
              </span>
            )}
          </div>

          <p className="text-xs text-text-secondary leading-relaxed">
            Verify with your accredited university domain (.edu, .ac.in, etc.). We use SHA-256 tokenization and never store raw identity documents.
          </p>

          {!user?.is_student_verified ? (
            <form onSubmit={handleStudentVerify} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  University Email Address
                </label>
                <input
                  type="email"
                  required
                  value={universityEmail}
                  onChange={(e) => setUniversityEmail(e.target.value)}
                  placeholder="e.g. rohit.sharma@iitb.ac.in"
                  className="w-full px-3.5 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  Student Roll / ID Number
                </label>
                <input
                  type="text"
                  required
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  placeholder="e.g. STU-2026-9812"
                  className="w-full px-3.5 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={verifyingStudent}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {verifyingStudent ? 'Verifying with Registrar...' : 'Verify Student & Apply 15% Off'}
              </Button>
            </form>
          ) : (
            <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 shrink-0" />
              <span>
                Verified Student! 15% discount is automatically deducted on every precheck calculation.
              </span>
            </div>
          )}
        </div>

        {/* 2. Aadhaar SHA-256 Masked Verification */}
        <div className="p-6 rounded-3xl bg-surface border border-border space-y-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-text-primary">Government Identity (Aadhaar)</h3>
                <p className="text-[11px] text-text-secondary">Tokenized cryptographic identity badge</p>
              </div>
            </div>
            {user?.is_aadhaar_verified ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-primary/15 text-primary border border-primary/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>VERIFIED</span>
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-500/10 text-zinc-400">
                OPTIONAL
              </span>
            )}
          </div>

          <p className="text-xs text-text-secondary leading-relaxed">
            Privacy Guarantee: We never store your 12-digit Aadhaar number. It is converted to an irreversible SHA-256 hash immediately upon entry and displayed as XXXX-XXXX-1234.
          </p>

          {!user?.is_aadhaar_verified ? (
            <form onSubmit={handleAadhaarVerify} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  12-Digit Aadhaar Number
                </label>
                <div className="relative">
                  <Hash className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    maxLength={12}
                    required
                    value={aadhaarNumber}
                    onChange={(e) => setAadhaarNumber(e.target.value.replace(/\D/g, ''))}
                    placeholder="•••• •••• ••••"
                    className="w-full pl-9 pr-3.5 py-2 text-xs font-mono rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={verifyingAadhaar || aadhaarNumber.length !== 12}
                className="w-full"
              >
                {verifyingAadhaar ? 'Generating SHA-256 Token...' : 'Tokenize & Verify Identity'}
              </Button>
            </form>
          ) : (
            <div className="p-3.5 rounded-2xl bg-surface-elevated border border-border text-xs text-text-secondary flex items-center justify-between">
              <span className="font-mono text-text-primary font-bold">
                {user.masked_aadhaar || 'XXXX-XXXX-8912'}
              </span>
              <span className="text-[10px] text-text-muted">SHA-256 Secured</span>
            </div>
          )}
        </div>

        {/* 3. Host Verification: DISCOM Utility & UPI Penny Drop */}
        <div className="p-6 rounded-3xl bg-surface border border-border space-y-5 shadow-sm md:col-span-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-text-primary">
                  Host Property Verification (DISCOM & UPI)
                </h3>
                <p className="text-[11px] text-text-secondary">
                  Electric utility consumer number verification + penny-drop bank account check
                </p>
              </div>
            </div>
            {user?.is_host_verified ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>HOST VERIFIED</span>
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-600 border border-amber-500/20">
                PENDING HOST CHECK
              </span>
            )}
          </div>

          {!user?.is_host_verified ? (
            <form onSubmit={handleHostVerify} className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  Electricity Board (DISCOM)
                </label>
                <select
                  value={discomProvider}
                  onChange={(e) => setDiscomProvider(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                >
                  <option value="BESCOM">BESCOM (Bengaluru)</option>
                  <option value="MSEDCL">MSEDCL (Maharashtra / Mumbai)</option>
                  <option value="BSES_RAJDHANI">BSES Rajdhani (Delhi)</option>
                  <option value="TATA_POWER">Tata Power (Mumbai/Delhi)</option>
                  <option value="TANGEDCO">TANGEDCO (Tamil Nadu)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  Consumer Account No.
                </label>
                <input
                  type="text"
                  required
                  value={consumerNumber}
                  onChange={(e) => setConsumerNumber(e.target.value)}
                  placeholder="e.g. CA-490182740"
                  className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-text-secondary mb-1">
                  Payout UPI VPA (Penny-Drop)
                </label>
                <input
                  type="text"
                  required
                  value={hostUpiVpa}
                  onChange={(e) => setHostUpiVpa(e.target.value)}
                  placeholder="e.g. host.space@icici"
                  className="w-full px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
                />
              </div>

              <div className="md:col-span-3 pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={verifyingHost}
                  className="w-full"
                >
                  {verifyingHost ? 'Executing DISCOM & Penny-Drop Matching...' : 'Verify Utility & UPI Account'}
                </Button>
              </div>
            </form>
          ) : (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-400 space-y-1">
              <div className="flex items-center gap-2 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Verified Commercial Host</span>
              </div>
              <p className="text-[11px]">
                Your physical space electricity account and bank beneficiary name have been matched.
              </p>
            </div>
          )}
        </div>

        {/* 4. Security & MFA Settings */}
        <div className="p-6 rounded-3xl bg-surface border border-border space-y-5 shadow-sm md:col-span-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-text-primary">Multi-Factor Authentication (MFA / TOTP)</h3>
                <p className="text-[11px] text-text-secondary">Protect your financial payouts and listings</p>
              </div>
            </div>
            {user?.mfa_enabled ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30">
                MFA ENABLED
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-500/10 text-zinc-400">
                DISABLED
              </span>
            )}
          </div>

          {/* Emergency Recovery Codes Display Modal/Banner */}
          {activeRecoveryCodes && (
            <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-amber-500 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Save Your Emergency Backup Recovery Codes</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(activeRecoveryCodes.join('\n'));
                    setCopiedCodes(true);
                    setTimeout(() => setCopiedCodes(false), 2000);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-surface border border-border text-[11px] font-semibold text-text-primary hover:bg-surface-elevated flex items-center gap-1.5 transition-colors"
                >
                  {copiedCodes ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 text-text-muted" />}
                  <span>{copiedCodes ? 'Copied All!' : 'Copy All Codes'}</span>
                </button>
              </div>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                Save these one-time codes in your password manager or safe storage. Each code can be used exactly once to log in if you lose access to your authenticator app.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs text-text-primary font-bold">
                {activeRecoveryCodes.map((c, i) => (
                  <div key={i} className="p-2 rounded-xl bg-surface border border-border text-center select-all">
                    {c}
                  </div>
                ))}
              </div>
              <div className="pt-1">
                <Button variant="outline" size="sm" onClick={() => setActiveRecoveryCodes(null)} className="w-full">
                  I have saved my backup recovery codes safely
                </Button>
              </div>
            </div>
          )}

          {!user?.mfa_enabled && !mfaData && (
            <Button variant="outline" size="sm" onClick={startMfaSetup} disabled={settingUpMfa}>
              {settingUpMfa ? 'Generating TOTP Secret...' : 'Set Up Two-Factor Authentication'}
            </Button>
          )}

          {mfaData && (
            <div className="p-5 rounded-2xl bg-surface-elevated border border-border space-y-4">
              <div>
                <h4 className="font-bold text-xs text-text-primary">Step 1: Add to Your Authenticator App</h4>
                <p className="text-[11px] text-text-secondary mt-0.5">
                  Scan this QR code with Google Authenticator, 1Password, or Authy, or copy the manual key:
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-4 p-4 rounded-xl bg-surface border border-border">
                {mfaData.provisioning_uri && (
                  <div className="p-2 rounded-xl bg-white flex items-center justify-center shrink-0 shadow-sm">
                    <img
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(mfaData.provisioning_uri)}`}
                      alt="TOTP Provisioning QR"
                      className="w-28 h-28"
                    />
                  </div>
                )}
                <div className="space-y-2 flex-1 w-full text-center sm:text-left">
                  <div className="text-[11px] font-semibold text-text-secondary">Manual Setup Key:</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 p-2 bg-surface-elevated border border-border rounded-xl font-mono text-xs font-bold text-primary select-all text-center sm:text-left break-all">
                      {mfaData.secret}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(mfaData.secret);
                        setCopiedKey(true);
                        setTimeout(() => setCopiedKey(false), 2000);
                      }}
                      className="p-2 rounded-xl bg-surface-elevated border border-border hover:bg-surface text-text-secondary hover:text-text-primary"
                      title="Copy Key"
                    >
                      {copiedKey ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-bold text-xs text-text-primary">Step 2: Enter Verification Code</h4>
                <p className="text-[11px] text-text-secondary mt-0.5">
                  Enter the 6-digit code currently shown in your authenticator app to finalize enrollment:
                </p>
              </div>

              <form onSubmit={confirmMfaSetup} className="flex gap-2">
                <input
                  type="text"
                  maxLength={6}
                  required
                  value={mfaOtp}
                  onChange={(e) => setMfaOtp(e.target.value.trim())}
                  placeholder="6-digit code"
                  className="flex-1 px-3 py-2 text-xs rounded-xl bg-surface border border-border text-text-primary text-center font-mono tracking-widest text-sm"
                />
                <Button type="submit" variant="primary" size="sm">
                  Confirm & Enable MFA
                </Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setMfaData(null)}>
                  Cancel
                </Button>
              </form>
            </div>
          )}

          {user?.mfa_enabled && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setRegenModalOpen(!regenModalOpen)}
                  className="flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Regenerate Backup Recovery Codes</span>
                </Button>
              </div>

              {regenModalOpen && (
                <form onSubmit={handleRegenerateRecoveryCodes} className="p-4 rounded-2xl bg-surface-elevated border border-border space-y-3 max-w-md">
                  <p className="text-xs text-text-secondary">
                    Re-authenticate with your password and current 6-digit TOTP code to generate new recovery codes:
                  </p>
                  <div className="space-y-2">
                    <input
                      type="password"
                      required
                      value={regenPassword}
                      onChange={(e) => setRegenPassword(e.target.value)}
                      placeholder="Account Password"
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface border border-border text-text-primary"
                    />
                    <input
                      type="text"
                      maxLength={6}
                      required
                      value={regenOtp}
                      onChange={(e) => setRegenOtp(e.target.value.trim())}
                      placeholder="Current 6-Digit TOTP"
                      className="w-full px-3 py-2 text-xs rounded-xl bg-surface border border-border text-text-primary font-mono"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" variant="primary" size="sm" disabled={isRegenerating}>
                      {isRegenerating ? 'Generating...' : 'Generate New Codes'}
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setRegenModalOpen(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              )}

              <div className="pt-2 border-t border-border">
                <p className="text-xs font-semibold text-text-secondary mb-2">
                  Disable Two-Factor Authentication (Requires Password + Current TOTP):
                </p>
                <form onSubmit={disableMfa} className="flex flex-col sm:flex-row gap-2 max-w-lg">
                  <input
                    type="password"
                    required
                    value={mfaPassword}
                    onChange={(e) => setMfaPassword(e.target.value)}
                    placeholder="Account Password"
                    className="flex-1 px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary"
                  />
                  <input
                    type="text"
                    maxLength={6}
                    required
                    value={mfaDisableOtp}
                    onChange={(e) => setMfaDisableOtp(e.target.value.trim())}
                    placeholder="6-Digit TOTP"
                    className="w-32 px-3 py-2 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary font-mono text-center"
                  />
                  <Button type="submit" variant="outline" size="sm" className="text-rose-500 hover:bg-rose-500/10">
                    Disable MFA
                  </Button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
