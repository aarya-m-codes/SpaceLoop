import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { scrollRevealVariants } from '../../utils/motion';

/**
 * ScrollReveal Component
 * Smoothly reveals child elements as they enter the viewport.
 * Uses subtle fade + upward movement.
 */
export const ScrollReveal = ({
  children,
  className = '',
  delay = 0,
  threshold = 0.15,
  once = true,
}) => {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      variants={scrollRevealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: threshold }}
      custom={delay}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default ScrollReveal;
