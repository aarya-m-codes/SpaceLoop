import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Building2,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState('seeker');
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState('');

  const { login, register } = useAuth();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectPath = location.state?.from || (role === 'host' ? '/host' : '/explore');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setLoading(true);

    try {
      if (isLogin) {
        const result = await login(email, password);
        success('Signed in successfully!');
        
        // Exact Role Detection and Dashboard Redirection
        const userRole =
          result?.activeRole ||
          result?.user?.role ||
          (result?.user?.is_admin ? 'admin' : role);
        
        if (location.state?.from) {
          navigate(location.state.from);
        } else if (userRole === 'admin' || result?.user?.is_admin) {
          navigate('/admin');
        } else if (userRole === 'host') {
          navigate('/host');
        } else {
          navigate('/seeker');
        }
      } else {
        await register({
          email,
          password,
          full_name: fullName,
          phone,
          role,
        });
        success('Account created! Welcome to SpaceLoop.');
        navigate(role === 'host' ? '/host' : '/seeker');
      }
    } catch (err) {
      const msg = err.message || 'Authentication failed. Please verify credentials.';
      setFormError(msg);
      toastError(msg);
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (targetRole) => {
    if (targetRole === 'host') {
      setEmail('host.ananya@spaceloop.in');
      setPassword('HostSecret2026!');
      setRole('host');
    } else if (targetRole === 'admin') {
      setEmail('admin@spaceloop.in');
      setPassword('AdminSecret2026!');
      setRole('admin');
    } else {
      setEmail('seeker.rohit@spaceloop.in');
      setPassword('SeekerSecret2026!');
      setRole('seeker');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-surface border border-border rounded-3xl p-6 sm:p-10 shadow-xl backdrop-blur-md">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-primary/10 text-primary items-center justify-center mb-3">
            <Building2 className="w-6 h-6" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
            {isLogin ? 'Welcome back to SpaceLoop' : 'Create your SpaceLoop account'}
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-text-secondary">
            {isLogin
              ? 'Access verified architectural workspaces with keyless entry'
              : 'Join India’s premier peer-to-peer physical space network'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="grid grid-cols-2 p-1 rounded-xl bg-surface-elevated border border-border text-xs font-semibold">
          <button
            type="button"
            onClick={() => {
              setIsLogin(true);
              setFormError('');
            }}
            className={`py-2 rounded-lg transition-all ${
              isLogin ? 'bg-primary text-white shadow-sm' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLogin(false);
              setFormError('');
            }}
            className={`py-2 rounded-lg transition-all ${
              !isLogin ? 'bg-primary text-white shadow-sm' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Error Notice */}
        {formError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
            {formError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Rohit Sharma"
                    className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Phone Number (SMS & Entry)</label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 9876543210"
                    className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              {/* Primary Role Preference */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">I want to:</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRole('seeker')}
                    className={`py-2 px-3 rounded-xl border text-xs font-medium transition-all ${
                      role === 'seeker'
                        ? 'border-primary bg-primary/10 text-primary font-bold'
                        : 'border-border bg-surface-elevated text-text-secondary'
                    }`}
                  >
                    Book Spaces (Seeker)
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('host')}
                    className={`py-2 px-3 rounded-xl border text-xs font-medium transition-all ${
                      role === 'host'
                        ? 'border-primary bg-primary/10 text-primary font-bold'
                        : 'border-border bg-surface-elevated text-text-secondary'
                    }`}
                  >
                    Host Spaces (Host)
                  </button>
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@university.edu or name@company.in"
                className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl bg-surface-elevated border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <Button type="submit" variant="primary" className="w-full mt-2" disabled={loading}>
            {loading ? 'Authenticating...' : isLogin ? 'Sign In to SpaceLoop' : 'Register Account'}
          </Button>
        </form>

        {/* Demo Fast Fill Pill Buttons */}
        <div className="pt-4 border-t border-border space-y-2">
          <p className="text-[11px] font-semibold text-text-muted uppercase tracking-wider text-center">
            Demo Credentials (Instant Fill)
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => setDemoCredentials('seeker')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-primary/10 border border-border text-[11px] text-text-secondary hover:text-primary transition-colors"
            >
              Seeker Demo
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('host')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-primary/10 border border-border text-[11px] text-text-secondary hover:text-primary transition-colors"
            >
              Host Demo
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('admin')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-rose-500/10 border border-border text-[11px] text-text-secondary hover:text-rose-500 transition-colors"
            >
              Admin Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
