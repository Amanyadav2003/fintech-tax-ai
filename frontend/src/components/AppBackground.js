import React, { useMemo } from 'react';

const taxChips = [
  ['Section 80C', '₹1.5L'],
  ['Standard deduction', '₹75,000'],
  ['87A rebate', 'Active'],
  ['HRA', 'Exempt'],
  ['NPS 80CCD', '₹50K'],
];

const createCoinStyle = () => {
  const scale = 0.6 + Math.random() * 0.8;
  const duration = 12 + Math.random() * 10;

  return {
    left: `${Math.random() * 96}%`,
    width: `${34 * scale}px`,
    height: `${34 * scale}px`,
    fontSize: `${16 * scale}px`,
    animationDuration: `${duration}s`,
    animationDelay: `-${Math.random() * duration}s`,
    '--coin-static-top': `${10 + Math.random() * 80}%`,
  };
};

function AppBackground({ variant = 'subtle', children }) {
  const isVibrant = variant === 'vibrant';
  const coins = useMemo(() => Array.from({ length: 14 }, createCoinStyle), []);

  return (
    <div className={`app-background app-background-${variant} relative isolate min-h-screen overflow-hidden bg-slate-50`}>
      <div className="aurora" aria-hidden="true"><i /><i /><i /></div>
      <div className="fx" aria-hidden="true">
        <div className="orbit"><i /><i /></div>
        {isVibrant && taxChips.map(([label, value], index) => (
          <span className={`chip c${index + 1}`} key={label}>{label} <b>{value}</b></span>
        ))}
        {coins.map((style, index) => <span className="coin" key={index} style={style}>₹</span>)}
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}

export default AppBackground;
