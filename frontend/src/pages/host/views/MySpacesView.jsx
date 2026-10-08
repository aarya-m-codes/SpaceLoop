import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Building2,
  PlusCircle,
  QrCode,
  Edit,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  ToggleLeft,
  ToggleRight,
  Printer,
  DollarSign,
  MapPin,
  Users,
} from 'lucide-react';
import { spacesApi, hostApi } from '../../../services/api';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';
import { useI18n } from '../../../i18n/I18nContext';

export const MySpacesView = () => {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const { t, formatCurrency } = useI18n();

  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState(null);

  const fetchSpaces = async () => {
    try {
      setLoading(true);
      const res = await hostApi.getDashboard();
      if (res && res.host_spaces) {
        setSpaces(res.host_spaces);
      } else {
        const fallback = await spacesApi.getSpaces();
        const list = fallback.spaces || (Array.isArray(fallback) ? fallback : []);
        setSpaces(list);
      }
    } catch (err) {
      console.warn('Failed to load host spaces:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpaces();
  }, []);

  const handleToggle = async (spaceId) => {
    try {
      setTogglingId(spaceId);
      const res = await spacesApi.toggleStatus(spaceId);
      success(res.message || 'Space availability toggled.');
      await fetchSpaces();
    } catch (err) {
      toastError(err.message || 'Failed to toggle space status.');
    } finally {
      setTogglingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-primary tracking-tight">
            Registered Spaces & Listings
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Configure premise specifications, generate physical door QR passes, and control live availability.
          </p>
        </div>

        <Link to="/host/spaces/new">
          <Button variant="primary" size="sm" className="flex items-center gap-1.5">
            <PlusCircle className="w-4 h-4" />
            <span>List New Space</span>
          </Button>
        </Link>
      </div>

      {/* Spaces Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-64 rounded-2xl bg-surface border border-border animate-pulse" />
          ))}
        </div>
      ) : spaces.length === 0 ? (
        <div className="p-12 rounded-2xl bg-surface border border-border text-center space-y-4">
          <Building2 className="w-12 h-12 text-text-muted mx-auto" />
          <h3 className="text-base font-bold text-text-primary">No Registered Spaces</h3>
          <p className="text-xs text-text-secondary max-w-sm mx-auto">
            You have not listed any physical workspaces yet. Add your first room or studio to start earning.
          </p>
          <Link to="/host/spaces/new">
            <Button variant="primary">Create Your First Listing</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {spaces.map((sp) => {
            const isActive = sp.is_active !== false;
            const price = sp.price_per_hour || sp.hourly_rate || sp.price || 150;
            return (
              <div
                key={sp.id}
                className="rounded-2xl bg-surface border border-border overflow-hidden shadow-xs hover:border-primary/40 transition flex flex-col justify-between"
              >
                {/* Image Banner */}
                <div className="relative h-44 bg-surface-elevated overflow-hidden">
                  <img
                    src={
                      sp.images?.[0] ||
                      sp.photo_url ||
                      'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'
                    }
                    alt={sp.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-3 left-3 flex items-center gap-1.5">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-surface/90 text-text-primary backdrop-blur-md border border-border">
                      {sp.space_type || sp.category || 'Workspace'}
                    </span>
                    {sp.is_verified && (
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/90 text-white backdrop-blur-md flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" />
                        <span>Verified</span>
                      </span>
                    )}
                  </div>

                  <div className="absolute top-3 right-3">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold backdrop-blur-md uppercase tracking-wider ${
                        isActive
                          ? 'bg-emerald-500/90 text-white'
                          : 'bg-slate-800/90 text-slate-300'
                      }`}
                    >
                      {isActive ? 'Published' : 'Paused'}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5 space-y-4 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-text-muted">ID #{sp.id}</span>
                      <span className="text-base font-black text-text-primary font-mono">
                        {formatCurrency(price)}/hr
                      </span>
                    </div>

                    <h3 className="font-bold text-base text-text-primary line-clamp-1">
                      {sp.title}
                    </h3>

                    <div className="flex items-center gap-3 text-xs text-text-secondary">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-text-muted" />
                        <span className="truncate max-w-[160px]">{sp.city || sp.location || 'Bangalore'}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5 text-text-muted" />
                        <span>{sp.capacity || 4} Guests</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="pt-4 border-t border-border flex items-center justify-between gap-2">
                    <button
                      type="button"
                      disabled={togglingId === sp.id}
                      onClick={() => handleToggle(sp.id)}
                      className="text-xs font-semibold text-text-muted hover:text-text-primary flex items-center gap-1 transition"
                    >
                      {isActive ? (
                        <>
                          <ToggleRight className="w-5 h-5 text-emerald-500" />
                          <span>Active</span>
                        </>
                      ) : (
                        <>
                          <ToggleLeft className="w-5 h-5 text-text-muted" />
                          <span>Paused</span>
                        </>
                      )}
                    </button>

                    <div className="flex items-center gap-1.5">
                      <Link to={`/spaces/${sp.id}/door-pass`}>
                        <Button variant="outline" size="sm" className="px-2.5 py-1 text-xs flex items-center gap-1">
                          <Printer className="w-3.5 h-3.5" />
                          <span>Door Pass</span>
                        </Button>
                      </Link>

                      <Link to={`/host/spaces/${sp.id}/edit`}>
                        <Button variant="outline" size="sm" className="px-2.5 py-1 text-xs flex items-center gap-1">
                          <Edit className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </Button>
                      </Link>

                      <Link to={`/spaces/${sp.id}`} target="_blank">
                        <Button variant="ghost" size="sm" className="px-2 py-1 text-xs">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MySpacesView;
