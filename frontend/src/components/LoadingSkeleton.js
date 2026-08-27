import React from 'react';
import './loadingSkeleton.css';

function LoadingSkeleton({ lines = 4 }) {
  return <div className="loading-skeleton" aria-label="Loading"><span className="skeleton-title" />{Array.from({ length: lines }, (_, index) => <span className="skeleton-line" key={index} />)}</div>;
}
export default LoadingSkeleton;
