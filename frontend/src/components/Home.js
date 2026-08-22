import React, { useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, FileText, Landmark, Receipt, ShieldCheck } from 'lucide-react';
import api from '../services/api';
import './home.css';

const needs = [
  ['Form 16', 'Salary, TDS, and employer details.', FileText],
  ['Bank interest certificates', 'Savings and fixed-deposit interest.', Landmark],
  ['80C investment proofs', 'PPF, ELSS, LIC, EPF, and tuition fees.', Receipt],
  ['80D health receipts', 'Premium receipts for health insurance.', ShieldCheck],
  ['Home loan certificate', 'Interest statement for Section 24(b).', FileText],
  ['Rent receipts', 'Keep these for HRA review.', Receipt],
];

function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}`; }

function Home({ user, onStart, onHistory, onViewResult }) {
  const [data, setData] = useState({ latest: null, recent: [], reminders: [] });
  useEffect(() => { Promise.all([api.get('tax/history'), api.get('tax/dashboard')]).then(([history, dashboard]) => { const recent = history.data || []; setData({ latest: recent[0] || null, recent: recent.slice(0, 3), reminders: dashboard.data?.compliance_dashboard?.reminders || [] }); }).catch(() => {}); }, []);
  return <section className="home-page"><div className="home-heading"><div><p className="eyebrow">TaxMate AI</p><h1>Welcome, {user.name || user.email}</h1><p>Keep your filing work organized and ready for the next step.</p></div><button className="primary-action" onClick={onStart}>Start New Analysis <ArrowRight size={18} /></button></div>
    <section className="home-section last-analysis">{data.latest ? <><div><p className="eyebrow">Your last analysis</p><h2>{String(data.latest.recommended_regime || 'new').toUpperCase()} regime recommended</h2><p>Potential savings {money(data.latest.potential_savings)}</p></div><button className="secondary-action" onClick={() => onViewResult(data.latest.filing_id)}>View Details</button></> : <><div><p className="eyebrow">Your first analysis</p><h2>Your tax picture starts here.</h2><p>Enter your income and deductions to see a personalized comparison.</p></div><button className="secondary-action" onClick={onStart}>Begin</button></>}</section>
    <section className="home-section"><div className="section-title"><div><p className="eyebrow">Preparation</p><h2>What You'll Need</h2></div><span>Informational only</span></div><div className="needs-grid">{needs.map(([title, text, Icon]) => <article className="need-card" key={title}><Icon size={20} /><h3>{title}</h3><p>{text}</p></article>)}</div></section>
    <div className="home-columns"><section className="home-section"><div className="section-title"><div><p className="eyebrow">Your workspace</p><h2>Recent Activity</h2></div><button className="text-action" onClick={onHistory}>View History <ArrowRight size={15} /></button></div>{data.recent.length ? <div className="activity-list">{data.recent.map(item => <button key={item.filing_id} className="activity-row" onClick={() => onViewResult(item.filing_id)}><span>{new Date(item.created_at).toLocaleDateString('en-IN')}</span><strong>{String(item.recommended_regime || 'new').toUpperCase()}</strong><span>{money(item.potential_savings)} saved</span></button>)}</div> : <p className="empty-copy">Completed analyses will appear here.</p>}</section><section className="home-section"><div className="section-title"><div><p className="eyebrow">Stay on track</p><h2>Upcoming Deadlines</h2></div><CalendarDays size={20} /></div><div className="deadline-list">{data.reminders.map(reminder => <div key={reminder.id}><strong>{reminder.title}</strong><span>{reminder.due_date}</span><p>{reminder.description}</p></div>)}</div></section></div>
  </section>;
}
export default Home;
