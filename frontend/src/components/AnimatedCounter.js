import React, { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

function AnimatedCounter({ target = 0 }) {
  const [value, setValue] = useState(0);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    const numericTarget = Number(target) || 0;
    if (prefersReducedMotion) {
      setValue(numericTarget);
      return undefined;
    }

    const duration = 900;
    const startedAt = performance.now();
    let animationFrame;
    const tick = (now) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(numericTarget * eased);
      if (progress < 1) animationFrame = requestAnimationFrame(tick);
    };
    animationFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrame);
  }, [target, prefersReducedMotion]);

  const displayValue = Number.isInteger(Number(target)) ? Math.round(value) : value.toFixed(2);
  return <motion.span initial={prefersReducedMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }}>{displayValue}</motion.span>;
}

export default AnimatedCounter;
