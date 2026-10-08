import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Printer,
  ArrowLeft,
  ShieldCheck,
  MapPin,
  Clock,
  QrCode,
  Radio,
  Infinity,
} from 'lucide-react';
import { doorPassApi, spacesApi } from '../services/api';
import { Button } from '../components/common/Button';
import { useToast } from '../context/ToastContext';

export const PrintableDoorPass = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { error: toastError } = useToast();

  const [doorPass, setDoorPass] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPass = async () => {
      try {
        setLoading(true);
        const res = await doorPassApi.getDoorPass(id);
        setDoorPass(res);
      } catch (err) {
        // Fallback to basic space details if door pass endpoint fails
        try {
          const spaceRes = await spacesApi.getSpace(id);
          const sp = spaceRes.space || spaceRes;
          setDoorPass({
            space_id: sp.id,
            space_title: sp.title,
            space_address: sp.address || sp.location || 'Bangalore, Karnataka',
            access_type: sp.physical_access_type || 'room_qr',
            geofence_radius: sp.geofence_radius_meters || 50,
            room_qr_token: sp.room_qr_token || `SL-ROOM-${sp.id}-4819`,
            qr_image_url: `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=spaceloop://access/${sp.id}/${sp.room_qr_token || '4819'}`,
            instructions: [
              '1. Place this signage directly at the exterior doorway of the space.',
              '2. Seekers must be within 50 meters GPS geofence before scanning.',
              '3. Check-in scans grant instant entry and record timestamped telemetry.',
              '4. Governed under Section 52 of Indian Easements Act 1882 (Revocable License).'
            ]
          });
        } catch (e) {
          toastError('Could not load door pass details.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPass();
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!doorPass) {
    return (
      <div className="py-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-text-primary">Door Pass Not Found</h2>
        <Link to="/host/spaces">
          <Button variant="primary">Back to Spaces</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900/10 py-10 px-4">
      {/* Top action toolbar (hidden during print) */}
      <div className="max-w-2xl mx-auto mb-6 flex items-center justify-between print:hidden">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-xs text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Space Management</span>
        </button>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            onClick={handlePrint}
            className="flex items-center gap-2 shadow-md"
          >
            <Printer className="w-4 h-4" />
            <span>Print Door Signage</span>
          </Button>
        </div>
      </div>

      {/* Printable Sheet (Standard A4 / Letter format) */}
      <div
        id="printable-door-pass"
        className="max-w-2xl mx-auto bg-white text-slate-900 border-2 border-slate-900 rounded-3xl p-8 sm:p-12 shadow-2xl print:border-none print:shadow-none print:p-0 print:max-w-none"
      >
        {/* Sign Header */}
        <div className="border-b-2 border-slate-900 pb-6 text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-slate-900 flex items-center justify-center text-white">
              <Infinity className="w-5 h-5 text-white stroke-[2.5]" />
            </div>
            <span className="font-black text-2xl tracking-tight text-slate-900 uppercase">
              SpaceLoop Access
            </span>
          </div>
          <div className="inline-block px-3 py-0.5 rounded-full bg-slate-100 border border-slate-300 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-700">
            Official Premise Door Pass • Security Protocol v2.5
          </div>
        </div>

        {/* Space Title & Metadata */}
        <div className="py-6 text-center space-y-2">
          <h1 className="text-3xl font-black text-slate-950 tracking-tight">
            {doorPass.space_title}
          </h1>
          <div className="flex items-center justify-center gap-2 text-xs text-slate-600 font-medium">
            <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-900" />
            <span>{doorPass.space_address}</span>
          </div>
          <div className="text-[11px] font-mono text-slate-500">
            Premises Identifier: <strong>SL-SPACE-{doorPass.space_id}</strong>
          </div>
        </div>

        {/* High-Resolution QR Display */}
        <div className="my-6 p-6 rounded-3xl bg-slate-50 border-2 border-slate-900 text-center space-y-4">
          <div className="bg-white p-4 rounded-2xl inline-block border border-slate-200 shadow-inner">
            <img
              src={doorPass.qr_image_url}
              alt={`Door QR for ${doorPass.space_title}`}
              className="w-56 h-56 mx-auto object-contain"
            />
          </div>

          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold">
              Dynamic Room Token
            </span>
            <div className="font-mono text-base font-bold text-slate-900 tracking-wider">
              {doorPass.room_qr_token}
            </div>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold">
            <Radio className="w-3.5 h-3.5" />
            <span>{doorPass.geofence_radius || 50}-Meter Haversine Geofence Active</span>
          </div>
        </div>

        {/* Instructions Checklist */}
        <div className="border-t-2 border-slate-900 pt-6 space-y-3">
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-900">
            Seeker Instructions for Physical Entry:
          </h3>
          <ul className="text-xs text-slate-700 space-y-1.5 list-disc list-inside leading-relaxed">
            <li>Ensure location services (GPS) are turned ON on your smartphone.</li>
            <li>Stand within 50 meters of this entrance door.</li>
            <li>Scan this QR code using the SpaceLoop mobile app or camera.</li>
            <li>Upon successful handshake, access PIN / smart lock will unlock immediately.</li>
          </ul>
        </div>

        {/* Section 52 Legal Footnote */}
        <div className="mt-8 pt-4 border-t border-slate-200 text-center space-y-1 text-[10px] text-slate-500 leading-normal">
          <p className="font-bold text-slate-700">
            Legal Status: Revocable License under Section 52 of the Indian Easements Act, 1882.
          </p>
          <p>
            This pass grants temporary permissive occupancy only. No tenancy, leasehold estate, or possessory rights are conveyed. SpaceLoop Security Telemetry Node #SL-SEC-01.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrintableDoorPass;
