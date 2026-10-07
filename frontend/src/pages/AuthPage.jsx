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

  const executeLogin = async (loginEmail, loginPassword) => {
    setFormError('');
    setLoading(true);

    try {
      const result = await login(loginEmail, loginPassword);
      success('Signed in successfully!');

      // Exact Role Detection from Authenticated Backend Data
      const rawRole =
        result?.activeRole ||
        result?.user?.active_role ||
        result?.user?.role ||
        (result?.user?.is_admin ? 'admin' : '');
      const userRole = String(rawRole).toLowerCase() === 'guest' ? 'seeker' : String(rawRole).toLowerCase();

      if (location.state?.from) {
        navigate(location.state.from);
      } else if (userRole === 'admin' || result?.user?.is_admin) {
        navigate('/admin');
      } else if (userRole === 'host') {
        navigate('/host');
      } else {
        navigate('/seeker');
      }
    } catch (err) {
      let msg = 'Authentication failed. Please verify credentials.';
      if (err) {
        if (typeof err === 'string' && err.trim()) {
          msg = err.trim();
        } else if (typeof err.message === 'string' && err.message !== '[object Object]' && err.message.trim()) {
          msg = err.message.trim();
        } else if (err.data?.error?.message) {
          msg = err.data.error.message;
        } else if (typeof err.data?.error === 'string') {
          msg = err.data.error;
        } else if (typeof err.data?.message === 'string') {
          msg = err.data.message;
        }
      }
      if (msg === '[object Object]') {
        msg = 'Invalid email or password.';
      }
      setFormError(msg);
      toastError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (targetRole) => {
    setIsLogin(true);
    let targetEmail = 'seeker.rohit@spaceloop.in';
    const targetPassword = 'SpaceLoopDemo123!';
    let demoRole = 'seeker';

    if (targetRole === 'host') {
      targetEmail = 'host.arjun@spaceloop.in';
      demoRole = 'host';
    } else if (targetRole === 'admin') {
      targetEmail = 'admin.spaceloop@spaceloop.in';
      demoRole = 'admin';
    }

    setEmail(targetEmail);
    setPassword(targetPassword);
    setRole(demoRole);

    await executeLogin(targetEmail, targetPassword);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLogin) {
      await executeLogin(email, password);
    } else {
      setFormError('');
      setLoading(true);
      try {
        const regResult = await register({
          email,
          password,
          full_name: fullName,
          phone,
          role,
        });
        success('Account created! Welcome to SpaceLoop.');
        const rawRegRole = regResult?.activeRole || regResult?.user?.role || role;
        const regRole = String(rawRegRole).toLowerCase() === 'guest' ? 'seeker' : String(rawRegRole).toLowerCase();
        navigate(regRole === 'host' ? '/host' : '/seeker');
      } catch (err) {
        let msg = 'Registration failed. Please check your information.';
        if (err) {
          if (typeof err === 'string' && err.trim()) {
            msg = err.trim();
          } else if (typeof err.message === 'string' && err.message !== '[object Object]' && err.message.trim()) {
            msg = err.message.trim();
          } else if (err.data?.error?.message) {
            msg = err.data.error.message;
          } else if (typeof err.data?.error === 'string') {
            msg = err.data.error;
          } else if (typeof err.data?.message === 'string') {
            msg = err.data.message;
          }
        }
        if (msg === '[object Object]') {
          msg = 'Unable to create account. Please try again.';
        }
        setFormError(msg);
        toastError(msg);
      } finally {
        setLoading(false);
      }
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
            {loading
              ? isLogin
                ? 'Signing in...'
                : 'Creating account...'
              : isLogin
              ? 'Sign In to SpaceLoop'
              : 'Register Account'}
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
              disabled={loading}
              onClick={() => handleDemoLogin('seeker')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-primary/10 border border-border text-[11px] text-text-secondary hover:text-primary transition-colors disabled:opacity-50"
            >
              Seeker Demo
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => handleDemoLogin('host')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-primary/10 border border-border text-[11px] text-text-secondary hover:text-primary transition-colors disabled:opacity-50"
            >
              Host Demo
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => handleDemoLogin('admin')}
              className="px-2.5 py-1 rounded-lg bg-surface-elevated hover:bg-rose-500/10 border border-border text-[11px] text-text-secondary hover:text-rose-500 transition-colors disabled:opacity-50"
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
