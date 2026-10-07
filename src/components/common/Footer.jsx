import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Heart, Globe, ArrowUpRight } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="w-full bg-surface border-t border-border mt-auto transition-colors duration-250">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand Info */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-base shadow-sm">
                SL
              </div>
              <span className="font-bold text-lg text-text-primary tracking-tight">
                SpaceLoop
              </span>
            </Link>
            <p className="text-sm text-text-secondary leading-relaxed">
              Discover and access flexible architectural workspaces, studios, and meeting venues on demand.
            </p>
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <ShieldCheck className="w-4 h-4 text-primary shrink-0" />
              <span>Verified Hosts & Secure Digital Access</span>
            </div>
          </div>

          {/* Explore Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Explore
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/explore?category=coworking" className="text-text-secondary hover:text-primary transition-colors">
                  Coworking Spaces
                </Link>
              </li>
              <li>
                <Link to="/explore?category=studios" className="text-text-secondary hover:text-primary transition-colors">
                  Creative Studios
                </Link>
              </li>
              <li>
                <Link to="/explore?category=meeting" className="text-text-secondary hover:text-primary transition-colors">
                  Meeting Rooms
                </Link>
              </li>
              <li>
                <Link to="/explore?category=rooftop" className="text-text-secondary hover:text-primary transition-colors">
                  Rooftops & Lounges
                </Link>
              </li>
            </ul>
          </div>

          {/* Hosting */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Host With Us
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/host" className="text-text-secondary hover:text-primary transition-colors">
                  List Your Space
                </Link>
              </li>
              <li>
                <Link to="/host/earnings" className="text-text-secondary hover:text-primary transition-colors">
                  Host Earnings Calculator
                </Link>
              </li>
              <li>
                <Link to="/safety" className="text-text-secondary hover:text-primary transition-colors">
                  SpaceLoop Protection
                </Link>
              </li>
              <li>
                <Link to="/resources" className="text-text-secondary hover:text-primary transition-colors">
                  Host Resources
                </Link>
              </li>
            </ul>
          </div>

          {/* Company & Legal */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Company
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/about" className="text-text-secondary hover:text-primary transition-colors">
                  About SpaceLoop
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-text-secondary hover:text-primary transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-text-secondary hover:text-primary transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link to="/help" className="text-text-secondary hover:text-primary transition-colors">
                  Help Center
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <p>© {new Date().getFullYear()} SpaceLoop Inc. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5" />
              <span>English (US)</span>
            </span>
            <span>$ USD</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
