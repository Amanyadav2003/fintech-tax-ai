import React from 'react';
import { CheckCircle2, ShieldCheck } from 'lucide-react';
import './profile.css';

function initials(name, email) {
  const source = (name || email || '?').trim();
  return source.split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
}

function Profile({ user }) {
  const maskedPan = user.pan ? `${user.pan.slice(0, 5)}****${user.pan.slice(-1)}` : 'Not provided';
  const memberSince = user.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Unavailable';

  return (
    <section className="profile-page">
      <div className="profile-hero">
        <div className="profile-avatar large">{user.profile_photo_url ? <img src={user.profile_photo_url} alt="Profile" /> : initials(user.name, user.email)}</div>
        <div><p className="eyebrow">My Profile</p><h1>{user.name || user.email}</h1><p className="profile-email">{user.email}</p><p className="member-since">Member since {memberSince}</p></div>
      </div>
      <div className="profile-grid">
        <div className="profile-card"><h2>Personal details</h2><dl><div><dt>Full name</dt><dd>{user.name || 'Not provided'}</dd></div><div><dt>Email</dt><dd>{user.email}</dd></div><div><dt>Phone number</dt><dd>{user.phone || 'Not provided'}</dd></div><div><dt>PAN</dt><dd>{maskedPan}</dd></div><div><dt>Age</dt><dd>{user.age || 'Not provided'}</dd></div></dl></div>
        <div className="profile-card"><h2>Filing details</h2><dl><div><dt>Employment type</dt><dd>{user.employment_type || 'Not provided'}</dd></div><div><dt>Employer / company</dt><dd>{user.employer_name || 'Not provided'}</dd></div><div><dt>Financial year</dt><dd>{user.financial_year || 'Not provided'}</dd></div><div><dt>PAN-Aadhaar linked</dt><dd>{user.pan_aadhaar_linked ? 'Yes' : 'No'}</dd></div><div><dt>Email reminders</dt><dd>{user.email_reminders_enabled ? 'Enabled' : 'Disabled'}</dd></div></dl></div>
      </div>
      <div className="profile-card security-card"><h2><ShieldCheck size={20} /> Account Security</h2><div className="security-badges"><span><CheckCircle2 size={16} /> Email verified</span><span><CheckCircle2 size={16} /> Two-factor login (OTP) enabled</span></div></div>
    </section>
  );
}

export { initials };
export default Profile;
