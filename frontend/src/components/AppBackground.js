import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

function AppBackground({ variant = 'subtle', children }) {
  const prefersReducedMotion = useReducedMotion();
  const isVibrant = variant === 'vibrant';

  return (
    <div className={`app-background app-background-${variant} relative isolate min-h-screen overflow-hidden bg-slate-50`}>
      <div className="ambient-effects" aria-hidden="true">
        <div className="ambient-orbit"><i /><i /></div>
        {Array.from({ length: 12 }, (_, index) => <span className="ambient-coin" key={index}>₹</span>)}
      </div>
      <motion.div
        aria-hidden="true"
        className={`app-background-glow pointer-events-none absolute -inset-[25%] z-0 ${isVibrant ? '' : 'opacity-90'}`}
        animate={prefersReducedMotion ? undefined : { x: ['-2%', '3%', '-2%'], y: ['-1%', '2%', '-1%'], scale: [1, 1.04, 1] }}
        transition={prefersReducedMotion ? undefined : { duration: isVibrant ? 18 : 42, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}

export default AppBackground;
