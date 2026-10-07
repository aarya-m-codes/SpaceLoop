import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Compass } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFound = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-surface-elevated text-primary flex items-center justify-center mb-4 border border-border">
        <Compass className="w-8 h-8" />
      </div>
      <h1 className="text-4xl font-extrabold text-text-primary tracking-tight">404</h1>
      <h2 className="text-lg font-semibold text-text-primary mt-2">Space Not Found</h2>
      <p className="text-sm text-text-secondary max-w-sm mt-1 mb-6">
        The architectural listing or page you are looking for does not exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="primary" icon={ArrowLeft}>
          Return Home
        </Button>
      </Link>
    </div>
  );
};

export default NotFound;
