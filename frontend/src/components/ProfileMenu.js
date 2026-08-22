import React, { useState } from 'react';
import { Bell, CircleHelp, FileText, LogOut, Menu, Receipt, ShieldCheck, UserRound, X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import api from '../services/api';
import { initials } from './Profile';
import './profileMenu.css';

function ProfileMenu({ user, onProfile, onDashboard, onHistory, onExpenses, onLogout }) {
  const [open, setOpen] = useState(false);
  const [reminders, setReminders] = useState(Boolean(user.email_reminders_enabled));
  const displayName = user.name || user.email;
  const avatar = user.profile_photo_url ? <img src={user.profile_photo_url} alt="" /> : initials(user.name, user.email);

  const updateReminders = async (event) => {
    const enabled = event.target.checked;
    setReminders(enabled);
    try { await api.patch('auth/notification-preferences', { email_reminders_enabled: enabled }); }
    catch { setReminders(!enabled); }
  };

  const closeAnd = (action) => { setOpen(false); action(); };

  return <>
    <div className="user-menu-trigger"><div className="avatar">{avatar}</div><span className="user-name">{displayName}</span><button className="icon-button" aria-label="Open navigation menu" onClick={() => setOpen(true)}><Menu size={22} /></button></div>
    <AnimatePresence>
      {open && <><motion.div className="drawer-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)} /><motion.aside className="profile-drawer" initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={{ type: 'spring', damping: 26, stiffness: 240 }} aria-label="Account navigation">
        <div className="drawer-header"><div><p className="eyebrow">Account</p><h2>Workspace menu</h2></div><button className="icon-button" aria-label="Close navigation menu" onClick={() => setOpen(false)}><X size={22} /></button></div>
        <div className="drawer-profile"><div className="avatar large">{avatar}</div><div><strong>{displayName}</strong><span>{user.email}</span></div></div>
        <nav className="drawer-nav"><button onClick={() => closeAnd(onProfile)}><UserRound size={18} />My Profile</button><button onClick={() => closeAnd(onDashboard)}><FileText size={18} />Compliance Dashboard</button><button onClick={() => closeAnd(onHistory)}><FileText size={18} />History</button><button onClick={() => closeAnd(onExpenses)}><Receipt size={18} />Expense Tracker</button><div className="drawer-section"><div className="drawer-section-title"><Bell size={18} />Notification Preferences</div><label className="drawer-toggle"><span>Email reminders</span><input type="checkbox" checked={reminders} onChange={updateReminders} /></label></div><div className="drawer-section"><div className="drawer-section-title"><CircleHelp size={18} />Help &amp; Support</div><p className="drawer-help">For account or filing questions, contact support@taxmate.ai.</p></div><div className="drawer-section"><div className="drawer-section-title"><ShieldCheck size={18} />Terms &amp; Privacy</div><div className="drawer-links"><a href="/terms">Terms of Service</a><a href="/privacy">Privacy Policy</a></div></div></nav>
        <button className="drawer-logout" onClick={() => closeAnd(onLogout)}><LogOut size={18} />Logout</button>
      </motion.aside></>}
    </AnimatePresence>
  </>;
}

export default ProfileMenu;
