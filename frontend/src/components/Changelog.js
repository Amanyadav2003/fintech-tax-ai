import React, { useEffect, useState } from 'react';
import { ArrowLeft, Check, History as HistoryIcon, RefreshCw } from 'lucide-react';
import './changelog.css';

import { CURRENT_VERSION, latestUpdate, markLatestUpdateRead, updates } from '../data/updates';

function ChangeGroup({ label, changes }) {
  if (!changes.length) return null;
  return <div className="update-group"><h3>{label}</h3><div className="update-items">{changes.map(change => <article key={change.title}><Check size={16} /><div><h4>{change.title}</h4><p>{change.description}</p></div></article>)}</div></div>;
}

function UpdateDetails({ update }) {
  return <div className="update-details"><div className="update-copy"><p className="update-version">v{update.version} <span>{update.releaseDate}</span></p><h2>{update.title}</h2><p>{update.description}</p></div><ChangeGroup label="NEW" changes={update.newFeatures} /><ChangeGroup label="IMPROVED" changes={update.improvements} /><ChangeGroup label="FIXED" changes={update.fixes} /></div>;
}

function Changelog({ onBack }) {
  const [checkState, setCheckState] = useState('idle');

  useEffect(() => {
    markLatestUpdateRead();
  }, []);

  const checkForUpdates = () => {
    setCheckState('checking');
    window.setTimeout(() => setCheckState(latestUpdate.version > CURRENT_VERSION ? 'available' : 'current'), 350);
  };

  const updateNow = () => {
    const separator = window.location.search ? '&' : '?';
    window.location.assign(`${window.location.pathname}${window.location.search}${separator}update=${Date.now()}${window.location.hash}`);
  };

  return <section className="changelog-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Home</button><div className="changelog-heading"><HistoryIcon size={22} /><div><p className="eyebrow">TaxMate AI</p><h1>What's New</h1></div></div><p className="changelog-intro">Stay up to date with the latest TaxMate AI improvements.</p><div className="update-toolbar"><p>Current version <strong>v{CURRENT_VERSION}</strong></p><button type="button" className="update-check-button" onClick={checkForUpdates} disabled={checkState === 'checking'}><RefreshCw size={16} className={checkState === 'checking' ? 'spin' : ''} />{checkState === 'checking' ? 'Checking for updates...' : 'Check for updates'}</button></div>{checkState === 'current' && <div className="update-status" role="status"><strong>You're up to date.</strong><span>You're using the latest version of TaxMate AI.</span></div>}{checkState === 'available' && <div className="update-status update-available" role="status"><strong>New update available!</strong><span>TaxMate AI v{latestUpdate.version} is now available.</span><button type="button" onClick={updateNow}>Update now</button></div>}<div className="latest-label">LATEST UPDATE</div><UpdateDetails update={latestUpdate} /><div className="older-updates">{updates.slice(1).map(update => <UpdateDetails key={update.version} update={update} />)}</div></section>;
}
export default Changelog;
