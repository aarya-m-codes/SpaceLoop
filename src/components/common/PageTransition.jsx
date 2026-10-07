import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { pageVariants } from '../../utils/motion';

/**
 * PageTransition Component
 * Wraps routes to provide smooth, subtle page transitions.
 * Automatically disables or simplifies motion if the user prefers reduced motion.
 */
export const PageTransition = ({ children, className = '' }) => {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <div className={`w-full ${className}`}>{children}</div>;
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`w-full ${className}`}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
