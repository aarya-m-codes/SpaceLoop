import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Heart, Globe, ArrowUpRight, Infinity } from 'lucide-react';
import { LanguageSelector } from './LanguageSelector';

export const Footer = () => {
  return (
    <footer className="w-full bg-surface border-t border-border mt-auto transition-colors duration-250">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand Info */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm">
                <Infinity className="w-4 h-4 text-white stroke-[2.5]" />
              </div>
              <span className="font-bold text-lg text-text-primary tracking-tight">
                SpaceLoop
              </span>
            </Link>
            <p className="text-sm text-text-secondary leading-relaxed">
              On-demand micro-leases for creative studios, focus pods, and workspaces. Governed under Section 52 of the Indian Easements Act 1882.
            </p>
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>DigiLocker KYC & 50m Haversine Perimeter</span>
            </div>
          </div>

          {/* Explore Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Explore
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/explore" className="text-text-secondary hover:text-primary transition-colors">
                  All Flexible Workspaces
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="text-text-secondary hover:text-primary transition-colors">
                  How It Works
                </Link>
              </li>
              <li>
                <Link to="/bookings" className="text-text-secondary hover:text-primary transition-colors">
                  Active Bookings & PINs
                </Link>
              </li>
              <li>
                <Link to="/verify" className="text-text-secondary hover:text-primary transition-colors">
                  Student & Seeker Verification
                </Link>
              </li>
            </ul>
          </div>

          {/* Hosting & Monetization */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Host With Us
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/host/spaces/new" className="text-text-secondary hover:text-primary transition-colors">
                  List Your Space
                </Link>
              </li>
              <li>
                <Link to="/calculator" className="text-text-secondary hover:text-primary transition-colors">
                  Earnings Calculator
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="text-text-secondary hover:text-primary transition-colors">
                  How It Works
                </Link>
              </li>
              <li>
                <Link to="/host/verification" className="text-text-secondary hover:text-primary transition-colors">
                  Discom CA Meter Check
                </Link>
              </li>
              <li>
                <Link to="/host" className="text-text-secondary hover:text-primary transition-colors">
                  Host Management Portal
                </Link>
              </li>
            </ul>
          </div>

          {/* Company & Architecture */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Platform & Architecture
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/architecture" className="text-text-secondary hover:text-primary transition-colors">
                  System Architecture & Team
                </Link>
              </li>
              <li>
                <Link to="/trust-safety" className="text-text-secondary hover:text-primary transition-colors">
                  Trust & Safety Protocol (Sec 52)
                </Link>
              </li>
              <li>
                <Link to="/explore" className="text-text-secondary hover:text-primary transition-colors">
                  Browse Workspaces
                </Link>
              </li>
              <li>
                <Link to="/admin" className="text-text-secondary hover:text-primary transition-colors">
                  Governance Admin
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <p>© {new Date().getFullYear()} SpaceLoop Platform. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <LanguageSelector />
            <span className="font-mono font-semibold text-text-secondary">₹ INR (UPI)</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
