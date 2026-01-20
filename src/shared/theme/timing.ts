/**
 * Animation Timing Constants
 * Consistent timing for micro-animations
 */

export const timing = {
  // Durations (ms)
  instant: 100,
  fast: 200,
  normal: 300,
  slow: 500,
  slower: 700,

  // Spring configs for Reanimated
  spring: {
    // Snappy - for buttons, toggles
    snappy: {
      damping: 20,
      stiffness: 300,
      mass: 0.8,
    },
    // Bouncy - for playful elements
    bouncy: {
      damping: 10,
      stiffness: 180,
      mass: 0.5,
    },
    // Gentle - for page transitions
    gentle: {
      damping: 25,
      stiffness: 120,
      mass: 1,
    },
    // Smooth - for subtle animations
    smooth: {
      damping: 30,
      stiffness: 200,
      mass: 1,
    },
  },
} as const;

export type Timing = typeof timing;
