import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * Button Component
 * Polished interactive button with restrained micro-interactions.
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  icon: Icon,
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();

  const baseStyles =
    'relative inline-flex items-center justify-center font-medium transition-colors rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 h-8',
    md: 'text-sm px-4 py-2.5 gap-2 h-10',
    lg: 'text-base px-6 py-3.5 gap-2.5 h-12',
  };

  const variantStyles = {
    primary:
      'bg-primary hover:bg-primary-hover text-white shadow-sm hover:shadow-md border border-transparent',
    secondary:
      'bg-surface-elevated hover:bg-border/60 text-text-primary border border-border shadow-sm',
    outline:
      'bg-transparent hover:bg-surface-elevated text-text-primary border border-border hover:border-primary/50',
    ghost:
      'bg-transparent hover:bg-surface-elevated text-text-secondary hover:text-text-primary',
  };

  const motionProps = shouldReduceMotion
    ? {}
    : {
        whileHover: disabled || loading ? {} : { y: -1 },
        whileTap: disabled || loading ? {} : { scale: 0.98, y: 1 },
        transition: { duration: 0.14, ease: [0.16, 1, 0.3, 1] },
      };

  return (
    <motion.button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${
        variantStyles[variant] || variantStyles.primary
      } ${className}`}
      {...motionProps}
      {...props}
    >
      {loading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : Icon ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}
      <span>{children}</span>
    </motion.button>
  );
};

export default Button;
