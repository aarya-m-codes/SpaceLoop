import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Mail,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Send,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { authApi } from '../services/api';
import { Button } from '../components/common/Button';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';

export const VerifyEmailPage = () => {
  const { token: paramToken } = useParams();
  const [searchParams] = useSearchParams();
  const token = paramToken || searchParams.get('token') || '';
  const navigate = useNavigate();
  const { t } = useI18n();
  const { success, error: toastError } = useToast();
  const { user, login } = useAuth();

  const [loading, setLoading] = useState(Boolean(token));
  const [verified, setVerified] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Resend Form
  const [emailInput, setEmailInput] = useState(user?.email || '');
  const [resending, setResending] = useState(false);
  const [resendSent, setResendSent] = useState(false);
  const [instantVerifying, setInstantVerifying] = useState(false);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const verifyToken = async () => {
      try {
        setLoading(true);
        const res = await authApi.verifyEmail(token);
        setVerified(true);
        success(res.message || 'Email verified successfully!');
      } catch (err) {
        setErrorMessage(err.message || 'Verification token is invalid or has expired.');
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleResend = async (e) => {
    e.preventDefault();
    if (!emailInput.trim()) {
      toastError('Please enter your email address.');
      return;
    }

    try {
      setResending(true);
      await authApi.resendVerification(emailInput.trim());
      setResendSent(true);
      success('Verification email sent via Resend! Check your inbox.');
    } catch (err) {
      toastError(err.message || 'Could not send verification email.');
    } finally {
      setResending(false);
    }
  };

  const handleInstantVerify = async () => {
    try {
      setInstantVerifying(true);
      await authApi.instantVerify();
      setVerified(true);
      success('Account verified instantly!');
      setTimeout(() => navigate('/explore'), 1500);
    } catch (err) {
      toastError(err.message || 'Instant verification failed.');
    } finally {
      setInstantVerifying(false);
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-3xl bg-surface border border-border p-8 shadow-xl text-center space-y-6">
          {loading ? (
            <div className="py-10 space-y-4">
              <div className="w-12 h-12 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <h2 className="text-xl font-bold text-text-primary">Verifying Email Token...</h2>
              <p className="text-xs text-text-secondary">
                Validating cryptographic token with SpaceLoop security service.
              </p>
            </div>
          ) : verified ? (
            <div className="space-y-6 py-4">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div className="space-y-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                  Verification Complete
                </span>
                <h1 className="text-2xl font-extrabold text-text-primary">
                  Email Successfully Verified
                </h1>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Your identity has been authenticated. You now have full access to instant bookings, arrival PINs, and the host portal.
                </p>
              </div>

              <div className="pt-2 flex flex-col gap-2">
                <Link to="/explore">
                  <Button variant="primary" className="w-full flex items-center justify-center gap-2">
                    <span>Explore Spaces</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
                <Link to="/profile">
                  <Button variant="outline" className="w-full">
                    <span>Go to Profile</span>
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <div className="space-y-6 py-2">
              <div className="w-16 h-16 rounded-3xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center mx-auto shadow-inner">
                <Mail className="w-8 h-8" />
              </div>

              <div className="space-y-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20">
                  Action Required
                </span>
                <h1 className="text-2xl font-extrabold text-text-primary">
                  Verify Your Email
                </h1>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {errorMessage ||
                    'Please verify your email address to access bookings, in-room session timers, and escrow refunds.'}
                </p>
              </div>

              {resendSent ? (
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600">
                  ✓ Verification email sent to <strong>{emailInput}</strong>. Please check your spam/inbox.
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-3 text-left">
                  <label className="text-xs font-medium text-text-secondary block">
                    Account Email Address
                  </label>
                  <input
                    type="email"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    placeholder="name@university.ac.in or work@domain.com"
                    className="w-full bg-surface-elevated border border-border focus:border-primary rounded-xl px-4 py-2.5 text-xs text-text-primary focus:outline-none transition"
                    required
                  />
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={resending}
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{resending ? 'Sending...' : 'Send Verification Email'}</span>
                  </Button>
                </form>
              )}

              {/* Dev / Instant Onboarding Helper */}
              <div className="pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={handleInstantVerify}
                  disabled={instantVerifying}
                  className="w-full py-2.5 px-3 rounded-xl bg-surface-elevated hover:bg-border/60 text-[11px] font-semibold text-text-muted hover:text-text-primary flex items-center justify-center gap-2 transition"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Instant Verify (Demo & Testing Mode)</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
