import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Calculator,
  TrendingUp,
  Building,
  MapPin,
  Maximize2,
  DollarSign,
  ShieldCheck,
  Zap,
  ArrowRight,
  Sparkles,
  Info,
  Calendar,
  Percent,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { calculatorApi } from '../services/api';

const SPACE_CATEGORIES = [
  { id: 'Study Pod', label: 'Study Pod', baseRate: 45, icon: '📚' },
  { id: 'Workspace', label: 'Workspace / Desk', baseRate: 65, icon: '💻' },
  { id: 'Meeting Room', label: 'Meeting Room', baseRate: 120, icon: '👥' },
  { id: 'Creative Studio', label: 'Creative Studio', baseRate: 90, icon: '🎨' },
  { id: 'Podcast Studio', label: 'Podcast Studio', baseRate: 150, icon: '🎙️' },
  { id: 'Maker Workshop', label: 'Maker Workshop', baseRate: 80, icon: '🛠️' },
  { id: 'Pop-Up Retail', label: 'Pop-Up Retail', baseRate: 140, icon: '🛍️' },
  { id: 'Storage', label: 'Storage / Micro-Depot', baseRate: 40, icon: '📦' },
  { id: 'Parking', label: 'EV / Parking Spot', baseRate: 35, icon: '🚗' },
];

const METRO_CITIES = [
  { id: 'Bengaluru', name: 'Bengaluru', multiplier: 1.25 },
  { id: 'Pune', name: 'Pune', multiplier: 1.0 },
  { id: 'Mumbai', name: 'Mumbai', multiplier: 1.35 },
  { id: 'Delhi NCR', name: 'Delhi NCR', multiplier: 1.2 },
  { id: 'Hyderabad', name: 'Hyderabad', multiplier: 1.1 },
];

export const CalculatorPage = () => {
  const navigate = useNavigate();

  const [spaceType, setSpaceType] = useState('Study Pod');
  const [sqft, setSqft] = useState(150);
  const [city, setCity] = useState('Bengaluru');
  const [hoursPerDay, setHoursPerDay] = useState(6);
  const [daysPerWeek, setDaysPerWeek] = useState(5);
  const [loading, setLoading] = useState(false);

  const [estimate, setEstimate] = useState({
    space_type: 'Study Pod',
    square_feet: 150,
    estimated_monthly_inr: 6750,
    estimated_hourly_inr: 55,
    estimated_annual_inr: 81000,
    occupancy_rate_pct: 65,
    peer_comparison: 'Top 15% yield in Bengaluru tech corridor',
  });

  const fetchEstimate = async () => {
    setLoading(true);
    try {
      const res = await calculatorApi.estimate({
        space_type: spaceType,
        square_feet: Number(sqft) || 150,
        city,
        hours_per_day: Number(hoursPerDay) || 6,
        days_per_week: Number(daysPerWeek) || 5,
      });

      if (res && res.estimated_monthly_inr) {
        setEstimate({
          space_type: res.space_type || spaceType,
          square_feet: res.square_feet || sqft,
          estimated_monthly_inr: res.estimated_monthly_inr,
          estimated_hourly_inr: res.estimated_hourly_inr || Math.round(res.estimated_monthly_inr / 120),
          estimated_annual_inr: res.estimated_annual_inr || res.estimated_monthly_inr * 12,
          occupancy_rate_pct: res.occupancy_rate_pct || 65,
          peer_comparison: res.peer_comparison || `Top tier in ${city}`,
        });
      } else {
        fallbackCalculate();
      }
    } catch (err) {
      fallbackCalculate();
    } finally {
      setLoading(false);
    }
  };

  const fallbackCalculate = () => {
    const cat = SPACE_CATEGORIES.find((c) => c.id === spaceType) || SPACE_CATEGORIES[0];
    const cityObj = METRO_CITIES.find((c) => c.id === city) || METRO_CITIES[0];
    const hourly = Math.round(cat.baseRate * cityObj.multiplier);
    const monthlyHours = hoursPerDay * daysPerWeek * 4;
    const monthly = Math.round(hourly * monthlyHours * 0.7); // 70% occupancy factor
    setEstimate({
      space_type: spaceType,
      square_feet: Number(sqft) || 150,
      estimated_monthly_inr: monthly,
      estimated_hourly_inr: hourly,
      estimated_annual_inr: monthly * 12,
      occupancy_rate_pct: 70,
      peer_comparison: `Top 12% in ${city}`,
    });
  };

  useEffect(() => {
    fetchEstimate();
  }, [spaceType, sqft, city, hoursPerDay, daysPerWeek]);

  return (
    <div className="min-h-screen bg-surface-base text-text-primary pb-24">
      {/* Top Hero Banner */}
      <div className="relative overflow-hidden bg-surface-elevated/40 border-b border-border py-16 px-4 sm:px-6 lg:px-8 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-4">
            <TrendingUp className="w-4 h-4" />
            <span>AI Dynamic Monetization Engine</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-text-primary mb-4">
            Calculate Your Idle Space Yield
          </h1>
          <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto">
            Discover how much passive revenue your unused desk, studio, or spare room can generate on SpaceLoop with Section 52 micro-leasing protection.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Controls Column */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-surface rounded-2xl border border-border p-6 shadow-sm space-y-6">
              <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
                <Building className="w-5 h-5 text-primary" />
                Select Space Category
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {SPACE_CATEGORIES.map((cat) => {
                  const isSelected = spaceType === cat.id;
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setSpaceType(cat.id)}
                      className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                        isSelected
                          ? 'border-primary bg-primary/10 text-primary shadow-xs'
                          : 'border-border bg-surface-elevated/50 hover:border-border-strong text-text-secondary'
                      }`}
                    >
                      <span className="text-xl mb-1">{cat.icon}</span>
                      <span className="text-xs font-bold leading-tight">{cat.label}</span>
                      <span className="text-[11px] opacity-75 mt-1">₹{cat.baseRate}/hr base</span>
                    </button>
                  );
                })}
              </div>

              {/* City Selection */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-primary" />
                  Target Metro Area
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {METRO_CITIES.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setCity(c.id)}
                      className={`py-2 px-3 rounded-xl border text-xs font-medium text-center transition ${
                        city === c.id
                          ? 'border-primary bg-primary text-white font-semibold shadow-xs'
                          : 'border-border bg-surface-elevated hover:bg-surface-elevated/80 text-text-secondary'
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Area Slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                    <Maximize2 className="w-4 h-4 text-primary" />
                    Available Space Area
                  </label>
                  <span className="text-sm font-bold text-text-primary bg-surface-elevated px-2.5 py-1 rounded-lg border border-border">
                    {sqft} sq.ft
                  </span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="1500"
                  step="10"
                  value={sqft}
                  onChange={(e) => setSqft(Number(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between text-[11px] text-text-muted mt-1 font-mono">
                  <span>40 sq.ft (Pod)</span>
                  <span>500 sq.ft (Studio)</span>
                  <span>1500 sq.ft (Floor)</span>
                </div>
              </div>

              {/* Hours / Week Availability */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-primary" />
                      Hours / Day
                    </label>
                    <span className="text-xs font-bold text-text-primary">{hoursPerDay} hrs</span>
                  </div>
                  <input
                    type="range"
                    min="2"
                    max="14"
                    step="1"
                    value={hoursPerDay}
                    onChange={(e) => setHoursPerDay(Number(e.target.value))}
                    className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
                      <Percent className="w-4 h-4 text-primary" />
                      Days / Week
                    </label>
                    <span className="text-xs font-bold text-text-primary">{daysPerWeek} days</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="7"
                    step="1"
                    value={daysPerWeek}
                    onChange={(e) => setDaysPerWeek(Number(e.target.value))}
                    className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>
              </div>
            </div>

            {/* Platform Guarantees */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-4 rounded-xl bg-surface border border-border flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">Section 52 Licensed</div>
                  <div className="text-[11px] text-text-muted mt-0.5">Revocable micro-lease protection under Indian Easements Act</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-surface border border-border flex items-start gap-3">
                <Zap className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">Instant UPI Payouts</div>
                  <div className="text-[11px] text-text-muted mt-0.5">Direct to your bank with zero hold delays</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-surface border border-border flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-text-primary">₹100 Micro-Escrow</div>
                  <div className="text-[11px] text-text-muted mt-0.5">Condition delta guarantee for every guest session</div>
                </div>
              </div>
            </div>
          </div>

          {/* Results Summary Column */}
          <div className="lg:col-span-5">
            <div className="sticky top-24 bg-gradient-to-b from-surface to-surface-elevated rounded-2xl border border-primary/30 p-6 shadow-xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <span className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                  <Calculator className="w-4 h-4" />
                  Yield Projection
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  {estimate.occupancy_rate_pct}% Est. Occupancy
                </span>
              </div>

              <div>
                <div className="text-xs font-medium text-text-secondary mb-1">Estimated Monthly Revenue</div>
                <div className="text-4xl sm:text-5xl font-black text-emerald-400 tracking-tight flex items-baseline gap-1">
                  ₹{Number(estimate.estimated_monthly_inr || 0).toLocaleString('en-IN')}
                  <span className="text-xs font-normal text-text-muted">/ month</span>
                </div>
                <div className="text-xs text-text-muted mt-2">
                  Based on {hoursPerDay * daysPerWeek * 4} active hours monthly across {city}.
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center p-3 rounded-xl bg-surface-base border border-border text-xs">
                  <span className="text-text-secondary">Hourly Listing Price:</span>
                  <span className="font-bold text-text-primary">
                    ₹{estimate.estimated_hourly_inr} / hour
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-xl bg-surface-base border border-border text-xs">
                  <span className="text-text-secondary">Projected Annual Yield:</span>
                  <span className="font-bold text-emerald-400">
                    ₹{Number(estimate.estimated_annual_inr || estimate.estimated_monthly_inr * 12).toLocaleString('en-IN')} / yr
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-xl bg-surface-base border border-border text-xs">
                  <span className="text-text-secondary">Local Competitiveness:</span>
                  <span className="font-semibold text-primary">
                    {estimate.peer_comparison}
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full flex items-center justify-center gap-2 text-sm font-bold shadow-md shadow-primary/20"
                  onClick={() =>
                    navigate('/host/spaces/new', {
                      state: {
                        prefillCategory: spaceType,
                        prefillSqft: sqft,
                        prefillCity: city,
                        prefillPrice: estimate.estimated_hourly_inr,
                      },
                    })
                  }
                >
                  List This Space Now
                  <ArrowRight className="w-4 h-4" />
                </Button>
                <p className="text-[11px] text-text-muted text-center mt-3">
                  Zero listing fees. 10% platform commission deducted automatically upon guest checkout.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalculatorPage;
