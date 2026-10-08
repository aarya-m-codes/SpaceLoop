import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Compass,
  CalendarCheck,
  Building2,
  Plus,
  Radio,
  ShieldCheck,
  User,
  LayoutDashboard,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../i18n/I18nContext';

export const MobileNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, activeRole } = useAuth();
  const { t } = useI18n();

  const isHostContext =
    activeRole === 'host' ||
    user?.role === 'host' ||
    Boolean(user?.is_host) ||
    location.pathname.startsWith('/host');

  const handleNav = (targetPath) => {
    if (location.pathname === targetPath) {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    } else {
      navigate(targetPath);
    }
  };

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface/95 backdrop-blur-xl border-t border-border px-3 py-2 flex items-center justify-around text-[10px] font-medium text-text-muted shadow-lg">
      {isHostContext ? (
        <>
          <button
            type="button"
            onClick={() => handleNav('/host')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname === '/host' || location.pathname === '/host/overview'
                ? 'text-primary font-bold'
                : 'hover:text-text-primary'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>{t('host_portal')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav('/host/spaces')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname.startsWith('/host/spaces') && !location.pathname.includes('/new')
                ? 'text-primary font-bold'
                : 'hover:text-text-primary'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Spaces</span>
          </button>

          {/* Center List Space Action */}
          <button
            type="button"
            onClick={() => handleNav('/host/spaces/new')}
            className="flex flex-col items-center gap-1 text-white"
          >
            <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center -mt-4 shadow-lg shadow-primary/30 text-white">
              <Plus className="w-5 h-5 stroke-[2.5]" />
            </div>
            <span className="font-bold text-[9px] text-primary">{t('list_your_space')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav('/host/bookings')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname.startsWith('/host/bookings') || location.pathname.startsWith('/host/reservations')
                ? 'text-primary font-bold'
                : 'hover:text-text-primary'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            <span>Bookings</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav('/host/live-sessions')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname.startsWith('/host/live-sessions')
                ? 'text-primary font-bold'
                : 'hover:text-text-primary'
            }`}
          >
            <Radio className="w-4 h-4 text-emerald-500 animate-pulse" />
            <span>Live Radar</span>
          </button>
        </>
      ) : (
        <>
          <button
            type="button"
            onClick={() => handleNav('/explore')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname === '/explore' ? 'text-primary font-bold' : 'hover:text-text-primary'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>{t('explore')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav('/bookings')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname === '/bookings' ? 'text-primary font-bold' : 'hover:text-text-primary'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            <span>{t('my_bookings')}</span>
          </button>

          {/* Center Switch to Host */}
          <button
            type="button"
            onClick={() => handleNav('/host')}
            className="flex flex-col items-center gap-1 text-white"
          >
            <div className="w-9 h-9 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center -mt-4 shadow-lg shadow-amber-500/30 text-white">
              <Building2 className="w-4 h-4 stroke-[2.5]" />
            </div>
            <span className="font-bold text-[9px] text-amber-500">{t('host_portal')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav('/verify')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname === '/verify' ? 'text-primary font-bold' : 'hover:text-text-primary'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Verify</span>
          </button>

          <button
            type="button"
            onClick={() => handleNav(isAuthenticated ? '/profile' : '/auth')}
            className={`flex flex-col items-center gap-1 transition-colors ${
              location.pathname === '/profile' || location.pathname === '/auth'
                ? 'text-primary font-bold'
                : 'hover:text-text-primary'
            }`}
          >
            <User className="w-4 h-4" />
            <span>{isAuthenticated ? 'Profile' : 'Sign In'}</span>
          </button>
        </>
      )}
    </nav>
  );
};

export default MobileNav;
