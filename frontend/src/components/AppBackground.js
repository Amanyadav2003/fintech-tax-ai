import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

function AppBackground({ variant = 'subtle', children }) {
  const prefersReducedMotion = useReducedMotion();
  const isVibrant = variant === 'vibrant';

  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-slate-50">
      <motion.div
        aria-hidden="true"
        className={`pointer-events-none absolute -inset-[25%] z-0 bg-[radial-gradient(circle_at_18%_18%,rgba(45,95,139,${isVibrant ? '0.34' : '0.11'}),transparent_34%),radial-gradient(circle_at_78%_20%,rgba(16,185,129,${isVibrant ? '0.22' : '0.08'}),transparent_30%),radial-gradient(circle_at_65%_82%,rgba(30,58,95,${isVibrant ? '0.24' : '0.08'}),transparent_35%)] ${isVibrant ? '' : 'opacity-90'}`}
        animate={prefersReducedMotion ? undefined : { x: ['-2%', '3%', '-2%'], y: ['-1%', '2%', '-1%'], scale: [1, 1.04, 1] }}
        transition={prefersReducedMotion ? undefined : { duration: isVibrant ? 18 : 42, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}

export default AppBackground;
