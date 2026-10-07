import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Sparkles,
  Camera,
  Upload,
  Building2,
  DollarSign,
  MapPin,
  Users,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  Bot,
  Zap,
} from 'lucide-react';
import { spacesApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common/Button';

const CATEGORIES = [
  'Coworking & Lounge',
  'Creative Studio',
  'Conference Room',
  'Outdoor & Lounge',
  'Private Office',
  'Event & Workshop',
];

const COMMON_AMENITIES = [
  'High-speed 1Gbps WiFi',
  'Smart Keyless Access',
  'Ergonomic Herman Miller Chairs',
  'Dual 4K Displays',
  'Zoom Rooms System',
  'Whiteboards',
  'Espresso Bar',
  'Secure Soundproofing',
  'Natural Light Skylights',
  'Air Conditioning',
  'Power Backup / Inverter',
  'Wheelchair Accessible',
];

export const HostListingForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { success, error: toastError } = useToast();

  const isEditMode = Boolean(id);

  // Form Fields
  const [title, setTitle] = useState('');
  const [spaceType, setSpaceType] = useState('Coworking & Lounge');
  const [description, setDescription] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [city, setCity] = useState('Bangalore');
  const [pricePerHour, setPricePerHour] = useState(150);
  const [capacity, setCapacity] = useState(6);
  const [amenities, setAmenities] = useState(['High-speed 1Gbps WiFi', 'Smart Keyless Access']);
  const [images, setImages] = useState([
    'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80',
  ]);
  const [instantBookingEnabled, setInstantBookingEnabled] = useState(true);

  // AI & Upload Assistant States
  const [loading, setLoading] = useState(false);
  const [aiAssisting, setAiAssisting] = useState(false);
  const [aiHighlights, setAiHighlights] = useState('');
  const [aiScanning, setAiScanning] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  // Load existing space in edit mode
  useEffect(() => {
    if (isEditMode) {
      const loadSpace = async () => {
        try {
          const res = await spacesApi.getSpace(id);
          const data = res.space || res;
          setTitle(data.title || '');
          setSpaceType(data.space_type || data.category || 'Coworking & Lounge');
          setDescription(data.description || '');
          setAddressLine1(data.address_line1 || data.location || '');
          setCity(data.city || 'Bangalore');
          setPricePerHour(data.price_per_hour ?? data.price ?? 150);
          setCapacity(data.capacity || 6);
          setAmenities(data.amenities || []);
          if (Array.isArray(data.images) && data.images.length > 0) {
            setImages(data.images);
          }
          setInstantBookingEnabled(data.instant_booking_enabled ?? true);
        } catch (err) {
          toastError(err.message || 'Could not load listing for editing.');
        }
      };
      loadSpace();
    }
  }, [id, isEditMode]);

  // AI Listing Assistant: auto-generate title & description
  const handleAiAssist = async () => {
    setAiAssisting(true);
    try {
      const res = await spacesApi.assistListing({
        category: spaceType,
        highlights: aiHighlights || `${spaceType} with high-speed internet and great lighting in ${city}`,
        city,
      });

      if (res.title) setTitle(res.title);
      if (res.description) setDescription(res.description);
      if (Array.isArray(res.amenities) && res.amenities.length > 0) {
        setAmenities((prev) => Array.from(new Set([...prev, ...res.amenities])));
      }
      success('AI generated high-converting title and listing description!');
    } catch (err) {
      toastError(err.message || 'AI Assistant temporarily unavailable.');
    } finally {
      setAiAssisting(false);
    }
  };

  // AI Space Scan: upload room photo and extract spatial traits
  const handleAiScan = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAiScanning(true);
    try {
      const formData = new FormData();
      formData.append('photo', file);

      const res = await spacesApi.aiScan(formData);
      if (res.space_type) setSpaceType(res.space_type);
      if (res.suggested_capacity) setCapacity(res.suggested_capacity);
      if (res.suggested_price) setPricePerHour(res.suggested_price);
      if (Array.isArray(res.detected_amenities)) {
        setAmenities((prev) => Array.from(new Set([...prev, ...res.detected_amenities])));
      }
      if (res.photo_url) {
        setImages((prev) => [res.photo_url, ...prev]);
      }
      success('AI Space Scan complete! Room traits and suggested capacity applied.');
    } catch (err) {
      toastError(err.message || 'Spatial scan failed.');
    } finally {
      setAiScanning(false);
    }
  };

  // Regular photo upload
  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingPhoto(true);
    try {
      const formData = new FormData();
      formData.append('photo', file);

      const res = await spacesApi.uploadPhoto(formData);
      const url = res.url || res.photo_url || res.filename;
      if (url) {
        setImages((prev) => [...prev, url]);
        success('Photo uploaded successfully!');
      }
    } catch (err) {
      toastError(err.message || 'Photo upload failed.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleToggleAmenity = (item) => {
    setAmenities((prev) =>
      prev.includes(item) ? prev.filter((a) => a !== item) : [...prev, item]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        title,
        space_type: spaceType,
        description,
        address_line1: addressLine1,
        city,
        price_per_hour: Number(pricePerHour),
        capacity: Number(capacity),
        amenities,
        images,
        instant_booking_enabled: instantBookingEnabled,
      };

      if (isEditMode) {
        await spacesApi.updateSpace(id, payload);
        success('Listing updated successfully!');
      } else {
        await spacesApi.createSpace(payload);
        success('New space published successfully!');
      }
      navigate('/host');
    } catch (err) {
      toastError(err.message || 'Failed to save space listing.');
    } finally {
      setLoading(false);
    }
  };

  // Pricing calculator projected earnings
  const estimatedHoursPerDay = 4;
  const estimatedMonthlyGross = pricePerHour * estimatedHoursPerDay * 25; // 25 days
  const hostNetMonthly = Math.round(estimatedMonthlyGross * 0.95);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Back & Title */}
      <div>
        <Link
          to="/host"
          className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-primary mb-2 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Host Dashboard</span>
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
          {isEditMode ? 'Edit Physical Space Listing' : 'List a New Space on SpaceLoop'}
        </h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Provide architectural highlights, set hourly pricing, and configure instant arrival PIN access.
        </p>
      </div>

      {/* AI Assistant Quick Tools */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 1. AI Listing Assistant */}
        <div className="p-5 rounded-2xl bg-primary/5 border border-primary/20 space-y-3">
          <div className="flex items-center gap-2 text-primary font-bold text-xs">
            <Sparkles className="w-4 h-4" />
            <span>AI Architectural Listing Assistant</span>
          </div>
          <p className="text-[11px] text-text-secondary">
            Auto-generate an evocative architectural title and description tailored for coworking seekers.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={aiHighlights}
              onChange={(e) => setAiHighlights(e.target.value)}
              placeholder="e.g. Teak wood sunlit terrace, fast WiFi..."
              className="flex-1 px-3 py-1.5 text-xs rounded-xl bg-surface border border-border text-text-primary"
            />
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleAiAssist}
              disabled={aiAssisting}
              className="shrink-0"
            >
              {aiAssisting ? 'Writing...' : 'Generate Copy'}
            </Button>
          </div>
        </div>

        {/* 2. AI Spatial Scan */}
        <div className="p-5 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 space-y-3">
          <div className="flex items-center gap-2 text-indigo-500 font-bold text-xs">
            <Camera className="w-4 h-4" />
            <span>AI Visual Spatial Scan</span>
          </div>
          <p className="text-[11px] text-text-secondary">
            Upload a room photograph to auto-classify category, lighting, and suggested seating capacity.
          </p>
          <label className="inline-flex items-center justify-center gap-2 w-full px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold cursor-pointer transition-colors">
            <Upload className="w-3.5 h-3.5" />
            <span>{aiScanning ? 'Scanning Acoustics & Capacity...' : 'Upload Photo for AI Scan'}</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleAiScan}
              disabled={aiScanning}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Main Listing Form */}
      <form onSubmit={handleSubmit} className="p-8 rounded-3xl bg-surface border border-border space-y-6 shadow-sm">
        {/* Title */}
        <div>
          <label className="block text-xs font-bold text-text-secondary mb-1">Space Title</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. The Glass Loft Pavilion & Terrace"
            className="w-full px-4 py-2.5 text-sm rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary font-medium"
          />
        </div>

        {/* Category & City */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-text-secondary mb-1">Space Category</label>
            <select
              value={spaceType}
              onChange={(e) => setSpaceType(e.target.value)}
              className="w-full px-4 py-2.5 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-text-secondary mb-1">City Hub</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full px-4 py-2.5 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
            >
              <option value="Bangalore">Bangalore (Silicon Hub)</option>
              <option value="Mumbai">Mumbai (Financial District)</option>
              <option value="Delhi NCR">Delhi NCR / Gurugram</option>
              <option value="Hyderabad">Hyderabad (HITEC City)</option>
              <option value="Pune">Pune (Tech Park)</option>
            </select>
          </div>
        </div>

        {/* Address */}
        <div>
          <label className="block text-xs font-bold text-text-secondary mb-1">
            Street Address / Landmark (For Geofencing)
          </label>
          <div className="relative">
            <MapPin className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              required
              value={addressLine1}
              onChange={(e) => setAddressLine1(e.target.value)}
              placeholder="e.g. 100 Feet Rd, Indiranagar, Near Metro Station"
              className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-bold text-text-secondary mb-1">
            Architectural & Spatial Description
          </label>
          <textarea
            rows={4}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the atmosphere, noise levels, seating ergonomics, natural light, and access details..."
            className="w-full p-3.5 text-xs rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary leading-relaxed"
          />
        </div>

        {/* Pricing & Capacity with Dynamic Pricing Calculator */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-text-secondary mb-1">
              Hourly Price (₹ INR / Hour)
            </label>
            <div className="relative">
              <DollarSign className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="number"
                min={20}
                max={5000}
                required
                value={pricePerHour}
                onChange={(e) => setPricePerHour(Number(e.target.value))}
                className="w-full pl-10 pr-4 py-2.5 text-sm font-extrabold rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-text-secondary mb-1">
              Guest Capacity (Max Seats)
            </label>
            <div className="relative">
              <Users className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="number"
                min={1}
                max={100}
                required
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                className="w-full pl-10 pr-4 py-2.5 text-sm font-extrabold rounded-xl bg-surface-elevated border border-border text-text-primary focus:outline-none focus:border-primary"
              />
            </div>
          </div>
        </div>

        {/* Pricing Calculator Live Insight */}
        <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-xs space-y-1.5">
          <div className="flex justify-between items-center text-text-secondary">
            <span>Projected Monthly Gross (at 4 hrs/day, 25 days):</span>
            <strong className="text-text-primary">₹{estimatedMonthlyGross.toLocaleString('en-IN')}</strong>
          </div>
          <div className="flex justify-between items-center text-emerald-600 dark:text-emerald-400 font-semibold">
            <span>Host Net Payout (after 5% SpaceLoop fee):</span>
            <strong>₹{hostNetMonthly.toLocaleString('en-IN')} / month</strong>
          </div>
        </div>

        {/* Amenities Selection */}
        <div>
          <label className="block text-xs font-bold text-text-secondary mb-2">
            Verified Amenities & Equipment
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {COMMON_AMENITIES.map((item) => {
              const checked = amenities.includes(item);
              return (
                <button
                  key={item}
                  type="button"
                  onClick={() => handleToggleAmenity(item)}
                  className={`p-2.5 rounded-xl border text-xs text-left transition-all flex items-center justify-between ${
                    checked
                      ? 'border-primary bg-primary/10 text-primary font-semibold'
                      : 'border-border bg-surface-elevated text-text-secondary hover:border-zinc-400'
                  }`}
                >
                  <span className="truncate">{item}</span>
                  {checked && <CheckCircle2 className="w-3.5 h-3.5 shrink-0 ml-1" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Photo Upload Section */}
        <div>
          <label className="block text-xs font-bold text-text-secondary mb-2">Space Photos</label>
          <div className="flex flex-wrap items-center gap-3">
            {images.map((img, idx) => (
              <div key={idx} className="relative w-24 h-20 rounded-xl overflow-hidden border border-border group">
                <img src={img} alt="Preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => setImages((prev) => prev.filter((_, i) => i !== idx))}
                  className="absolute top-1 right-1 p-1 rounded-md bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity text-[10px]"
                >
                  ✕
                </button>
              </div>
            ))}

            <label className="w-24 h-20 rounded-xl border-2 border-dashed border-border hover:border-primary flex flex-col items-center justify-center text-text-muted hover:text-primary cursor-pointer transition-colors">
              <Upload className="w-4 h-4 mb-1" />
              <span className="text-[10px] font-semibold">{uploadingPhoto ? 'Uploading...' : 'Add Photo'}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                disabled={uploadingPhoto}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Instant Keyless Booking Toggle */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-surface-elevated border border-border">
          <div className="space-y-0.5">
            <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-primary" />
              <span>Instant Arrival PIN Entry</span>
            </span>
            <p className="text-[11px] text-text-secondary">
              Automatically issue 4-digit PINs without manual approval for verified seekers.
            </p>
          </div>
          <input
            type="checkbox"
            checked={instantBookingEnabled}
            onChange={(e) => setInstantBookingEnabled(e.target.checked)}
            className="w-5 h-5 rounded text-primary focus:ring-primary border-border cursor-pointer"
          />
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{loading ? 'Publishing Space...' : isEditMode ? 'Update Space Listing' : 'Publish Space Listing'}</span>
        </Button>
      </form>
    </div>
  );
};

export default HostListingForm;
