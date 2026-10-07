/**
 * SpaceLoop Motion Foundation
 * Reusable Framer Motion variants & easing curves.
 * Respects performance and natural easing principles.
 */

// Premium natural easing curve: smooth entry, gradual deceleration
export const EASING_NATURAL = [0.16, 1, 0.3, 1];
export const EASING_SMOOTH = [0.4, 0, 0.2, 1];

// 1. Page Transitions: subtle fade + slight vertical shift, no dramatic zoom
export const pageVariants = {
  initial: {
    opacity: 0,
    y: 8,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.28,
      ease: EASING_NATURAL,
    },
  },
  exit: {
    opacity: 0,
    y: -6,
    transition: {
      duration: 0.18,
      ease: EASING_SMOOTH,
    },
  },
};

// 2. Scroll Reveal Variants (Fade + upward reveal)
export const scrollRevealVariants = {
  hidden: {
    opacity: 0,
    y: 16,
  },
  visible: (custom = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.42,
      delay: custom * 0.07,
      ease: EASING_NATURAL,
    },
  }),
};

// 3. Staggered Container for Grids and Lists
export const staggerContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

// 4. Space Card Interactive Gestures
export const cardHoverMotion = {
  rest: {
    y: 0,
    scale: 1,
    transition: { duration: 0.25, ease: EASING_NATURAL },
  },
  hover: {
    y: -4,
    scale: 1.01,
    transition: { duration: 0.25, ease: EASING_NATURAL },
  },
};

// 5. Card Image Gentle Zoom
export const cardImageMotion = {
  rest: {
    scale: 1,
    transition: { duration: 0.4, ease: EASING_NATURAL },
  },
  hover: {
    scale: 1.045,
    transition: { duration: 0.4, ease: EASING_NATURAL },
  },
};

// 6. Button Interactive Feedback (Micro-interaction)
export const buttonFeedbackMotion = {
  whileHover: { y: -1, transition: { duration: 0.15, ease: EASING_NATURAL } },
  whileTap: { scale: 0.98, y: 1, transition: { duration: 0.1, ease: EASING_NATURAL } },
};

// 7. Navigation Drawer Animation (Mobile)
export const mobileMenuVariants = {
  closed: {
    opacity: 0,
    height: 0,
    transition: { duration: 0.22, ease: EASING_SMOOTH },
  },
  open: {
    opacity: 1,
    height: 'auto',
    transition: { duration: 0.28, ease: EASING_NATURAL },
  },
};
